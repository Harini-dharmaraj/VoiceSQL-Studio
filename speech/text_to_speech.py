import os
import re
import subprocess
import requests
import pandas as pd

def summarize_query_for_voice(natural_query, df_or_msg, success):
    """
    Generate a concise, natural spoken English sentence summarizing query results.
    """
    if not success:
        clean_err = str(df_or_msg)[:70].replace('"', '').replace("'", "")
        return f"Database query failed. {clean_err}"

    if not isinstance(df_or_msg, pd.DataFrame):
        return str(df_or_msg)

    df = df_or_msg
    row_count = len(df)

    # Check if table only contains an error column
    if "error" in [c.lower() for c in df.columns]:
        first_err = str(df.iloc[0, 0])
        return f"Query returned an error notice: {first_err[:60]}."

    if row_count == 0:
        return "The query executed successfully, but returned zero matching records."

    # Revenue & Profit aggregation
    if "total_revenue" in df.columns and "total_profit" in df.columns and row_count == 1:
        rev = float(df.iloc[0]["total_revenue"] or 0)
        prof = float(df.iloc[0]["total_profit"] or 0)
        return f"Total revenue is ${rev:,.0f} with a total net profit of ${prof:,.0f}."

    # 1. Single column aggregation (e.g. COUNT(*), AVG, SUM, MAX, MIN)
    if len(df.columns) == 1 and row_count == 1:
        col_name = df.columns[0].lower().replace('_', ' ')
        val = df.iloc[0, 0]
        try:
            if isinstance(val, (int, float)):
                if any(k in col_name for k in ["salary", "budget", "revenue", "price", "sale", "profit", "spent", "total"]):
                    val_str = f"${float(val):,.0f}"
                else:
                    val_str = f"{float(val):,.2f}".rstrip('0').rstrip('.')
            else:
                val_str = str(val)
        except Exception:
            val_str = str(val)

        if "count" in col_name or "total" in col_name:
            return f"The total count is {val_str}."
        elif "avg" in col_name or "average" in col_name:
            return f"The average {col_name.replace('avg', '').strip()} is {val_str}."
        elif "max" in col_name or "highest" in col_name:
            return f"The highest value is {val_str}."
        elif "min" in col_name or "lowest" in col_name:
            return f"The lowest value is {val_str}."
        return f"The result for {col_name} is {val_str}."

    # 2. Single row result
    if row_count == 1:
        row = df.iloc[0]
        details = []

        if "product_name" in df.columns:
            details.append(f"{row['product_name']}")
            if "category" in df.columns:
                details.append(f"in {row['category']}")
            if "unit_price" in df.columns:
                try:
                    details.append(f"priced at ${float(row['unit_price']):,.0f}")
                except Exception:
                    pass

        elif "customer_name" in df.columns:
            details.append(f"{row['customer_name']}")
            if "city" in df.columns:
                details.append(f"from {row['city']}")
            if "total_spent" in df.columns:
                try:
                    details.append(f"spending a total of ${float(row['total_spent']):,.0f}")
                except Exception:
                    pass

        elif "patient_name" in df.columns:
            details.append(f"{row['patient_name']}")
            if "diagnosis" in df.columns:
                details.append(f"diagnosed with {row['diagnosis']}")
            if "treatment_cost" in df.columns:
                try:
                    details.append(f"treatment cost ${float(row['treatment_cost']):,.0f}")
                except Exception:
                    pass

        elif "doctor_name" in df.columns:
            details.append(f"{row['doctor_name']}")
            if "specialization" in df.columns:
                details.append(f"specializing in {row['specialization']}")
            if "consultation_fee" in df.columns:
                try:
                    details.append(f"consultation fee ${float(row['consultation_fee']):,.0f}")
                except Exception:
                    pass

        elif "student_name" in df.columns:
            details.append(f"{row['student_name']}")
            if "major" in df.columns:
                details.append(f"majoring in {row['major']}")
            if "gpa" in df.columns:
                details.append(f"with GPA {row['gpa']}")

        elif "first_name" in df.columns and "last_name" in df.columns:
            details.append(f"{row['first_name']} {row['last_name']}")
            if "job_title" in df.columns:
                details.append(f"working as {row['job_title']}")
            if "salary" in df.columns:
                try:
                    details.append(f"with a salary of ${float(row['salary']):,.0f}")
                except Exception:
                    pass

        elif "order_id" in df.columns:
            details.append(f"Order #{row['order_id']}")
            if "order_status" in df.columns:
                details.append(f"status is {row['order_status']}")
            if "order_total" in df.columns:
                try:
                    details.append(f"total amount ${float(row['order_total']):,.0f}")
                except Exception:
                    pass

        if details:
            return f"Found 1 result: {', '.join(details)}."
        else:
            first_val = str(df.iloc[0, 0])
            return f"Found 1 record with value {first_val}."

    # 3. Small list (2 to 5 items)
    if 2 <= row_count <= 5:
        names = []
        if "patient_name" in df.columns:
            names = [str(r) for r in df["patient_name"].tolist()]
        elif "doctor_name" in df.columns:
            names = [str(r) for r in df["doctor_name"].tolist()]
        elif "student_name" in df.columns:
            names = [str(r) for r in df["student_name"].tolist()]
        elif "customer_name" in df.columns:
            names = [str(r) for r in df["customer_name"].tolist()]
        elif "product_name" in df.columns:
            names = [str(r) for r in df["product_name"].tolist()]
        elif "first_name" in df.columns and "last_name" in df.columns:
            names = [f"{r['first_name']} {r['last_name']}" for _, r in df.iterrows()]
        elif "category" in df.columns:
            names = [str(r) for r in df["category"].tolist()]

        if names:
            if len(names) == 2:
                joined = f"{names[0]} and {names[1]}"
            else:
                joined = f"{', '.join(names[:-1])}, and {names[-1]}"
            return f"Found {row_count} records: {joined}."
        return f"Found {row_count} records matching your query."

    # 4. Larger result sets (> 5 rows)
    item_type = "records"
    if "admission_id" in df.columns or "diagnosis" in df.columns:
        item_type = "patient admissions"
    elif "bill_id" in df.columns or "claim_status" in df.columns:
        item_type = "medical billing claims"
    elif "patient_name" in df.columns and "age" in df.columns:
        item_type = "patient profiles"
    elif "doctor_name" in df.columns or "license_number" in df.columns:
        item_type = "physicians"
    elif "dept_name" in df.columns or "head_of_department" in df.columns:
        item_type = "hospital departments"
    elif "product_name" in df.columns:
        item_type = "products"
    elif "customer_name" in df.columns:
        item_type = "customers"
    elif "order_id" in df.columns:
        item_type = "orders"
    elif "first_name" in df.columns or "employee_name" in df.columns:
        item_type = "employees"

    return f"Retrieved {row_count} {item_type} from the database. You can review the details in the table below."


