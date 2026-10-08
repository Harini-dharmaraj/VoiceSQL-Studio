import os
import streamlit as st
import pandas as pd
import altair as alt
from speech.voice_recorder import record_audio
from speech.noise_removal import remove_noise, is_audio_silent
from speech.speech_to_text import speech_to_text
from speech.text_to_speech import summarize_query_for_voice, generate_voice_response, get_browser_tts_html
from sql_generator.generate_sql import generate_sql
from sql_generator.validator import validate_sql
from database.execute_query import execute_sql_query
from database.history import log_query
from utils.config_manager import load_config
from database.db_connection import get_db_connection

def show_voice_query_page():
    config = load_config()
    db_engine = config.get("db_type", "SQLite")
    db_name = config.get("mysql_database", "voice_to_sql") if db_engine == "MySQL" else "demo.db"
    duration = int(config.get("recording_duration", 5))
    tts_enabled = config.get("tts_enabled", True)

    os.makedirs("audio", exist_ok=True)

    # Check live DB connection
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

    # ==========================================
    # HEADER & SYSTEM STATUS BADGES
    # ==========================================
    col_head1, col_head2 = st.columns([3, 2])
    with col_head1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px;">
            <span style="font-size: 32px;">🎙️</span>
            <span style="font-size: 28px; font-weight: 800; color: #0F172A; letter-spacing: -0.03em;">AI Voice Studio</span>
        </div>
        <p style="font-size: 14px; color: #64748B; margin-top: 0; margin-bottom: 12px;">
            Speak naturally or type your query — AI translates voice to SQL, queries the database, and speaks the results aloud.
        </p>
        """, unsafe_allow_html=True)

    with col_head2:
        db_badge_bg = "#ECFDF5" if db_online else "#FEF2F2"
        db_badge_border = "#A7F3D0" if db_online else "#FECACA"
        db_badge_color = "#059669" if db_online else "#DC2626"
        db_dot_color = "#10B981" if db_online else "#EF4444"
        db_status_text = f"{db_engine} Connected" if db_online else f"{db_engine} Disconnected"

        tts_badge_bg = "#EFF6FF" if tts_enabled else "#F1F5F9"
        tts_badge_border = "#BFDBFE" if tts_enabled else "#CBD5E1"
        tts_badge_color = "#1D4ED8" if tts_enabled else "#64748B"

        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; flex-wrap: wrap; padding-top: 8px;">
            <span style="
                background: {db_badge_bg};
                color: {db_badge_color};
                border: 1px solid {db_badge_border};
                padding: 5px 12px;
                border-radius: 9999px;
                font-weight: 600;
                font-size: 12px;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            ">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: {db_dot_color}; display: inline-block;"></span>
                {db_status_text}
            </span>
            <span style="
                background: {tts_badge_bg};
                color: {tts_badge_color};
                border: 1px solid {tts_badge_border};
                padding: 5px 12px;
                border-radius: 9999px;
                font-weight: 600;
                font-size: 12px;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            ">
                {'🔊 Spoken AI Voice On' if tts_enabled else '🔇 Voice Muted'}
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 8px 0 18px 0;'>", unsafe_allow_html=True)

    # Session state initialization
    if "user_query_text" not in st.session_state:
        st.session_state.user_query_text = ""
    if "trigger_browser_tts" not in st.session_state:
        st.session_state.trigger_browser_tts = False

    # ==========================================
    # QUICK INSPIRATION PROMPT CHIPS
    # ==========================================
    st.markdown("""
    <div style="font-size: 12px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">
        💡 Click to try sample queries:
    </div>
    """, unsafe_allow_html=True)

    chips = [
        ("🏥 ICU Admissions", "Show patients admitted to ICU"),
        ("💰 Treatment Costs", "Show highest treatment cost admissions"),
        ("🩺 Doctors List", "Show all doctors and their consultation fees"),
        ("📋 Denied Claims", "Show denied or pending insurance claims"),
        ("❤️ Cardiology", "Show patients diagnosed with heart or coronary condition"),
        ("🏢 Departments", "Show hospital departments by bed capacity"),
    ]

    chip_cols = st.columns(len(chips))
    for col, (label, prompt) in zip(chip_cols, chips):
        with col:
            if st.button(label, key=f"chip_{label}", use_container_width=True):
                st.session_state.user_query_text = prompt
                _run_pipeline(prompt, tts_enabled)
                st.session_state.trigger_browser_tts = True
                st.rerun()

    st.write("")

    # ==========================================
    # QUERY INPUT & ACTION BAR (FORM WITH ENTER TO SUBMIT)
    # ==========================================
    with st.form(key="query_submission_form", clear_on_submit=False, border=False):
        col_inp, col_run = st.columns([4.2, 1.2])
        with col_inp:
            user_input = st.text_input(
                "Ask in plain English or speak into your microphone (press Enter ↵ to run):",
                value=st.session_state.user_query_text,
                placeholder="E.g., 'Show all the doctors', 'Find patients admitted to ICU'...",
                label_visibility="visible"
            )
        with col_run:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            run_clicked = st.form_submit_button("⚡ Run SQL Query", type="primary", use_container_width=True)

    # Browser Microphone Recording (Cloud & Local compatible)
    if hasattr(st, "audio_input"):
        st.markdown("##### 🎙️ Record Voice Query (Browser Microphone)")
        st.caption("Click the microphone button below to record your voice from your browser, then click stop:")
        audio_val = st.audio_input("Speak your query here", key="browser_mic_input")
        if audio_val is not None:
            audio_bytes = audio_val.getvalue()
            audio_hash = hash(audio_bytes)
            if st.session_state.get("last_recorded_audio_hash") != audio_hash:
                st.session_state["last_recorded_audio_hash"] = audio_hash
                os.makedirs("audio", exist_ok=True)
                with open("audio/audio.wav", "wb") as f:
                    f.write(audio_bytes)
                st.session_state.raw_audio_path = "audio/audio.wav"

                status_box = st.empty()
                if is_audio_silent("audio/audio.wav"):
                    status_box.warning("⚠️ No audible speech detected. The recording was too faint or silent. Please speak closer to your microphone.")
                else:
                    with status_box.container():
                        st.info("🔇 **Enhancing audio & transcribing speech with Whisper AI...**")
                    clean_audio = remove_noise(input_file="audio/audio.wav", output_file="audio/clean_audio.wav")
                    st.session_state.clean_audio_path = clean_audio
                    transcribed = speech_to_text(clean_audio)

                    if transcribed and transcribed.strip():
                        clean_text = transcribed.strip().rstrip(".").strip()
                        st.session_state.user_query_text = clean_text
                        st.session_state["last_transcribed_speech"] = clean_text
                        _run_pipeline(clean_text, tts_enabled)
                        st.session_state.trigger_browser_tts = True
                        status_box.empty()
                        st.rerun()
                    else:
                        status_box.warning("⚠️ Could not clearly recognize speech. Please speak clearly into your microphone or try the prompt buttons above.")

    # Check if a physical microphone hardware exists on this host
    has_local_mic = False
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        has_local_mic = any(d.get('max_input_channels', 0) > 0 for d in devices)
    except Exception:
        has_local_mic = False

    record_clicked = False
    if has_local_mic:
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            record_clicked = st.button("🎙️ Local PC Mic (5s Timer)", use_container_width=True)
        with col_btn2:
            clear_clicked = st.button("🔄 Reset", use_container_width=True)
    else:
        clear_clicked = st.button("🔄 Reset", use_container_width=True)

    if clear_clicked:
        st.session_state.user_query_text = ""
        st.session_state.pop("clean_audio_path", None)
        st.session_state.pop("raw_audio_path", None)
        st.session_state.pop("active_sql", None)
        st.session_state.pop("active_result", None)
        st.session_state.pop("voice_summary", None)
        st.session_state.pop("voice_audio_path", None)
        st.session_state.pop("last_transcribed_speech", None)
        st.session_state.pop("last_recorded_audio_hash", None)
        st.session_state.trigger_browser_tts = False
        st.rerun()

    # ==========================================
    # VOICE PIPELINE EXECUTION (LOCAL PC SOUNDCARD)
    # ==========================================
    if record_clicked:
        try:
            status_container = st.empty()
            with status_container.container():
                st.info(f"🎙️ **[Stage 1/5] Listening...** Recording your microphone for {duration} seconds. Please speak now!")
            record_audio(filename="audio/audio.wav", duration=duration)
            st.session_state.raw_audio_path = "audio/audio.wav"

            with status_container.container():
                st.info("🔇 **[Stage 2/5] Enhancing audio...** Normalizing gain and gently removing background noise.")
            clean_audio = remove_noise(input_file="audio/audio.wav", output_file="audio/clean_audio.wav")
            st.session_state.clean_audio_path = clean_audio

            if is_audio_silent("audio/audio.wav"):
                status_container.warning("⚠️ Microphone recording was too faint or silent. Please speak closer to your microphone and ensure your microphone input volume is turned up.")
            else:
                with status_container.container():
                    st.info("🧠 **[Stage 3/5] Transcribing speech...** Running OpenAI Whisper English speech recognition.")
                transcribed = speech_to_text(clean_audio)

                if not transcribed or not transcribed.strip():
                    status_container.warning("⚠️ No clear speech was recognized. Please speak closer to your microphone and try again.")
                else:
                    clean_text = transcribed.strip().rstrip(".").strip()
                    st.session_state.user_query_text = clean_text
                    st.session_state["last_transcribed_speech"] = clean_text
                    with status_container.container():
                        st.info(f"🤖 **[Stage 4/5] Generating SQL...** Interpreting: \"{clean_text}\"")
                    _run_pipeline(clean_text, tts_enabled)
                    with status_container.container():
                        st.success("✅ **[Stage 5/5] Complete!** Query executed and voice response generated.")
                    st.session_state.trigger_browser_tts = True
                    status_container.empty()
                    st.rerun()

        except Exception as e:
            err_str = str(e)
            if "device -1" in err_str or "querying device" in err_str:
                st.warning("⚠️ **Cloud Server Note:** When deployed on the cloud, the remote Linux server has no physical sound card. Please use the **🎙️ Speak into your Microphone** widget above to record directly from your browser!")
            else:
                st.error(f"❌ Microphone/Audio Error: {e}")
                st.info("💡 Ensure your microphone is connected and authorized in Windows settings.")

    # Manual Run Triggered
    if run_clicked:
        q = user_input.strip()
        if not q:
            st.warning("⚠️ Please speak into the microphone or type a question in the box above.")
        else:
            st.session_state.user_query_text = q
            st.session_state["last_transcribed_speech"] = q
            with st.spinner("🤖 Translating query and fetching results..."):
                _run_pipeline(q, tts_enabled)
            st.session_state.trigger_browser_tts = True
            st.rerun()

    # ==========================================
    # TEXT-TO-SPEECH (VOICE OUTPUT) CARD
    # ==========================================
    if "last_transcribed_speech" in st.session_state and st.session_state["last_transcribed_speech"]:
        st.markdown(f"""
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 10px 14px; margin: 12px 0; display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">🗣️</span>
            <div>
                <span style="font-size: 11px; font-weight: 700; color: #1E40AF; text-transform: uppercase; letter-spacing: 0.05em;">Active Natural Language Query:</span>
                <div style="font-size: 14.5px; font-weight: 600; color: #1E3A8A;">"{st.session_state['last_transcribed_speech']}"</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if "voice_summary" in st.session_state and st.session_state.voice_summary:
        summary_text = st.session_state.voice_summary
        audio_path = st.session_state.get("voice_audio_path")

        st.markdown(f"""
        <div class="voice-response-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="voice-pulse"></span>
                    <span style="font-weight: 700; color: #065F46; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em;">
                        AI Spoken Response (Voice Output)
                    </span>
                </div>
                <span style="font-size: 11px; background: rgba(16, 185, 129, 0.15); color: #047857; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">
                    Windows SAPI • 100% Offline
                </span>
            </div>
            <div style="font-size: 16px; font-weight: 600; color: #064E3B; line-height: 1.5; margin: 8px 0 12px 0;">
                "{summary_text}"
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Audio Player & Browser Trigger
        if audio_path and os.path.exists(audio_path):
            st.audio(audio_path, autoplay=True)

        col_audio1, col_audio2 = st.columns([2, 3])
        with col_audio1:
            if st.button("🔊 Replay Voice Answer", key="replay_voice_btn", use_container_width=True):
                st.markdown(get_browser_tts_html(summary_text), unsafe_allow_html=True)
        with col_audio2:
            st.markdown(get_browser_tts_html(summary_text), unsafe_allow_html=True)

    # ==========================================
    # RESULTS & TABS DATA HUB
    # ==========================================
    if "active_sql" in st.session_state and st.session_state.active_sql:
        st.markdown("<hr style='margin: 18px 0;'>", unsafe_allow_html=True)

        tab_grid, tab_chart, tab_sql, tab_audio = st.tabs([
            "📊 Query Output", 
            "📈 Smart Chart", 
            "💻 Generated SQL", 
            "🎧 Voice & Audio Inspector"
        ])

        # TAB 1: Query Output
        with tab_grid:
            if st.session_state.get("active_sql_valid", False):
                if "active_result" in st.session_state and st.session_state.active_result is not None:
                    success, df_or_msg, latency, err = st.session_state.active_result
                    if success:
                        if isinstance(df_or_msg, pd.DataFrame):
                            df = df_or_msg
                            col_m1, col_m2, col_m3 = st.columns([2, 2, 2])
                            with col_m1:
                                st.metric("Records Found", f"{len(df)}")
                            with col_m2:
                                st.metric("Execution Latency", f"{latency:.1f} ms")
                            with col_m3:
                                csv = df.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label="📥 Download CSV",
                                    data=csv,
                                    file_name="query_results.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                            st.write("")
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.info(df_or_msg)
                    else:
                        st.error(f"❌ Database execution error: {err}")
            else:
                st.error("❌ Safety Block: The generated SQL query was flagged as unsafe. Execution was aborted.")

        # TAB 2: Smart Chart Visualization
        with tab_chart:
            if "active_result" in st.session_state and st.session_state.active_result is not None:
                success, df_or_msg, latency, err = st.session_state.active_result
                if success and isinstance(df_or_msg, pd.DataFrame):
                    _render_smart_chart(df_or_msg)
                else:
                    st.info("Execute a successful query to view automatic charts.")
            else:
                st.info("No query results available to visualize.")

        # TAB 3: SQL Breakdown
        with tab_sql:
            st.markdown("##### Executed SQL Query")
            st.code(st.session_state.active_sql, language="sql")
            
            explanation = _explain_sql(st.session_state.active_sql)
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; margin-top: 10px; font-size: 13.5px; color: #334155;">
                <b>🤖 Query Explanation:</b> {explanation}
            </div>
            """, unsafe_allow_html=True)

        # TAB 4: Voice Inspector
        with tab_audio:
            st.markdown("##### Audio Stream Analysis")
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                st.caption("🎙️ Original Raw Microphone Audio")
                raw_path = st.session_state.get("raw_audio_path", "audio/audio.wav")
                if os.path.exists(raw_path):
                    st.audio(raw_path)
                else:
                    st.caption("No voice recorded yet.")

            with col_a2:
                st.caption("🔇 Cleaned Audio (Noise Reduction Filtered)")
                clean_path = st.session_state.get("clean_audio_path", "audio/clean_audio.wav")
                if os.path.exists(clean_path):
                    st.audio(clean_path)
                else:
                    st.caption("No cleaned audio yet.")


