import streamlit as st
import pandas as pd
import altair as alt
from database.history import get_query_history

def show_analytics_page():
    st.title("📈 Query Metrics & Analytics")
    st.caption("Visual dashboard for query count trends, system response latency, and database table statistics.")
    st.divider()

    # Load history log
    df = get_query_history(limit=500)

    if df.empty:
        st.info("No execution data available. Please trigger queries on the Text or Voice Query playgrounds first to populate charts.")
        return

    # Convert timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # ==========================================
    # KPI metrics row
    # ==========================================
    total = len(df)
    success_df = df[df["status"] == "Success"]
    failed_df = df[df["status"] == "Failed"]
    success_rate = (len(success_df) / total * 100) if total > 0 else 0.0
    avg_latency = df["execution_time"].mean() if not df["execution_time"].empty else 0.0
    max_latency = df["execution_time"].max() if not df["execution_time"].empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Executions", f"{total}")
    with col2:
        st.metric("Success Rate", f"{success_rate:.1f}%", delta=f"{len(success_df)} / {total}")
    with col3:
        st.metric("Avg Latency", f"{avg_latency:.1f} ms")
    with col4:
        st.metric("Peak Latency", f"{max_latency:.1f} ms")

    st.divider()

    # ==========================================
    # Charts Grid
    # ==========================================
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Query Success Ratio")
        # Aggregations
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        
        pie_chart = alt.Chart(status_counts).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(
                field="Status", 
                type="nominal", 
                scale=alt.Scale(
                    domain=['Success', 'Failed'], 
                    range=['#10B981', '#EF4444'] # Green vs Red HSL equivalents
                )
            ),
            tooltip=["Status", "Count"]
        ).properties(
            height=300
        )
        st.altair_chart(pie_chart, use_container_width=True)

    with right_col:
        st.subheader("Table Access Frequency")
        # Count references to tables in the generated SQL queries
        table_counts = {"employees": 0, "departments": 0, "projects": 0, "employee_projects": 0}
        for q in df["sql_query"]:
            q_lower = str(q).lower()
            for t in table_counts.keys():
                if t in q_lower:
                    table_counts[t] += 1
                    
        table_freq_df = pd.DataFrame(list(table_counts.items()), columns=["Table", "Query References"]).sort_values(by="Query References", ascending=False)
        
        bar_chart = alt.Chart(table_freq_df).mark_bar(cornerRadiusEnd=5, color="#F59E0B").encode(
            x=alt.X("Query References:Q", title="References Count"),
            y=alt.Y("Table:N", sort="-x", title="Database Tables"),
            tooltip=["Table", "Query References"]
        ).properties(
            height=300
        )
        st.altair_chart(bar_chart, use_container_width=True)

    # Latency Over Time (Full Width)
    st.divider()
    st.subheader("System Latency Timeline (ms)")
    
    df_sorted = df.sort_values(by="timestamp")
    
    line_chart = alt.Chart(df_sorted).mark_line(color="#3B82F6", strokeWidth=2).encode(
        x=alt.X("timestamp:T", title="Execution Timestamp"),
        y=alt.Y("execution_time:Q", title="Latency (ms)"),
        tooltip=["timestamp:T", "execution_time:Q", "status:N", "natural_query:N"]
    ).properties(
        height=320
    ).interactive()
    
    st.altair_chart(line_chart, use_container_width=True)
