import time
import warnings
import pandas as pd
from database.db_connection import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

def execute_sql_query(query):
    """
    Execute SQL, measure execution latency, and return results.
    Returns: (success, result_data, execution_time_ms, error_msg)
    """
    start_time = time.time()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        query_strip = query.strip().upper()
        
        # Check if the query is a data-retrieval command
        is_select = any(query_strip.startswith(prefix) for prefix in ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "PRAGMA"])
        
        if is_select:
            # Load SELECT query results into a Pandas DataFrame
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = pd.read_sql_query(query, conn)
            execution_time_ms = (time.time() - start_time) * 1000
            return True, df, execution_time_ms, ""
        else:
            # Non-select operations (INSERT, UPDATE, CREATE, etc.)
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            row_count = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            execution_time_ms = (time.time() - start_time) * 1000
            msg = f"Query executed successfully. Rows affected: {row_count}"
            return True, msg, execution_time_ms, ""
            
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return False, None, execution_time_ms, str(e)
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
