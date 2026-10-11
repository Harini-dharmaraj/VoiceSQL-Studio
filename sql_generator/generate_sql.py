import os
import re
import requests
import json
from utils.config_manager import load_config
from database.db_connection import get_db_schema_context
from sql_generator.semantic_matcher import semantic_vector_engine
from sql_generator.query_normalizer import normalize_colloquial_query

_local_generator = None

def get_local_generator():
    """Lazily load the local Transformers pipeline to optimize startup memory and speed."""
    global _local_generator
    if _local_generator is None:
        from transformers import pipeline
        model_path = "saved_model" if (os.path.isdir("saved_model") and os.path.exists(os.path.join("saved_model", "config.json"))) else "google/flan-t5-small"
        _local_generator = pipeline(
            "text2text-generation",
            model=model_path
        )
    return _local_generator

def clean_sql_string(sql: str) -> str:
    """Strip markdown backticks, explanations, and trailing characters to clean the SQL query."""
    sql = re.sub(r'```(?:sql)?', '', sql, flags=re.IGNORECASE)
    sql = sql.replace("```", "").strip()

    lines = [line.strip() for line in sql.split('\n') if line.strip()]
    cleaned_lines = []
    found_sql = False
    for l in lines:
        if any(l.upper().startswith(p) for p in ["SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN", "FROM", "WHERE", "JOIN", "ORDER", "GROUP", "LIMIT", "HAVING"]):
            found_sql = True
            cleaned_lines.append(l)
        elif found_sql and not any(p in l.lower() for p in ["here is", "this query", "note:", "explanation:"]):
            cleaned_lines.append(l)

    if cleaned_lines:
        sql = " ".join(cleaned_lines)
    else:
        sql = " ".join(lines)

    sql = " ".join(sql.split())
    if not sql.endswith(";") and sql:
        sql += ";"
    return sql

def classify_query_complexity(sql: str, question: str = "") -> dict:
    """
    ML/NLP Query Complexity Classifier:
    Analyzes relational depth, aggregation operators, and logical predicates to classify query complexity.
    Categories: Simple (🟢), Medium (🟡), Complex (🔴).
    """
    if not sql:
        return {"level": "Unknown", "badge": "⚪ Unknown", "tag": "Unclassified", "reason": "No SQL generated."}

    sql_u = sql.upper()
    has_join = "JOIN" in sql_u
    join_count = sql_u.count("JOIN")
    has_group = "GROUP BY" in sql_u
    has_agg = any(fn in sql_u for fn in ["COUNT(", "AVG(", "SUM(", "MAX(", "MIN("])
    has_subquery = sql_u.count("SELECT") > 1
    has_where = "WHERE" in sql_u

    if join_count >= 2 or has_subquery:
        return {
            "level": "Complex",
            "badge": "🔴 Complex",
            "tag": "Multi-Table Relational JOIN",
            "reason": f"Requires joining {join_count + 1} relational tables with foreign-key traversal."
        }
    elif has_join or (has_group and has_agg):
        return {
            "level": "Medium",
            "badge": "🟡 Medium",
            "tag": "Relational Aggregation / Join",
            "reason": "Performs mathematical grouping or single foreign-key cross-table join."
        }
    elif has_agg:
        return {
            "level": "Medium",
            "badge": "🟡 Medium",
            "tag": "Statistical Aggregation",
            "reason": "Calculates summary metrics (SUM/AVG/COUNT) across tabular columns."
        }
    elif has_where:
        return {
            "level": "Simple",
            "badge": "🟢 Simple",
            "tag": "Filtered Retrieval",
            "reason": "Direct single-table projection with conditional WHERE filter."
        }
    else:
        return {
            "level": "Simple",
            "badge": "🟢 Simple",
            "tag": "Direct Projection",
            "reason": "Direct table scan or sorted top-K retrieval without joins."
        }

def explain_sql_query(sql: str) -> str:
    """
    Explainable AI (XAI) Engine:
    Translates compiled SQL queries into clear, human-understandable English explanation.
    """
    if not sql:
        return "No query available to explain."

    sql_u = sql.upper()
    steps = []

    # 1. Target table(s)
    tables = []
    for t in ["MOVIES", "DIRECTORS", "ACTORS", "MOVIE_CAST", "REVIEWS"]:
        if f" {t} " in f" {sql_u} ":
            tables.append(t.title())

    if tables:
        steps.append(f"Queries the **{', '.join(tables)}** table(s)")
    else:
        steps.append("Retrieves data from the connected database")

    # 2. Joins
    if "JOIN" in sql_u:
        steps.append("links related records across tables using relational foreign keys")

    # 3. Aggregations
    if "COUNT(" in sql_u:
        steps.append("calculates the total count of matching records")
    elif "AVG(" in sql_u:
        steps.append("computes the average numerical value")
    elif "SUM(" in sql_u:
        steps.append("calculates the cumulative sum")

    # 4. Filters
    if "WHERE" in sql_u:
        # Extract condition snippet
        match = re.search(r'WHERE\s+(.*?)(?:GROUP|ORDER|LIMIT|;|$)', sql, re.IGNORECASE)
        if match:
            cond = match.group(1).strip()
            steps.append(f"applies the filter condition (`{cond}`)")
        else:
            steps.append("filters the dataset based on your query criteria")

    # 5. Grouping
    if "GROUP BY" in sql_u:
        steps.append("groups identical values into summary rows")

    # 6. Sorting & Limits
    if "ORDER BY" in sql_u:
        if "DESC" in sql_u:
            steps.append("sorts results in descending order (highest first)")
        else:
            steps.append("sorts results in ascending order")

    if "LIMIT" in sql_u:
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_u)
        limit_val = limit_match.group(1) if limit_match else "specific"
        steps.append(f"restricts the response to the top {limit_val} items")

    return "; then ".join(steps).capitalize() + "."

