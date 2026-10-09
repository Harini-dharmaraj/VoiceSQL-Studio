import os
import json

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "db_type": "SQLite",
    "mysql_host": "localhost",
    "mysql_port": 3306,
    "mysql_user": "root",
    "mysql_password": "",
    "mysql_database": "voice_to_sql",
    "ai_provider": "Mock",
    "gemini_api_key": "",
    "openai_api_key": "",
    "recording_duration": 5,
    "whisper_model": "base.en"
}

def load_config():
    """Load configuration from config.json, creating it with defaults if it doesn't exist."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                config.update(loaded)
        except Exception as e:
            print(f"Error reading config: {e}")

    # Check Streamlit Cloud secrets if available
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GEMINI_API_KEY" in st.secrets and not config.get("gemini_api_key"):
                config["gemini_api_key"] = str(st.secrets["GEMINI_API_KEY"]).strip()
                config["ai_provider"] = "Google Gemini"
            elif "gemini_api_key" in st.secrets and not config.get("gemini_api_key"):
                config["gemini_api_key"] = str(st.secrets["gemini_api_key"]).strip()
                config["ai_provider"] = "Google Gemini"
            if "OPENAI_API_KEY" in st.secrets and not config.get("openai_api_key"):
                config["openai_api_key"] = str(st.secrets["OPENAI_API_KEY"]).strip()
    except Exception:
        pass

    # Check environment variables
    if not config.get("gemini_api_key"):
        env_gemini = os.environ.get("GEMINI_API_KEY") or os.environ.get("gemini_api_key")
        if env_gemini:
            config["gemini_api_key"] = env_gemini.strip()
            config["ai_provider"] = "Google Gemini"

    if not config.get("openai_api_key"):
        env_openai = os.environ.get("OPENAI_API_KEY") or os.environ.get("openai_api_key")
        if env_openai:
            config["openai_api_key"] = env_openai.strip()

    return config

def save_config(config):
    """Save configuration dictionary to config.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
