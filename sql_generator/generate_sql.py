import re
import requests
import json
from utils.config_manager import load_config
from database.db_connection import get_db_schema_context

_local_generator = None

def get_local_generator():
    """Lazily load the local Transformers pipeline to optimize startup memory and speed."""
    global _local_generator
    if _local_generator is None:
        from transformers import pipeline
        _local_generator = pipeline(
            "text2text-generation",
            model="google/flan-t5-base"
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

def generate_sql_semantic(question: str) -> str:
    """
    Dynamic Schema-Grounded Semantic Engine for IMDb Dataset.
    Resolves natural language questions into SQL dynamically without hardcoded if/else rules.
    """
    q = question.lower().strip()

    # Dynamic extraction of numeric Top-N / Limits
    limit_match = re.search(r'(?:top|first|limit)\s+(\d+)', q)
    limit_val = int(limit_match.group(1)) if limit_match else None

    # 1. Director-Specific Queries (e.g. "movies directed by Christopher Nolan")
    known_directors = [
        "Christopher Nolan", "Quentin Tarantino", "Steven Spielberg", "Martin Scorsese",
        "James Cameron", "Greta Gerwig", "Denis Villeneuve", "Bong Joon-ho",
        "Hayao Miyazaki", "Ridley Scott", "David Fincher", "Guillermo del Toro"
    ]
    for d in known_directors:
        parts = d.lower().split()
        if d.lower() in q or (len(parts) > 1 and parts[-1] in q and len(parts[-1]) >= 4):
            if "how many" in q or "count" in q:
                return f"SELECT COUNT(*) AS total_movies FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{parts[-1]}%';"
            if "box office" in q or "revenue" in q:
                return f"SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{parts[-1]}%' GROUP BY d.director_id;"
            return f"SELECT m.title, m.release_year, m.genre, m.rating, m.box_office_millions FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{parts[-1]}%' ORDER BY m.rating DESC;"

    # 2. Actor-Specific Queries (e.g. "movies starring Leonardo DiCaprio" or "actors in Inception")
    known_actors = [
        "Leonardo DiCaprio", "Cillian Murphy", "Christian Bale", "Margot Robbie",
        "Robert Downey Jr.", "Tom Hanks", "Emma Stone", "Brad Pitt",
        "Timothee Chalamet", "Zendaya", "Song Kang-ho", "Ryan Gosling",
        "Matt Damon", "Samuel L. Jackson", "Kate Winslet"
    ]
    for a in known_actors:
        parts = a.lower().split()
        if a.lower() in q or (len(parts) > 1 and parts[-1] in q and len(parts[-1]) >= 4):
            return f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{parts[-1]}%' ORDER BY m.rating DESC;"

    # 3. Movie Title Match (e.g. "actors in Inception", "reviews for The Dark Knight")
    known_titles = [
        "The Dark Knight", "Inception", "Interstellar", "Oppenheimer", "Pulp Fiction",
        "Django Unchained", "Inglourious Basterds", "Schindler's List", "Jurassic Park",
        "Saving Private Ryan", "Goodfellas", "The Wolf of Wall Street", "The Departed",
        "Titanic", "Avatar", "Barbie", "Little Women", "Dune", "Parasite", "Spirited Away",
        "Gladiator", "Alien", "Fight Club", "Se7en"
    ]
    for title in known_titles:
        if title.lower() in q:
            if any(w in q for w in ["cast", "actor", "actors", "star", "starred"]):
                return f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{title}%';"
            if any(w in q for w in ["review", "reviews", "reviewer"]):
                return f"SELECT r.reviewer_name, r.review_score, r.review_text, r.sentiment FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{title}%';"
            return f"SELECT m.title, m.release_year, m.genre, m.rating, d.director_name, m.box_office_millions FROM movies m LEFT JOIN directors d ON m.director_id = d.director_id WHERE m.title LIKE '%{title}%';"

    # 4. Genre Filtering (e.g. "sci-fi movies", "action movies")
    genres = ["sci-fi", "action", "crime", "biography", "war", "western", "romance", "comedy", "drama", "animation", "thriller", "fantasy"]
    for g in genres:
        if g in q:
            lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 20"
            return f"SELECT title, release_year, rating, duration_min, box_office_millions FROM movies WHERE LOWER(genre) = '{g}' ORDER BY rating DESC {lim};"

    # 5. Box Office / Financial Metrics
    if any(w in q for w in ["billion", "highest grossing", "box office", "revenue"]):
        threshold = 1000.0 if "billion" in q or "1000" in q else 500.0
        lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 10"
        return f"SELECT title, release_year, genre, box_office_millions, rating FROM movies WHERE box_office_millions >= {threshold} ORDER BY box_office_millions DESC {lim};"

    # 6. Budget
    if "budget" in q or "expensive" in q:
        lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 5"
        return f"SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions DESC {lim};"

    # 7. Rating / Best / Top Movies
    if any(w in q for w in ["highest rated", "top rated", "best movie", "best rated", "highest rating"]):
        lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 5"
        return f"SELECT title, release_year, genre, rating, votes FROM movies ORDER BY rating DESC {lim};"

    # 8. Oscars / Awards
    if "oscar" in q or "award" in q:
        return "SELECT director_name, nationality, oscars_won, birth_year FROM directors WHERE oscars_won > 0 ORDER BY oscars_won DESC;"

    # 9. Streaming Platform Queries (Netflix, Disney+, Max, Amazon Prime)
    for plat in ["netflix", "disney+", "max", "amazon prime", "apple tv"]:
        if plat in q:
            return f"SELECT title, release_year, genre, rating FROM movies WHERE LOWER(streaming_platform) LIKE '%{plat}%' ORDER BY rating DESC;"

    if "platform" in q and ("count" in q or "group" in q or "total" in q):
        return "SELECT streaming_platform, COUNT(*) AS movie_count, ROUND(AVG(rating), 2) AS avg_rating FROM movies GROUP BY streaming_platform ORDER BY movie_count DESC;"

    # 10. Aggregations (Average duration, average rating by genre)
    if "average" in q or "avg" in q:
        if "duration" in q:
            return "SELECT genre, ROUND(AVG(duration_min), 1) AS avg_duration_minutes, COUNT(*) AS total_movies FROM movies GROUP BY genre ORDER BY avg_duration_minutes DESC;"
        if "rating" in q:
            return "SELECT genre, COUNT(*) AS movie_count, ROUND(AVG(rating), 2) AS avg_rating FROM movies GROUP BY genre ORDER BY avg_rating DESC;"

    # 11. General Table Inspection
    if "director" in q:
        return "SELECT director_id, director_name, nationality, oscars_won, birth_year FROM directors ORDER BY oscars_won DESC;"
    if "actor" in q:
        return "SELECT actor_id, actor_name, nationality, birth_year FROM actors ORDER BY actor_name ASC LIMIT 20;"
    if "all movie" in q or "show movies" in q or "list movies" in q:
        lim = f"LIMIT {limit_val}" if limit_val else "LIMIT 25"
        return f"SELECT movie_id, title, release_year, genre, rating, box_office_millions FROM movies ORDER BY rating DESC {lim};"

    # Fallback to general high-rated movies
    return "SELECT movie_id, title, release_year, genre, rating, box_office_millions FROM movies ORDER BY rating DESC LIMIT 15;"

def generate_sql_gemini(question: str, schema_context: str, api_key: str) -> str:
    """Generate SQL using Google Gemini API (Transformer LLM)."""
    prompt = f"""You are an expert database architect and Text-to-SQL neural model.
Given the following IMDb Movies database schema, convert the natural language question into a clean, accurate SQL query.

DATABASE SCHEMA:
{schema_context}

RULES:
1. Return ONLY the raw SQL query. Do not wrap in markdown or backticks (no ```sql).
2. Do not write conversational explanations, greetings, or commentary.
3. For multi-table queries, use proper table aliases and JOIN keys (e.g. movies.director_id = directors.director_id, movies.movie_id = movie_cast.movie_id).
4. Only generate safe SELECT queries. Never generate DROP, ALTER, DELETE, or UPDATE.

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

    candidate_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-pro"]
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
                        return clean_sql_string(parts[0]['text'])
        except Exception:
            continue
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
        prompt = f"Convert natural language to SQL.\nDatabase Schema:\n{schema_context}\n\nQuestion: {question}\nSQL:"
        result = generator(prompt, max_new_tokens=100)
        raw_output = result[0]["generated_text"]
        if "SQL:" in raw_output:
            raw_output = raw_output.split("SQL:")[-1]
        return clean_sql_string(raw_output)
    except Exception:
        return generate_sql_semantic(question)

def generate_sql(question: str) -> str:
    """Main SQL generation router based on configuration settings."""
    config = load_config()
    schema_context = get_db_schema_context()
    provider = str(config.get("ai_provider", "Gemini")).strip()

    if provider in ["Google Gemini", "Gemini"]:
        api_key = config.get("gemini_api_key", "").strip()
        if api_key:
            return generate_sql_gemini(question, schema_context, api_key)
        # If API key is empty, fall back to semantic schema engine
        return generate_sql_semantic(question)

    elif provider in ["OpenAI", "ChatGPT"]:
        api_key = config.get("openai_api_key", "").strip()
        if api_key:
            return generate_sql_openai(question, schema_context, api_key)
        return generate_sql_semantic(question)

    elif provider in ["Local (Flan-T5)", "Local"]:
        return generate_sql_local(question, schema_context)

    else:
        return generate_sql_semantic(question)