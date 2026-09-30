import streamlit as st
from utils.config_manager import load_config
from components.stats import show_stats
from components.status import show_status
from components.activity import show_activity
from components.pipeline import show_pipeline
from components.voice_card import show_voice_card

def show_dashboard():
    config = load_config()
    db_name = config.get("db_type", "SQLite")

    # ==========================================
    # Header Section
    # ==========================================
    col1, col2 = st.columns([4, 2])

    with col1:
        st.title("🤖 AI Voice-to-SQL Platform")
        st.caption("Intelligent database querying powered by Speech Recognition and Generative AI.")

    with col2:
        db_online = False
        try:
            from database.db_connection import get_db_connection
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            db_online = True
        except Exception:
            db_online = False

        status_badge = f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%; padding-top: 10px;">
            <span style="
                background: {'#ECFDF5' if db_online else '#FEF2F2'};
                color: {'#059669' if db_online else '#DC2626'};
                border: 1px solid {'#A7F3D0' if db_online else '#FECACA'};
                padding: 6px 14px;
                border-radius: 9999px;
                font-weight: 600;
                font-size: 12px;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            ">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: {'#10B981' if db_online else '#EF4444'};"></span>
                {f'{db_name} Online' if db_online else 'Database Offline'}
            </span>
        </div>
        """
        st.markdown(status_badge, unsafe_allow_html=True)

    st.divider()

    # ==========================================
    # Metric Statistics Row
    # ==========================================
    show_stats()

    st.divider()

    # ==========================================
    # Voice Playground & Real-Time System Status
    # ==========================================
    col_left, col_right = st.columns([5, 3], gap="large")

    with col_left:
        show_voice_card()

    with col_right:
        show_status()

    st.divider()

    # ==========================================
    # End-to-End AI Pipeline
    # ==========================================
    show_pipeline()

    st.divider()

    # ==========================================
    # Live Recent Activity
    # ==========================================
    show_activity()