def _run_pipeline(question, tts_enabled=True):
    """Core translation, SQL execution, and TTS synthesis pipeline."""
    sql = generate_sql(question)
    is_valid = validate_sql(sql)
    st.session_state.active_sql = sql
    st.session_state.active_sql_valid = is_valid

    if is_valid:
        success, df_or_msg, latency, err = execute_sql_query(sql)
        status_str = "Success" if success else "Failed"
        log_query(
            natural_query=question,
            sql_query=sql,
            status=status_str,
            error_msg=err,
            execution_time=latency
        )
        st.session_state.active_result = (success, df_or_msg, latency, err)

        # Text-to-Speech (Voice Output) Generation
        if tts_enabled:
            summary = summarize_query_for_voice(question, df_or_msg, success)
            st.session_state.voice_summary = summary
            audio_file = generate_voice_response(summary, output_file="audio/ai_response.mp3")
            st.session_state.voice_audio_path = audio_file
        else:
            st.session_state.voice_summary = None
            st.session_state.voice_audio_path = None
    else:
        st.session_state.active_result = None
        st.session_state.voice_summary = "Query validation failed. The query was flagged as unsafe."
        st.session_state.voice_audio_path = None


def _render_smart_chart(df: pd.DataFrame):
    """Dynamically detects columns and generates an appropriate Altair chart."""
    if df.empty:
        st.info("The query returned an empty table; no data to visualize.")
        return

    # Check for single value result
    if df.shape == (1, 1):
        col_name = df.columns[0].replace('_', ' ').title()
        val = df.iloc[0, 0]
        st.metric(label=f"Summary: {col_name}", value=str(val))
        return

    # Identify numeric and text columns
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    # Exclude technical IDs from being the primary numeric metric
    metric_cols = [c for c in num_cols if not c.lower().endswith('_id') and c.lower() != 'id']
    cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns.tolist()

    if metric_cols and cat_cols:
        x_col = cat_cols[0]
        y_col = metric_cols[0]
        st.markdown(f"###### 📊 {y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}")
        
        chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#2563EB").encode(
            x=alt.X(f"{x_col}:N", sort="-y", title=x_col.replace('_', ' ').title()),
            y=alt.Y(f"{y_col}:Q", title=y_col.replace('_', ' ').title()),
            tooltip=[f"{c}:N" if c in cat_cols else f"{c}:Q" for c in [x_col, y_col]]
        ).properties(height=340).interactive()
        
        st.altair_chart(chart, use_container_width=True)

    elif len(cat_cols) >= 1 and len(df) <= 15:
        # Category count chart
        col_to_count = cat_cols[0]
        st.markdown(f"###### 📊 Frequency Distribution: {col_to_count.replace('_', ' ').title()}")
        counts = df[col_to_count].value_counts().reset_index()
        counts.columns = [col_to_count, "Count"]
        
        chart = alt.Chart(counts).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#8B5CF6").encode(
            x=alt.X(f"{col_to_count}:N", sort="-y"),
            y=alt.Y("Count:Q"),
            tooltip=[f"{col_to_count}:N", "Count:Q"]
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("ℹ️ All columns are textual. Please inspect the structured results in the **Query Output** tab.")