def generate_voice_response(text, output_file="audio/ai_response.mp3"):
    """
    Universal Speech Synthesizer:
    1. Primary: Direct HTTP Google TTS (cross-platform, Linux Cloud + Windows, zero pip packages).
    2. Fallback: Windows SAPI PowerShell synthesizer (offline fallback).
    Returns path to audio file if created, or None.
    """
    try:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        abs_path = os.path.abspath(output_file)
        
        # Clean speech text
        clean_text = re.sub(r'[\$\*\_`#]', '', text)
        clean_text = clean_text.replace('"', ' ').replace("'", " ").strip()
        if not clean_text:
            return None

        # Strategy 1: Google Translate TTS (works on Linux Streamlit Cloud and Windows)
        try:
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={requests.utils.quote(clean_text[:250])}&tl=en&client=tw-ob"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200 and len(res.content) > 100:
                with open(abs_path, "wb") as f:
                    f.write(res.content)
                return output_file
        except Exception:
            pass

        # Strategy 2: Windows native PowerShell SpeechSynthesizer (offline Windows fallback)
        try:
            wav_path = abs_path.replace(".mp3", ".wav")
            worker_path = os.path.abspath("speech/tts_worker.ps1")
            if os.path.exists(worker_path):
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", worker_path, clean_text[:200], wav_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:
                    return wav_path
        except Exception:
            pass

    except Exception as e:
        print(f"TTS generation error: {e}")
    return None


def get_browser_tts_html(text):
    """
    HTML/JS snippet using the Web Speech API with an instant interactive trigger button.
    """
    clean = re.sub(r'[\$\*\_`#"\']', ' ', text).strip()
    return f"""
    <div style="margin-top: 10px; display: inline-block;">
        <button id="tts_btn" onclick="
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance('{clean}');
                u.rate = 1.0;
                window.speechSynthesis.speak(u);
            }}
        " style="
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 7px 16px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 6px rgba(16, 185, 129, 0.25);
        ">
            🔊 Speak Aloud in Browser
        </button>
    </div>
    <script>
    // Automatic trigger on load
    if ('speechSynthesis' in window) {{
        window.speechSynthesis.cancel();
        setTimeout(function() {{
            const u = new SpeechSynthesisUtterance('{clean}');
            u.rate = 1.0;
            window.speechSynthesis.speak(u);
        }}, 300);
    }}
    </script>
    """
