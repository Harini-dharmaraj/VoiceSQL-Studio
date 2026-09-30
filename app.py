import streamlit as st
import importlib
import os

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
    init_database()

# ==========================================
# IMPORTS WITH DYNAMIC MODULE RELOAD
# ==========================================

import database.db_connection
importlib.reload(database.db_connection)

import components.sidebar
importlib.reload(components.sidebar)

import pages.voice_query
importlib.reload(pages.voice_query)

import pages.database
importlib.reload(pages.database)

import pages.history
importlib.reload(pages.history)

import pages.analytics
importlib.reload(pages.analytics)

import pages.settings
importlib.reload(pages.settings)

try:
    import speech.text_to_speech
    importlib.reload(speech.text_to_speech)
except Exception:
    pass

from components.sidebar import show_sidebar
from pages.voice_query import show_voice_query_page
from pages.analytics import show_analytics_page
from pages.database import show_database_page
from pages.history import show_history_page
from pages.settings import show_settings

# ==========================================
# SIDEBAR
# ==========================================

selected = show_sidebar()

# ==========================================
# PAGE ROUTING
# ==========================================

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