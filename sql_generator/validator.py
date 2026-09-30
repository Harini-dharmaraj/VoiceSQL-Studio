import re

FORBIDDEN = [
    "DROP",
    "DELETE",
    "TRUNCATE",
    "ALTER",
    "UPDATE",
    "INSERT",
    "REPLACE",
    "GRANT",
    "REVOKE"
]

def validate_sql(sql):
    """
    Validate SQL query to verify it is read-only and safe to execute.
    Returns: True if valid and safe, False otherwise.
    """
    if not sql:
        return False
        
    sql_upper = sql.upper().strip()
    
    # Check for forbidden keywords using word boundaries
    for keyword in FORBIDDEN:
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, sql_upper):
            return False
            
    return True