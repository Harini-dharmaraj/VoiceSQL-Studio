import os
import streamlit as st
from utils.config_manager import load_config, save_config
from database.db_connection import init_database, test_mysql_connection
from speech.text_to_speech import generate_voice_response, get_browser_tts_html

def show_settings():
    st.title("⚙️ System & Engine Settings")
    st.caption("Manage database connectivity, generative AI models, and real-time voice speech synthesis.")
    st.divider()

    config = load_config()

    tab_db, tab_ai, tab_voice = st.tabs(["🗄️ Database Engine", "🧠 AI Model Settings", "🔊 Voice & TTS Settings"])

    # ==========================================
    # Database Settings Tab (SQLite & MySQL)
    # ==========================================
    with tab_db:
        st.subheader("Database Configuration")
        current_db = config.get("db_type", "SQLite")
        db_type = st.selectbox("Select Database Engine", ["SQLite", "MySQL"], index=0 if current_db == "SQLite" else 1)

        if db_type == "SQLite":
            st.info("🟢 Database Status: Active & Connected (Local Embedded File)")
            st.markdown(
                """
                *   **Database Engine**: SQLite
                *   **File Location**: `database/demo.db`
                *   **Connection URL**: `sqlite:///database/demo.db`
                """
            )
            mysql_host = config.get("mysql_host", "localhost")
            mysql_port = config.get("mysql_port", 3306)
            mysql_user = config.get("mysql_user", "root")
            mysql_password = config.get("mysql_password", "")
            mysql_database = config.get("mysql_database", "voice_to_sql")
        else:
            st.info("🐬 MySQL Server Configuration")
            col_h, col_p = st.columns([3, 1])
            with col_h:
                mysql_host = st.text_input("MySQL Host", value=config.get("mysql_host", "localhost"))
            with col_p:
                mysql_port = st.number_input("Port", value=int(config.get("mysql_port", 3306)), min_value=1, max_value=65535)

            col_u, col_pw = st.columns(2)
            with col_u:
                mysql_user = st.text_input("Username", value=config.get("mysql_user", "root"))
            with col_pw:
                mysql_password = st.text_input("Password", value=config.get("mysql_password", ""), type="password")

            mysql_database = st.text_input("Database Name", value=config.get("mysql_database", "voice_to_sql"))

            if st.button("🔌 Test MySQL Connection"):
                with st.spinner("Testing connection to MySQL server..."):
                    ok, test_msg = test_mysql_connection(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database)
                if ok:
                    st.success(f"✅ {test_msg}")
                else:
                    st.error(f"❌ Connection Failed: {test_msg}")

        # Seeding Actions
        st.markdown("### Production Datasets Seeding")
        st.write("Populate the database with realistic business datasets or reset to default schemas:")
        
        col_seed1, col_seed2 = st.columns(2)
        with col_seed1:
            if st.button("🛒 Load E-Commerce Sales Dataset (Recommended)", type="primary", use_container_width=True):
                from database.seed_ecommerce import generate_and_seed_ecommerce
                with st.spinner("Seeding 50 customers, 30 products, 120 orders, and 225 order items..."):
                    ok_ecom, msg_ecom = generate_and_seed_ecommerce()
                if ok_ecom:
                    st.success(f"🎉 {msg_ecom}")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {msg_ecom}")

        with col_seed2:
            if st.button("👥 Load HR & Employees Dataset", type="secondary", use_container_width=True):
                with st.spinner(f"Initializing HR schema on {db_type}..."):
                    success, msg = init_database()
                if success:
                    st.success(f"🎉 {db_type} tables reset to HR sample data!")
                    st.rerun()
                else:
                    st.error(f"❌ Seeding Error: {msg}")

    # ==========================================
    # AI Model Settings Tab
    # ==========================================
    with tab_ai:
        st.subheader("AI Text-to-SQL Engine")
        
        current_provider = config.get("ai_provider", "Offline Rules (Fast)")
        if current_provider == "Mock":
            current_provider = "Offline Rules (Fast)"
            
        provider_options = ["Offline Rules (Fast)", "Google Gemini", "OpenAI", "Local (Flan-T5)"]
        default_idx = provider_options.index(current_provider) if current_provider in provider_options else 0

        ai_provider_label = st.selectbox(
            "Select SQL Generator Provider", 
            provider_options,
            index=default_idx
        )

        gemini_api_key = config.get("gemini_api_key", "")
        openai_api_key = config.get("openai_api_key", "")

        if ai_provider_label == "Google Gemini":
            st.markdown("""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; font-size: 13px; color: #1E40AF;">
                🔑 <b>Get your free API Key:</b> Visit <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #2563EB; font-weight: 700; text-decoration: underline;">Google AI Studio</a>, click <i>"Create API Key"</i>, and paste it below. (Free tier, no credit card required).
            </div>
            """, unsafe_allow_html=True)
            gemini_api_key = st.text_input("Google Gemini API Key", value=gemini_api_key, type="password", placeholder="AIzaSy...")
        elif ai_provider_label == "OpenAI":
            openai_api_key = st.text_input("OpenAI API Key", value=openai_api_key, type="password", placeholder="sk-...")
        elif ai_provider_label == "Local (Flan-T5)":
            st.warning("⚠️ Local Flan-T5 runs locally on CPU/GPU. The first execution will download the model weights (approx 990MB).")
        elif ai_provider_label == "Offline Rules (Fast)":
            st.info("ℹ️ Uses pre-defined query rules. Fast and works 100% offline without needing an API key.")

    # ==========================================
    # Voice & TTS Settings Tab
    # ==========================================
    with tab_voice:
        st.subheader("🎙️ Voice Input & Text-to-Speech (TTS)")
        
        recording_duration = st.slider(
            "Voice Recording Duration (seconds)", 
            min_value=3, 
            max_value=15, 
            value=int(config.get("recording_duration", 5)),
            help="How long the system listens when you click 'Record Voice'."
        )

        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.subheader("🔊 AI Voice Output (Spoken Results)")

        tts_enabled = st.checkbox(
            "Enable Spoken Voice Answers (Text-to-Speech)",
            value=config.get("tts_enabled", True),
            help="When enabled, the AI summarizes query results and speaks them aloud via audio output."
        )

        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; margin: 12px 0; font-size: 13px; color: #475569;">
            💡 <b>How it works:</b> AI results are summarized into conversational English and synthesized offline using high-performance Windows Speech Synthesis (SAPI) with browser Web Speech API fallback.
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔊 Test AI Voice Output"):
            test_phrase = "Hello! The AI Voice to SQL speech synthesizer is working properly."
            with st.spinner("Synthesizing test audio..."):
                audio_file = generate_voice_response(test_phrase, "audio/test_speech.wav")
            if audio_file and os.path.exists(audio_file):
                st.success("🔊 Playing test speech:")
                st.audio(audio_file, autoplay=True)
                st.markdown(get_browser_tts_html(test_phrase), unsafe_allow_html=True)
            else:
                st.markdown(get_browser_tts_html(test_phrase), unsafe_allow_html=True)
                st.info("Browser audio fallback triggered.")

    # ==========================================
    # Save button
    # ==========================================
    st.divider()
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        config["db_type"] = db_type
        config["mysql_host"] = mysql_host
        config["mysql_port"] = int(mysql_port)
        config["mysql_user"] = mysql_user
        config["mysql_password"] = mysql_password
        config["mysql_database"] = mysql_database
        
        # Map label back to internal code name
        if ai_provider_label == "Offline Rules (Fast)":
            config["ai_provider"] = "Mock"
        else:
            config["ai_provider"] = ai_provider_label
            
        config["gemini_api_key"] = gemini_api_key
        config["openai_api_key"] = openai_api_key
        config["recording_duration"] = int(recording_duration)
        config["tts_enabled"] = bool(tts_enabled)
        
        if save_config(config):
            st.success("💾 Settings saved successfully! Page will refresh...")
            st.rerun()
        else:
            st.error("❌ Failed to save configuration.")
