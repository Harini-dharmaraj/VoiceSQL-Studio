import streamlit as st
from utils.config_manager import load_config
from database.db_connection import get_db_connection

def show_sidebar():
    config = load_config()
    db_engine = config.get("db_type", "SQLite")
    ai_provider = config.get("ai_provider", "Offline Rules")
    if ai_provider == "Mock":
        ai_provider = "Offline Rules"
    tts_enabled = config.get("tts_enabled", True)

    # Check live DB status
    db_online = False
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        db_online = True
    except Exception:
        db_online = False

    nav_map = {
        "Voice Assistant": "🎙️  Voice Studio",
        "Analytics": "📊  Metrics & Analytics",
        "Database": "🗄️  Database Manager",
        "History": "📜  Query History",
        "Settings": "⚙️  Settings"
    }

    with st.sidebar:
        # Sleek Brand Banner
        st.markdown("""
<div style="padding: 10px 0 18px 0;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45); border: 1px solid rgba(255, 255, 255, 0.2);">⚡</div>
        <div>
            <div style="font-size: 17px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em;">VoiceSQL Studio</div>
            <div style="font-size: 11.5px; color: #94A3B8; font-weight: 500;">AI Voice-to-Database Engine</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        st.caption("WORKSPACE NAVIGATION")

        page = st.radio(
            "Navigation",
            options=list(nav_map.keys()),
            format_func=lambda x: nav_map.get(x, x),
            label_visibility="collapsed"
        )

        st.markdown("<hr style='border-color: #1E293B; margin: 24px 0 16px 0;'>", unsafe_allow_html=True)

        # Environment Status Card (No inner blank lines and unindented to prevent markdown code-block parsing)
        db_color = "#10B981" if db_online else "#EF4444"
        db_text = f"{db_engine} (Online)" if db_online else f"{db_engine} (Offline)"
        tts_text = "🔊 Voice Output Active" if tts_enabled else "🔇 Voice Muted"
        tts_color = "#38BDF8" if tts_enabled else "#94A3B8"

        status_html = f"""
<div style="background: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 14px; font-size: 12px; color: #94A3B8; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);">
    <div style="font-size: 10.5px; font-weight: 700; color: #E2E8F0; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
        <span>System Status</span>
        <span style="font-size: 10px; background: #1F2937; padding: 2px 6px; border-radius: 4px; color: #38BDF8;">v2.0</span>
    </div>
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: #64748B;">Database:</span>
        <span style="color: {db_color}; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;">
            <span style="width: 7px; height: 7px; border-radius: 50%; background: {db_color}; display: inline-block;"></span>
            {db_text}
        </span>
    </div>
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: #64748B;">AI Engine:</span>
        <span style="color: #C084FC; font-weight: 600;">{ai_provider}</span>
    </div>
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <span style="color: #64748B;">Spoken TTS:</span>
        <span style="color: {tts_color}; font-weight: 600;">{tts_text}</span>
    </div>
</div>
"""
        st.markdown(status_html.strip(), unsafe_allow_html=True)

    return page