GENRE_MAP = {
    'sci-fi': 'Sci-Fi', 'scifi': 'Sci-Fi', 'science fiction': 'Sci-Fi',
    'action': 'Action', 'crime': 'Crime', 'biography': 'Biography',
    'war': 'War', 'western': 'Western', 'romance': 'Romance',
    'comedy': 'Comedy', 'drama': 'Drama', 'animation': 'Animation',
    'thriller': 'Thriller', 'fantasy': 'Fantasy'
}

def get_active_tables_info() -> dict:
    """Retrieve all current user tables, column definitions, and data types from SQLite or MySQL."""
    try:
        from database.db_connection import get_db_connection
        from utils.config_manager import load_config
        config = load_config()
        conn = get_db_connection()
        cur = conn.cursor()
        tables_meta = {}

        if config.get("db_type") == "SQLite":
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'query_history';")
            tables = [r[0] for r in cur.fetchall()]
            for tbl in tables:
                cur.execute(f"PRAGMA table_info('{tbl}');")
                cols = cur.fetchall()
                col_names = [c[1] for c in cols]
                num_cols = [c[1] for c in cols if any(t in str(c[2]).upper() for t in ['INT', 'REAL', 'FLOAT', 'DOUBLE', 'NUMERIC', 'DECIMAL'])]
                text_cols = [c[1] for c in cols if not any(t in str(c[2]).upper() for t in ['INT', 'REAL', 'FLOAT', 'DOUBLE', 'NUMERIC', 'DECIMAL'])]
                tables_meta[tbl] = {
                    "columns": col_names,
                    "numeric_cols": num_cols,
                    "text_cols": text_cols
                }
        else:
            cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{config.get('mysql_database', 'voice_to_sql')}' AND table_name != 'query_history';")
            tables = [r[0] for r in cur.fetchall()]
            for tbl in tables:
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{config.get('mysql_database', 'voice_to_sql')}' AND table_name = '{tbl}';")
                cols = cur.fetchall()
                col_names = [c[0] for c in cols]
                num_cols = [c[0] for c in cols if any(t in str(c[1]).upper() for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC'])]
                text_cols = [c[0] for c in cols if not any(t in str(c[1]).upper() for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC'])]
                tables_meta[tbl] = {
                    "columns": col_names,
                    "numeric_cols": num_cols,
                    "text_cols": text_cols
                }

        cur.close()
        conn.close()
        return tables_meta
    except Exception:
        return {}

def resolve_custom_table_query(q: str, target_table: str, meta: dict, limit_val: int = None) -> str:
    """
    Generates precision SQL queries for user-uploaded custom datasets / tables
    (e.g., students, products, patients, customers, sales, employees, etc.).
    """
    cols = meta["columns"]
    num_cols = [c for c in meta["numeric_cols"] if not c.lower().endswith("_id") and c.lower() != "id"]
    if not num_cols:
        num_cols = meta["numeric_cols"]
    text_cols = meta["text_cols"]

    lim_str = f" LIMIT {limit_val}" if limit_val else ""
    lim_top = f" LIMIT {limit_val or 5}"

    # 1. Count query
    if any(w in q for w in ["how many", "count", "total count", "number of"]) and not any(w in q for w in ["sum", "average", "avg", "salary", "price", "fee", "cost", "amount", "revenue", "gpa"]):
        return f"SELECT COUNT(*) AS total_{target_table} FROM {target_table};"

    # Match which numeric column is mentioned
    matched_num = None
    for nc in num_cols:
        if nc.lower() in q or nc.lower().replace("_", " ") in q:
            matched_num = nc
            break
    if not matched_num and num_cols:
        matched_num = num_cols[0]

    # Match which text column is mentioned
    matched_text = None
    for tc in text_cols:
        if tc.lower() in q or tc.lower().replace("_", " ") in q:
            matched_text = tc
            break

    # 2. Average calculation
    if "average" in q or "avg" in q:
        if matched_num:
            if any(w in q for w in ["by", "group", "each", "per"]) and text_cols:
                grp_col = matched_text or text_cols[0]
                return f"SELECT {grp_col}, ROUND(AVG({matched_num}), 2) AS avg_{matched_num} FROM {target_table} GROUP BY {grp_col} ORDER BY avg_{matched_num} DESC;"
            return f"SELECT ROUND(AVG({matched_num}), 2) AS avg_{matched_num} FROM {target_table};"

    # 3. Sum / Cumulative Total
    if any(w in q for w in ["sum", "total revenue", "total sales", "total amount", "total cost", "total spending"]):
        if matched_num:
            return f"SELECT ROUND(SUM({matched_num}), 2) AS total_{matched_num} FROM {target_table};"

    # 4. Highest / Top / Maximum / Best / Oldest
    if any(w in q for w in ["highest", "max", "maximum", "top", "best", "most", "oldest", "expensive", "costliest"]):
        if matched_num:
            return f"SELECT * FROM {target_table} ORDER BY {matched_num} DESC{lim_top};"

    # 5. Lowest / Minimum / Least / Cheapest / Youngest
    if any(w in q for w in ["lowest", "min", "minimum", "least", "cheapest", "youngest"]):
        if matched_num:
            return f"SELECT * FROM {target_table} ORDER BY {matched_num} ASC{lim_top};"

    # 6. Numeric threshold filter (e.g., above 50, greater than 100, > 20)
    thresh_match = re.search(r'(?:above|over|greater than|more than|>|>=)\s*(\d+(?:\.\d+)?)', q)
    if thresh_match and matched_num:
        val = thresh_match.group(1)
        return f"SELECT * FROM {target_table} WHERE {matched_num} >= {val}{lim_str};"

    below_match = re.search(r'(?:below|under|less than|<|<=)\s*(\d+(?:\.\d+)?)', q)
    if below_match and matched_num:
        val = below_match.group(1)
        return f"SELECT * FROM {target_table} WHERE {matched_num} <= {val}{lim_str};"

    # 7. Specific entity lookup & column projection (e.g. "Show the gpa of the student Alice Chen")
    requested_cols = [c for c in cols if c.lower() in q or c.lower().replace("_", " ") in q]
    entity_clause = None

    try:
        from database.db_connection import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        
        stopwords = {
            "show", "the", "of", "student", "students", "details", "for", "named", "called",
            "is", "what", "who", "which", "are", "get", "give", "me", "find", "all",
            "table", "data", "records", "record", "list", "select", "from", "where", "with",
            "a", "an", "on", "at", "to", "info", "information"
        }
        for c in cols:
            stopwords.add(c.lower())
            for part in c.lower().split("_"):
                stopwords.add(part)

        tokens = [w for w in re.findall(r'[a-zA-Z0-9]+', q) if w.lower() not in stopwords and len(w) > 1]
        
        candidates = []
        if len(tokens) >= 2:
            candidates.append(" ".join(tokens))
            for i in range(len(tokens) - 1):
                candidates.append(f"{tokens[i]} {tokens[i+1]}")
        for t in tokens:
            candidates.append(t)

        for cand in candidates:
            for tc in text_cols:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {target_table} WHERE LOWER({tc}) LIKE ?;", (f"%{cand.lower()}%",))
                    cnt = cur.fetchone()[0]
                except Exception:
                    cur.execute(f"SELECT COUNT(*) FROM {target_table} WHERE LOWER({tc}) LIKE %s;", (f"%{cand.lower()}%",))
                    cnt = cur.fetchone()[0]
                if cnt > 0:
                    entity_clause = f"LOWER({tc}) LIKE '%{cand.lower()}%'"
                    if tc not in requested_cols:
                        requested_cols.insert(0, tc)
                    break
            if entity_clause:
                break
        cur.close()
        conn.close()
    except Exception:
        pass

    if entity_clause:
        proj = ", ".join(requested_cols) if requested_cols else "*"
        return f"SELECT {proj} FROM {target_table} WHERE {entity_clause};"

    if requested_cols:
        proj = ", ".join(requested_cols)
        return f"SELECT {proj} FROM {target_table}{lim_str or ' LIMIT 15'};"

    # 8. Default projection
    lim_def = f" LIMIT {limit_val or 15}"
    return f"SELECT * FROM {target_table}{lim_def};"

WORD_TO_NUM = {
    "zero": 0, "no": 0, "none": 0,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

def parse_oscar_condition(q: str):
    """
    Parses Oscar/Award criteria from query into SQL condition or ordering.
    Returns (condition_type, clause_string).
    condition_type can be:
      - 'ORDER_MAX'
      - 'CLAUSE'
      - (None, None) if not an oscar query
    """
    if not any(w in q for w in ["oscar", "oscars", "award", "awards", "trophy", "trophies"]):
        return None, None

    # 1. Most / Highest / Top Oscars
    if re.search(r'\b(?:most|highest|maximum)\s*(?:number\s+of\s*)?(?:oscars?|awards?|troph(?:y|ies))\b', q) or \
       re.search(r'\b(?:oscars?|awards?)\s+(?:highest|most|maximum)\b', q):
        return "ORDER_MAX", None

    # 2. Zero / No Oscars
    if re.search(r'\b(?:no|zero|without(?:\s+any)?|never\s+won(?:\s+an?)?)\s*(?:oscars?|awards?|troph(?:y|ies))\b', q) or \
       re.search(r'\b0\s*(?:oscars?|awards?|troph(?:y|ies))\b', q):
        return "CLAUSE", "oscars_won = 0"

    # 3. Greater than or equal to: "at least 2", "minimum of 2", "2 or more", ">= 2"
    gte_m = re.search(r'(?:at\s+least|minimum\s+of|minimum|>=)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)', q)
    if not gte_m:
        gte_m = re.search(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:or\s+more|and\s+above)\b', q)
    if gte_m:
        val = WORD_TO_NUM.get(gte_m.group(1).lower(), int(gte_m.group(1)) if gte_m.group(1).isdigit() else 1)
        return "CLAUSE", f"oscars_won >= {val}"

    # 4. Greater than: "more than 2", "over 2", "> 2", "greater than 2", "above 2"
    gt_m = re.search(r'(?:more\s+than|over|greater\s+than|above|>)\s*(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)', q)
    if gt_m:
        val = WORD_TO_NUM.get(gt_m.group(1).lower(), int(gt_m.group(1)) if gt_m.group(1).isdigit() else 0)
        return "CLAUSE", f"oscars_won > {val}"

    # 5. Less than or equal to: "at most 2", "maximum of 2", "<= 2"
    lte_m = re.search(r'(?:at\s+most|maximum\s+of|maximum|<=)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)', q)
    if lte_m:
        val = WORD_TO_NUM.get(lte_m.group(1).lower(), int(lte_m.group(1)) if lte_m.group(1).isdigit() else 1)
        return "CLAUSE", f"oscars_won <= {val}"

    # 6. Less than: "less than 2", "under 2", "fewer than 2", "< 2"
    lt_m = re.search(r'(?:less\s+than|under|fewer\s+than|<)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)', q)
    if lt_m:
        val = WORD_TO_NUM.get(lt_m.group(1).lower(), int(lt_m.group(1)) if lt_m.group(1).isdigit() else 1)
        return "CLAUSE", f"oscars_won < {val}"

    # 7. Exact count: "won 2 oscars", "with 2 oscars", "got 2 oscars", "2 oscars", "two oscars"
    exact_m = re.search(r'(?:won|has|have|got|with|having|exactly|equal\s+to|equals|==?)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:oscars?|awards?|troph(?:y|ies))\b', q)
    if not exact_m:
        exact_m = re.search(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:oscars?|awards?|troph(?:y|ies))\b', q)
    if exact_m:
        val = WORD_TO_NUM.get(exact_m.group(1).lower(), int(exact_m.group(1)) if exact_m.group(1).isdigit() else 1)
        return "CLAUSE", f"oscars_won = {val}"

    # 8. General Oscar mention ("won oscars", "has oscars", "oscar winning", "directors who have won oscars")
    return "CLAUSE", "oscars_won > 0"

def generate_sql_semantic(question: str) -> str:
    """
    Dynamic Schema-Grounded Semantic Engine for IMDb Dataset & User-Created Custom Datasets.
    Resolves natural language queries into SQL across all 5 movie tables (movies, directors, actors, movie_cast, reviews)
    AS WELL AS any user-uploaded custom tables (e.g. students, products, patients, customers, etc.).
    Seamlessly supports standard English, local/colloquial English, phonetic typos, joins, aggregations, and filters.
    """
    norm_q = normalize_colloquial_query(question)
    q = norm_q.lower().strip()

    # Dynamic extraction of numeric Top-N / Limits
    limit_match = re.search(r'(?:top|first|limit)\s+(\d+)', q)
    limit_val = int(limit_match.group(1)) if limit_match else None

    # --- DYNAMIC CUSTOM DATASET RESOLVER ---
    # Check if the active database contains custom tables (e.g., uploaded CSV/Excel or seeded datasets)
    db_tables = get_active_tables_info()
    movie_tables = {"movies", "directors", "actors", "movie_cast", "reviews"}
    custom_tables = {k: v for k, v in db_tables.items() if k not in movie_tables}

    # Does the question specifically target a custom table?
    target_custom = None
    if custom_tables:
        for tbl_name, tbl_meta in custom_tables.items():
            singular = tbl_name.rstrip("s") if len(tbl_name) > 3 else tbl_name
            clean_tbl_name = tbl_name.replace("_", " ")
            if tbl_name in q or singular in q or clean_tbl_name in q:
                target_custom = (tbl_name, tbl_meta)
                break
            for c in tbl_meta["columns"]:
                if len(c) >= 4 and c.lower() in q and c.lower() not in ["name", "title", "id", "date", "type", "description"]:
                    target_custom = (tbl_name, tbl_meta)
                    break
            if target_custom:
                break

    # If query explicitly targets a custom table, generate SQL for it!
    if target_custom:
        return resolve_custom_table_query(q, target_custom[0], target_custom[1], limit_val)

    # If the database ONLY contains custom tables (movies not present):
    if custom_tables and not any(t in db_tables for t in movie_tables):
        first_tbl = list(custom_tables.keys())[0]
        return resolve_custom_table_query(q, first_tbl, custom_tables[first_tbl], limit_val)

    # Temporal matches
    between_match = re.search(r'(?:between)\s*(\d{4})\s*(?:and|to|-)\s*(\d{4})', q)
    after_match = re.search(r'(?:after|since|newer than|later than|from)\s*(\d{4})', q)
    before_match = re.search(r'(?:before|prior to|older than|earlier than)\s*(\d{4})', q)

    # Extract exact 4-digit years (e.g. 2008, 1994, 2020)
    all_years = re.findall(r'\b(19\d{2}|20\d{2})\b', q)
    year_found = int(all_years[0]) if all_years else None

    # --- 1. REVIEWS TABLE (Individual movie reviews, sentiment, positive reviews, review counts) ---
    known_titles = [
        "The Dark Knight", "Inception", "Interstellar", "Oppenheimer", "Pulp Fiction",
        "Django Unchained", "Inglourious Basterds", "Schindler's List", "Jurassic Park",
        "Saving Private Ryan", "Goodfellas", "The Wolf of Wall Street", "The Departed",
        "Titanic", "Avatar: The Way of Water", "Avatar", "Barbie", "Little Women", 
        "Dune: Part Two", "Dune: Part One", "Dune", "Parasite", "Spirited Away", "Princess Mononoke",
        "Gladiator", "Alien", "Fight Club", "Se7en", "The Social Network", "Pan's Labyrinth",
        "The Shape of Water"
    ]

    matched_title = None
    for title in known_titles:
        if title.lower() in q:
            matched_title = title
            break

    # Reviews specifically
    if any(w in q for w in ["review", "reviews", "reviewer", "sentiment", "feedback", "critic", "critics", "talk"]):
        if matched_title:
            return f"SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{matched_title}%';"
        if "positive" in q or "good" in q:
            return "SELECT m.title, r.reviewer_name, r.review_score, r.review_text, r.sentiment FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.sentiment = 'Positive' ORDER BY r.review_score DESC;"
        review_score_match = re.search(r'(?:score|rating|above|more than|>|>=)\s*(\d+(?:\.\d+)?)', q)
        if review_score_match and float(review_score_match.group(1)) <= 10.0:
            val = float(review_score_match.group(1))
            return f"SELECT m.title, r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.review_score >= {val} ORDER BY r.review_score DESC;"
        if "how many" in q or "count" in q or "total" in q:
            return "SELECT COUNT(*) AS total_reviews FROM reviews;"
        return "SELECT r.review_id, m.title, r.reviewer_name, r.review_score, r.review_text, r.sentiment FROM reviews r JOIN movies m ON r.movie_id = m.movie_id ORDER BY r.review_score DESC;"

    # --- 2. STREAMING PLATFORM (Netflix, Disney+, Max, Amazon Prime, OTT) ---
    for plat_key, plat_name in [("netflix", "Netflix"), ("disney+", "Disney+"), ("disney plus", "Disney+"), ("max", "Max"), ("amazon prime", "Amazon Prime"), ("prime video", "Amazon Prime")]:
        if plat_key in q:
            lim = f" LIMIT {limit_val}" if limit_val else ""
            return f"SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = '{plat_name}' ORDER BY rating DESC{lim};"

    if 'streaming platform' in q or ('platform' in q and any(w in q for w in ['count', 'group', 'total', 'how many', 'each'])):
        return 'SELECT streaming_platform, COUNT(*) AS movie_count FROM movies GROUP BY streaming_platform ORDER BY movie_count DESC;'

    # --- 3. AGGREGATIONS & GROUPING ---
    # Total box office revenue by director
    if any(w in q for w in ['box office', 'revenue', 'collection']) and ('by director' in q or ('director' in q and any(w in q for w in ['all', 'each', 'group', 'highest', 'list']))):
        lim = f" LIMIT {limit_val}" if limit_val else ""
        return f"SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id GROUP BY d.director_id, d.director_name ORDER BY total_box_office DESC{lim};"

    # Average metrics
    if 'average' in q or 'avg' in q:
        if 'genre' in q or 'rating' in q:
            return 'SELECT genre, COUNT(*) AS movie_count, ROUND(AVG(rating), 2) AS avg_rating FROM movies GROUP BY genre ORDER BY avg_rating DESC;'
        if 'duration' in q:
            return 'SELECT genre, ROUND(AVG(duration_min), 1) AS avg_duration_minutes, COUNT(*) AS total_movies FROM movies GROUP BY genre ORDER BY avg_duration_minutes DESC;'
        if 'box office' in q or 'collection' in q or 'revenue' in q:
            return 'SELECT ROUND(AVG(box_office_millions), 1) AS avg_box_office FROM movies;'
        return 'SELECT ROUND(AVG(rating), 2) AS avg_rating FROM movies;'

    # --- 4. DIRECTORS TABLE & DIRECTOR-SPECIFIC QUERIES ---
    known_directors = [
        "Christopher Nolan", "Quentin Tarantino", "Steven Spielberg", "Martin Scorsese",
        "James Cameron", "Greta Gerwig", "Denis Villeneuve", "Bong Joon-ho",
        "Hayao Miyazaki", "Ridley Scott", "David Fincher", "Guillermo del Toro"
    ]
    for d in known_directors:
        parts = d.lower().split()
        if d.lower() in q or (len(parts) > 1 and parts[-1] in q and len(parts[-1]) >= 4):
            last = parts[-1].capitalize()
            if "oscar" in q or "award" in q:
                return f"SELECT director_name, nationality, oscars_won FROM directors WHERE director_name LIKE '%{last}%';"
            if any(w in q for w in ["how many", "count"]):
                return f"SELECT COUNT(*) AS total_movies FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last}%';"
            if any(w in q for w in ["box office", "revenue", "collection"]):
                return f"SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last}%' GROUP BY d.director_id;"
            if year_found:
                return f"SELECT m.title, m.release_year, m.genre, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last}%' AND m.release_year = {year_found};"
            lim = f" LIMIT {limit_val}" if limit_val else ""
            return f"SELECT m.title, m.release_year, m.genre, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last}%'{lim};"

    # General Counts across tables (unqualified queries like "how many directors are there?", "total actors")
    if any(w in q for w in ['how many', 'count', 'total']) and not any(w in q for w in ['box office', 'revenue', 'collection', 'oscar', 'award', 'troph']):
        if 'director' in q and not any(w in q for w in ['born', 'from', 'american', 'british', 'oscar', 'award']):
            return 'SELECT COUNT(*) AS total_directors FROM directors;'
        if ('actor' in q or 'hero' in q) and not any(w in q for w in ['born', 'from', 'american', 'british']):
            return 'SELECT COUNT(*) AS total_actors FROM actors;'
        if 'review' in q:
            return 'SELECT COUNT(*) AS total_reviews FROM reviews;'
        if year_found:
            return f'SELECT COUNT(*) AS total_movies FROM movies WHERE release_year = {year_found};'
        if any(w in q for w in ['movie', 'film', 'cinema', 'picture']):
            return 'SELECT COUNT(*) AS total_movies FROM movies;'

    # --- 5. ACTORS & MOVIE_CAST TABLE ---
    known_actors = [
        "Leonardo DiCaprio", "Cillian Murphy", "Christian Bale", "Margot Robbie",
        "Robert Downey Jr.", "Tom Hanks", "Emma Stone", "Brad Pitt",
        "Timothee Chalamet", "Zendaya", "Song Kang-ho", "Ryan Gosling",
        "Matt Damon", "Samuel L. Jackson", "Kate Winslet"
    ]
    for a in known_actors:
        parts = a.lower().split()
        if a.lower() in q or (len(parts) > 1 and parts[-1] in q and len(parts[-1]) >= 4):
            last = parts[-1].capitalize()
            if matched_title:
                return f"SELECT a.actor_name, c.role_name, m.title FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{last}%' AND m.title LIKE '%{matched_title}%';"
            lim = f" LIMIT {limit_val}" if limit_val else ""
            return f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{last}%'{lim};"

    # --- 6. MOVIE TITLE MATCH (Cast, Director, Details) ---
    if matched_title:
        if any(w in q for w in ["cast", "actor", "actors", "hero", "heroine", "star", "starred", "acted", "acting", "people", "artist"]):
            return f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{matched_title}%';"
        if any(w in q for w in ["director", "directed by", "directed", "who took", "who made"]):
            return f"SELECT d.director_name, d.nationality, d.oscars_won FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE m.title LIKE '%{matched_title}%';"
        return f"SELECT m.title, m.release_year, m.genre, m.rating, d.director_name, m.box_office_millions FROM movies m LEFT JOIN directors d ON m.director_id = d.director_id WHERE m.title LIKE '%{matched_title}%';"

    # Nationalities mapping
    NATIONALITIES = {
        "american": "American", "america": "American", "usa": "American", "us": "American",
        "british": "British", "uk": "British", "english": "British", "britain": "British",
        "irish": "Irish", "ireland": "Irish",
        "australian": "Australian", "australia": "Australian",
        "canadian": "Canadian", "canada": "Canadian",
        "south korean": "South Korean", "korean": "South Korean", "korea": "South Korean",
        "japanese": "Japanese", "japan": "Japanese",
        "mexican": "Mexican", "mexico": "Mexican",
        "french": "French", "france": "French"
    }
    found_nat = None
    for nat_key, nat_val in NATIONALITIES.items():
        if re.search(r'\b' + re.escape(nat_key) + r'\b', q):
            found_nat = nat_val
            break

    # --- 7. OSCARS & AWARDS ---
    oscar_type, oscar_clause = parse_oscar_condition(q)
    if oscar_type:
        clauses = []
        if found_nat:
            clauses.append(f"LOWER(nationality) LIKE '%{found_nat.lower()}%'")
        if after_match:
            clauses.append(f"birth_year >= {int(after_match.group(1))}")
        elif before_match:
            clauses.append(f"birth_year <= {int(before_match.group(1))}")
        elif between_match:
            clauses.append(f"birth_year BETWEEN {int(between_match.group(1))} AND {int(between_match.group(2))}")
        elif year_found:
            clauses.append(f"birth_year = {year_found}")

        if oscar_type == "ORDER_MAX":
            where_str = f" WHERE {' AND '.join(clauses)}" if clauses else ""
            return f"SELECT director_name, nationality, oscars_won FROM directors{where_str} ORDER BY oscars_won DESC LIMIT 1;"

        if oscar_clause:
            clauses.append(oscar_clause)

        where_str = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        if "how many" in q or "count" in q:
            return f"SELECT COUNT(*) AS total_directors FROM directors{where_str};"
        lim = f" LIMIT {limit_val}" if limit_val else ""
        return f"SELECT director_name, nationality, oscars_won FROM directors{where_str} ORDER BY oscars_won DESC{lim};"

    # Actor Queries (e.g. "show all American actors", "actors born on the year 1956", "actors born after 1980")
    if any(w in q for w in ["actor", "actors", "hero", "heroes", "heroine", "artist"]):
        clauses = []
        if found_nat:
            clauses.append(f"LOWER(nationality) LIKE '%{found_nat.lower()}%'")
        if after_match:
            clauses.append(f"birth_year >= {int(after_match.group(1))}")
        elif before_match:
            clauses.append(f"birth_year <= {int(before_match.group(1))}")
        elif between_match:
            clauses.append(f"birth_year BETWEEN {int(between_match.group(1))} AND {int(between_match.group(2))}")
        elif year_found:
            clauses.append(f"birth_year = {year_found}")

        where_str = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        if "how many" in q or "count" in q:
            return f"SELECT COUNT(*) AS total_actors FROM actors{where_str};"
        lim = f" LIMIT {limit_val}" if limit_val else ("" if clauses else " LIMIT 20")
        return f"SELECT actor_id, actor_name, nationality, birth_year FROM actors{where_str} ORDER BY birth_year DESC, actor_name ASC{lim};"

    # Director Queries (e.g. "American directors", "directors born in 1970", "directors with more than 2 oscars")
    if any(w in q for w in ["director", "directors"]):
        clauses = []
        if found_nat:
            clauses.append(f"LOWER(nationality) LIKE '%{found_nat.lower()}%'")
        if after_match:
            clauses.append(f"birth_year >= {int(after_match.group(1))}")
        elif before_match:
            clauses.append(f"birth_year <= {int(before_match.group(1))}")
        elif between_match:
            clauses.append(f"birth_year BETWEEN {int(between_match.group(1))} AND {int(between_match.group(2))}")
        elif year_found:
            clauses.append(f"birth_year = {year_found}")

        if oscar_clause:
            clauses.append(oscar_clause)

        where_str = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        if "how many" in q or "count" in q:
            return f"SELECT COUNT(*) AS total_directors FROM directors{where_str};"
        lim = f" LIMIT {limit_val}" if limit_val else ("" if clauses else " LIMIT 20")
        return f"SELECT director_id, director_name, nationality, oscars_won, birth_year FROM directors{where_str} ORDER BY oscars_won DESC, birth_year DESC{lim};"

    # --- 8. BUDGET (Expensive / Cheap / Low Budget / Costly) ---
    if any(w in q for w in ["cheap", "low budget"]):
        lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 5"
        return f"SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions ASC {lim};"
    if any(w in q for w in ["budget", "expensive", "costly", "high budget", "pricey", "money spent"]):
        lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 5"
        return f"SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions DESC {lim};"

    # --- 9. BOX OFFICE & COLLECTIONS (Highest collected, Grossing, Blockbusters) ---
    if any(w in q for w in ["box office", "collection", "collected", "revenue", "grossing", "made more than", "billion", "blockbuster", "commercial success", "earnings"]):
        clean_q = re.sub(r'(?:top|first|limit)\s+\d+', '', q)
        thresh_match = re.search(r'(?:more than|over|above|>|>=|\$)\s*(\d+)', clean_q)
        if not thresh_match:
            thresh_match = re.search(r'\b(500|600|700|800|900|1000|2000)\b', clean_q)
        threshold = int(thresh_match.group(1)) if thresh_match else None

        lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 5"
        if threshold:
            return f"SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= {threshold} ORDER BY box_office_millions DESC;"
        return f"SELECT title, release_year, box_office_millions FROM movies ORDER BY box_office_millions DESC {lim};"

    # --- 10. DURATION & RUNTIME (Lengthy, Longest, Shortest) ---
    dur_match = re.search(r'(?:duration|runtime|longer than|over)\s*(?:over|more than|above)?\s*(\d+)', q)
    if any(w in q for w in ["duration", "runtime", "longest", "lengthy", "running time"]) or dur_match:
        thresh = int(dur_match.group(1)) if dur_match else 160
        lim = f"LIMIT {limit_val}" if limit_val else ""
        lim_str = f" {lim}" if lim else ""
        return f"SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= {thresh} ORDER BY duration_min DESC{lim_str};"
    if any(w in q for w in ["shortest", "short duration", "short runtime"]):
        return f"SELECT title, duration_min, genre, rating FROM movies ORDER BY duration_min ASC LIMIT 5;"

    # --- 11. TEMPORAL FILTERS (After, Before, Between, Exact Year) ---
    if after_match:
        yr = int(after_match.group(1))
        lim = f"LIMIT {limit_val}" if limit_val else ""
        lim_str = f" {lim}" if lim else ""
        return f"SELECT title, release_year, genre, rating FROM movies WHERE release_year >= {yr} ORDER BY release_year DESC{lim_str};"

    if before_match:
        yr = int(before_match.group(1))
        lim = f"LIMIT {limit_val}" if limit_val else ""
        lim_str = f" {lim}" if lim else ""
        return f"SELECT title, release_year, genre, rating FROM movies WHERE release_year <= {yr} ORDER BY release_year DESC{lim_str};"

    if between_match:
        y1, y2 = int(between_match.group(1)), int(between_match.group(2))
        return f"SELECT title, release_year, genre, rating FROM movies WHERE release_year BETWEEN {y1} AND {y2} ORDER BY release_year DESC;"

    # --- 12. GENRES ---
    matched_genre = None
    for g_key, g_val in GENRE_MAP.items():
        if g_key in q:
            matched_genre = g_val
            break

    if year_found and matched_genre:
        return f"SELECT title, release_year, genre, rating FROM movies WHERE genre = '{matched_genre}' AND release_year = {year_found} ORDER BY rating DESC;"

    if year_found:
        return f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {year_found} ORDER BY rating DESC;"

    if matched_genre:
        lim = f"LIMIT {limit_val}" if limit_val else ""
        lim_str = f" {lim}" if lim else ""
        return f"SELECT title, release_year, rating FROM movies WHERE genre = '{matched_genre}' ORDER BY rating DESC{lim_str};"

    # --- 13. RATINGS & TOP FILMS ---
    rating_match = re.search(r'(?:rating|rated|score)\s*(?:above|over|higher than|>|>=)\s*(\d+(?:\.\d+)?)', q)
    if rating_match:
        val = float(rating_match.group(1))
        return f"SELECT title, release_year, genre, rating FROM movies WHERE rating >= {val} ORDER BY rating DESC;"

    if any(w in q for w in ["vote", "votes", "voted"]):
        return f"SELECT title, release_year, rating, votes FROM movies ORDER BY votes DESC LIMIT 5;"

    if any(w in q for w in ["highest rated", "top rated", "best movie", "best rated", "highest rating", "top", "acclaimed", "critically acclaimed"]):
        lim = limit_val if limit_val else 5
        return f"SELECT title, release_year, genre, rating FROM movies ORDER BY rating DESC LIMIT {lim};"

    # --- 14. DEFAULT / ALL MOVIES ---
    lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 15"
    return f"SELECT movie_id, title, release_year, genre, rating, box_office_millions FROM movies ORDER BY rating DESC {lim};"

def get_gemini_models(api_key: str) -> list:
    """Fetch active models from Google AI Studio for this key, prioritizing fast flash models."""
    default_candidates = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest"
    ]
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            models_data = res.json().get("models", [])
            valid_models = []
            for m in models_data:
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods and "gemini" in name.lower() and not name.endswith("-vision"):
                    valid_models.append(name)
            if valid_models:
                flash_models = [m for m in valid_models if "flash" in m]
                pro_models = [m for m in valid_models if "pro" in m]
                others = [m for m in valid_models if m not in flash_models and m not in pro_models]
                return flash_models + pro_models + others
    except Exception:
        pass
    return default_candidates

def generate_sql_gemini(question: str, schema_context: str, api_key: str) -> str:
    """Generate SQL using Google Gemini API (Transformer LLM)."""
    prompt = f"""You are an expert database architect and Text-to-SQL neural model.
Given the active database schema below, translate the natural language question into a syntactically correct and semantically accurate SQL query.

DATABASE SCHEMA:
{schema_context}

RULES:
1. Return ONLY the raw SQL query. Do not wrap in markdown or backticks (no ```sql).
2. Do not include conversational explanations, markdown formatting, greetings, or commentary.
3. For multi-table queries, use proper table aliases and JOIN conditions matching foreign keys defined in the schema.
4. For exact matches and filters (e.g. "won 2 oscars", "rating > 8"), generate strict WHERE conditions.
5. Support any table in the schema (movies, directors, actors, reviews, or user-uploaded custom tables).
6. Only generate safe SELECT queries. Never generate DROP, ALTER, DELETE, or UPDATE.

USER QUESTION: {question}
SQL QUERY:"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 300
        }
    }

    # Retrieve cached working model if available
    cached_model = None
    try:
        import streamlit as st
        cached_model = st.session_state.get("gemini_working_model")
    except Exception:
        pass

    candidate_models = [cached_model] if cached_model else []
    discovered_models = get_gemini_models(api_key)
    for m in discovered_models:
        if m and m not in candidate_models:
            candidate_models.append(m)

    last_err = None
    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                res_data = response.json()
                candidates = res_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        try:
                            import streamlit as st
                            st.session_state["active_llm_model"] = f"Gemini ({model})"
                            st.session_state["gemini_working_model"] = model
                            st.session_state.pop("llm_warning", None)
                        except Exception:
                            pass
                        return clean_sql_string(parts[0]['text'])
            else:
                last_err = f"Gemini HTTP {response.status_code}: {response.text[:120]}"
        except Exception as e:
            last_err = str(e)
            continue

    try:
        import streamlit as st
        if last_err:
            st.session_state["llm_warning"] = f"⚠️ Gemini API issue ({last_err}). Reverted to schema rules engine."
    except Exception:
        pass

    return generate_sql_semantic(question)

def generate_sql_openai(question: str, schema_context: str, api_key: str) -> str:
    """Generate SQL using OpenAI GPT-4o-mini / GPT-3.5-turbo (Transformer LLM)."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"Database Schema:\n{schema_context}\n\nConvert natural language to pure SQL:\nQuestion: {question}\nSQL Query:"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a database expert that outputs raw SQL code only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            sql = res_data['choices'][0]['message']['content']
            return clean_sql_string(sql)
    except Exception:
        pass
    return generate_sql_semantic(question)

def generate_sql_local(question: str, schema_context: str) -> str:
    """Generate SQL using local Hugging Face Transformers model (Flan-T5)."""
    try:
        generator = get_local_generator()
        prompt = (
            f"Translate to SQL for IMDb database (tables: movies, directors, actors, movie_cast, reviews). "
            f"Question: {question}"
        )
        result = generator(prompt, max_new_tokens=100)
        raw_output = result[0]["generated_text"]
        if "SQL:" in raw_output:
            raw_output = raw_output.split("SQL:")[-1]
        cleaned = clean_sql_string(raw_output)
        if cleaned and any(kw in cleaned.upper() for kw in ["SELECT", "SHOW", "DESCRIBE"]):
            return cleaned
        return generate_sql_semantic(question)
    except Exception:
        return generate_sql_semantic(question)

def generate_sql(question: str) -> str:
    """Main SQL generation router based on configuration settings."""
    config = load_config()
    schema_context = get_db_schema_context()
    provider = str(config.get("ai_provider", "Google Gemini")).strip()

    # Preprocess and normalize colloquial English, typos, and local slang
    norm_question = normalize_colloquial_query(question)

    # 1. Google Gemini (State-of-the-art neural Text-to-SQL for arbitrary queries)
    gemini_key = config.get("gemini_api_key", "").strip()
    if gemini_key and (provider in ["Google Gemini", "Gemini", "Mock"] or not provider):
        return generate_sql_gemini(norm_question, schema_context, gemini_key)
    elif provider in ["Google Gemini", "Gemini"] and gemini_key:
        return generate_sql_gemini(norm_question, schema_context, gemini_key)

    # 2. OpenAI GPT
    openai_key = config.get("openai_api_key", "").strip()
    if provider in ["OpenAI", "ChatGPT"] and openai_key:
        return generate_sql_openai(norm_question, schema_context, openai_key)

    # 3. Local Transformers Fine-Tuned Model
    has_saved_model = os.path.isdir("saved_model") and os.path.exists(os.path.join("saved_model", "config.json"))
    if provider in ["Local (Flan-T5)", "Local"] or (has_saved_model and provider in ["Offline Rules", "Local (Flan-T5)"]):
        return generate_sql_local(norm_question, schema_context)

    # 4. Neural Schema-Grounded Semantic Parser (Zero-setup offline engine)
    return generate_sql_semantic(norm_question)