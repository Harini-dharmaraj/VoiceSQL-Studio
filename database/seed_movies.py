import os
import sqlite3

def generate_and_seed_movies(db_path="database/demo.db"):
    """
    Seeds the SQLite database with an expanded, realistic IMDb Movies & Streaming dataset (120+ movies).
    Contains full schemas: movies, directors, actors, movie_cast, and reviews.
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
    # SEED DATA: DIRECTORS (25 Directors)
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
        (12, "Guillermo del Toro", "Mexican", 1964, 3),
        (13, "Francis Ford Coppola", "American", 1939, 5),
        (14, "Peter Jackson", "New Zealander", 1961, 3),
        (15, "Stanley Kubrick", "American", 1928, 1),
        (16, "Jordan Peele", "American", 1979, 1),
        (17, "Wes Anderson", "American", 1969, 1),
        (18, "Alfonso Cuarón", "Mexican", 1961, 4),
        (19, "Damien Chazelle", "American", 1985, 1),
        (20, "Paul Thomas Anderson", "American", 1970, 0),
        (21, "George Miller", "Australian", 1945, 1),
        (22, "Chad Stahelski", "American", 1968, 0),
        (23, "Anthony Russo", "American", 1970, 0),
        (24, "Joseph Kosinski", "American", 1974, 0),
        (25, "Jon Favreau", "American", 1966, 0)
    ]
    cur.executemany("INSERT INTO directors VALUES (?, ?, ?, ?, ?);", directors)

    # ==========================================
    # SEED DATA: ACTORS (30 Actors)
    # ==========================================
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
        (15, "Kate Winslet", "British", 1975),
        (16, "Tom Cruise", "American", 1962),
        (17, "Keanu Reeves", "Canadian", 1964),
        (18, "Daniel Kaluuya", "British", 1989),
        (19, "Al Pacino", "American", 1940),
        (20, "Robert De Niro", "American", 1943),
        (21, "Morgan Freeman", "American", 1937),
        (22, "Scarlett Johansson", "American", 1984),
        (23, "Joaquin Phoenix", "American", 1974),
        (24, "Charlize Theron", "South African", 1975),
        (25, "Chris Evans", "American", 1981),
        (26, "Florence Pugh", "British", 1996),
        (27, "Javier Bardem", "Spanish", 1969),
        (28, "Willem Dafoe", "American", 1955),
        (29, "Matthew McConaughey", "American", 1969),
        (30, "Amy Adams", "American", 1974)
    ]
    cur.executemany("INSERT INTO actors VALUES (?, ?, ?, ?);", actors)

    # ==========================================
    # SEED DATA: MOVIES (125 Diverse Records)
    # ==========================================
    # Format: (movie_id, title, release_year, genre, rating, votes, duration_min, director_id, budget, box_office, streaming_platform)
    movies = [
        # --- Christopher Nolan (dir_id: 1) ---
        (1, "The Dark Knight", 2008, "Action", 9.0, 2800000, 152, 1, 185.0, 1006.2, "Max"),
        (2, "Inception", 2010, "Sci-Fi", 8.8, 2450000, 148, 1, 160.0, 836.8, "Netflix"),
        (3, "Interstellar", 2014, "Sci-Fi", 8.7, 2000000, 169, 1, 165.0, 701.7, "Amazon Prime"),
        (4, "Oppenheimer", 2023, "Biography", 8.9, 720000, 180, 1, 100.0, 957.0, "Amazon Prime"),
        (5, "The Prestige", 2006, "Drama", 8.5, 1400000, 130, 1, 40.0, 109.7, "Max"),
        (6, "Memento", 2000, "Mystery", 8.4, 1300000, 113, 1, 9.0, 40.0, "Amazon Prime"),
        (7, "Dunkirk", 2017, "War", 7.8, 700000, 106, 1, 100.0, 527.0, "Netflix"),
        (8, "Tenet", 2020, "Sci-Fi", 7.3, 550000, 150, 1, 205.0, 365.3, "Max"),
        (9, "The Dark Knight Rises", 2012, "Action", 8.4, 1750000, 164, 1, 250.0, 1081.1, "Max"),
        (10, "Batman Begins", 2005, "Action", 8.2, 1550000, 140, 1, 150.0, 373.7, "Max"),

        # --- Quentin Tarantino (dir_id: 2) ---
        (11, "Pulp Fiction", 1994, "Crime", 8.9, 2150000, 154, 2, 8.5, 213.9, "Netflix"),
        (12, "Django Unchained", 2012, "Western", 8.5, 1600000, 165, 2, 100.0, 425.4, "Netflix"),
        (13, "Inglourious Basterds", 2009, "War", 8.4, 1520000, 153, 2, 70.0, 321.5, "Amazon Prime"),
        (14, "Once Upon a Time in Hollywood", 2019, "Comedy", 7.6, 800000, 161, 2, 90.0, 377.6, "Netflix"),
        (15, "Kill Bill: Vol. 1", 2003, "Action", 8.2, 1150000, 111, 2, 30.0, 180.9, "Amazon Prime"),
        (16, "Kill Bill: Vol. 2", 2004, "Action", 8.0, 800000, 137, 2, 30.0, 152.2, "Amazon Prime"),
        (17, "The Hateful Eight", 2015, "Western", 7.8, 620000, 168, 2, 44.0, 155.8, "Netflix"),
        (18, "Reservoir Dogs", 1992, "Crime", 8.3, 1050000, 99, 2, 1.2, 22.0, "Amazon Prime"),

        # --- Steven Spielberg (dir_id: 3) ---
        (19, "Schindler's List", 1993, "Biography", 9.0, 1400000, 195, 3, 22.0, 322.2, "Netflix"),
        (20, "Jurassic Park", 1993, "Adventure", 8.2, 1050000, 127, 3, 63.0, 1045.7, "Amazon Prime"),
        (21, "Saving Private Ryan", 1998, "War", 8.6, 1450000, 169, 3, 70.0, 482.3, "Paramount+"),
        (22, "Catch Me If You Can", 2002, "Biography", 8.1, 1020000, 141, 3, 52.0, 352.1, "Netflix"),
        (23, "Raiders of the Lost Ark", 1981, "Action", 8.4, 1000000, 115, 3, 18.0, 389.9, "Disney+"),
        (24, "E.T. the Extra-Terrestrial", 1982, "Sci-Fi", 7.9, 430000, 115, 3, 10.5, 792.9, "Amazon Prime"),
        (25, "Jaws", 1975, "Thriller", 8.1, 640000, 124, 3, 9.0, 476.5, "Netflix"),
        (26, "Minority Report", 2002, "Sci-Fi", 7.6, 560000, 145, 3, 102.0, 358.4, "Paramount+"),
        (27, "Ready Player One", 2018, "Sci-Fi", 7.4, 460000, 140, 3, 175.0, 582.9, "Max"),

        # --- Martin Scorsese (dir_id: 4) ---
        (28, "Goodfellas", 1990, "Crime", 8.7, 1200000, 145, 4, 25.0, 47.1, "Max"),
        (29, "The Wolf of Wall Street", 2013, "Biography", 8.2, 1500000, 180, 4, 100.0, 406.9, "Netflix"),
        (30, "The Departed", 2006, "Crime", 8.5, 1380000, 151, 4, 90.0, 291.5, "Max"),
        (31, "Taxi Driver", 1976, "Crime", 8.2, 900000, 114, 4, 1.9, 28.6, "Netflix"),
        (32, "Shutter Island", 2010, "Mystery", 8.2, 1400000, 138, 4, 80.0, 294.8, "Amazon Prime"),
        (33, "Casino", 1995, "Crime", 8.2, 560000, 178, 4, 52.0, 116.1, "Max"),
        (34, "Killers of the Flower Moon", 2023, "Crime", 7.6, 230000, 206, 4, 200.0, 157.0, "Apple TV+"),
        (35, "The Irishman", 2019, "Biography", 7.8, 410000, 209, 4, 160.0, 8.0, "Netflix"),

        # --- James Cameron (dir_id: 5) ---
        (36, "Titanic", 1997, "Romance", 7.9, 1250000, 195, 5, 200.0, 2264.7, "Disney+"),
        (37, "Avatar", 2009, "Sci-Fi", 7.9, 1350000, 162, 5, 237.0, 2923.7, "Disney+"),
        (38, "Avatar: The Way of Water", 2022, "Sci-Fi", 7.6, 480000, 192, 5, 350.0, 2320.3, "Disney+"),
        (39, "Terminator 2: Judgment Day", 1991, "Action", 8.6, 1150000, 137, 5, 102.0, 520.9, "Amazon Prime"),
        (40, "Aliens", 1986, "Sci-Fi", 8.4, 750000, 137, 5, 18.5, 183.3, "Disney+"),
        (41, "The Terminator", 1984, "Action", 8.1, 900000, 107, 5, 6.4, 78.4, "Max"),

        # --- Greta Gerwig (dir_id: 6) ---
        (42, "Barbie", 2023, "Comedy", 6.8, 520000, 114, 6, 145.0, 1445.6, "Max"),
        (43, "Little Women", 2019, "Drama", 7.8, 240000, 135, 6, 40.0, 218.9, "Netflix"),
        (44, "Lady Bird", 2017, "Comedy", 7.4, 310000, 94, 6, 10.0, 78.6, "Netflix"),

        # --- Denis Villeneuve (dir_id: 7) ---
        (45, "Dune: Part Two", 2024, "Sci-Fi", 8.6, 470000, 166, 7, 190.0, 711.8, "Max"),
        (46, "Dune", 2021, "Sci-Fi", 8.0, 740000, 155, 7, 165.0, 402.0, "Max"),
        (47, "Blade Runner 2049", 2017, "Sci-Fi", 8.0, 620000, 164, 7, 150.0, 267.5, "Max"),
        (48, "Arrival", 2016, "Sci-Fi", 7.9, 730000, 116, 7, 47.0, 203.4, "Paramount+"),
        (49, "Sicario", 2015, "Action", 7.7, 460000, 121, 7, 30.0, 84.9, "Amazon Prime"),
        (50, "Prisoners", 2013, "Thriller", 8.1, 780000, 153, 7, 46.0, 122.1, "Netflix"),

        # --- Bong Joon-ho (dir_id: 8) ---
        (51, "Parasite", 2019, "Thriller", 8.5, 900000, 132, 8, 11.4, 263.1, "Max"),
        (52, "Snowpiercer", 2013, "Action", 7.1, 370000, 126, 8, 40.0, 86.8, "Netflix"),
        (53, "Memories of Murder", 2003, "Crime", 8.1, 210000, 132, 8, 2.8, 11.5, "Amazon Prime"),

        # --- Hayao Miyazaki (dir_id: 9) ---
        (54, "Spirited Away", 2001, "Animation", 8.6, 820000, 125, 9, 19.0, 395.8, "Max"),
        (55, "Princess Mononoke", 1997, "Animation", 8.3, 430000, 134, 9, 23.5, 170.0, "Max"),
        (56, "The Boy and the Heron", 2023, "Animation", 7.5, 120000, 124, 9, 30.0, 167.9, "Max"),
        (57, "Howl's Moving Castle", 2004, "Animation", 8.2, 450000, 119, 9, 24.0, 236.0, "Max"),

        # --- Ridley Scott (dir_id: 10) ---
        (58, "Gladiator", 2000, "Action", 8.5, 1580000, 155, 10, 103.0, 503.1, "Amazon Prime"),
        (59, "Alien", 1979, "Horror", 8.5, 930000, 117, 10, 11.0, 184.7, "Disney+"),
        (60, "Blade Runner", 1982, "Sci-Fi", 8.1, 800000, 117, 10, 28.0, 41.7, "Max"),
        (61, "The Martian", 2015, "Sci-Fi", 8.0, 900000, 144, 10, 108.0, 630.2, "Disney+"),
        (62, "Napoleon", 2023, "Biography", 6.4, 140000, 158, 10, 200.0, 221.4, "Apple TV+"),

        # --- David Fincher (dir_id: 11) ---
        (63, "Fight Club", 1999, "Drama", 8.8, 2250000, 139, 11, 63.0, 101.2, "Amazon Prime"),
        (64, "Se7en", 1995, "Crime", 8.6, 1750000, 127, 11, 33.0, 327.3, "Max"),
        (65, "The Social Network", 2010, "Biography", 7.8, 740000, 120, 11, 40.0, 224.9, "Max"),
        (66, "Gone Girl", 2014, "Mystery", 8.1, 1050000, 149, 11, 61.0, 369.3, "Max"),
        (67, "Zodiac", 2007, "Crime", 7.7, 580000, 157, 11, 65.0, 84.8, "Paramount+"),
        (68, "Mank", 2020, "Biography", 6.8, 80000, 131, 11, 25.0, 0.1, "Netflix"),

        # --- Guillermo del Toro (dir_id: 12) ---
        (69, "Pan's Labyrinth", 2006, "Fantasy", 8.2, 690000, 118, 12, 19.0, 83.9, "Netflix"),
        (70, "The Shape of Water", 2017, "Fantasy", 7.3, 430000, 123, 12, 20.0, 195.3, "Disney+"),
        (71, "Pacific Rim", 2013, "Action", 6.9, 520000, 131, 12, 190.0, 411.0, "Max"),
        (72, "Hellboy", 2004, "Action", 6.8, 330000, 122, 12, 66.0, 99.8, "Max"),

        # --- Francis Ford Coppola (dir_id: 13) ---
        (73, "The Godfather", 1972, "Crime", 9.2, 2000000, 175, 13, 6.0, 250.0, "Paramount+"),
        (74, "The Godfather Part II", 1974, "Crime", 9.0, 1350000, 202, 13, 13.0, 48.0, "Paramount+"),
        (75, "Apocalypse Now", 1979, "War", 8.4, 700000, 147, 13, 31.5, 105.0, "Paramount+"),

        # --- Peter Jackson (dir_id: 14) ---
        (76, "The Lord of the Rings: The Return of the King", 2003, "Fantasy", 9.0, 1950000, 201, 14, 94.0, 1146.0, "Max"),
        (77, "The Lord of the Rings: The Fellowship of the Ring", 2001, "Fantasy", 8.8, 1980000, 178, 14, 93.0, 898.2, "Max"),
        (78, "The Lord of the Rings: The Two Towers", 2002, "Fantasy", 8.8, 1780000, 179, 14, 94.0, 947.9, "Max"),
        (79, "King Kong", 2005, "Action", 7.2, 440000, 187, 14, 207.0, 562.9, "Amazon Prime"),

        # --- Stanley Kubrick (dir_id: 15) ---
        (80, "2001: A Space Odyssey", 1968, "Sci-Fi", 8.3, 720000, 149, 15, 12.0, 65.0, "Max"),
        (81, "The Shining", 1980, "Horror", 8.4, 1100000, 146, 15, 19.0, 47.0, "Max"),
        (82, "A Clockwork Orange", 1971, "Sci-Fi", 8.3, 840000, 136, 15, 2.2, 27.0, "Max"),
        (83, "Full Metal Jacket", 1987, "War", 8.3, 750000, 116, 15, 30.0, 120.0, "Max"),

        # --- Jordan Peele (dir_id: 16) - High ROI Outliers ---
        (84, "Get Out", 2017, "Horror", 7.8, 670000, 104, 16, 4.5, 255.4, "Netflix"),
        (85, "Us", 2019, "Horror", 6.8, 320000, 116, 16, 20.0, 256.1, "Amazon Prime"),
        (86, "Nope", 2022, "Sci-Fi", 6.8, 260000, 130, 16, 68.0, 171.2, "Amazon Prime"),

        # --- Wes Anderson (dir_id: 17) ---
        (87, "The Grand Budapest Hotel", 2014, "Comedy", 8.1, 880000, 99, 17, 25.0, 173.0, "Disney+"),
        (88, "Fantastic Mr. Fox", 2009, "Animation", 7.9, 270000, 87, 17, 40.0, 46.5, "Disney+"),
        (89, "Moonrise Kingdom", 2012, "Comedy", 7.8, 360000, 94, 17, 16.0, 68.3, "Amazon Prime"),

        # --- Alfonso Cuaron (dir_id: 18) ---
        (90, "Gravity", 2013, "Sci-Fi", 7.7, 840000, 91, 18, 100.0, 723.2, "Max"),
        (91, "Children of Men", 2006, "Sci-Fi", 7.9, 530000, 109, 18, 76.0, 70.0, "Paramount+"),
        (92, "Roma", 2018, "Drama", 7.7, 170000, 135, 18, 15.0, 5.0, "Netflix"),

        # --- Damien Chazelle (dir_id: 19) ---
        (93, "Whiplash", 2014, "Drama", 8.5, 950000, 107, 19, 3.3, 49.0, "Netflix"),
        (94, "La La Land", 2016, "Comedy", 8.0, 630000, 128, 19, 30.0, 448.9, "Netflix"),
        (95, "First Man", 2018, "Biography", 7.3, 200000, 141, 19, 59.0, 105.7, "Amazon Prime"),
        (96, "Babylon", 2022, "Drama", 7.1, 160000, 189, 19, 80.0, 63.4, "Paramount+"),

        # --- Paul Thomas Anderson (dir_id: 20) ---
        (97, "There Will Be Blood", 2007, "Drama", 8.2, 620000, 158, 20, 25.0, 76.2, "Paramount+"),
        (98, "Boogie Nights", 1997, "Drama", 7.9, 270000, 155, 20, 15.0, 43.1, "Max"),

        # --- George Miller (dir_id: 21) ---
        (99, "Mad Max: Fury Road", 2015, "Action", 8.1, 1070000, 120, 21, 150.0, 380.4, "Max"),
        (100, "Furiosa: A Mad Max Saga", 2024, "Action", 7.6, 170000, 148, 21, 168.0, 172.8, "Max"),

        # --- Chad Stahelski (dir_id: 22) ---
        (101, "John Wick", 2014, "Action", 7.4, 710000, 101, 22, 20.0, 86.0, "Netflix"),
        (102, "John Wick: Chapter 2", 2017, "Action", 7.4, 480000, 122, 22, 40.0, 174.3, "Netflix"),
        (103, "John Wick: Chapter 3 - Parabellum", 2019, "Action", 7.4, 430000, 130, 22, 75.0, 327.7, "Netflix"),
        (104, "John Wick: Chapter 4", 2023, "Action", 7.7, 340000, 169, 22, 100.0, 440.1, "Netflix"),

        # --- Anthony Russo / Joe Russo (dir_id: 23) - Mega Blockbusters ---
        (105, "Avengers: Endgame", 2019, "Action", 8.4, 1250000, 181, 23, 356.0, 2799.4, "Disney+"),
        (106, "Avengers: Infinity War", 2018, "Action", 8.4, 1180000, 149, 23, 325.0, 2052.4, "Disney+"),
        (107, "Captain America: Civil War", 2016, "Action", 7.8, 770000, 147, 23, 250.0, 1153.3, "Disney+"),
        (108, "Captain America: The Winter Soldier", 2014, "Action", 7.8, 850000, 136, 23, 177.0, 714.4, "Disney+"),

        # --- Joseph Kosinski (dir_id: 24) ---
        (109, "Top Gun: Maverick", 2022, "Action", 8.2, 690000, 130, 24, 170.0, 1495.7, "Paramount+"),
        (110, "Tron: Legacy", 2010, "Sci-Fi", 6.8, 350000, 125, 24, 170.0, 400.1, "Disney+"),

        # --- Jon Favreau (dir_id: 25) ---
        (111, "Iron Man", 2008, "Action", 7.9, 1100000, 126, 25, 140.0, 585.8, "Disney+"),
        (112, "The Lion King", 2019, "Animation", 6.8, 250000, 118, 25, 260.0, 1663.0, "Disney+"),
        (113, "The Jungle Book", 2016, "Adventure", 7.4, 280000, 106, 25, 175.0, 966.5, "Disney+"),
        (114, "Elf", 2003, "Comedy", 7.1, 310000, 97, 25, 33.0, 225.1, "Max"),

        # --- High-Budget Flops & Catastrophic Outliers (Critical for ML Anomaly Detection!) ---
        (115, "John Carter", 2012, "Sci-Fi", 6.6, 280000, 132, 25, 263.0, 284.1, "Disney+"),
        (116, "The Lone Ranger", 2013, "Western", 6.4, 250000, 149, 3, 225.0, 260.5, "Disney+"),
        (117, "Madame Web", 2024, "Action", 3.8, 68000, 116, 22, 80.0, 100.5, "Netflix"),
        (118, "Cats", 2019, "Comedy", 2.8, 55000, 110, 14, 95.0, 75.5, "Amazon Prime"),
        (119, "Battleship", 2012, "Action", 5.8, 250000, 131, 21, 220.0, 303.0, "Netflix"),
        (120, "Green Lantern", 2011, "Action", 5.5, 290000, 114, 23, 200.0, 219.8, "Max"),
        (121, "Jupiter Ascending", 2015, "Sci-Fi", 5.3, 170000, 127, 21, 176.0, 183.9, "Max"),

        # --- Low-Budget Astronomical Return Outliers (Positive Anomalies!) ---
        (122, "Paranormal Activity", 2007, "Horror", 6.3, 250000, 86, 16, 0.015, 193.4, "Paramount+"),
        (123, "The Blair Witch Project", 1999, "Horror", 6.5, 270000, 81, 16, 0.06, 248.6, "Amazon Prime"),
        (124, "Everything Everywhere All At Once", 2022, "Sci-Fi", 7.8, 520000, 139, 12, 14.3, 143.4, "Netflix"),
        (125, "Slumdog Millionaire", 2008, "Drama", 8.0, 870000, 120, 8, 15.0, 378.1, "Max")
    ]
    cur.executemany("INSERT INTO movies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", movies)

    # ==========================================
    # SEED DATA: MOVIE CAST
    # ==========================================
    movie_cast = [
        (1, 1, 3, "Bruce Wayne / Batman"),
        (2, 2, 1, "Dom Cobb"),
        (3, 2, 2, "Robert Fischer"),
        (4, 3, 29, "Joseph Cooper"),
        (5, 3, 30, "Dr. Amelia Brand"),
        (6, 4, 2, "J. Robert Oppenheimer"),
        (7, 4, 5, "Lewis Strauss"),
        (8, 4, 7, "Jean Tatlock"),
        (9, 4, 26, "Katherine Oppenheimer"),
        (10, 11, 14, "Jules Winnfield"),
        (11, 12, 1, "Calvin Candie"),
        (12, 12, 14, "Stephen"),
        (13, 13, 8, "Lt. Aldo Raine"),
        (14, 14, 1, "Rick Dalton"),
        (15, 14, 8, "Cliff Booth"),
        (16, 14, 4, "Sharon Tate"),
        (17, 21, 6, "Captain John Miller"),
        (18, 21, 13, "Private James Ryan"),
        (19, 22, 1, "Frank Abagnale Jr."),
        (20, 22, 6, "Carl Hanratty"),
        (21, 29, 1, "Jordan Belfort"),
        (22, 29, 4, "Naomi Lapaglia"),
        (23, 29, 29, "Mark Hanna"),
        (24, 30, 1, "Billy Costigan"),
        (25, 30, 13, "Colin Sullivan"),
        (26, 32, 1, "Teddy Daniels"),
        (27, 36, 1, "Jack Dawson"),
        (28, 36, 15, "Rose DeWitt Bukater"),
        (29, 42, 4, "Barbie"),
        (30, 42, 12, "Ken"),
        (31, 45, 9, "Paul Atreides"),
        (32, 45, 10, "Chani"),
        (33, 45, 26, "Princess Irulan"),
        (34, 45, 27, "Stilgar"),
        (35, 46, 9, "Paul Atreides"),
        (36, 46, 10, "Chani"),
        (37, 46, 27, "Stilgar"),
        (38, 51, 11, "Kim Ki-taek"),
        (39, 58, 23, "Commodus"),
        (40, 63, 8, "Tyler Durden"),
        (41, 64, 8, "Detective David Mills"),
        (42, 64, 21, "Detective William Somerset"),
        (43, 73, 19, "Michael Corleone"),
        (44, 73, 20, "Vito Corleone"),
        (45, 74, 19, "Michael Corleone"),
        (46, 74, 20, "Young Vito Corleone"),
        (47, 84, 18, "Chris Washington"),
        (48, 93, 28, "Terence Fletcher"),
        (49, 94, 12, "Sebastian Wilder"),
        (50, 94, 7, "Mia Dolan"),
        (51, 99, 24, "Imperator Furiosa"),
        (52, 101, 17, "John Wick"),
        (53, 104, 17, "John Wick"),
        (54, 105, 5, "Tony Stark / Iron Man"),
        (55, 105, 25, "Steve Rogers / Captain America"),
        (56, 105, 22, "Natasha Romanoff / Black Widow"),
        (57, 109, 16, "Pete 'Maverick' Mitchell"),
        (58, 111, 5, "Tony Stark / Iron Man")
    ]
    cur.executemany("INSERT INTO movie_cast VALUES (?, ?, ?, ?);", movie_cast)

    # ==========================================
    # SEED DATA: REVIEWS
    # ==========================================
    reviews = [
        (1, 1, "Peter Travers", 9.8, "A visionary comic-book movie that transcends its genre.", "Positive"),
        (2, 2, "Roger Ebert", 9.5, "Mind-bending narrative with breathtaking visual ingenuity.", "Positive"),
        (3, 3, "A.O. Scott", 9.2, "An emotional and scientific epic on cosmic love and survival.", "Positive"),
        (4, 4, "Manohla Dargis", 9.6, "A cinematic tour-de-force capturing historical brilliance and terror.", "Positive"),
        (5, 11, "Richard Roeper", 9.4, "Quentin Tarantino's masterpiece of pop culture and non-linear storytelling.", "Positive"),
        (6, 20, "James Berardinelli", 8.8, "Spielberg delivers pure movie magic with awe-inspiring practical effects.", "Positive"),
        (7, 29, "Owen Gleiberman", 8.5, "Insanely entertaining, hyper-energetic satire of Wall Street excess.", "Positive"),
        (8, 36, "David Ansen", 9.0, "Spectacular storytelling with emotional weight that stands the test of time.", "Positive"),
        (9, 42, "Clarisse Loughrey", 8.0, "Hilarious, intelligent, and feminist pop-cultural triumph.", "Positive"),
        (10, 45, "David Ehrlich", 9.7, "Denis Villeneuve achieves sci-fi perfection in a monumental sequel.", "Positive"),
        (11, 51, "Justin Chang", 9.8, "A masterclass in tension, social commentary, and unexpected genre twists.", "Positive"),
        (12, 63, "Kenneth Turan", 9.1, "Brilliant, subversive satire of toxic masculinity and consumerism.", "Positive"),
        (13, 73, "Gene Siskel", 9.9, "The gold standard of American cinema and family crime dynasties.", "Positive"),
        (14, 84, "Ann Hornaday", 9.4, "An ingenious horror satire that redefined modern psychological thrillers.", "Positive"),
        (15, 93, "Stephanie Zacharek", 9.3, "Electrifying, relentless, and driven by blistering performances.", "Positive"),
        (16, 94, "Todd McCarthy", 8.8, "A radiant love letter to musical cinema and pursuing dreams.", "Positive"),
        (17, 99, "Mark Kermode", 9.2, "A relentless triumph of practical stunt work and visual adrenaline.", "Positive"),
        (18, 105, "Robbie Collin", 9.0, "The emotional and grand climax to a decade of superhero storytelling.", "Positive"),
        (19, 109, "Peter Bradshaw", 8.7, "A jaw-dropping, high-octane blockbuster with genuine emotional resonance.", "Positive"),
        (20, 117, "Alonso Duralde", 3.2, "Convoluted, lifeless, and fundamentally uninspired comic book adaptation.", "Negative"),
        (21, 118, "Peter Travers", 2.5, "A nightmarish visual miscalculation that defies logic.", "Negative"),
        (22, 122, "Roger Ebert", 7.5, "Terrifyingly effective proof that sound and suggestion beat big budgets.", "Positive")
    ]
    cur.executemany("INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?);", reviews)

    conn.commit()
    conn.close()
    return True, f"Successfully seeded {len(movies)} movies, {len(directors)} directors, {len(actors)} actors, and {len(reviews)} reviews!"

if __name__ == "__main__":
    ok, msg = generate_and_seed_movies()
    print(msg)
