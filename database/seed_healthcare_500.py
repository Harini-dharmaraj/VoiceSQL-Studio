import os
import sys
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import sqlite3
from database.db_connection import get_db_connection
from utils.config_manager import load_config

def generate_and_seed_healthcare_500():
    """
    Generates a unified Hospital & Healthcare Electronic Health Records (EHR) system
    with over 550+ patient admission transactions and billing records.
    """
    random.seed(42)
    os.makedirs("datasets", exist_ok=True)
    os.makedirs("database", exist_ok=True)

    # 1. DEPARTMENTS
    dept_catalog = [
        (1, "Cardiology", "Dr. Cristina Yang", 45, 8500000.00),
        (2, "Neurology & Neurosurgery", "Dr. Derek Shepherd", 35, 9200000.00),
        (3, "Oncology", "Dr. James Wilson", 50, 11000000.00),
        (4, "Pediatrics", "Dr. Shaun Murphy", 40, 6000000.00),
        (5, "Orthopedics", "Dr. Callie Torres", 38, 7200000.00),
        (6, "General Surgery", "Dr. Meredith Grey", 42, 7800000.00),
        (7, "Internal Medicine", "Dr. John Watson", 55, 5500000.00),
        (8, "Emergency & Trauma", "Dr. Robert Chase", 30, 9800000.00)
    ]
    df_departments = pd.DataFrame([
        {
            "dept_id": d[0],
            "dept_name": d[1],
            "head_of_department": d[2],
            "total_beds": d[3],
            "annual_operating_budget": d[4]
        }
        for d in dept_catalog
    ])

    # 2. DOCTORS
    doctors_catalog = [
        (1, "Dr. Cristina Yang", "Cardiology", "LIC-NY-8491", 16, 420.00),
        (2, "Dr. Preston Burke", "Cardiology", "LIC-NY-6120", 22, 480.00),
        (3, "Dr. Derek Shepherd", "Neurology & Neurosurgery", "LIC-NY-9021", 20, 500.00),
        (4, "Dr. Amelia Shepherd", "Neurology & Neurosurgery", "LIC-NY-7411", 14, 430.00),
        (5, "Dr. James Wilson", "Oncology", "LIC-NY-5231", 19, 390.00),
        (6, "Dr. Allison Cameron", "Oncology", "LIC-NY-3199", 11, 280.00),
        (7, "Dr. Shaun Murphy", "Pediatrics", "LIC-NY-4211", 9, 290.00),
        (8, "Dr. Arizona Robbins", "Pediatrics", "LIC-NY-8820", 17, 360.00),
        (9, "Dr. Callie Torres", "Orthopedics", "LIC-NY-7120", 18, 390.00),
        (10, "Dr. Atticus Lincoln", "Orthopedics", "LIC-NY-4890", 12, 330.00),
        (11, "Dr. Meredith Grey", "General Surgery", "LIC-NY-9912", 18, 410.00),
        (12, "Dr. Miranda Bailey", "General Surgery", "LIC-NY-8311", 21, 460.00),
        (13, "Dr. John Watson", "Internal Medicine", "LIC-NY-5011", 15, 250.00),
        (14, "Dr. Gregory House", "Internal Medicine", "LIC-NY-1001", 25, 550.00),
        (15, "Dr. Robert Chase", "Emergency & Trauma", "LIC-NY-7721", 14, 380.00),
        (16, "Dr. Owen Hunt", "Emergency & Trauma", "LIC-NY-6641", 19, 440.00)
    ]
    df_doctors = pd.DataFrame([
        {
            "doctor_id": d[0],
            "doctor_name": d[1],
            "department": d[2],
            "license_number": d[3],
            "experience_years": d[4],
            "consultation_fee": d[5]
        }
        for d in doctors_catalog
    ])

    # 3. PATIENTS (250 distinct patient profiles)
    first_names_m = ["Liam", "Noah", "Oliver", "James", "Elijah", "William", "Henry", "Lucas", "Benjamin", "Theodore",
                     "Jack", "Levi", "Alexander", "Jackson", "Mateo", "Daniel", "Michael", "Mason", "Sebastian", "Ethan",
                     "Logan", "Owen", "Samuel", "Jacob", "Asher", "Aiden", "John", "Joseph", "David", "Wyatt"]
    first_names_f = ["Olivia", "Emma", "Charlotte", "Amelia", "Sophia", "Mia", "Isabella", "Ava", "Evelyn", "Luna",
                     "Harper", "Camila", "Sofia", "Scarlett", "Elizabeth", "Eleanor", "Emily", "Chloe", "Mila", "Violet",
                     "Penelope", "Gianna", "Aria", "Abigail", "Ella", "Avery", "Hazel", "Nora", "Layla", "Lily"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
                  "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"]
    cities = [
        ("New York", "NY"), ("Buffalo", "NY"), ("Rochester", "NY"), ("Albany", "NY"),
        ("Syracuse", "NY"), ("Yonkers", "NY"), ("Boston", "MA"), ("Philadelphia", "PA")
    ]
    blood_types = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
    insurers = ["Blue Cross Blue Shield", "UnitedHealth", "Aetna", "Medicare", "Medicaid", "Cigna", "Self-Pay / Uninsured"]

    patients_data = []
    for pid in range(1, 251):
        if pid % 2 == 0:
            fn = random.choice(first_names_f)
            gender = "Female"
        else:
            fn = random.choice(first_names_m)
            gender = "Male"
        ln = random.choice(last_names)
        city, state = random.choice(cities)
        btype = random.choice(blood_types)
        age = random.choices(
            [random.randint(5, 17), random.randint(18, 45), random.randint(46, 65), random.randint(66, 88)],
            weights=[0.10, 0.35, 0.35, 0.20]
        )[0]
        ins = random.choices(insurers, weights=[0.25, 0.22, 0.18, 0.15, 0.10, 0.06, 0.04])[0]
        phone = f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

        patients_data.append({
            "patient_id": pid,
            "patient_name": f"{fn} {ln}",
            "age": age,
            "gender": gender,
            "blood_type": btype,
            "city": city,
            "state": state,
            "emergency_contact_phone": phone,
            "insurance_provider": ins
        })
    df_patients = pd.DataFrame(patients_data)

    # 4. ADMISSIONS (550 clinical admission records!)
    clinical_cases = [
        ("Coronary Artery Bypass Graft (CABG)", "Cardiology", 28500.00, 8, "ICU"),
        ("Acute Myocardial Infarction", "Cardiology", 19200.00, 5, "Cardiac Care Unit"),
        ("Atrial Fibrillation Management", "Cardiology", 7800.00, 3, "Cardiac Care Unit"),
        ("Brain Tumor Craniotomy", "Neurology & Neurosurgery", 38000.00, 10, "ICU"),
        ("Acute Ischemic Stroke", "Neurology & Neurosurgery", 22500.00, 7, "ICU"),
        ("Chronic Subdural Hematoma", "Neurology & Neurosurgery", 16800.00, 5, "Private Suite"),
        ("Malignant Lymphoma Chemotherapy", "Oncology", 26400.00, 4, "Private Suite"),
        ("Lung Carcinoma Targeted Therapy", "Oncology", 31500.00, 6, "Private Suite"),
        ("Breast Cancer Resection", "Oncology", 18200.00, 4, "Private Suite"),
        ("Pediatric Severe Pneumonia", "Pediatrics", 6200.00, 4, "General Ward"),
        ("Pediatric Asthma Crisis", "Pediatrics", 3800.00, 2, "General Ward"),
        ("Pediatric Appendectomy", "Pediatrics", 7400.00, 3, "General Ward"),
        ("Total Knee Arthroplasty", "Orthopedics", 17500.00, 4, "Semi-Private"),
        ("Total Hip Replacement", "Orthopedics", 21000.00, 5, "Semi-Private"),
        ("Compound Femur Fracture", "Orthopedics", 15800.00, 6, "Semi-Private"),
        ("Laparoscopic Cholecystectomy", "General Surgery", 9200.00, 2, "General Ward"),
        ("Acute Perforated Appendicitis", "General Surgery", 11500.00, 4, "General Ward"),
        ("Bowel Resection & Anastomosis", "General Surgery", 24000.00, 7, "ICU"),
        ("Severe Sepsis Protocol", "Internal Medicine", 14500.00, 6, "ICU"),
        ("Diabetic Ketoacidosis Crisis", "Internal Medicine", 8900.00, 4, "Semi-Private"),
        ("Acute Kidney Failure Hemodialysis", "Internal Medicine", 17200.00, 5, "Private Suite"),
        ("Severe Polytrauma Stabilization", "Emergency & Trauma", 34000.00, 8, "ICU"),
        ("Motor Vehicle Collision Trauma", "Emergency & Trauma", 27500.00, 7, "ICU")
    ]

    adm_types = ["Emergency", "Urgent", "Elective", "Trauma"]
    dis_statuses = ["Discharged to Home", "Transferred to Inpatient Rehab", "Outpatient Follow-Up", "Home Health Care"]

    admissions_data = []
    billing_data = []

    start_date = datetime(2025, 1, 1)

    for aid in range(1, 551):
        # Pick patient (from the 250 pool)
        pid = random.randint(1, 250)
        p_row = next(p for p in patients_data if p["patient_id"] == pid)
        ins_name = p_row["insurance_provider"]

        # Case selection
        case_info = random.choice(clinical_cases)
        diag_name = case_info[0]
        dept_name = case_info[1]
        base_cost = case_info[2]
        base_stay = case_info[3]
        pref_room = case_info[4]

        # Select doctor from that department
        dept_docs = [d for d in doctors_catalog if d[2] == dept_name]
        doc = random.choice(dept_docs) if dept_docs else random.choice(doctors_catalog)
        doc_id = doc[0]

        # Dates
        days_offset = random.randint(0, 450)
        adm_dt = start_date + timedelta(days=days_offset)
        stay_days = max(1, int(random.gauss(base_stay, 1.8)))
        dis_dt = adm_dt + timedelta(days=stay_days)

        adm_type = random.choices(adm_types, weights=[0.55, 0.25, 0.15, 0.05])[0]
        dis_status = random.choices(dis_statuses, weights=[0.70, 0.15, 0.10, 0.05])[0]

        actual_treatment_cost = round(base_cost * random.uniform(0.90, 1.22), 2)

        admissions_data.append({
            "admission_id": aid,
            "patient_id": pid,
            "doctor_id": doc_id,
            "admission_date": adm_dt.strftime("%Y-%m-%d"),
            "discharge_date": dis_dt.strftime("%Y-%m-%d"),
            "admission_type": adm_type,
            "diagnosis": diag_name,
            "room_type": pref_room,
            "treatment_cost": actual_treatment_cost,
            "discharge_status": dis_status
        })

        # Generate Billing Record for this Admission
        if "Self-Pay" in ins_name:
            ins_paid = 0.00
            copay = actual_treatment_cost
            claim_status = "Direct Patient Billing"
            pay_method = random.choice(["Credit Card", "Payment Plan Installments", "Cash / Debit"])
        elif "Medicare" in ins_name or "Medicaid" in ins_name:
            ins_paid = round(actual_treatment_cost * 0.88, 2)
            copay = round(actual_treatment_cost - ins_paid, 2)
            claim_status = random.choices(["Approved & Settled", "Approved & Settled", "Pending Review"], weights=[0.85, 0.1, 0.05])[0]
            pay_method = "Government Program Direct"
        else:
            ins_paid = round(actual_treatment_cost * random.uniform(0.75, 0.90), 2)
            copay = round(actual_treatment_cost - ins_paid, 2)
            claim_status = random.choices(
                ["Approved & Settled", "Approved & Settled", "Pending Review", "Denied / Appeal"],
                weights=[0.80, 0.10, 0.07, 0.03]
            )[0]
            pay_method = random.choice(["Insurance Direct", "Credit Card", "HSA Account"])

        billing_data.append({
            "bill_id": aid,
            "admission_id": aid,
            "patient_id": pid,
            "total_billed_amount": actual_treatment_cost,
            "insurance_paid_amount": ins_paid,
            "patient_copay_amount": copay,
            "claim_status": claim_status,
            "payment_method": pay_method
        })

    df_admissions = pd.DataFrame(admissions_data)
    df_billing = pd.DataFrame(billing_data)

    print(f"Generated {len(df_patients)} patients, {len(df_doctors)} doctors, {len(df_admissions)} admissions, and {len(df_billing)} billing claims!")

    # Save to CSV files in datasets/
    df_patients.to_csv("datasets/patients.csv", index=False)
    df_admissions.to_csv("datasets/patient_admissions.csv", index=False)
    df_billing.to_csv("datasets/medical_billing.csv", index=False)
    df_doctors.to_csv("datasets/doctors.csv", index=False)
    df_departments.to_csv("datasets/hospital_departments.csv", index=False)

    # 5. SEED INTO SQLITE (Unified Healthcare EHR Only)
    lite_conn = sqlite3.connect("database/demo.db")
    lite_cur = lite_conn.cursor()
    # Drop legacy non-healthcare tables
    legacy_tables = [
        "departments", "employees", "projects", "employee_projects",
        "customers", "products", "orders", "order_items",
        "hospital_rooms", "students", "courses", "product_reviews"
    ]
    for lt in legacy_tables:
        lite_cur.execute(f"DROP TABLE IF EXISTS {lt};")
    lite_conn.commit()

    df_patients.to_sql("patients", lite_conn, if_exists="replace", index=False)
    df_admissions.to_sql("patient_admissions", lite_conn, if_exists="replace", index=False)
    df_billing.to_sql("medical_billing", lite_conn, if_exists="replace", index=False)
    df_doctors.to_sql("doctors", lite_conn, if_exists="replace", index=False)
    df_departments.to_sql("hospital_departments", lite_conn, if_exists="replace", index=False)
    lite_cur.execute("VACUUM;")
    lite_conn.commit()
    lite_cur.close()
    lite_conn.close()
    print("Successfully seeded into SQLite (database/demo.db) with 100% Healthcare theme!")

    # 6. SEED INTO MYSQL (IF RUNNING)
    config = load_config()
    if config.get("db_type") == "MySQL":
        try:
            mysql_conn = get_db_connection()
            cur = mysql_conn.cursor()

            tables_setup = [
                ("hospital_departments", """
                CREATE TABLE hospital_departments (
                    dept_id INT PRIMARY KEY,
                    dept_name VARCHAR(100),
                    head_of_department VARCHAR(100),
                    total_beds INT,
                    annual_operating_budget DECIMAL(12,2)
                );
                """, "INSERT INTO hospital_departments VALUES (%s, %s, %s, %s, %s)", df_departments),
                ("doctors", """
                CREATE TABLE doctors (
                    doctor_id INT PRIMARY KEY,
                    doctor_name VARCHAR(100),
                    department VARCHAR(100),
                    license_number VARCHAR(40),
                    experience_years INT,
                    consultation_fee DECIMAL(10,2)
                );
                """, "INSERT INTO doctors VALUES (%s, %s, %s, %s, %s, %s)", df_doctors),
                ("patients", """
                CREATE TABLE patients (
                    patient_id INT PRIMARY KEY,
                    patient_name VARCHAR(100),
                    age INT,
                    gender VARCHAR(20),
                    blood_type VARCHAR(10),
                    city VARCHAR(60),
                    state VARCHAR(40),
                    emergency_contact_phone VARCHAR(30),
                    insurance_provider VARCHAR(80)
                );
                """, "INSERT INTO patients VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", df_patients),
                ("patient_admissions", """
                CREATE TABLE patient_admissions (
                    admission_id INT PRIMARY KEY,
                    patient_id INT,
                    doctor_id INT,
                    admission_date DATE,
                    discharge_date DATE,
                    admission_type VARCHAR(50),
                    diagnosis VARCHAR(120),
                    room_type VARCHAR(50),
                    treatment_cost DECIMAL(10,2),
                    discharge_status VARCHAR(80)
                );
                """, "INSERT INTO patient_admissions VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", df_admissions),
                ("medical_billing", """
                CREATE TABLE medical_billing (
                    bill_id INT PRIMARY KEY,
                    admission_id INT,
                    patient_id INT,
                    total_billed_amount DECIMAL(10,2),
                    insurance_paid_amount DECIMAL(10,2),
                    patient_copay_amount DECIMAL(10,2),
                    claim_status VARCHAR(60),
                    payment_method VARCHAR(60)
                );
                """, "INSERT INTO medical_billing VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", df_billing)
            ]

            for tname, create_sql, insert_sql, df_obj in tables_setup:
                cur.execute(f"DROP TABLE IF EXISTS `{tname}`;")
                cur.execute(create_sql)
                cur.executemany(insert_sql, [tuple(x) for x in df_obj.values])

            mysql_conn.commit()
            cur.close()
            mysql_conn.close()
            print("Successfully seeded into MySQL!")
        except Exception as e:
            print("MySQL seed note:", e)

    return True, f"Successfully seeded Hospital EHR System with 550 patient admissions, 550 billing claims, 250 patients, and 16 doctors!"

if __name__ == "__main__":
    ok, msg = generate_and_seed_healthcare_500()
    print("Execution:", ok, msg)
