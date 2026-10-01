import re
import requests
import json
from utils.config_manager import load_config
from database.db_connection import get_db_schema_context

_local_generator = None

def get_local_generator():
    """Lazily load the local Transformers pipeline to optimize startup memory and speed."""
    global _local_generator
    if _local_generator is None:
        from transformers import pipeline
        _local_generator = pipeline(
            "text2text-generation",
            model="google/flan-t5-base"
        )
    return _local_generator

def clean_sql_string(sql):
    """Strip markdown backticks, explanations, and trailing characters to clean the SQL query."""
    sql = re.sub(r'```(?:sql)?', '', sql, flags=re.IGNORECASE)
    sql = sql.replace("```", "").strip()
    
    # Extract only lines that appear to be SQL
    lines = [line.strip() for line in sql.split('\n') if line.strip()]
    cleaned_lines = []
    found_sql = False
    for l in lines:
        if any(l.upper().startswith(p) for p in ["SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN", "FROM", "WHERE", "JOIN", "ORDER", "GROUP", "LIMIT", "HAVING"]):
            found_sql = True
            cleaned_lines.append(l)
        elif found_sql and not any(p in l.lower() for p in ["here is", "this query", "note:", "explanation:"]):
            cleaned_lines.append(l)
            
    if cleaned_lines:
        sql = " ".join(cleaned_lines)
    else:
        sql = " ".join(lines)
        
    sql = " ".join(sql.split())
    if not sql.endswith(";") and sql:
        sql += ";"
    return sql

def generate_sql_mock(question):
    """Rule-based query generator supporting both E-Commerce and Legacy schema."""
    q = question.lower()
    
    # ==========================================
    # E-COMMERCE & RETAIL QUERIES
    # ==========================================
    if "expensive product" in q or ("highest" in q and "price" in q):
        return "SELECT product_name, category, unit_price FROM products ORDER BY unit_price DESC LIMIT 5;"
    elif "cheapest product" in q or ("lowest" in q and "price" in q):
        return "SELECT product_name, category, unit_price FROM products ORDER BY unit_price ASC LIMIT 5;"
    elif "technology" in q and "product" in q:
        return "SELECT product_name, sub_category, unit_price FROM products WHERE category = 'Technology' ORDER BY unit_price DESC;"
    elif "furniture" in q:
        return "SELECT product_name, sub_category, unit_price FROM products WHERE category = 'Furniture' ORDER BY unit_price DESC;"
    elif "office" in q and ("supply" in q or "supplies" in q or "product" in q):
        return "SELECT product_name, sub_category, unit_price FROM products WHERE category = 'Office Supplies' ORDER BY unit_price DESC;"
    elif "all products" in q or "show products" in q or "list products" in q:
        return "SELECT product_id, product_name, category, unit_price, cost_price FROM products ORDER BY product_id ASC;"
    elif "total revenue" in q or "total sale" in q or "total sales" in q:
        return "SELECT SUM(total_sale_amount) AS total_revenue, SUM(profit_amount) AS total_profit FROM order_items;"
    elif "top customer" in q or "highest spending" in q:
        return "SELECT c.customer_name, c.city, c.customer_segment, SUM(o.order_total) AS total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.customer_name, c.city, c.customer_segment ORDER BY total_spent DESC LIMIT 5;"
    elif "customer" in q and ("all" in q or "show" in q or "list" in q):
        return "SELECT customer_id, customer_name, email, city, state, customer_segment FROM customers LIMIT 25;"
    elif "delivered" in q and "order" in q:
        return "SELECT order_id, order_date, shipping_mode, payment_method, order_total FROM orders WHERE order_status = 'Delivered' ORDER BY order_id DESC LIMIT 15;"
    elif "all order" in q or "show order" in q or "list order" in q:
        return "SELECT order_id, customer_id, order_date, shipping_mode, payment_method, order_status, order_total FROM orders ORDER BY order_id DESC LIMIT 20;"
    elif "payment" in q:
        return "SELECT payment_method, COUNT(*) AS total_orders, SUM(order_total) AS total_volume FROM orders GROUP BY payment_method ORDER BY total_volume DESC;"
    elif "shipping" in q or "delivery" in q:
        return "SELECT shipping_mode, COUNT(*) AS order_count FROM orders GROUP BY shipping_mode;"
    elif "profit" in q and "product" in q:
        return "SELECT p.product_name, p.category, SUM(oi.profit_amount) AS total_profit FROM products p JOIN order_items oi ON p.product_id = oi.product_id GROUP BY p.product_id, p.product_name, p.category ORDER BY total_profit DESC LIMIT 5;"

    # ==========================================
    # LEGACY EMPLOYEE & PROJECT QUERIES
    # ==========================================
    if "highest" in q and "salary" in q:
        return "SELECT * FROM employees WHERE salary = (SELECT MAX(salary) FROM employees);"
    elif "salary" in q and "above" in q:
        match = re.search(r'above\s+(\d+)', q)
        val = match.group(1) if match else "50000"
        return f"SELECT * FROM employees WHERE salary > {val};"
    elif "engineering" in q and ("employee" in q or "department" in q):
        return "SELECT * FROM employees WHERE department_id = 1;"
    elif "hr" in q or "human resources" in q:
        return "SELECT * FROM employees WHERE department_id = 2;"
    elif "project" in q and "budget" in q:
        return "SELECT project_name, budget FROM projects ORDER BY budget DESC;"
    elif "employee" in q and ("all" in q or "show" in q):
        return "SELECT * FROM employees;"
    elif "department" in q:
        return "SELECT * FROM departments;"

    # ==========================================
    # DYNAMIC TABLE INSPECTION (User-Uploaded Tables)
    # ==========================================
    try:
        from database.db_connection import get_db_connection
        cfg = load_config()
        conn = get_db_connection()
        cur = conn.cursor()
        if cfg.get("db_type") == "SQLite":
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'query_history';")
        else:
            cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{cfg.get('mysql_database', 'voice_to_sql')}' AND table_name != 'query_history';")
        all_tables = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()

        for t in all_tables:
            t_clean = t.lower()
            if t_clean in q or (len(t_clean) > 3 and t_clean.rstrip('s') in q):
                if "count" in q or "how many" in q or "total" in q:
                    return f"SELECT COUNT(*) AS total_count FROM {t};"
                return f"SELECT * FROM {t} LIMIT 25;"
    except Exception:
        pass

    return "SELECT * FROM products LIMIT 10;"

