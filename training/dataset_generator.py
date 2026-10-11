import json
import os

SCHEMA_CONTEXT = """
Schema:
movies(movie_id, title, release_year, genre, rating, votes, duration_min, director_id, budget_millions, box_office_millions, streaming_platform)
directors(director_id, director_name, nationality, birth_year, oscars_won)
actors(actor_id, actor_name, nationality, birth_year)
movie_cast(cast_id, movie_id, actor_id, role_name)
reviews(review_id, movie_id, reviewer_name, review_score, review_text, sentiment)
"""

def generate_training_dataset(output_path="training/dataset.json"):
    """
    Generates a rich supervised training dataset of (Natural Language Question, SQL Query)
    covering standard English, local/colloquial English, phonetic speech typos, and
    queries across ALL 5 tables of the movie database (movies, directors, actors, movie_cast, reviews).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    dataset = []

    # =========================================================================
    # 1. ACTORS TABLE (Birth years, Nationalities, Counts, Local English terms)
    # =========================================================================
    birth_years = [
        (1956, "Tom Hanks"),
        (1963, "Brad Pitt"),
        (1965, "Robert Downey Jr."),
        (1970, "Matt Damon"),
        (1974, "Christian Bale / Leonardo DiCaprio"),
        (1976, "Cillian Murphy"),
        (1980, "Ryan Gosling"),
        (1988, "Emma Stone"),
        (1990, "Margot Robbie"),
        (1995, "Timothee Chalamet"),
        (1996, "Zendaya")
    ]
    for yr, _ in birth_years:
        dataset.extend([
            {"question": f"Show the actors who were born on the year {yr}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
            {"question": f"Which actors were born in {yr}?", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
            {"question": f"Actors born in {yr}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
            {"question": f"Find actors whose birth year is {yr}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
            # Local English / Colloquial variants
            {"question": f"actors born on {yr}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
            {"question": f"hero born in {yr}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
            {"question": f"who are the heroes born on {yr}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
            {"question": f"actor list with dob {yr}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year = {yr};"},
        ])

    # Actor birth year ranges & general
    dataset.extend([
        {"question": "Show actors born after 1980", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year >= 1980 ORDER BY birth_year DESC;"},
        {"question": "List actors born since 1985", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year >= 1985 ORDER BY birth_year DESC;"},
        {"question": "young actors born after 1980", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year >= 1980 ORDER BY birth_year DESC;"},
        {"question": "Find actors born before 1970", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year <= 1970 ORDER BY birth_year ASC;"},
        {"question": "old actors born before 1970", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year <= 1970 ORDER BY birth_year ASC;"},
        {"question": "Actors born between 1970 and 1980", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE birth_year BETWEEN 1970 AND 1980;"},
        {"question": "How many actors are in the database?", "sql": "SELECT COUNT(*) AS total_actors FROM actors;"},
        {"question": "total actors count", "sql": "SELECT COUNT(*) AS total_actors FROM actors;"},
        {"question": "count how many hero and heroine are there", "sql": "SELECT COUNT(*) AS total_actors FROM actors;"},
        {"question": "show all actors", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors ORDER BY actor_name ASC;"},
        {"question": "tell me full actor list", "sql": "SELECT actor_id, actor_name, nationality, birth_year FROM actors ORDER BY actor_name ASC;"},
    ])

    # Actor nationalities
    nationalities = ["American", "British", "Irish", "Australian", "Canadian", "South Korean", "French"]
    for nat in nationalities:
        dataset.extend([
            {"question": f"Show all the {nat} actors", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE LOWER(nationality) LIKE '%{nat.lower()}%' ORDER BY actor_name ASC;"},
            {"question": f"List {nat} actors", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE LOWER(nationality) LIKE '%{nat.lower()}%' ORDER BY actor_name ASC;"},
            {"question": f"Actors from {nat}", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE LOWER(nationality) LIKE '%{nat.lower()}%' ORDER BY actor_name ASC;"},
            {"question": f"How many {nat} actors are there?", "sql": f"SELECT COUNT(*) AS total_actors FROM actors WHERE LOWER(nationality) LIKE '%{nat.lower()}%';"},
            # Local English / Colloquial variants
            {"question": f"who are the {nat} heroes", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE LOWER(nationality) LIKE '%{nat.lower()}%' ORDER BY actor_name ASC;"},
            {"question": f"{nat} country actors list", "sql": f"SELECT actor_id, actor_name, nationality, birth_year FROM actors WHERE LOWER(nationality) LIKE '%{nat.lower()}%' ORDER BY actor_name ASC;"},
        ])

    # =========================================================================
    # 2. DIRECTORS TABLE (Oscars, Nationality, Birth year, Counts)
    # =========================================================================
    dataset.extend([
        {"question": "Show directors who have won Oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won > 0 ORDER BY oscars_won DESC;"},
        {"question": "Which directors won more than 2 Oscars?", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won > 2 ORDER BY oscars_won DESC;"},
        {"question": "show the directors who won 2 oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 2 ORDER BY oscars_won DESC;"},
        {"question": "directors who won 2 oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 2 ORDER BY oscars_won DESC;"},
        {"question": "directors with 2 oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 2 ORDER BY oscars_won DESC;"},
        {"question": "which directors won 3 oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 3 ORDER BY oscars_won DESC;"},
        {"question": "directors who won 1 oscar", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 1 ORDER BY oscars_won DESC;"},
        {"question": "directors with 0 oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 0 ORDER BY oscars_won DESC;"},
        {"question": "which director won the most oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors ORDER BY oscars_won DESC LIMIT 1;"},
        {"question": "how many directors won 2 oscars", "sql": "SELECT COUNT(*) AS total_directors FROM directors WHERE oscars_won = 2;"},
        {"question": "Directors with academy awards", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won > 0 ORDER BY oscars_won DESC;"},
        {"question": "Show American directors", "sql": "SELECT director_id, director_name, nationality, oscars_won, birth_year FROM directors WHERE LOWER(nationality) LIKE '%american%' ORDER BY oscars_won DESC;"},
        {"question": "Show British directors", "sql": "SELECT director_id, director_name, nationality, oscars_won, birth_year FROM directors WHERE LOWER(nationality) LIKE '%british%' ORDER BY oscars_won DESC;"},
        {"question": "How many directors are there?", "sql": "SELECT COUNT(*) AS total_directors FROM directors;"},
        {"question": "total directors count", "sql": "SELECT COUNT(*) AS total_directors FROM directors;"},
        # Local English / Colloquial & Typo variants
        {"question": "which directer got oscar award", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won > 0 ORDER BY oscars_won DESC;"},
        {"question": "who won oscar director", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won > 0 ORDER BY oscars_won DESC;"},
        {"question": "who won 2 oscar awards", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 2 ORDER BY oscars_won DESC;"},
        {"question": "directer with two oscars", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won = 2 ORDER BY oscars_won DESC;"},
        {"question": "directers with oscar trophies", "sql": "SELECT director_name, nationality, oscars_won FROM directors WHERE oscars_won > 0 ORDER BY oscars_won DESC;"},
        {"question": "give me american directer list", "sql": "SELECT director_id, director_name, nationality, oscars_won, birth_year FROM directors WHERE LOWER(nationality) LIKE '%american%' ORDER BY oscars_won DESC;"},
        {"question": "all directers list", "sql": "SELECT director_id, director_name, nationality, oscars_won, birth_year FROM directors ORDER BY director_name ASC;"},
    ])

    # =========================================================================
    # 3. MOVIES + DIRECTORS (JOIN: Who directed what, Box Office by Director)
    # =========================================================================
    director_names = [
        ("Christopher Nolan", "Nolan"),
        ("Quentin Tarantino", "Tarantino"),
        ("Steven Spielberg", "Spielberg"),
        ("Martin Scorsese", "Scorsese"),
        ("James Cameron", "Cameron"),
        ("Greta Gerwig", "Gerwig"),
        ("Denis Villeneuve", "Villeneuve"),
        ("Bong Joon-ho", "Bong"),
        ("Hayao Miyazaki", "Miyazaki"),
        ("Ridley Scott", "Scott"),
        ("David Fincher", "Fincher"),
        ("Guillermo del Toro", "Toro")
    ]
    for full_d, last_d in director_names:
        dataset.extend([
            {"question": f"Show all movies directed by {full_d}", "sql": f"SELECT m.title, m.release_year, m.genre, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%';"},
            {"question": f"Movies by {last_d}", "sql": f"SELECT m.title, m.release_year, m.genre, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%';"},
            {"question": f"How many movies did {full_d} direct?", "sql": f"SELECT COUNT(*) AS total_movies FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%';"},
            {"question": f"Total box office revenue by {last_d}", "sql": f"SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%' GROUP BY d.director_id;"},
            # Local English / Colloquial variants
            {"question": f"which pictures directed by {last_d}", "sql": f"SELECT m.title, m.release_year, m.genre, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%';"},
            {"question": f"{last_d} cinema list", "sql": f"SELECT m.title, m.release_year, m.genre, m.rating FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%';"},
            {"question": f"how many cinema taken by {last_d}", "sql": f"SELECT COUNT(*) AS total_movies FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%';"},
            {"question": f"what is the total collection of {last_d} movies", "sql": f"SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%' GROUP BY d.director_id;"},
            {"question": f"box office collection of {full_d} films", "sql": f"SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE d.director_name LIKE '%{last_d}%' GROUP BY d.director_id;"},
        ])

    dataset.extend([
        {"question": "Total box office revenue by director", "sql": "SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id GROUP BY d.director_id, d.director_name ORDER BY total_box_office DESC;"},
        {"question": "directors collection list", "sql": "SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id GROUP BY d.director_id, d.director_name ORDER BY total_box_office DESC;"},
        {"question": "which directer collected highest money", "sql": "SELECT d.director_name, COUNT(m.movie_id) AS total_movies, ROUND(SUM(m.box_office_millions), 1) AS total_box_office FROM movies m JOIN directors d ON m.director_id = d.director_id GROUP BY d.director_id, d.director_name ORDER BY total_box_office DESC LIMIT 5;"},
    ])

    # =========================================================================
    # 4. MOVIES + MOVIE_CAST + ACTORS (Multi-Table JOIN: Cast, Roles, Actors)
    # =========================================================================
    movie_cast_queries = [
        ("Inception", "Inception"),
        ("The Dark Knight", "The Dark Knight"),
        ("Titanic", "Titanic"),
        ("Oppenheimer", "Oppenheimer"),
        ("Pulp Fiction", "Pulp Fiction"),
        ("Django Unchained", "Django Unchained"),
        ("Barbie", "Barbie"),
        ("Dune", "Dune"),
        ("Fight Club", "Fight Club"),
        ("Avatar", "Avatar")
    ]
    for movie_title, movie_kw in movie_cast_queries:
        dataset.extend([
            {"question": f"Find actors who acted in {movie_title}", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"Who acted in {movie_title}?", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"Cast of {movie_title}", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            # Local English / Colloquial variants
            {"question": f"who is the hero of {movie_title}", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"hero in {movie_title}", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"who acted inside {movie_title}", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"star cast of {movie_title}", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"who are the acting people in {movie_title}", "sql": f"SELECT a.actor_name, c.role_name FROM movie_cast c JOIN movies m ON c.movie_id = m.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"who directed {movie_title}?", "sql": f"SELECT d.director_name, d.nationality, d.oscars_won FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"directer of {movie_title}", "sql": f"SELECT d.director_name, d.nationality, d.oscars_won FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"who took the movie {movie_title}", "sql": f"SELECT d.director_name, d.nationality, d.oscars_won FROM movies m JOIN directors d ON m.director_id = d.director_id WHERE m.title LIKE '%{movie_kw}%';"},
        ])

    # Actor-specific filmography
    actor_filmographies = [
        ("Leonardo DiCaprio", "DiCaprio"),
        ("Christian Bale", "Bale"),
        ("Cillian Murphy", "Murphy"),
        ("Margot Robbie", "Robbie"),
        ("Brad Pitt", "Pitt"),
        ("Matt Damon", "Damon"),
        ("Timothee Chalamet", "Chalamet"),
        ("Zendaya", "Zendaya"),
        ("Tom Hanks", "Hanks")
    ]
    for actor_full, actor_kw in actor_filmographies:
        dataset.extend([
            {"question": f"Show all movies starring {actor_full}", "sql": f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{actor_kw}%';"},
            {"question": f"Movies starring {actor_kw}", "sql": f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{actor_kw}%';"},
            {"question": f"What movies did {actor_full} act in?", "sql": f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{actor_kw}%';"},
            # Local English / Colloquial variants
            {"question": f"{actor_kw} pictures list", "sql": f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{actor_kw}%';"},
            {"question": f"films acted by {actor_kw}", "sql": f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{actor_kw}%';"},
            {"question": f"which cinema hero is {actor_kw}", "sql": f"SELECT m.title, m.release_year, m.genre, c.role_name FROM movies m JOIN movie_cast c ON m.movie_id = c.movie_id JOIN actors a ON c.actor_id = a.actor_id WHERE a.actor_name LIKE '%{actor_kw}%';"},
        ])

    # =========================================================================
    # 5. REVIEWS TABLE (Reviews, Scores, Sentiment, Joins with Movies)
    # =========================================================================
    review_movies = [
        ("Oppenheimer", "Oppenheimer"),
        ("Inception", "Inception"),
        ("The Dark Knight", "The Dark Knight"),
        ("Interstellar", "Interstellar"),
        ("Titanic", "Titanic"),
        ("Barbie", "Barbie"),
        ("Fight Club", "Fight Club"),
        ("Parasite", "Parasite")
    ]
    for movie_title, movie_kw in review_movies:
        dataset.extend([
            {"question": f"Reviews for the movie {movie_title}", "sql": f"SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"Show reviews for {movie_title}", "sql": f"SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{movie_kw}%';"},
            # Local English / Colloquial variants
            {"question": f"what is the public talk of {movie_title}", "sql": f"SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"audience talk for {movie_title}", "sql": f"SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"people feedback for {movie_title}", "sql": f"SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{movie_kw}%';"},
            {"question": f"what critics say about {movie_title}", "sql": f"SELECT r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE m.title LIKE '%{movie_kw}%';"},
        ])

    dataset.extend([
        {"question": "Show all positive reviews", "sql": "SELECT m.title, r.reviewer_name, r.review_score, r.review_text, r.sentiment FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.sentiment = 'Positive' ORDER BY r.review_score DESC;"},
        {"question": "Which movies got positive reviews?", "sql": "SELECT m.title, r.reviewer_name, r.review_score, r.review_text, r.sentiment FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.sentiment = 'Positive' ORDER BY r.review_score DESC;"},
        {"question": "positive talk movies", "sql": "SELECT m.title, r.reviewer_name, r.review_score, r.review_text, r.sentiment FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.sentiment = 'Positive' ORDER BY r.review_score DESC;"},
        {"question": "good feedback movies", "sql": "SELECT m.title, r.reviewer_name, r.review_score, r.review_text, r.sentiment FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.sentiment = 'Positive' ORDER BY r.review_score DESC;"},
        {"question": "Reviews with score above 9", "sql": "SELECT m.title, r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.review_score >= 9.0 ORDER BY r.review_score DESC;"},
        {"question": "highest rated reviews", "sql": "SELECT m.title, r.reviewer_name, r.review_score, r.review_text FROM reviews r JOIN movies m ON r.movie_id = m.movie_id WHERE r.review_score >= 9.0 ORDER BY r.review_score DESC;"},
        {"question": "How many reviews are there?", "sql": "SELECT COUNT(*) AS total_reviews FROM reviews;"},
        {"question": "total reviews count", "sql": "SELECT COUNT(*) AS total_reviews FROM reviews;"},
    ])

    # =========================================================================
    # 6. MOVIES TABLE (Box Office, Collections, Superhits, Budgets)
    # =========================================================================
    dataset.extend([
        # Highest grossing / Collection queries
        {"question": "Which movies made more than 1000 million at the box office?", "sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 1000 ORDER BY box_office_millions DESC;"},
        {"question": "Show blockbuster movies", "sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 800 ORDER BY box_office_millions DESC;"},
        {"question": "Highest grossing movies of all time", "sql": "SELECT title, release_year, box_office_millions FROM movies ORDER BY box_office_millions DESC LIMIT 10;"},
        {"question": "Movies that made over 1 billion", "sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 1000 ORDER BY box_office_millions DESC;"},
        # Local English / Colloquial variants
        {"question": "which picture collected more", "sql": "SELECT title, release_year, box_office_millions FROM movies ORDER BY box_office_millions DESC LIMIT 5;"},
        {"question": "highest collection movies", "sql": "SELECT title, release_year, box_office_millions FROM movies ORDER BY box_office_millions DESC LIMIT 5;"},
        {"question": "top collected cinema", "sql": "SELECT title, release_year, box_office_millions FROM movies ORDER BY box_office_millions DESC LIMIT 5;"},
        {"question": "tell me highest collection movie", "sql": "SELECT title, release_year, box_office_millions FROM movies ORDER BY box_office_millions DESC LIMIT 5;"},
        {"question": "which film collection is highest", "sql": "SELECT title, release_year, box_office_millions FROM movies ORDER BY box_office_millions DESC LIMIT 5;"},
        {"question": "which cinema collected more than 1000 million", "sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 1000 ORDER BY box_office_millions DESC;"},
        {"question": "cinema colletion above 1000", "sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 1000 ORDER BY box_office_millions DESC;"},
        {"question": "superhit movies list", "sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 800 ORDER BY box_office_millions DESC;"},
        {"question": "top 5 super hit cinema", "sql": "SELECT title, release_year, box_office_millions FROM movies WHERE box_office_millions >= 800 ORDER BY box_office_millions DESC LIMIT 5;"},

        # Budgets
        {"question": "Top 5 most expensive budget movies", "sql": "SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions DESC LIMIT 5;"},
        {"question": "Show cheap low budget movies", "sql": "SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions ASC LIMIT 5;"},
        {"question": "costliest movie in database", "sql": "SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions DESC LIMIT 5;"},
        {"question": "which picture spent more money", "sql": "SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions DESC LIMIT 5;"},
        {"question": "low budget cinema list", "sql": "SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions ASC LIMIT 5;"},
        {"question": "costly films list", "sql": "SELECT title, release_year, budget_millions, box_office_millions FROM movies ORDER BY budget_millions DESC LIMIT 5;"},
    ])

    # =========================================================================
    # 7. MOVIES TABLE (Ratings, Votes, Acclaim)
    # =========================================================================
    dataset.extend([
        {"question": "Show top 5 highest rated movies", "sql": "SELECT title, release_year, genre, rating FROM movies ORDER BY rating DESC LIMIT 5;"},
        {"question": "Critically acclaimed top rated films", "sql": "SELECT title, release_year, genre, rating FROM movies ORDER BY rating DESC LIMIT 10;"},
        {"question": "Movies with rating above 8.5", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE rating >= 8.5 ORDER BY rating DESC;"},
        {"question": "Average movie rating by genre", "sql": "SELECT genre, COUNT(*) AS movie_count, ROUND(AVG(rating), 2) AS avg_rating FROM movies GROUP BY genre ORDER BY avg_rating DESC;"},
        {"question": "Movies with highest votes", "sql": "SELECT title, release_year, rating, votes FROM movies ORDER BY votes DESC LIMIT 5;"},
        # Local English / Colloquial variants
        {"question": "best rating cinema", "sql": "SELECT title, release_year, genre, rating FROM movies ORDER BY rating DESC LIMIT 5;"},
        {"question": "which picture got good rating", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE rating >= 8.5 ORDER BY rating DESC;"},
        {"question": "top rated movies in database", "sql": "SELECT title, release_year, genre, rating FROM movies ORDER BY rating DESC LIMIT 5;"},
        {"question": "cinema with rating more than 8.5", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE rating >= 8.5 ORDER BY rating DESC;"},
        {"question": "which film public voted more", "sql": "SELECT title, release_year, rating, votes FROM movies ORDER BY votes DESC LIMIT 5;"},
    ])

    # =========================================================================
    # 8. MOVIES TABLE (Duration, Runtime, Length)
    # =========================================================================
    dataset.extend([
        {"question": "Longest movies with duration over 160 minutes", "sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 160 ORDER BY duration_min DESC;"},
        {"question": "Show lengthy movies", "sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 160 ORDER BY duration_min DESC;"},
        {"question": "Show movies longer than 150 minutes", "sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 150 ORDER BY duration_min DESC;"},
        {"question": "What is the average duration of movies by genre?", "sql": "SELECT genre, ROUND(AVG(duration_min), 1) AS avg_duration_minutes, COUNT(*) AS total_movies FROM movies GROUP BY genre ORDER BY avg_duration_minutes DESC;"},
        # Local English / Colloquial variants
        {"question": "lengthy picture list", "sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 160 ORDER BY duration_min DESC;"},
        {"question": "which movie running time is more", "sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 160 ORDER BY duration_min DESC;"},
        {"question": "cinema running more than 150 minutes", "sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 150 ORDER BY duration_min DESC;"},
        {"question": "long duration films", "sql": "SELECT title, duration_min, genre, rating FROM movies WHERE duration_min >= 160 ORDER BY duration_min DESC;"},
        {"question": "shortest duration movies", "sql": "SELECT title, duration_min, genre, rating FROM movies ORDER BY duration_min ASC LIMIT 5;"},
    ])

    # =========================================================================
    # 9. STREAMING PLATFORMS (Netflix, Disney+, Max, Amazon Prime, OTT)
    # =========================================================================
    platforms = [
        ("Netflix", "netflix"),
        ("Disney+", "disney+"),
        ("Max", "max"),
        ("Amazon Prime", "amazon prime")
    ]
    for plat_name, plat_slug in platforms:
        dataset.extend([
            {"question": f"Movies available on {plat_name}", "sql": f"SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = '{plat_name}' ORDER BY rating DESC;"},
            {"question": f"Show movies streaming on {plat_name}", "sql": f"SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = '{plat_name}' ORDER BY rating DESC;"},
            # Local English / Colloquial variants
            {"question": f"which cinema is inside {plat_slug}", "sql": f"SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = '{plat_name}' ORDER BY rating DESC;"},
            {"question": f"movies in {plat_slug} ott", "sql": f"SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = '{plat_name}' ORDER BY rating DESC;"},
            {"question": f"{plat_slug} ott films list", "sql": f"SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = '{plat_name}' ORDER BY rating DESC;"},
            {"question": f"pictures streaming in {plat_slug}", "sql": f"SELECT title, release_year, genre, rating FROM movies WHERE streaming_platform = '{plat_name}' ORDER BY rating DESC;"},
        ])

    dataset.extend([
        {"question": "Count of movies by streaming platform", "sql": "SELECT streaming_platform, COUNT(*) AS movie_count FROM movies GROUP BY streaming_platform ORDER BY movie_count DESC;"},
        {"question": "how many movies in each streaming platform", "sql": "SELECT streaming_platform, COUNT(*) AS movie_count FROM movies GROUP BY streaming_platform ORDER BY movie_count DESC;"},
        {"question": "ott platform movies count", "sql": "SELECT streaming_platform, COUNT(*) AS movie_count FROM movies GROUP BY streaming_platform ORDER BY movie_count DESC;"},
    ])

    # =========================================================================
    # 10. TEMPORAL / RELEASE YEARS (2008, 1994, 2010, 2023, After, Before)
    # =========================================================================
    years = [2008, 1994, 2010, 2014, 2020, 2023, 1993, 1997, 1999]
    for yr in years:
        dataset.extend([
            {"question": f"Show the movies released on {yr}", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            {"question": f"Movies released in {yr}", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            {"question": f"List movies from {yr}", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            {"question": f"What movies came out in {yr}?", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            # Local English / Colloquial & Typo variants
            {"question": f"cinema relised on {yr}", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            {"question": f"movies relesed in {yr}", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            {"question": f"which picture came in {yr}", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            {"question": f"{yr} cinema list", "sql": f"SELECT title, release_year, genre, rating, box_office_millions FROM movies WHERE release_year = {yr} ORDER BY rating DESC;"},
            {"question": f"how many movies released in {yr}", "sql": f"SELECT COUNT(*) AS total_movies FROM movies WHERE release_year = {yr};"},
        ])

    dataset.extend([
        {"question": "Movies released after 2020", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year >= 2020 ORDER BY release_year DESC;"},
        {"question": "Show films made since 2015", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year >= 2015 ORDER BY release_year DESC;"},
        {"question": "Movies released before 2000", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year <= 2000 ORDER BY release_year ASC;"},
        {"question": "Classic movies from the 90s", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year BETWEEN 1990 AND 1999 ORDER BY rating DESC;"},
        # Local English / Colloquial variants
        {"question": "latest cinema after 2020", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year >= 2020 ORDER BY release_year DESC;"},
        {"question": "old pictures before 2000", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year <= 2000 ORDER BY release_year ASC;"},
        {"question": "cinema released between 1990 and 1999", "sql": "SELECT title, release_year, genre, rating FROM movies WHERE release_year BETWEEN 1990 AND 1999 ORDER BY rating DESC;"},
    ])

    # =========================================================================
    # 11. GENRES (Sci-Fi, Action, Crime, Biography, War, Drama, Comedy)
    # =========================================================================
    genres = [
        ("Sci-Fi", "sci-fi"),
        ("Action", "action"),
        ("Crime", "crime"),
        ("Biography", "biography"),
        ("War", "war"),
        ("Drama", "drama"),
        ("Comedy", "comedy"),
        ("Fantasy", "fantasy"),
        ("Romance", "romance")
    ]
    for g_title, g_slug in genres:
        dataset.extend([
            {"question": f"List all {g_slug} movies", "sql": f"SELECT title, release_year, rating FROM movies WHERE genre = '{g_title}' ORDER BY rating DESC;"},
            {"question": f"Show top {g_slug} movies", "sql": f"SELECT title, release_year, rating FROM movies WHERE genre = '{g_title}' ORDER BY rating DESC LIMIT 5;"},
            {"question": f"How many {g_slug} movies are there?", "sql": f"SELECT COUNT(*) AS total_movies FROM movies WHERE genre = '{g_title}';"},
            # Local English / Colloquial variants
            {"question": f"give me {g_slug} cinema list", "sql": f"SELECT title, release_year, rating FROM movies WHERE genre = '{g_title}' ORDER BY rating DESC;"},
            {"question": f"top {g_slug} picture", "sql": f"SELECT title, release_year, rating FROM movies WHERE genre = '{g_title}' ORDER BY rating DESC LIMIT 5;"},
            {"question": f"{g_slug} films count", "sql": f"SELECT COUNT(*) AS total_movies FROM movies WHERE genre = '{g_title}';"},
        ])

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"[VoiceSQL Studio] Successfully generated {len(dataset)} supervised training pairs in '{output_path}'.")
    return dataset

if __name__ == "__main__":
    generate_training_dataset()
