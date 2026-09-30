import streamlit as st
import pandas as pd
from speech.voice_recorder import record_audio
from speech.noise_removal import remove_noise
from speech.speech_to_text import speech_to_text
from sql_generator.generate_sql import generate_sql
from sql_generator.validator import validate_sql
from database.execute_query import execute_sql_query
from database.history import log_query
from utils.config_manager import load_config

def show_voice_card():
    st.subheader("🎤 AI Voice Assistant")
    st.caption("Speak naturally into your microphone or type your question below.")

    config = load_config()
    duration = int(config.get("recording_duration", 5))

    if "recognized_text" not in st.session_state:
        st.session_state.recognized_text = ""

    # Quick prompt chips for convenience
    st.markdown("""
    <div style="font-size: 12px; font-weight: 600; color: #64748B; margin-bottom: 6px;">💡 QUICK PROMPTS</div>
    """, unsafe_allow_html=True)
    
    chip_cols = st.columns(4)
    quick_prompts = [
        ("👥 All Employees", "Show all employees"),
        ("💰 Highest Salary", "Find employee with highest salary"),
        ("💻 Engineering", "Show employees in Engineering department"),
        ("📊 Projects Budget", "Show all projects ordered by budget"),
    ]
    for col, (label, prompt) in zip(chip_cols, quick_prompts):
        with col:
            if st.button(label, key=f"chip_{label}", use_container_width=True):
                st.session_state.recognized_text = prompt
                st.rerun()

    query = st.text_area(
        "Ask your database",
        value=st.session_state.recognized_text,
        placeholder="Example: Show all employees whose salary is above 50000",
        height=110,
        label_visibility="collapsed"
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        record_clicked = st.button("🎙️ Record Voice", use_container_width=True)
    with col2:
        reset_clicked = st.button("🔄 Reset", use_container_width=True)
    with col3:
        run_clicked = st.button("⚡ Run Query", type="primary", use_container_width=True)

    if record_clicked:
        with st.spinner(f"🎙️ Recording for {duration} seconds... Please speak now."):
            record_audio(filename="audio/audio.wav", duration=duration)
        
        with st.spinner("🔇 Filtering background noise..."):
            clean_audio = remove_noise(input_file="audio/audio.wav", output_file="audio/clean_audio.wav")
        
        with st.spinner("🧠 Transcribing speech with Whisper..."):
            recognized_text = speech_to_text(clean_audio)

        st.session_state.recognized_text = recognized_text
        st.session_state.dashboard_clean_audio = clean_audio
        st.rerun()

    if reset_clicked:
        st.session_state.recognized_text = ""
        st.session_state.pop("last_generated_sql", None)
        st.session_state.pop("dashboard_query_result", None)
        st.session_state.pop("dashboard_clean_audio", None)
        st.rerun()

    if st.session_state.get("dashboard_clean_audio"):
        st.caption("🔊 Cleaned Voice Playback:")
        st.audio(st.session_state.dashboard_clean_audio)

    if run_clicked:
        question = query.strip()
        if not question:
            st.warning("⚠️ Please speak into the mic or enter a query above.")
        else:
            with st.spinner("🤖 Translating natural language to SQL..."):
                sql_query = generate_sql(question)
                is_valid = validate_sql(sql_query)
                
            st.session_state.last_generated_sql = sql_query
            st.session_state.last_natural_query = question
            st.session_state.sql_validated = is_valid

            if is_valid:
                with st.spinner("Executing query on database..."):
                    success, df_or_msg, latency, err = execute_sql_query(sql_query)

                status_str = "Success" if success else "Failed"
                log_query(
                    natural_query=question,
                    sql_query=sql_query,
                    status=status_str,
                    error_msg=err,
                    execution_time=latency
                )
                st.session_state.dashboard_query_result = (success, df_or_msg, latency, err)
            else:
                st.session_state.dashboard_query_result = None

    if "last_generated_sql" in st.session_state:
        st.divider()
        if st.session_state.get("sql_validated", False):
            if "dashboard_query_result" in st.session_state and st.session_state.dashboard_query_result is not None:
                success, df_or_msg, latency, err = st.session_state.dashboard_query_result
                if success:
                    st.markdown("#### 📊 Query Results")
                    if isinstance(df_or_msg, pd.DataFrame):
                        col_meta1, col_meta2 = st.columns([3, 1])
                        with col_meta1:
                            st.caption(f"Retrieved **{len(df_or_msg)} records** in **{latency:.1f} ms**")
                        with col_meta2:
                            csv = df_or_msg.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Export CSV",
                                data=csv,
                                file_name="query_results.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        st.dataframe(df_or_msg, use_container_width=True)
                    else:
                        st.info(df_or_msg)
                    
                    # Optional collapsed SQL expander for curiosity/audit
                    with st.expander("🔍 View Generated SQL (Optional)", expanded=False):
                        st.code(st.session_state.last_generated_sql, language="sql")
                else:
                    st.error(f"❌ Database execution error: {err}")
                    with st.expander("🔍 View Generated SQL", expanded=True):
                        st.code(st.session_state.last_generated_sql, language="sql")
        else:
            st.error("❌ Safety Block: Unsafe command detected. Execution was blocked for security.")