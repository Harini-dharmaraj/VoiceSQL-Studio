import os
import sys
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import sqlite3
from database.db_connection import get_db_connection
from utils.config_manager import load_config

def seed_all_datasets():
    """Generates and seeds multiple realistic datasets: E-Commerce, Healthcare, and Education."""
    random.seed(101)
    os.makedirs("datasets", exist_ok=True)
    os.makedirs("database", exist_ok=True)

    print("--- 1. GENERATING HEALTHCARE DATASET ---")
    doctors_list = [
        ("Dr. Gregory House", "Diagnostic Medicine", 22, 350.00),
        ("Dr. Meredith Grey", "General Surgery", 15, 280.00),
        ("Dr. Derek Shepherd", "Neurosurgery", 18, 450.00),
        ("Dr. Cristina Yang", "Cardiothoracic Surgery", 14, 400.00),
        ("Dr. John Watson", "Internal Medicine", 12, 200.00),
        ("Dr. Shaun Murphy", "Pediatric Surgery", 8, 260.00),
        ("Dr. Lisa Cuddy", "Endocrinology", 20, 310.00),
        ("Dr. James Wilson", "Oncology", 19, 380.00),
        ("Dr. Allison Cameron", "Immunology", 10, 220.00),
        ("Dr. Robert Chase", "Intensive Care", 13, 270.00),
    ]
    df_doctors = pd.DataFrame([
        {
            "doctor_id": i + 1,
            "doctor_name": d[0],
            "specialization": d[1],
            "experience_years": d[2],
            "consultation_fee": d[3]
        }
        for i, d in enumerate(doctors_list)
    ])

    diagnoses = [
        ("Acute Bronchitis", 1500.00), ("Coronary Artery Disease", 18500.00),
        ("Type 2 Diabetes Complications", 4200.00), ("Appendicitis", 6500.00),
        ("Pneumonia", 5800.00), ("Fractured Femur", 12000.00),
        ("Migraine Chronic", 1200.00), ("Hypertension Crisis", 3900.00),
        ("Kidney Stone Removal", 8400.00), ("Chemotherapy Cycle", 24000.00),
        ("Knee Replacement", 16500.00), ("Asthma Exacerbation", 2100.00)
    ]
    blood_types = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
    patient_names = [
        "Liam Johnson", "Olivia Smith", "Noah Williams", "Emma Brown", "Oliver Jones",
        "Charlotte Garcia", "Elijah Miller", "Amelia Davis", "James Rodriguez", "Ava Martinez",
        "William Hernandez", "Sophia Lopez", "Benjamin Gonzalez", "Isabella Wilson", "Lucas Anderson",
        "Mia Thomas", "Henry Taylor", "Evelyn Moore", "Alexander Jackson", "Harper Martin",
        "Sebastian Lee", "Camila Perez", "Jack Thompson", "Gianna White", "Owen Harris",
        "Abigail Sanchez", "Daniel Clark", "Emily Ramirez", "Matthew Lewis", "Elizabeth Robinson",
        "David Walker", "Avery Young", "Joseph Allen", "Sofia King", "Carter Wright",
        "Ella Scott", "Luke Torres", "Madison Nguyen", "Anthony Hill", "Scarlett Flores"
    ]

    patients_data = []
    base_adm = datetime(2026, 1, 10)
    for pid, pname in enumerate(patient_names, start=1):
        age = random.randint(18, 82)
        gender = random.choice(["Male", "Female"])
        btype = random.choice(blood_types)
        diag, cost = random.choice(diagnoses)
        doc = random.choice(doctors_list)[0]
        adm_date = base_adm + timedelta(days=random.randint(0, 240))
        los = random.randint(1, 12)
        dis_date = adm_date + timedelta(days=los)
        insurance = random.choices(["Covered (Private)", "Medicare", "Uninsured", "Medicaid"], weights=[0.5, 0.25, 0.1, 0.15])[0]
        final_bill = round(cost * (random.uniform(0.85, 1.25)), 2)

        patients_data.append({
            "patient_id": pid,
            "patient_name": pname,
            "age": age,
            "gender": gender,
            "blood_type": btype,
            "diagnosis": diag,
            "doctor_name": doc,
            "admission_date": adm_date.strftime("%Y-%m-%d"),
            "discharge_date": dis_date.strftime("%Y-%m-%d"),
            "treatment_cost": final_bill,
            "insurance_status": insurance
        })
    df_patients = pd.DataFrame(patients_data)

    rooms_data = []
    room_types = [("General Ward", 250.00), ("Semi-Private", 500.00), ("Private Suite", 950.00), ("ICU", 2200.00)]
    for r_num in range(101, 131):
        rtype, rate = random.choice(room_types)
        status = random.choice(["Occupied", "Occupied", "Available", "Cleaning"])
        rooms_data.append({
            "room_number": r_num,
            "room_type": rtype,
            "daily_rate": rate,
            "status": status
        })
    df_rooms = pd.DataFrame(rooms_data)

    print("--- 2. GENERATING EDUCATION / UNIVERSITY DATASET ---")
    majors = ["Computer Science", "Data Science", "Electrical Engineering", "Finance & Economics", "Biomedical Sciences"]
    students_data = []
    student_firsts = ["Aiden", "Chloe", "Ethan", "Grace", "Jackson", "Hannah", "Leo", "Lily", "Mason", "Zoe",
                      "Logan", "Nora", "Caleb", "Riley", "Ryan", "Stella", "Nathan", "Maya", "Isaac", "Penelope",
                      "Samuel", "Leah", "Christian", "Audrey", "Julian", "Claire", "Aaron", "Skylar", "Eli", "Bella"]
    student_lasts = ["Chen", "Sharma", "Patel", "Kim", "O'Connor", "Dubois", "Santos", "Novak", "Kowalski", "Muller"]

    for sid in range(1, 41):
        sname = f"{random.choice(student_firsts)} {random.choice(student_lasts)}"
        major = random.choice(majors)
        gpa = round(random.uniform(2.65, 4.0), 2)
        grad_year = random.choice([2026, 2027, 2028])
        scholarship = "Yes" if gpa >= 3.6 else "No"
        students_data.append({
            "student_id": sid,
            "student_name": sname,
            "major": major,
            "gpa": gpa,
            "graduation_year": grad_year,
            "scholarship_awarded": scholarship
        })
    df_students = pd.DataFrame(students_data)

    courses_list = [
        ("CS-101", "Introduction to Artificial Intelligence", "Computer Science", 4, "Prof. Andrew Ng"),
        ("CS-205", "Database Systems & SQL Optimization", "Computer Science", 3, "Prof. Michael Stonebraker"),
        ("DS-301", "Machine Learning & Deep Neural Nets", "Data Science", 4, "Prof. Yann LeCun"),
        ("EE-210", "Digital Circuit Design & Microprocessors", "Electrical Engineering", 4, "Prof. Lynn Conway"),
        ("FIN-401", "Quantitative Portfolio Analytics", "Finance & Economics", 3, "Prof. Eugene Fama"),
        ("BIO-220", "Molecular Genetics & Genomics", "Biomedical Sciences", 4, "Prof. Jennifer Doudna"),
        ("CS-450", "Cloud Computing & Distributed Architecture", "Computer Science", 3, "Prof. Leslie Lamport")
    ]
    df_courses = pd.DataFrame([
        {
            "course_code": c[0],
            "course_name": c[1],
            "department": c[2],
            "credits": c[3],
            "instructor_name": c[4]
        }
        for c in courses_list
    ])

    print("--- 3. GENERATING PRODUCT REVIEWS DATASET ---")
    reviews_data = []
    sentiments = ["Positive", "Positive", "Positive", "Neutral", "Negative"]
    for rev_id in range(1, 81):
        pid = random.randint(1, 30)
        sent = random.choice(sentiments)
        rating = random.choice([5, 5, 4]) if sent == "Positive" else (3 if sent == "Neutral" else random.choice([1, 2]))
        verified = random.choice(["Yes", "Yes", "Yes", "No"])
        reviews_data.append({
            "review_id": rev_id,
            "product_id": pid,
            "rating": rating,
            "sentiment": sent,
            "verified_purchase": verified
        })
    df_reviews = pd.DataFrame(reviews_data)

    # Save all new CSVs in datasets/
    df_doctors.to_csv("datasets/doctors.csv", index=False)
    df_patients.to_csv("datasets/patients.csv", index=False)
    df_rooms.to_csv("datasets/hospital_rooms.csv", index=False)
    df_students.to_csv("datasets/students.csv", index=False)
    df_courses.to_csv("datasets/courses.csv", index=False)
    df_reviews.to_csv("datasets/product_reviews.csv", index=False)

    print("--- 4. SEEDING INTO SQLITE (database/demo.db) ---")
    lite_conn = sqlite3.connect("database/demo.db")
    df_doctors.to_sql("doctors", lite_conn, if_exists="replace", index=False)
    df_patients.to_sql("patients", lite_conn, if_exists="replace", index=False)
    df_rooms.to_sql("hospital_rooms", lite_conn, if_exists="replace", index=False)
    df_students.to_sql("students", lite_conn, if_exists="replace", index=False)
    df_courses.to_sql("courses", lite_conn, if_exists="replace", index=False)
    df_reviews.to_sql("product_reviews", lite_conn, if_exists="replace", index=False)
    lite_conn.commit()
    lite_conn.close()

    print("--- 5. SEEDING INTO MYSQL (IF ONLINE) ---")
    config = load_config()
    try:
        mysql_conn = get_db_connection()
        cur = mysql_conn.cursor()
        
        # Patients
        cur.execute("DROP TABLE IF EXISTS patients;")
        cur.execute("""
        CREATE TABLE patients (
            patient_id INT PRIMARY KEY,
            patient_name VARCHAR(100),
            age INT,
            gender VARCHAR(20),
            blood_type VARCHAR(10),
            diagnosis VARCHAR(100),
            doctor_name VARCHAR(100),
            admission_date DATE,
            discharge_date DATE,
            treatment_cost DECIMAL(10,2),
            insurance_status VARCHAR(50)
        );
        """)
        cur.executemany(
            "INSERT INTO patients VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [tuple(x) for x in df_patients.values]
        )

        # Doctors
        cur.execute("DROP TABLE IF EXISTS doctors;")
        cur.execute("""
        CREATE TABLE doctors (
            doctor_id INT PRIMARY KEY,
            doctor_name VARCHAR(100),
            specialization VARCHAR(100),
            experience_years INT,
            consultation_fee DECIMAL(10,2)
        );
        """)
        cur.executemany(
            "INSERT INTO doctors VALUES (%s, %s, %s, %s, %s)",
            [tuple(x) for x in df_doctors.values]
        )

        # Hospital Rooms
        cur.execute("DROP TABLE IF EXISTS hospital_rooms;")
        cur.execute("""
        CREATE TABLE hospital_rooms (
            room_number INT PRIMARY KEY,
            room_type VARCHAR(50),
            daily_rate DECIMAL(10,2),
            status VARCHAR(30)
        );
        """)
        cur.executemany(
            "INSERT INTO hospital_rooms VALUES (%s, %s, %s, %s)",
            [tuple(x) for x in df_rooms.values]
        )

        # Students
        cur.execute("DROP TABLE IF EXISTS students;")
        cur.execute("""
        CREATE TABLE students (
            student_id INT PRIMARY KEY,
            student_name VARCHAR(100),
            major VARCHAR(100),
            gpa DECIMAL(4,2),
            graduation_year INT,
            scholarship_awarded VARCHAR(10)
        );
        """)
        cur.executemany(
            "INSERT INTO students VALUES (%s, %s, %s, %s, %s, %s)",
            [tuple(x) for x in df_students.values]
        )

        # Courses
        cur.execute("DROP TABLE IF EXISTS courses;")
        cur.execute("""
        CREATE TABLE courses (
            course_code VARCHAR(30) PRIMARY KEY,
            course_name VARCHAR(120),
            department VARCHAR(100),
            credits INT,
            instructor_name VARCHAR(100)
        );
        """)
        cur.executemany(
            "INSERT INTO courses VALUES (%s, %s, %s, %s, %s)",
            [tuple(x) for x in df_courses.values]
        )

        # Product Reviews
        cur.execute("DROP TABLE IF EXISTS product_reviews;")
        cur.execute("""
        CREATE TABLE product_reviews (
            review_id INT PRIMARY KEY,
            product_id INT,
            rating INT,
            sentiment VARCHAR(30),
            verified_purchase VARCHAR(10)
        );
        """)
        cur.executemany(
            "INSERT INTO product_reviews VALUES (%s, %s, %s, %s, %s)",
            [tuple(x) for x in df_reviews.values]
        )

        mysql_conn.commit()
        cur.close()
        mysql_conn.close()
        print("Seeded successfully into MySQL!")
    except Exception as e:
        print("Note: MySQL not connected or offline, skipped MySQL insert:", e)

    return True, "Successfully created and seeded 6 new datasets: patients, doctors, hospital_rooms, students, courses, product_reviews!"

if __name__ == "__main__":
    ok, msg = seed_all_datasets()
    print("Result:", ok, msg)
