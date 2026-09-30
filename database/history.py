import pandas as pd
from database.db_connection import get_db_connection
from utils.config_manager import load_config

def log_query(natural_query, sql_query, status, error_msg, execution_time):
    """Log an executed query details into the database's query_history table."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        config = load_config()
        
        # Adjust placeholders based on database engine
        if config["db_type"] == "SQLite":
            cursor.execute("""
            INSERT INTO query_history (natural_query, sql_query, status, error_msg, execution_time)
            VALUES (?, ?, ?, ?, ?)
            """, (natural_query, sql_query, status, error_msg, execution_time))
        else:
            cursor.execute("""
            INSERT INTO query_history (natural_query, sql_query, status, error_msg, execution_time)
            VALUES (%s, %s, %s, %s, %s)
            """, (natural_query, sql_query, status, error_msg, execution_time))
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

def get_query_history(limit=100):
    """Retrieve executed queries history as a DataFrame."""
    conn = None
    try:
        conn = get_db_connection()
        query = f"SELECT id, timestamp, natural_query, sql_query, status, error_msg, execution_time FROM query_history ORDER BY id DESC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error fetching query history: {e}")
        return pd.DataFrame(columns=["id", "timestamp", "natural_query", "sql_query", "status", "error_msg", "execution_time"])
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
