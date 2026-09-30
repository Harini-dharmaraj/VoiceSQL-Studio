import streamlit as st
import textwrap
from database.history import get_query_history

def show_activity():
    st.subheader("📜 Recent Voice & Text Inquiries")
    st.caption("Real-time feed of user requests and database responses.")

    # Fetch top 5 latest activities
    df = get_query_history(limit=5)

    if df.empty:
        st.markdown(
            textwrap.dedent("""
            <div style="
                background: #FFFFFF;
                border: 1px dashed #CBD5E1;
                border-radius: 12px;
                padding: 32px 20px;
                text-align: center;
                color: #64748B;
                margin-top: 8px;
            ">
                <div style="font-size: 32px; margin-bottom: 8px;">💬</div>
                <div style="font-weight: 600; font-size: 15px; color: #334155;">No Inquiries Yet</div>
                <div style="font-size: 13px; margin-top: 4px;">Speak or type your question above to see live activity appear here.</div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        return

    items_html = ""
    for _, row in df.iterrows():
        is_success = str(row["status"]).lower() == "success"
        status_bg = "#ECFDF5" if is_success else "#FEF2F2"
        status_color = "#059669" if is_success else "#DC2626"
        status_border = "#A7F3D0" if is_success else "#FECACA"
        status_text = "COMPLETED" if is_success else "ERROR"
        status_icon = "●" if is_success else "●"

        time_val = str(row["timestamp"])[:19]
        natural_q = str(row["natural_query"]) if row["natural_query"] else "Direct Query"
        latency = f"{float(row['execution_time']):.1f} ms" if pd_not_na(row.get("execution_time")) else "--"

        items_html += f"""
<div style="
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
">
    <div style="flex: 1;">
        <div style="font-size: 14px; font-weight: 600; color: #0F172A; margin-bottom: 4px;">
            "{natural_q}"
        </div>
        <div style="display: flex; align-items: center; gap: 12px; font-size: 12px; color: #64748B;">
            <span>🕒 {time_val}</span>
            <span>⚡ {latency} response</span>
        </div>
    </div>
    <div>
        <span style="
            background: {status_bg};
            color: {status_color};
            border: 1px solid {status_border};
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        ">{status_icon} {status_text}</span>
    </div>
</div>
"""

    st.markdown(items_html.strip(), unsafe_allow_html=True)

def pd_not_na(val):
    if val is None:
        return False
    try:
        import pandas as pd
        return pd.notna(val)
    except Exception:
        return True