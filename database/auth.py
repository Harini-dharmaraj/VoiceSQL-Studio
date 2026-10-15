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

SYSTEM_TABLES = {"users", "user_datasets", "query_history", "sqlite_sequence"}

def get_admin_usernames() -> list[str]:
    """Retrieve list of configured admin usernames from config."""
    try:
        config = load_config()
        admins = config.get("admin_users", ["admin", "harini"])
        if isinstance(admins, list):
            return [str(a).strip().lower() for a in admins]
        elif isinstance(admins, str):
            return [admins.strip().lower()]
    except Exception:
        pass
    return ["admin", "harini"]

def is_admin_user(user: dict = None) -> bool:
    """Check if given user (or active session user) has admin privileges."""
    if user is None:
        try:
            import streamlit as st
            user = st.session_state.get("current_user", {})
        except Exception:
            user = {}
    if not user:
        return False
    if user.get("role") == "admin":
        return True
    u_name = str(user.get("username", "")).strip().lower()
    return u_name in get_admin_usernames()

def init_auth_tables():
    """Ensure users and user_datasets tables exist in the database with role column and admin sync."""
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")
    admin_list = get_admin_usernames()
    
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
                role TEXT DEFAULT 'user',
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
            
            # Migration check: Ensure 'role' column exists in existing SQLite table
            cur.execute("PRAGMA table_info(users);")
            cols = [col[1] for col in cur.fetchall()]
            if "role" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';")

        else:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(150),
                role VARCHAR(20) DEFAULT 'user',
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

            # Migration check: Ensure 'role' column exists in existing MySQL table
            db_name = config.get("mysql_database", "voice_to_sql")
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{db_name}' AND table_name = 'users' AND column_name = 'role';")
            if not cur.fetchone():
                cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';")

        conn.commit()

        # Seed dedicated Admin account with preset ID & password: admin / admin123
        admin_hash = hash_password("admin123")
        cur.execute("SELECT user_id FROM users WHERE username = 'admin' OR email = 'admin@voicesql.com';")
        admin_row = cur.fetchone()
        if not admin_row:
            if is_sqlite:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?);",
                    ("admin", "admin@voicesql.com", admin_hash, "System Administrator", "admin")
                )
            else:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (%s, %s, %s, %s, %s);",
                    ("admin", "admin@voicesql.com", admin_hash, "System Administrator", "admin")
                )
            conn.commit()
        else:
            # Ensure admin password is reset to admin123 and role is admin
            if is_sqlite:
                cur.execute("UPDATE users SET password_hash = ?, role = 'admin' WHERE user_id = ?;", (admin_hash, admin_row[0]))
            else:
                cur.execute("UPDATE users SET password_hash = %s, role = 'admin' WHERE user_id = %s;", (admin_hash, admin_row[0]))
            conn.commit()

        # Sync configured admin users so developer account always has role = 'admin'
        for adm in admin_list:
            if is_sqlite:
                cur.execute("UPDATE users SET role = 'admin' WHERE LOWER(username) = ?;", (adm,))
            else:
                cur.execute("UPDATE users SET role = 'admin' WHERE LOWER(username) = %s;", (adm,))
        conn.commit()

    except Exception as e:
        print(f"Error initializing auth tables: {e}")
    finally:
        cur.close()
        conn.close()

def register_user(username: str, email: str, password: str, full_name: str = "") -> tuple[bool, str]:
    """Register a new user account with role assignment."""
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
    admin_list = get_admin_usernames()
    assigned_role = "admin" if username in admin_list else "user"

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

        # Insert new user with role
        if is_sqlite:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?);",
                (username, email, pwd_hash, full_name or username.capitalize(), assigned_role)
            )
        else:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (%s, %s, %s, %s, %s);",
                (username, email, pwd_hash, full_name or username.capitalize(), assigned_role)
            )
        conn.commit()
        return True, "Account created successfully! You can now sign in."
    except Exception as e:
        return False, f"Database error: {e}"
    finally:
        cur.close()
        conn.close()

