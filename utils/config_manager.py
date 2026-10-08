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
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default keys exist
            updated = False
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
                    updated = True
            if updated:
                save_config(config)
            return config
    except Exception as e:
        print(f"Error reading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration dictionary to config.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
