import streamlit as st
import pandas as pd
from database.history import get_query_history

def show_stats():
    df = get_query_history(limit=500)
    
    total_queries = 0
    successful = 0
    today_queries = 0
    avg_latency = "--"
    success_rate = "100%"
    
    if not df.empty:
        total_queries = len(df)
        successful = len(df[df["status"] == "Success"])
        if total_queries > 0:
            success_rate = f"{(successful / total_queries * 100):.0f}%"
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        today = pd.Timestamp.now().normalize()
        if df['timestamp'].dt.tz is not None:
            today = today.tz_localize(df['timestamp'].dt.tz)
            
        today_queries = len(df[df['timestamp'] >= today])
        
        mean_lat = df["execution_time"].mean()
        if pd.notna(mean_lat):
            avg_latency = f"{mean_lat:.1f} ms"

    cols = st.columns(4)

    cards = [
        {
            "icon": "📄",
            "icon_bg": "#EFF6FF",
            "label": "Total Queries",
            "val": str(total_queries),
            "sub": "All-time executed",
            "badge": f"{total_queries} runs",
            "badge_color": "#2563EB",
            "badge_bg": "#DBEAFE"
        },
        {
            "icon": "✅",
            "icon_bg": "#ECFDF5",
            "label": "Successful",
            "val": str(successful),
            "sub": f"{success_rate} success rate",
            "badge": "Active",
            "badge_color": "#059669",
            "badge_bg": "#D1FAE5"
        },
        {
            "icon": "📅",
            "icon_bg": "#FFFBEB",
            "label": "Today's Queries",
            "val": str(today_queries),
            "sub": "Logged past 24h",
            "badge": "Today",
            "badge_color": "#D97706",
            "badge_bg": "#FEF3C7"
        },
        {
            "icon": "⚡",
            "icon_bg": "#F5F3FF",
            "label": "Avg Response",
            "val": avg_latency,
            "sub": "End-to-end latency",
            "badge": "Fast",
            "badge_color": "#7C3AED",
            "badge_bg": "#EDE9FE"
        },
    ]

    for col, c in zip(cols, cards):
        with col:
            st.markdown(
                f"""
<div style="
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease;
">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div style="
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: {c['icon_bg']};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        ">{c['icon']}</div>
        <span style="
            background: {c['badge_bg']};
            color: {c['badge_color']};
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 9999px;
        ">{c['badge']}</span>
    </div>
    <div>
        <div style="font-size: 28px; font-weight: 700; color: #0F172A; line-height: 1.1; margin-bottom: 4px;">{c['val']}</div>
        <div style="font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 2px;">{c['label']}</div>
        <div style="font-size: 11px; color: #94A3B8;">{c['sub']}</div>
    </div>
</div>
""",
                unsafe_allow_html=True,
            )