def authenticate_user(username_or_email: str, password: str) -> tuple[bool, dict | str]:
    """Authenticate user with username/email and password, retrieving role."""
    init_auth_tables()
    ident = username_or_email.strip().lower()
    if not ident or not password:
        return False, "Please enter both username/email and password."

    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")
    admin_list = get_admin_usernames()

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if is_sqlite:
            cur.execute(
                "SELECT user_id, username, email, password_hash, full_name, created_at, role FROM users WHERE username = ? OR email = ?;",
                (ident, ident)
            )
        else:
            cur.execute(
                "SELECT user_id, username, email, password_hash, full_name, created_at, role FROM users WHERE username = %s OR email = %s;",
                (ident, ident)
            )
        row = cur.fetchone()
        if not row:
            return False, "User not found. Check your credentials or create a new account."

        user_id, username, email, stored_hash, full_name, created_at, role = row
        if verify_password(password, stored_hash):
            is_adm = (role == "admin") or (username.lower() in admin_list)
            user_dict = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "full_name": full_name or username.capitalize(),
                "created_at": str(created_at),
                "role": "admin" if is_adm else (role or "user")
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

def get_all_users_for_admin() -> list[dict]:
    """
    Retrieve registered users for the admin management view.
    NOTE: password_hash is strictly excluded for security and privacy.
    """
    init_auth_tables()
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT u.user_id, u.username, u.email, u.full_name, u.role, u.created_at,
                   COUNT(d.dataset_id) as total_datasets
            FROM users u
            LEFT JOIN user_datasets d ON u.user_id = d.user_id
            GROUP BY u.user_id
            ORDER BY u.user_id ASC;
        """)
        rows = cur.fetchall()
        return [
            {
                "user_id": r[0],
                "username": r[1],
                "email": r[2],
                "full_name": r[3],
                "role": r[4] or "user",
                "created_at": str(r[5]),
                "total_datasets": r[6]
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error fetching admin user list: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def update_user_role(target_user_id: int, new_role: str) -> tuple[bool, str]:
    """Change a user's role (admin / user)."""
    if new_role not in ["admin", "user"]:
        return False, "Invalid role. Must be 'admin' or 'user'."
    init_auth_tables()
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if is_sqlite:
            cur.execute("UPDATE users SET role = ? WHERE user_id = ?;", (new_role, target_user_id))
        else:
            cur.execute("UPDATE users SET role = %s WHERE user_id = %s;", (new_role, target_user_id))
        conn.commit()
        return True, f"User role updated to '{new_role}' successfully."
    except Exception as e:
        return False, f"Failed to update role: {e}"
    finally:
        cur.close()
        conn.close()

def delete_user_by_admin(target_user_id: int) -> tuple[bool, str]:
    """Delete a user account and associated dataset records."""
    init_auth_tables()
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if is_sqlite:
            cur.execute("DELETE FROM user_datasets WHERE user_id = ?;", (target_user_id,))
            cur.execute("DELETE FROM users WHERE user_id = ?;", (target_user_id,))
        else:
            cur.execute("DELETE FROM user_datasets WHERE user_id = %s;", (target_user_id,))
            cur.execute("DELETE FROM users WHERE user_id = %s;", (target_user_id,))
        conn.commit()
        return True, "User account deleted successfully."
    except Exception as e:
        return False, f"Failed to delete user: {e}"
    finally:
        cur.close()
        conn.close()

def get_all_user_datasets_for_admin() -> list[dict]:
    """Retrieve all datasets uploaded across all users for admin oversight."""
    init_auth_tables()
    config = load_config()
    is_sqlite = (config.get("db_type", "SQLite") == "SQLite")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT d.dataset_id, u.username, u.email, d.table_name, d.display_name, d.row_count, d.created_at
            FROM user_datasets d
            JOIN users u ON d.user_id = u.user_id
            ORDER BY d.created_at DESC;
        """)
        rows = cur.fetchall()
        return [
            {
                "dataset_id": r[0],
                "username": r[1],
                "email": r[2],
                "table_name": r[3],
                "display_name": r[4],
                "row_count": r[5],
                "created_at": str(r[6])
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error fetching all user datasets: {e}")
        return []
    finally:
        cur.close()
        conn.close()