def _explain_sql(sql: str) -> str:
    """Provides a concise plain-English explanation of the SQL structure."""
    sql_upper = sql.upper()
    parts = []
    
    if "SELECT" in sql_upper:
        if "COUNT(" in sql_upper:
            parts.append("Calculates the total count of matching rows")
        elif "AVG(" in sql_upper:
            parts.append("Computes the arithmetic average of numeric values")
        elif "MAX(" in sql_upper:
            parts.append("Finds the maximum value in the dataset")
        elif "MIN(" in sql_upper:
            parts.append("Finds the minimum value in the dataset")
        else:
            parts.append("Retrieves matching records from the database")

    for tbl in ["EMPLOYEES", "DEPARTMENTS", "PROJECTS", "EMPLOYEE_PROJECTS"]:
        if f"FROM {tbl}" in sql_upper or f"JOIN {tbl}" in sql_upper:
            parts.append(f"from the `{tbl.lower()}` table")

    if "JOIN" in sql_upper:
        parts.append("cross-referencing related tables using foreign key relationships")

    if "WHERE" in sql_upper:
        parts.append("applying specific filter criteria")

    if "ORDER BY" in sql_upper:
        parts.append("sorting the output")

    if "LIMIT" in sql_upper:
        parts.append("limiting the number of returned results")

    if not parts:
        return "Executes a standard SELECT query on the connected database."
    return ", ".join(parts) + "."
