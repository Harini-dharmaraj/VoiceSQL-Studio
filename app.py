import os
import streamlit as st

# ==========================================
# PAGE CONFIG (MUST BE FIRST)
# ==========================================

st.set_page_config(
    page_title="VoiceSQL Studio • AI Voice-to-SQL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# LOAD CSS
# ==========================================

def load_css():
    if os.path.exists("style.css"):
        with open("style.css", "r", encoding="utf-8") as css:
            st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

load_css()

# ==========================================
# AUTO INITIALIZE DB
# ==========================================

from utils.config_manager import load_config
from database.db_connection import init_database

config = load_config()
if config.get("db_type") == "SQLite" and not os.path.exists("database/demo.db"):
    try:
        from database.seed_ecommerce import generate_and_seed_ecommerce
        generate_and_seed_ecommerce()
    except Exception:
        init_database()

# ==========================================
# PAGE IMPORTS
# ==========================================

from components.sidebar import show_sidebar
from pages.voice_query import show_voice_query_page
from pages.analytics import show_analytics_page
from pages.database import show_database_page
from pages.history import show_history_page
from pages.settings import show_settings

# ==========================================
# SIDEBAR NAVIGATION & ROUTING
# ==========================================

selected = show_sidebar()

if selected == "Database":
    show_database_page()
elif selected == "History":
    show_history_page()
elif selected == "Analytics":
    show_analytics_page()
elif selected == "Settings":
    show_settings()
else:
    # Default landing: Voice Studio
    show_voice_query_page()