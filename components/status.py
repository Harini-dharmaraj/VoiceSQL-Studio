import streamlit as st
from utils.config_manager import load_config
from database.db_connection import get_db_connection

def show_status():
    config = load_config()
    
    db_online = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        db_online = True
    except Exception:
        db_online = False
        
    db_name = config.get("db_type", "SQLite")
    ai_provider = config.get("ai_provider", "Offline Rules")
    if ai_provider == "Mock":
        ai_provider = "Offline Rules (Fast)"
    
    db_badge_bg = "#ECFDF5" if db_online else "#FEF2F2"
    db_badge_color = "#059669" if db_online else "#DC2626"
    db_badge_border = "#A7F3D0" if db_online else "#FECACA"
    db_badge_text = f"Connected ({db_name})" if db_online else "Offline"
    
    status_rows = [
        ("🎙️", "Audio Input", "16kHz Mono", "#EFF6FF", "#2563EB", "#BFDBFE"),
        ("🔇", "DSP Filter", "NoiseReduce", "#F0FDF4", "#16A34A", "#BBF7D0"),
        ("🧠", "Speech Engine", "OpenAI Whisper", "#FFFBEB", "#D97706", "#FDE68A"),
        ("🤖", "SQL Engine", ai_provider, "#F5F3FF", "#7C3AED", "#DDD6FE"),
        ("🗄️", "Database", db_badge_text, db_badge_bg, db_badge_color, db_badge_border),
    ]

    rows_html = ""
    for icon, label, val, bg, color, border in status_rows:
        rows_html += f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #F1F5F9;
            font-size: 13px;
        ">
            <div style="display: flex; align-items: center; gap: 8px; color: #475569; font-weight: 500;">
                <span>{icon}</span>
                <span>{label}</span>
            </div>
            <span style="
                background: {bg};
                color: {color};
                border: 1px solid {border};
                padding: 2px 10px;
                border-radius: 9999px;
                font-weight: 600;
                font-size: 11px;
            ">{val}</span>
        </div>
        """

    html_content = f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        margin-bottom: 16px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #E2E8F0;">
            <div style="font-size: 16px; font-weight: 700; color: #0F172A;">⚙️ System Status</div>
            <span style="
                background: #ECFDF5;
                color: #059669;
                border: 1px solid #A7F3D0;
                padding: 2px 10px;
                border-radius: 9999px;
                font-size: 11px;
                font-weight: 600;
            ">● Operational</span>
        </div>
        {rows_html}
    </div>
    """

    st.markdown(html_content.strip(), unsafe_allow_html=True)