def generate_sql_gemini(question, schema_context, api_key):
    """Generate SQL using Google Gemini API (via direct REST API)."""
    prompt = f"""You are a senior database architect and Text-to-SQL expert.
Given the following database schema, convert the user's natural language question into a clean, accurate SQL query.

DATABASE SCHEMA:
{schema_context}

RULES:
1. Return ONLY the raw SQL query. Do not wrap in markdown or backticks (no ```sql).
2. Do not write explanations, greetings, or conversational commentary.
3. For aggregation or JOIN queries, use proper table aliases and JOIN keys.
4. Only generate safe SELECT queries. Never generate DROP, ALTER, DELETE, or UPDATE.

USER QUESTION: {question}
SQL QUERY:"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 300
        }
    }

    # Try supported models in sequence
    candidate_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-pro"]
    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                res_data = response.json()
                candidates = res_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        return clean_sql_string(parts[0]['text'])
        except Exception:
            continue

    # Safe Fallback to rule engine if API key is invalid or quota is exceeded
    return generate_sql_mock(question)

def generate_sql_openai(question, schema_context, api_key):
    """Generate SQL using OpenAI Chat Completion API (via direct HTTP request)."""
    prompt = f"""You are a database expert. Convert this natural language question into a clean SQL query.
Schema:
{schema_context}

Output ONLY the raw SQL query without markdown backticks or explanations.

Question: {question}
SQL:"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a database expert that outputs raw SQL code only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            sql = res_data['choices'][0]['message']['content']
            return clean_sql_string(sql)
    except Exception:
        pass
    return generate_sql_mock(question)

def generate_sql_local(question, schema_context):
    """Generate SQL using local Transformers model with safe fallback."""
    try:
        generator = get_local_generator()
        prompt = f"Convert natural language to SQL.\nDatabase Schema:\n{schema_context}\n\nQuestion: {question}\nSQL:"
        result = generator(prompt, max_new_tokens=100)
        raw_output = result[0]["generated_text"]
        if "SQL:" in raw_output:
            raw_output = raw_output.split("SQL:")[-1]
        return clean_sql_string(raw_output)
    except Exception:
        return generate_sql_mock(question)

def generate_sql(question):
    """Main SQL generation router based on configuration settings."""
    config = load_config()
    schema_context = get_db_schema_context()
    
    provider = str(config.get("ai_provider", "Mock")).strip()
    
    if provider in ["Google Gemini", "Gemini"]:
        api_key = config.get("gemini_api_key", "").strip()
        if not api_key:
            return "SELECT 'Error: Gemini API Key not configured in Settings. Please enter your key in Settings.' AS error;"
        return generate_sql_gemini(question, schema_context, api_key)
        
    elif provider in ["OpenAI", "ChatGPT"]:
        api_key = config.get("openai_api_key", "").strip()
        if not api_key:
            return "SELECT 'Error: OpenAI API Key not configured in Settings. Please enter your key in Settings.' AS error;"
        return generate_sql_openai(question, schema_context, api_key)
        
    elif provider in ["Local (Flan-T5)", "Local"]:
        return generate_sql_local(question, schema_context)
        
    else:
        # Default: "Offline Rules", "Offline Rules (Fast)", "Mock"
        return generate_sql_mock(question)