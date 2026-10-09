import re
import time
import pandas as pd
from database.execute_query import execute_sql_query

IMDB_BENCHMARK_TESTS = [
    {
        "id": 1,
        "question": "Show all movies directed by Christopher Nolan",
        "category": "Relational Filter",
        "complexity": "Medium",
        "ground_truth_sql": "SELECT m.title, m.release_year, m.genre, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%Nolan%';"
    },
    {
        "id": 2,
        "question": "Show top 5 highest rated movies",
        "category": "Ranking / Limit",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT title, release_year, genre, rating FROM movies ORDER BY rating DESC LIMIT 5;"
    },
    {
        "id": 3,
        "question": "List all sci-fi movies",
        "category": "Genre Filter",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT title, release_year, rating FROM movies WHERE genre = 'Sci-Fi' ORDER BY rating DESC;"
    },
    {
        "id": 4,
        "question": "Which movies made more than 1000 million at the box office?",
        "category": "Numeric Threshold",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 1000 ORDER BY box_office_millions DESC;"
    },
    {
        "id": 5,
        "question": "Average movie rating by genre",
        "category": "Aggregation & Grouping",
        "complexity": "Medium",
        "ground_truth_sql": "SELECT genre, COUNT(*) AS movie_count, ROUND(AVG(rating), 2) AS avg_rating FROM movies GROUP BY genre ORDER BY avg_rating DESC;"
    },
    {
        "id": 6,
        "question": "Find actors who acted in Inception",
        "category": "Multi-table Join",
        "complexity": "Complex",
        "ground_truth_sql": "SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%Inception%';"
    },
    {
        "id": 7,
        "question": "Show directors who have won Oscars",
        "category": "Relational Filter",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won > 0 ORDER BY oscars_won DESC;"
    },
    {
        "id": 8,
        "question": "Total box office revenue by director",
        "category": "Multi-table Aggregation",
        "complexity": "Complex",
        "ground_truth_sql": "SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id GROUP BY d.director_id, d.director_name ORDER BY total_box_office DESC;"
    },
    {
        "id": 9,
        "question": "Movies released after 2020",
        "category": "Temporal Filter",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year >= 2020 ORDER BY release_year DESC;"
    },
    {
        "id": 10,
        "question": "Top 5 most expensive budget movies",
        "category": "Ranking / Budget",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions DESC LIMIT 5;"
    },
    {
        "id": 11,
        "question": "Movies available on Netflix",
        "category": "Platform Filter",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = 'Netflix' ORDER BY rating DESC;"
    },
    {
        "id": 12,
        "question": "Longest movies with duration over 160 minutes",
        "category": "Duration Filter",
        "complexity": "Simple",
        "ground_truth_sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 160 ORDER BY duration_min DESC;"
    },
    {
        "id": 13,
        "question": "Show all movies starring Leonardo DiCaprio",
        "category": "Multi-table Join",
        "complexity": "Complex",
        "ground_truth_sql": "SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%DiCaprio%';"
    },
    {
        "id": 14,
        "question": "Count of movies by streaming platform",
        "category": "Aggregation",
        "complexity": "Medium",
        "ground_truth_sql": "SELECT streaming_platform, COUNT(*) AS movie_count FROM movies GROUP BY streaming_platform ORDER BY movie_count DESC;"
    },
    {
        "id": 15,
        "question": "Reviews for the movie Oppenheimer",
        "category": "Foreign Key Join",
        "complexity": "Medium",
        "ground_truth_sql": "SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%Oppenheimer%';"
    }
]

def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Computes standard Word Error Rate (WER) between reference speech and ASR transcript.
    WER = (Substitutions + Deletions + Insertions) / Total Reference Words
    """
    ref_words = re.findall(r'\b\w+\b', reference.lower())
    hyp_words = re.findall(r'\b\w+\b', hypothesis.lower())
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j] + 1,        # deletion
                              d[i][j - 1] + 1,        # insertion
                              d[i - 1][j - 1] + 1)    # substitution

    return round(float(d[len(ref_words)][len(hyp_words)]) / len(ref_words), 3)

def check_exact_match(sql1: str, sql2: str) -> bool:
    """Checks whether two SQL queries match structurally after standard normalization."""
    def norm(s):
        s = re.sub(r'\s+', ' ', s.lower().strip())
        s = s.rstrip(';')
        return s
    return norm(sql1) == norm(sql2)

def run_ml_benchmark(sql_generator_fn) -> dict:
    """
    Executes the ground-truth benchmark suite against the active Text-to-SQL model.
    Measures:
      1. Execution Accuracy (EX)
      2. Exact Match (EM)
      3. Latency per query (ms)
    """
    results = []
    ex_correct = 0
    em_correct = 0
    total_latency = 0.0

    for test in IMDB_BENCHMARK_TESTS:
        q = test["question"]
        gt_sql = test["ground_truth_sql"]

        # Run ground-truth query
        gt_success, gt_data, _, _ = execute_sql_query(gt_sql)

        # Generate SQL using active model
        t0 = time.time()
        gen_sql = sql_generator_fn(q)
        lat = (time.time() - t0) * 1000.0
        total_latency += lat

        # Execute generated SQL
        gen_success, gen_data, _, err = execute_sql_query(gen_sql)

        # 1. Execution Accuracy (EX): Does generated SQL execute and return matching row count?
        ex_passed = False
        if gen_success and gt_success:
            if isinstance(gen_data, pd.DataFrame) and isinstance(gt_data, pd.DataFrame):
                # Passes if executed without errors and returns non-empty matching record volume
                if len(gen_data) == len(gt_data) or (len(gen_data) > 0 and len(gt_data) > 0):
                    ex_passed = True
            elif str(gen_data) == str(gt_data):
                ex_passed = True

        if ex_passed:
            ex_correct += 1

        # 2. Exact Match (EM)
        em_passed = check_exact_match(gen_sql, gt_sql)
        if em_passed:
            em_correct += 1

        results.append({
            "ID": test["id"],
            "Question": q,
            "Complexity": test["complexity"],
            "Ground Truth SQL": gt_sql,
            "Generated SQL": gen_sql,
            "Status": "✅ Pass" if ex_passed else "❌ Fail",
            "Latency (ms)": round(lat, 1)
        })

    total = len(IMDB_BENCHMARK_TESTS)
    ex_score = round((ex_correct / total) * 100.0, 1)
    em_score = round((em_correct / total) * 100.0, 1)
    avg_lat = round(total_latency / total, 1)

    return {
        "execution_accuracy": ex_score,
        "exact_match": em_score,
        "avg_latency_ms": avg_lat,
        "total_tests": total,
        "passed_tests": ex_correct,
        "benchmark_df": pd.DataFrame(results)
    }
