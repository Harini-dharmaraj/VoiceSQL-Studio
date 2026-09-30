import streamlit as st

def show_about_page():
    st.title("ℹ️ About the Project")
    st.caption("AI Voice-to-SQL Generator with Background Noise Removal and Intelligent Database Query System.")
    st.divider()

    # Introduction
    st.markdown(
        """
        ### Project Overview
        This intelligent web application enables users to interact with relational databases using **natural voice commands** instead of writing manual SQL. 
        It integrates advanced speech processing, background noise reduction, speech-to-text translation, AI-driven SQL synthesis, and query optimization, making databases accessible to non-technical users.
        """
    )

    st.divider()

    # System Pipeline
    st.subheader("🔁 End-to-End System Pipeline")
    st.write("Here is how your voice command travels through the system:")

    import textwrap
    flow_html = textwrap.dedent("""
        <div style="display: flex; flex-direction: column; gap: 15px; margin: 20px 0;">
            <div style="background: #1E293B; border-left: 5px solid #3B82F6; padding: 15px; border-radius: 8px; color: white;">
                <strong style="color: #60A5FA;">🎙️ Stage 1: Voice Recording</strong><br>
                Captures raw speech signals from the local microphone using <code>sounddevice</code> at a sample rate of 16kHz.
            </div>
            <div style="background: #1E293B; border-left: 5px solid #10B981; padding: 15px; border-radius: 8px; color: white;">
                <strong style="color: #34D399;">🔇 Stage 2: Background Noise Removal</strong><br>
                Applies spectral gating noise reduction via <code>noisereduce</code> to clean ambient sounds (fan hum, clicks) for cleaner recognition.
            </div>
            <div style="background: #1E293B; border-left: 5px solid #F59E0B; padding: 15px; border-radius: 8px; color: white;">
                <strong style="color: #FBBF24;">📝 Stage 3: Speech-to-Text Conversion</strong><br>
                Translates the cleaned WAV audio file into natural text commands using the pre-trained <code>OpenAI Whisper</code> neural network.
            </div>
            <div style="background: #1E293B; border-left: 5px solid #8B5CF6; padding: 15px; border-radius: 8px; color: white;">
                <strong style="color: #A78BFA;">🤖 Stage 4: AI SQL Synthesis</strong><br>
                Feeds the text query and active database schema context into the selected AI Model (Gemini, OpenAI, or Flan-T5) to write an SQL statement.
            </div>
            <div style="background: #1E293B; border-left: 5px solid #EC4899; padding: 15px; border-radius: 8px; color: white;">
                <strong style="color: #F472B6;">🛡️ Stage 5: Security Sanitizer</strong><br>
                Validates query strings against regex rules blocking destructive commands (DROP, DELETE, ALTER, etc.) before running on the database.
            </div>
            <div style="background: #1E293B; border-left: 5px solid #06B6D4; padding: 15px; border-radius: 8px; color: white;">
                <strong style="color: #67E8F9;">🗄️ Stage 6: Database Execution</strong><br>
                Connects dynamically to the database, executes the safe query, logs execution history, and returns structured DataFrames with CSV export.
            </div>
        </div>
    """).strip()
    st.markdown(flow_html, unsafe_allow_html=True)

    st.divider()

    # Tech Stack
    st.subheader("🛠️ Technologies & Libraries")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            **Frontend & UI**
            * **Streamlit**: Web server hosting dashboard, configuration modules, and charts.
            * **Altair**: Interactive data visualization.
            * **HTML5 / CSS3**: Elegant visual styles and customized responsive cards.
            
            **Speech Processing**
            * **sounddevice & soundfile**: Audio recording and file save controls.
            * **noisereduce**: DSP algorithm for ambient sound cleaning.
            * **OpenAI Whisper**: Speech transcribing neural engine.
            """
        )
    with col2:
        st.markdown(
            """
            **AI SQL Translation**
            * **Transformers (Hugging Face)**: Offline Flan-T5 tokenizers and pipelines.
            * **Google Gemini & OpenAI APIs**: Advanced deep reasoning query builders.
            
            **Relational Database**
            * **SQLite**: Lightweight file database (active).
            * **MySQL**: Production relational database (Phase 2 Upgrade).
            * **Pandas**: Structured dataset querying and CSV management.
            """
        )

    st.divider()
    st.write("💡 *Developed for Final Year Capstone Project. Designed for intuitive and accessible database interactions.*")
