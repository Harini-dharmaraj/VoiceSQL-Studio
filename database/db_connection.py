import os
import sqlite3

def get_db_connection():
    """Retrieve connection to SQLite or MySQL depending on current configurations."""
    from utils.config_manager import load_config
    config = load_config()
    
    if config["db_type"] == "SQLite":
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect("database/demo.db", check_same_thread=False)
        return conn
    else:
        import mysql.connector
        conn = mysql.connector.connect(
            host=config["mysql_host"],
            port=int(config["mysql_port"]),
            user=config["mysql_user"],
            password=config["mysql_password"],
            database=config["mysql_database"],
            buffered=True
        )
        return conn

def test_mysql_connection(host, port, user, password, database):
    """Test MySQL connection credentials and create the DB if it does not exist."""
    try:
        import mysql.connector
        # First connect without database selection to ensure server is reachable
        conn = mysql.connector.connect(
            host=host,
            port=int(port),
            user=user,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.close()
        conn.close()
        
        # Test connection selecting the database
        conn = mysql.connector.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database
        )
        conn.close()
        return True, "MySQL connection successful!"
    except Exception as e:
        return False, str(e)

def init_database():
    """Execute sample_data.sql to initialize tables and insert seed data."""
    from utils.config_manager import load_config
    config = load_config()
    
    sql_script_path = "database/sample_data.sql"
    if not os.path.exists(sql_script_path):
        return False, "Sample data script not found at database/sample_data.sql"
        
    with open(sql_script_path, "r") as f:
        sql_content = f.read()
        
    # Split queries by semicolon, filtering out comment lines and blank lines
    queries = []
    for q in sql_content.split(";"):
        lines = []
        for line in q.split("\n"):
            line_stripped = line.strip()
            # Skip comment lines and empty lines
            if line_stripped and not line_stripped.startswith("--") and not line_stripped.startswith("#"):
                lines.append(line)
        cleaned_query = "\n".join(lines).strip()
        if cleaned_query:
            queries.append(cleaned_query)
            
    if config["db_type"] == "SQLite":
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect("database/demo.db")
        cursor = conn.cursor()
        try:
            for query in queries:
                cursor.execute(query)
            # Create query_history table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                natural_query TEXT,
                sql_query TEXT,
                status TEXT,
                error_msg TEXT,
                execution_time REAL
            );
            """)
            conn.commit()
            return True, "SQLite database initialized successfully with sample data!"
        except Exception as e:
            conn.rollback()
            return False, f"SQLite initialization error: {e}"
        finally:
            cursor.close()
            conn.close()
    else:
        import mysql.connector
        try:
            # Create database first
            conn = mysql.connector.connect(
                host=config["mysql_host"],
                port=int(config["mysql_port"]),
                user=config["mysql_user"],
                password=config["mysql_password"]
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['mysql_database']}")
            cursor.close()
            conn.close()
            
            # Connect to database and seed tables
            conn = mysql.connector.connect(
                host=config["mysql_host"],
                port=int(config["mysql_port"]),
                user=config["mysql_user"],
                password=config["mysql_password"],
                database=config["mysql_database"]
            )
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)
            # Create query_history table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                natural_query TEXT,
                sql_query TEXT,
                status VARCHAR(50),
                error_msg TEXT,
                execution_time DECIMAL(10, 3)
            );
            """)
            conn.commit()
            return True, "MySQL database initialized successfully with sample data!"
        except Exception as e:
            return False, f"MySQL initialization error: {e}"
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

def get_db_schema_context():
    """Retrieve schema metadata formatted as a string for context feeding in AI prompting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        return f"Database offline or misconfigured: {e}"
        
    from utils.config_manager import load_config
    config = load_config()
    
    schema_str = ""
    try:
        if config["db_type"] == "SQLite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'query_history';")
            tables = [r[0] for r in cursor.fetchall()]
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                col_desc = [f"{col[1]} ({col[2]})" for col in columns]
                schema_str += f"Table: {table}\nColumns: {', '.join(col_desc)}\n\n"
        else:
            cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{config['mysql_database']}' AND table_name != 'query_history';")
            tables = [r[0] for r in cursor.fetchall()]
            for table in tables:
                cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{config['mysql_database']}' AND table_name = '{table}';")
                columns = cursor.fetchall()
                col_desc = [f"{col[0]} ({col[1]})" for col in columns]
                schema_str += f"Table: {table}\nColumns: {', '.join(col_desc)}\n\n"
    except Exception as e:
        schema_str = f"Error extracting schema: {e}"
    finally:
        cursor.close()
        conn.close()
        
    return schema_str
