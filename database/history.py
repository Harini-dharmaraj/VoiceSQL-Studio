import pandas as pd
from database.db_connection import get_db_connection
from utils.config_manager import load_config

def _ensure_history_schema(cursor, is_sqlite, db_name="voice_to_sql"):
    """Ensure username column exists in query_history table."""
    try:
        if is_sqlite:
            cursor.execute("PRAGMA table_info(query_history);")
            cols = [c[1] for c in cursor.fetchall()]
            if "username" not in cols:
                cursor.execute("ALTER TABLE query_history ADD COLUMN username TEXT DEFAULT 'user';")
        else:
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{db_name}' AND table_name = 'query_history' AND column_name = 'username';")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE query_history ADD COLUMN username VARCHAR(80) DEFAULT 'user';")
    except Exception:
        pass

def log_query(natural_query, sql_query, status, error_msg, execution_time, username=None):
    """Log an executed query details with username into the database's query_history table."""
    if username is None:
        try:
            import streamlit as st
            user = st.session_state.get("current_user", {})
            username = user.get("username", "user")
        except Exception:
            username = "user"

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        config = load_config()
        is_sqlite = (config.get("db_type", "SQLite") == "SQLite")
        db_name = config.get("mysql_database", "voice_to_sql")
        
        _ensure_history_schema(cursor, is_sqlite, db_name)

        if is_sqlite:
            cursor.execute("""
            INSERT INTO query_history (username, natural_query, sql_query, status, error_msg, execution_time)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (username, natural_query, sql_query, status, error_msg, execution_time))
        else:
            cursor.execute("""
            INSERT INTO query_history (username, natural_query, sql_query, status, error_msg, execution_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, natural_query, sql_query, status, error_msg, execution_time))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging query to history: {e}")
        return False
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

def get_query_history(limit=100, username=None):
    """Retrieve executed queries history as a DataFrame. Can filter by username."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        config = load_config()
        is_sqlite = (config.get("db_type", "SQLite") == "SQLite")
        db_name = config.get("mysql_database", "voice_to_sql")
        _ensure_history_schema(cursor, is_sqlite, db_name)
        cursor.close()

        if username:
            if is_sqlite:
                query = f"SELECT id, timestamp, username, natural_query, sql_query, status, error_msg, execution_time FROM query_history WHERE username = ? ORDER BY id DESC LIMIT {limit}"
                df = pd.read_sql_query(query, conn, params=(username,))
            else:
                query = f"SELECT id, timestamp, username, natural_query, sql_query, status, error_msg, execution_time FROM query_history WHERE username = %s ORDER BY id DESC LIMIT {limit}"
                df = pd.read_sql_query(query, conn, params=(username,))
        else:
            query = f"SELECT id, timestamp, username, natural_query, sql_query, status, error_msg, execution_time FROM query_history ORDER BY id DESC LIMIT {limit}"
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error fetching query history: {e}")
        return pd.DataFrame(columns=["id", "timestamp", "username", "natural_query", "sql_query", "status", "error_msg", "execution_time"])
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def clear_query_history():
    """Delete all records from the query_history table."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_history")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing query history: {e}")
        return False
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
