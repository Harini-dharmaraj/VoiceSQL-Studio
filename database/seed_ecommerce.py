import os
import sys
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from database.db_connection import get_db_connection
from utils.config_manager import load_config

def generate_and_seed_ecommerce():
    """Generates realistic E-Commerce Store dataset and seeds into active database."""
    random.seed(42)
    os.makedirs("datasets", exist_ok=True)

    # 1. CUSTOMERS
    first_names = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Margaret", "Anthony", "Betty", "Donald", "Sandra", "Mark", "Ashley",
        "Paul", "Dorothy", "Steven", "Kimberly", "Andrew", "Emily", "Kenneth", "Donna",
        "Joshua", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
        "Edward", "Deborah"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
    ]
    cities = [
        ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"),
        ("Phoenix", "AZ"), ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"),
        ("Dallas", "TX"), ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
        ("San Francisco", "CA"), ("Seattle", "WA"), ("Denver", "CO"), ("Boston", "MA")
    ]
    segments = ["Consumer", "Corporate", "Home Office"]

    customers_data = []
    for cid in range(1, 51):
        fn = first_names[cid - 1]
        ln = random.choice(last_names)
        city, state = random.choice(cities)
        email = f"{fn.lower()}.{ln.lower()}{random.randint(10, 99)}@example.com"
        segment = random.choices(segments, weights=[0.55, 0.30, 0.15])[0]
        customers_data.append({
            "customer_id": cid,
            "customer_name": f"{fn} {ln}",
            "email": email,
            "city": city,
            "state": state,
            "country": "United States",
            "customer_segment": segment
        })
    df_customers = pd.DataFrame(customers_data)

    # 2. PRODUCTS
    products_catalog = [
        ("Apple iPhone 15 Pro", "Technology", "Phones", 999.00, 750.00),
        ("Samsung Galaxy S24 Ultra", "Technology", "Phones", 1199.00, 890.00),
        ("Google Pixel 8 Pro", "Technology", "Phones", 899.00, 680.00),
        ("Apple MacBook Pro 14", "Technology", "Laptops", 1999.00, 1550.00),
        ("Dell XPS 15 Laptop", "Technology", "Laptops", 1699.00, 1300.00),
        ("Lenovo ThinkPad X1 Carbon", "Technology", "Laptops", 1450.00, 1100.00),
        ("Sony WH-1000XM5 Headphones", "Technology", "Audio", 399.00, 260.00),
        ("Apple AirPods Pro 2", "Technology", "Audio", 249.00, 160.00),
        ("Bose QuietComfort Ultra", "Technology", "Audio", 429.00, 290.00),
        ("LG 27-inch 4K UltraFine Monitor", "Technology", "Displays", 549.00, 390.00),
        ("Dell UltraSharp 34 Curved", "Technology", "Displays", 799.00, 580.00),
        ("Logitech MX Master 3S Mouse", "Technology", "Accessories", 99.00, 55.00),
        ("Keychron K2 Mechanical Keyboard", "Technology", "Accessories", 89.00, 48.00),
        ("Anker 100W USB-C Fast Charger", "Technology", "Accessories", 49.00, 22.00),
        
        ("Herman Miller Aeron Chair", "Furniture", "Chairs", 1250.00, 820.00),
        ("Steelcase Gesture Office Chair", "Furniture", "Chairs", 1100.00, 740.00),
        ("Branch Ergonomic Task Chair", "Furniture", "Chairs", 349.00, 210.00),
        ("Uplift V2 Standing Desk", "Furniture", "Desks", 699.00, 440.00),
        ("Fully Jarvis Bamboo Standing Desk", "Furniture", "Desks", 649.00, 410.00),
        ("IKEA Bekant Corner Desk", "Furniture", "Desks", 279.00, 160.00),
        ("Modern 3-Drawer Steel File Cabinet", "Furniture", "Storage", 189.00, 110.00),
        ("Tribesigns 5-Tier Bookcase", "Furniture", "Storage", 159.00, 85.00),
        ("Luxor Mobile Whiteboard Stand", "Furniture", "Furnishings", 229.00, 130.00),
        
        ("HP LaserJet Pro Multifunction Printer", "Office Supplies", "Machines", 389.00, 270.00),
        ("Epson EcoTank Wireless Printer", "Office Supplies", "Machines", 299.00, 210.00),
        ("Fellowes 12-Sheet Cross-Cut Shredder", "Office Supplies", "Machines", 149.00, 95.00),
        ("Hammermill Premium Copy Paper (Case)", "Office Supplies", "Paper", 48.00, 28.00),
        ("Moleskine Classic Hardcover Journal", "Office Supplies", "Paper", 22.00, 9.00),
        ("Avery Heavy-Duty 3-Ring Binders (6-Pk)", "Office Supplies", "Binders", 34.00, 15.00),
        ("Pilot G2 Gel Roller Pens (Pack of 12)", "Office Supplies", "Writing", 18.00, 7.00),
    ]

    products_data = []
    for pid, (pname, cat, subcat, price, cost) in enumerate(products_catalog, start=1):
        products_data.append({
            "product_id": pid,
            "product_name": pname,
            "category": cat,
            "sub_category": subcat,
            "unit_price": price,
            "cost_price": cost
        })
    df_products = pd.DataFrame(products_data)

    # 3. ORDERS & ORDER ITEMS
    shipping_modes = ["Standard Delivery", "Express Air", "Same Day Priority"]
    payment_methods = ["Credit Card", "PayPal", "Apple Pay", "Wire Transfer"]
    statuses = ["Delivered", "Delivered", "Delivered", "Delivered", "Shipped", "Processing"]

    orders_data = []
    order_items_data = []
    item_id_counter = 1

    start_date = datetime(2026, 1, 1)
    
    for oid in range(1, 121):
        cid = random.randint(1, 50)
        days_offset = random.randint(0, 260)
        order_dt = start_date + timedelta(days=days_offset)
        ship_mode = random.choices(shipping_modes, weights=[0.60, 0.30, 0.10])[0]
        pay_method = random.choice(payment_methods)
        status = random.choice(statuses)

        # Number of items in this order (1 to 4)
        num_items = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
        chosen_products = random.sample(products_catalog, num_items)

        order_total_sales = 0.0

        for prod_tuple in chosen_products:
            pname = prod_tuple[0]
            pid = next(p["product_id"] for p in products_data if p["product_name"] == pname)
            u_price = prod_tuple[3]
            u_cost = prod_tuple[4]
            qty = random.choices([1, 2, 3, 5], weights=[0.7, 0.2, 0.07, 0.03])[0]
            discount_pct = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[0.5, 0.2, 0.15, 0.1, 0.05])[0]

            gross_amount = u_price * qty
            total_sale = round(gross_amount * (1.0 - discount_pct), 2)
            total_cost = round(u_cost * qty, 2)
            profit = round(total_sale - total_cost, 2)

            order_total_sales += total_sale

            order_items_data.append({
                "item_id": item_id_counter,
                "order_id": oid,
                "product_id": pid,
                "quantity": qty,
                "discount_percent": int(discount_pct * 100),
                "total_sale_amount": total_sale,
                "profit_amount": profit
            })
            item_id_counter += 1

        orders_data.append({
            "order_id": oid,
            "customer_id": cid,
            "order_date": order_dt.strftime("%Y-%m-%d"),
            "shipping_mode": ship_mode,
            "payment_method": pay_method,
            "order_status": status,
            "order_total": round(order_total_sales, 2)
        })

    df_orders = pd.DataFrame(orders_data)
    df_order_items = pd.DataFrame(order_items_data)

    # Save to CSV files for user reference
    df_customers.to_csv("datasets/customers.csv", index=False)
    df_products.to_csv("datasets/products.csv", index=False)
    df_orders.to_csv("datasets/orders.csv", index=False)
    df_order_items.to_csv("datasets/order_items.csv", index=False)

    # Seed into active database
    config = load_config()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if config.get("db_type") == "SQLite":
            df_customers.to_sql("customers", conn, if_exists="replace", index=False)
            df_products.to_sql("products", conn, if_exists="replace", index=False)
            df_orders.to_sql("orders", conn, if_exists="replace", index=False)
            df_order_items.to_sql("order_items", conn, if_exists="replace", index=False)
            conn.commit()
        else:
            # MySQL Database
            tables_to_create = [
                ("customers", """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INT PRIMARY KEY,
                    customer_name VARCHAR(100),
                    email VARCHAR(120),
                    city VARCHAR(60),
                    state VARCHAR(40),
                    country VARCHAR(40),
                    customer_segment VARCHAR(50)
                );
                """),
                ("products", """
                CREATE TABLE IF NOT EXISTS products (
                    product_id INT PRIMARY KEY,
                    product_name VARCHAR(150),
                    category VARCHAR(60),
                    sub_category VARCHAR(60),
                    unit_price DECIMAL(10, 2),
                    cost_price DECIMAL(10, 2)
                );
                """),
                ("orders", """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INT PRIMARY KEY,
                    customer_id INT,
                    order_date DATE,
                    shipping_mode VARCHAR(60),
                    payment_method VARCHAR(60),
                    order_status VARCHAR(50),
                    order_total DECIMAL(10, 2)
                );
                """),
                ("order_items", """
                CREATE TABLE IF NOT EXISTS order_items (
                    item_id INT PRIMARY KEY,
                    order_id INT,
                    product_id INT,
                    quantity INT,
                    discount_percent INT,
                    total_sale_amount DECIMAL(10, 2),
                    profit_amount DECIMAL(10, 2)
                );
                """)
            ]

            for tname, create_sql in tables_to_create:
                cursor.execute(f"DROP TABLE IF EXISTS {tname};")
                cursor.execute(create_sql)

            # Insert customers
            c_query = "INSERT INTO customers (customer_id, customer_name, email, city, state, country, customer_segment) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.executemany(c_query, [tuple(x) for x in df_customers.values])

            # Insert products
            p_query = "INSERT INTO products (product_id, product_name, category, sub_category, unit_price, cost_price) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.executemany(p_query, [tuple(x) for x in df_products.values])

            # Insert orders
            o_query = "INSERT INTO orders (order_id, customer_id, order_date, shipping_mode, payment_method, order_status, order_total) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.executemany(o_query, [tuple(x) for x in df_orders.values])

            # Insert order_items
            oi_query = "INSERT INTO order_items (item_id, order_id, product_id, quantity, discount_percent, total_sale_amount, profit_amount) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.executemany(oi_query, [tuple(x) for x in df_order_items.values])

            conn.commit()

        return True, f"Successfully seeded 50 customers, 30 products, 120 orders, and {len(df_order_items)} order items into {config.get('db_type', 'MySQL')}!"
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    ok, msg = generate_and_seed_ecommerce()
    print("Seeding Result:", ok, msg)
