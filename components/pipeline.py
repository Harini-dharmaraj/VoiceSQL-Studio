import streamlit as st
from utils.config_manager import load_config

def show_pipeline():
    config = load_config()
    db_engine = config.get("db_type", "SQLite")
    ai_engine = config.get("ai_provider", "Offline Rules")
    if ai_engine == "Mock":
        ai_engine = "Offline Rules"

    st.subheader("🧠 End-to-End Processing Pipeline")
    st.caption("How your spoken or typed natural language flows through the system.")

    steps = [
        {
            "num": "01",
            "icon": "🎙️",
            "title": "Voice Input",
            "desc": "16kHz Audio Stream",
            "color": "#3B82F6",
            "bg": "#EFF6FF"
        },
        {
            "num": "02",
            "icon": "🔇",
            "title": "Noise Reduction",
            "desc": "DSP Spectral Gating",
            "color": "#10B981",
            "bg": "#ECFDF5"
        },
        {
            "num": "03",
            "icon": "📝",
            "title": "Whisper STT",
            "desc": "Neural Speech-to-Text",
            "color": "#F59E0B",
            "bg": "#FFFBEB"
        },
        {
            "num": "04",
            "icon": "🤖",
            "title": "SQL Synthesis",
            "desc": f"{ai_engine}",
            "color": "#8B5CF6",
            "bg": "#F5F3FF"
        },
        {
            "num": "05",
            "icon": "🗄️",
            "title": "Database Engine",
            "desc": f"{db_engine} Database",
            "color": "#06B6D4",
            "bg": "#ECFEFF"
        },
        {
            "num": "06",
            "icon": "📊",
            "title": "Result Analytics",
            "desc": "DataFrames & Visuals",
            "color": "#EC4899",
            "bg": "#FDF2F8"
        }
    ]

    pipeline_cards = ""
    for i, s in enumerate(steps):
        arrow = """<div style="color: #94A3B8; font-size: 18px; font-weight: bold; margin: 0 4px;">→</div>""" if i < len(steps) - 1 else ""
        pipeline_cards += f"""
        <div style="
            flex: 1;
            min-width: 140px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            position: relative;
        ">
            <div style="
                display: inline-block;
                background: {s['bg']};
                color: {s['color']};
                font-size: 11px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 9999px;
                margin-bottom: 8px;
            ">STEP {s['num']}</div>
            <div style="font-size: 26px; margin-bottom: 6px;">{s['icon']}</div>
            <div style="font-weight: 600; font-size: 13px; color: #0F172A; margin-bottom: 2px;">{s['title']}</div>
            <div style="font-size: 11px; color: #64748B;">{s['desc']}</div>
        </div>
        {arrow}
        """

    html_content = f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 6px;
        overflow-x: auto;
        padding: 4px 2px 12px 2px;
    ">
        {pipeline_cards}
    </div>
    """

    st.markdown(html_content.strip(), unsafe_allow_html=True)