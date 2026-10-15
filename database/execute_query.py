import time
import re
import warnings
import pandas as pd
from database.db_connection import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

RESTRICTED_AUTH_TABLES = ["users", "user_datasets"]

def is_query_authorized(query: str, allow_system_tables: bool = False, user_role: str = None) -> tuple[bool, str]:
    """Check if query touches sensitive authentication tables without admin clearance."""
    if allow_system_tables:
        return True, ""
    
    # Auto-detect role from session state if in Streamlit context
    if user_role is None:
        try:
            import streamlit as st
            user = st.session_state.get("current_user", {})
            user_role = user.get("role", "user")
        except Exception:
            user_role = "user"

    if user_role == "admin":
        return True, ""

    # Inspect SQL tokens for restricted table names
    for tbl in RESTRICTED_AUTH_TABLES:
        pattern = rf"\b{re.escape(tbl)}\b"
        if re.search(pattern, query, re.IGNORECASE):
            return False, f"Security Restriction: Access to internal user authentication table '{tbl}' is restricted to administrators."

    return True, ""

def execute_sql_query(query: str, allow_system_tables: bool = False, user_role: str = None):
    """
    Execute SQL, measure execution latency, and return results.
    Guarded against unauthorized access to authentication/system tables.
    Returns: (success, result_data, execution_time_ms, error_msg)
    """
    start_time = time.time()
    
    # Security Guard Check
    authorized, auth_err = is_query_authorized(query, allow_system_tables, user_role)
    if not authorized:
        return False, None, 0, auth_err

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
