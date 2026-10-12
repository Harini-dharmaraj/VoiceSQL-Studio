import hashlib
import secrets
from database.db_connection import get_db_connection
from utils.config_manager import load_config

def hash_password(password: str) -> str:
    """Generate salted SHA-256 hash."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}:{h}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt:hash."""
    try:
        salt, h = stored_hash.split(":")
        check = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        return h == check
    except Exception:
        return False

def init_auth_tables():
    """Ensure users and user_datasets tables exist in the database."""
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if is_sqlite:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_datasets (
                dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                table_name TEXT NOT NULL,
                display_name TEXT,
                row_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            """)
        else:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(150),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_datasets (
                dataset_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                table_name VARCHAR(100) NOT NULL,
                display_name VARCHAR(150),
                row_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """)
        conn.commit()

        # Seed default demo account if not exists
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'demo' OR email = 'demo@voicesql.com';")
        if cur.fetchone()[0] == 0:
            demo_hash = hash_password("demo123")
            if is_sqlite:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?);",
                    ("demo", "demo@voicesql.com", demo_hash, "Demo Explorer")
                )
            else:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, full_name) VALUES (%s, %s, %s, %s);",
                    ("demo", "demo@voicesql.com", demo_hash, "Demo Explorer")
                )
            conn.commit()
    except Exception as e:
        print(f"Error initializing auth tables: {e}")
    finally:
        cur.close()
        conn.close()

def register_user(username: str, email: str, password: str, full_name: str = "") -> tuple[bool, str]:
    """Register a new user account."""
    init_auth_tables()
    username = username.strip().lower()
    email = email.strip().lower()
    full_name = full_name.strip()

    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not email or "@" not in email:
        return False, "Please enter a valid email address."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."

    pwd_hash = hash_password(password)
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if username or email exists
        if is_sqlite:
            cur.execute("SELECT user_id FROM users WHERE username = ? OR email = ?;", (username, email))
        else:
            cur.execute("SELECT user_id FROM users WHERE username = %s OR email = %s;", (username, email))
        
        if cur.fetchone():
            return False, "A user with this username or email already exists."

        # Insert new user
        if is_sqlite:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?);",
                (username, email, pwd_hash, full_name or username.capitalize())
            )
        else:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, full_name) VALUES (%s, %s, %s, %s);",
                (username, email, pwd_hash, full_name or username.capitalize())
            )
        conn.commit()
        return True, "Account created successfully! You can now sign in."
    except Exception as e:
        return False, f"Database error: {e}"
    finally:
        cur.close()
        conn.close()

def authenticate_user(username_or_email: str, password: str) -> tuple[bool, dict | str]:
    """Authenticate user with username/email and password."""
    init_auth_tables()
    ident = username_or_email.strip().lower()
    if not ident or not password:
        return False, "Please enter both username/email and password."

    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if is_sqlite:
            cur.execute(
                "SELECT user_id, username, email, password_hash, full_name, created_at FROM users WHERE username = ? OR email = ?;",
                (ident, ident)
            )
        else:
            cur.execute(
                "SELECT user_id, username, email, password_hash, full_name, created_at FROM users WHERE username = %s OR email = %s;",
                (ident, ident)
            )
        row = cur.fetchone()
        if not row:
            return False, "User not found. Check your credentials or create a new account."

        user_id, username, email, stored_hash, full_name, created_at = row
        if verify_password(password, stored_hash):
            user_dict = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "full_name": full_name or username.capitalize(),
                "created_at": str(created_at)
            }
            return True, user_dict
        else:
            return False, "Incorrect password. Please try again."
    except Exception as e:
        return False, f"Authentication error: {e}"
    finally:
        cur.close()
        conn.close()

def record_user_dataset(user_id: int, table_name: str, display_name: str = "", row_count: int = 0):
    """Link an uploaded custom dataset table to a specific user."""
    init_auth_tables()
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if already recorded
        if is_sqlite:
            cur.execute("SELECT dataset_id FROM user_datasets WHERE user_id = ? AND table_name = ?;", (user_id, table_name))
        else:
            cur.execute("SELECT dataset_id FROM user_datasets WHERE user_id = %s AND table_name = %s;", (user_id, table_name))
        existing = cur.fetchone()

        if existing:
            if is_sqlite:
                cur.execute("UPDATE user_datasets SET row_count = ? WHERE dataset_id = ?;", (row_count, existing[0]))
            else:
                cur.execute("UPDATE user_datasets SET row_count = %s WHERE dataset_id = %s;", (row_count, existing[0]))
        else:
            if is_sqlite:
                cur.execute(
                    "INSERT INTO user_datasets (user_id, table_name, display_name, row_count) VALUES (?, ?, ?, ?);",
                    (user_id, table_name, display_name or table_name, row_count)
                )
            else:
                cur.execute(
                    "INSERT INTO user_datasets (user_id, table_name, display_name, row_count) VALUES (%s, %s, %s, %s);",
                    (user_id, table_name, display_name or table_name, row_count)
                )
        conn.commit()
    except Exception as e:
        print(f"Error recording user dataset: {e}")
    finally:
        cur.close()
        conn.close()

def get_user_datasets(user_id: int) -> list[dict]:
    """Retrieve all custom dataset tables created/uploaded by this user."""
    init_auth_tables()
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if is_sqlite:
            cur.execute(
                "SELECT dataset_id, table_name, display_name, row_count, created_at FROM user_datasets WHERE user_id = ? ORDER BY created_at DESC;",
                (user_id,)
            )
        else:
            cur.execute(
                "SELECT dataset_id, table_name, display_name, row_count, created_at FROM user_datasets WHERE user_id = %s ORDER BY created_at DESC;",
                (user_id,)
            )
        rows = cur.fetchall()
        return [
            {
                "dataset_id": r[0],
                "table_name": r[1],
                "display_name": r[2],
                "row_count": r[3],
                "created_at": str(r[4])
            }
            for r in rows
        ]
    except Exception:
        return []
    finally:
        cur.close()
        conn.close()
