import os
import sqlite3

def generate_and_seed_movies(db_path="database/demo.db"):
    """
    Seeds the SQLite database with an IMDb Movies & Streaming dataset.
    Contains realistic schemas: movies, directors, actors, movie_cast, and reviews.
    """
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Drop existing tables
    tables = ["reviews", "movie_cast", "movies", "directors", "actors"]
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t};")

    # 1. Directors table
    cur.execute("""
    CREATE TABLE directors (
        director_id INTEGER PRIMARY KEY,
        director_name TEXT NOT NULL,
        nationality TEXT,
        birth_year INTEGER,
        oscars_won INTEGER DEFAULT 0
    );
    """)

    # 2. Actors table
    cur.execute("""
    CREATE TABLE actors (
        actor_id INTEGER PRIMARY KEY,
        actor_name TEXT NOT NULL,
        nationality TEXT,
        birth_year INTEGER
    );
    """)

    # 3. Movies table
    cur.execute("""
    CREATE TABLE movies (
        movie_id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        release_year INTEGER NOT NULL,
        genre TEXT NOT NULL,
        rating REAL NOT NULL,
        votes INTEGER NOT NULL,
        duration_min INTEGER NOT NULL,
        director_id INTEGER,
        budget_millions REAL,
        box_office_millions REAL,
        streaming_platform TEXT,
        FOREIGN KEY (director_id) REFERENCES directors(director_id)
    );
    """)

    # 4. Movie Cast table (Many-to-Many junction)
    cur.execute("""
    CREATE TABLE movie_cast (
        cast_id INTEGER PRIMARY KEY,
        movie_id INTEGER NOT NULL,
        actor_id INTEGER NOT NULL,
        role_name TEXT,
        FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
        FOREIGN KEY (actor_id) REFERENCES actors(actor_id)
    );
    """)

    # 5. Reviews table
    cur.execute("""
    CREATE TABLE reviews (
        review_id INTEGER PRIMARY KEY,
        movie_id INTEGER NOT NULL,
        reviewer_name TEXT NOT NULL,
        review_score REAL NOT NULL,
        review_text TEXT,
        sentiment TEXT,
        FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
    );
    """)

    # ==========================================
    # SEED DATA
    # ==========================================

    directors = [
        (1, "Christopher Nolan", "British-American", 1970, 2),
        (2, "Quentin Tarantino", "American", 1963, 2),
        (3, "Steven Spielberg", "American", 1946, 3),
        (4, "Martin Scorsese", "American", 1942, 1),
        (5, "James Cameron", "Canadian", 1954, 3),
        (6, "Greta Gerwig", "American", 1983, 0),
        (7, "Denis Villeneuve", "Canadian", 1967, 0),
        (8, "Bong Joon-ho", "South Korean", 1969, 4),
        (9, "Hayao Miyazaki", "Japanese", 1941, 2),
        (10, "Ridley Scott", "British", 1937, 0),
        (11, "David Fincher", "American", 1962, 0),
        (12, "Guillermo del Toro", "Mexican", 1964, 3)
    ]
    cur.executemany("INSERT INTO directors VALUES (?, ?, ?, ?, ?);", directors)

    actors = [
        (1, "Leonardo DiCaprio", "American", 1974),
        (2, "Cillian Murphy", "Irish", 1976),
        (3, "Christian Bale", "British", 1974),
        (4, "Margot Robbie", "Australian", 1990),
        (5, "Robert Downey Jr.", "American", 1965),
        (6, "Tom Hanks", "American", 1956),
        (7, "Emma Stone", "American", 1988),
        (8, "Brad Pitt", "American", 1963),
        (9, "Timothee Chalamet", "American-French", 1995),
        (10, "Zendaya", "American", 1996),
        (11, "Song Kang-ho", "South Korean", 1967),
        (12, "Ryan Gosling", "Canadian", 1980),
        (13, "Matt Damon", "American", 1970),
        (14, "Samuel L. Jackson", "American", 1948),
        (15, "Kate Winslet", "British", 1975)
    ]
    cur.executemany("INSERT INTO actors VALUES (?, ?, ?, ?);", actors)

    movies = [
        # (id, title, year, genre, rating, votes, duration, director_id, budget, box_office, platform)
        (1, "The Dark Knight", 2008, "Action", 9.0, 2800000, 152, 1, 185.0, 1006.0, "Max"),
        (2, "Inception", 2010, "Sci-Fi", 8.8, 2450000, 148, 1, 160.0, 836.8, "Netflix"),
        (3, "Interstellar", 2014, "Sci-Fi", 8.7, 2000000, 169, 1, 165.0, 701.7, "Amazon Prime"),
        (4, "Oppenheimer", 2023, "Biography", 8.9, 720000, 180, 1, 100.0, 957.0, "Amazon Prime"),
        (5, "Pulp Fiction", 1994, "Crime", 8.9, 2150000, 154, 2, 8.5, 213.9, "Netflix"),
        (6, "Django Unchained", 2012, "Western", 8.5, 1600000, 165, 2, 100.0, 425.4, "Netflix"),
        (7, "Inglourious Basterds", 2009, "War", 8.4, 1520000, 153, 2, 70.0, 321.5, "Amazon Prime"),
        (8, "Schindler's List", 1993, "Biography", 9.0, 1400000, 195, 3, 22.0, 322.2, "Netflix"),
        (9, "Jurassic Park", 1993, "Sci-Fi", 8.2, 1050000, 127, 3, 63.0, 1047.0, "Netflix"),
        (10, "Saving Private Ryan", 1998, "War", 8.6, 1450000, 169, 3, 70.0, 482.3, "Amazon Prime"),
        (11, "Goodfellas", 1990, "Crime", 8.7, 1200000, 145, 4, 25.0, 47.1, "Max"),
        (12, "The Wolf of Wall Street", 2013, "Biography", 8.2, 1500000, 180, 4, 100.0, 406.9, "Netflix"),
        (13, "The Departed", 2006, "Crime", 8.5, 1370000, 151, 4, 90.0, 291.5, "Max"),
        (14, "Titanic", 1997, "Romance", 7.9, 1260000, 194, 5, 200.0, 2264.0, "Disney+"),
        (15, "Avatar", 2009, "Sci-Fi", 7.9, 1360000, 162, 5, 237.0, 2923.0, "Disney+"),
        (16, "Avatar: The Way of Water", 2022, "Sci-Fi", 7.6, 470000, 192, 5, 350.0, 2320.0, "Disney+"),
        (17, "Barbie", 2023, "Comedy", 7.0, 520000, 114, 6, 145.0, 1446.0, "Max"),
        (18, "Little Women", 2019, "Drama", 7.8, 230000, 135, 6, 40.0, 218.9, "Netflix"),
        (19, "Dune: Part One", 2021, "Sci-Fi", 8.0, 740000, 155, 7, 165.0, 402.0, "Max"),
        (20, "Dune: Part Two", 2024, "Sci-Fi", 8.6, 490000, 166, 7, 190.0, 714.4, "Max"),
        (21, "Parasite", 2019, "Thriller", 8.5, 900000, 132, 8, 11.4, 263.1, "Max"),
        (22, "Spirited Away", 2001, "Animation", 8.6, 820000, 125, 9, 19.2, 395.8, "Max"),
        (23, "Princess Mononoke", 1997, "Animation", 8.4, 420000, 134, 9, 23.5, 170.0, "Max"),
        (24, "Gladiator", 2000, "Action", 8.5, 1560000, 155, 10, 103.0, 503.2, "Amazon Prime"),
        (25, "Alien", 1979, "Sci-Fi", 8.5, 920000, 117, 10, 11.0, 186.0, "Disney+"),
        (26, "Fight Club", 1999, "Drama", 8.8, 2240000, 139, 11, 63.0, 101.2, "Amazon Prime"),
        (27, "Se7en", 1995, "Crime", 8.6, 1750000, 127, 11, 33.0, 327.3, "Max"),
        (28, "The Social Network", 2010, "Biography", 7.8, 740000, 120, 11, 40.0, 224.9, "Netflix"),
        (29, "Pan's Labyrinth", 2006, "Fantasy", 8.2, 690000, 118, 12, 19.0, 83.9, "Netflix"),
        (30, "The Shape of Water", 2017, "Fantasy", 7.3, 440000, 123, 12, 19.5, 195.3, "Disney+")
    ]
    cur.executemany("INSERT INTO movies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", movies)

    movie_cast = [
        (1, 1, 3, "Bruce Wayne / Batman"),
        (2, 2, 1, "Dom Cobb"),
        (3, 2, 2, "Robert Fischer"),
        (4, 3, 13, "Dr. Mann"),
        (5, 4, 2, "J. Robert Oppenheimer"),
        (6, 4, 5, "Lewis Strauss"),
        (7, 4, 13, "Leslie Groves"),
        (8, 5, 14, "Jules Winnfield"),
        (9, 6, 1, "Calvin Candie"),
        (10, 6, 14, "Stephen"),
        (11, 7, 8, "Lt. Aldo Raine"),
        (12, 10, 6, "Captain John Miller"),
        (13, 10, 13, "Private James Ryan"),
        (14, 12, 1, "Jordan Belfort"),
        (15, 12, 4, "Naomi Lapaglia"),
        (16, 13, 1, "Billy Costigan"),
        (17, 13, 13, "Colin Sullivan"),
        (18, 14, 1, "Jack Dawson"),
        (19, 14, 15, "Rose DeWitt Bukater"),
        (20, 17, 4, "Barbie"),
        (21, 17, 12, "Ken"),
        (22, 18, 7, "Jo March"),
        (23, 18, 9, "Theodore Laurie Laurence"),
        (24, 19, 9, "Paul Atreides"),
        (25, 19, 10, "Chani"),
        (26, 20, 9, "Paul Atreides"),
        (27, 20, 10, "Chani"),
        (28, 21, 11, "Kim Ki-taek"),
        (29, 26, 8, "Tyler Durden"),
        (30, 27, 8, "Detective David Mills")
    ]
    cur.executemany("INSERT INTO movie_cast VALUES (?, ?, ?, ?);", movie_cast)

    reviews = [
        (1, 1, "Peter Travers", 9.8, "A visionary comic-book movie that transcends its genre.", "Positive"),
        (2, 2, "Roger Ebert", 9.5, "Mind-bending narrative with breathtaking visual ingenuity.", "Positive"),
        (3, 3, "A.O. Scott", 9.2, "An emotional and scientific epic on cosmic love and survival.", "Positive"),
        (4, 4, "Manohla Dargis", 9.6, "A cinematic tour-de-force capturing historical brilliance and terror.", "Positive"),
        (5, 12, "Richard Roeper", 8.8, "Insanely entertaining, hyper-energetic satire of excess.", "Positive"),
        (6, 14, "James Berardinelli", 8.5, "Spectacular storytelling with emotional weight that stands the test of time.", "Positive"),
        (7, 17, "Clarisse Loughrey", 8.0, "Hilarious, intelligent, and feminist pop-cultural triumph.", "Positive"),
        (8, 20, "David Ehrlich", 9.4, "Denis Villeneuve achieves sci-fi perfection in a monumental sequel.", "Positive"),
        (9, 21, "Justin Chang", 9.7, "A masterclass in tension, social commentary, and unexpected genre twists.", "Positive"),
        (10, 26, "Owen Gleiberman", 9.1, "Brilliant, subversive satire of toxic masculinity and consumerism.", "Positive")
    ]
    cur.executemany("INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?);", reviews)

    conn.commit()
    conn.close()
    return True, f"Successfully seeded {len(movies)} movies, {len(directors)} directors, {len(actors)} actors, and {len(reviews)} reviews!"

if __name__ == "__main__":
    ok, msg = generate_and_seed_movies()
    print(msg)
