import streamlit as st
import pandas as pd
from database.history import get_query_history, clear_query_history
from database.execute_query import execute_sql_query

def show_history_page():
    st.title("📜 Query History Log")
    st.caption("Inspect and audit all natural language queries, generated SQL, execution metrics, and logs.")
    st.divider()

    # Load history
    df = get_query_history(limit=200)

    if df.empty:
        st.info("No queries logged in the history yet. Try running some text or voice queries!")
        return

    # Statistics / KPI summary
    total_logs = len(df)
    successes = len(df[df["status"] == "Success"])
    failed = len(df[df["status"] == "Failed"])
    avg_latency = df["execution_time"].mean() if not df["execution_time"].empty else 0.0

    col_tot, col_succ, col_fail, col_lat = st.columns(4)
    col_tot.metric("Total Executed", f"{total_logs}")
    col_succ.metric("Successful", f"{successes}", delta=f"{successes/total_logs*100:.1f}%" if total_logs > 0 else "0%")
    col_fail.metric("Failed", f"{failed}")
    col_lat.metric("Avg Latency", f"{avg_latency:.2f} ms")

    st.divider()

    # Search filter bar
    search_keyword = st.text_input("🔍 Search History by Natural Language or SQL Query", value="")
    
    filtered_df = df.copy()
    if search_keyword.strip():
        k = search_keyword.lower()
        filtered_df = filtered_df[
            filtered_df["natural_query"].str.lower().str.contains(k, na=False) |
            filtered_df["sql_query"].str.lower().str.contains(k, na=False)
        ]

    st.subheader(f"Logged Queries ({len(filtered_df)})")
    
    # Format and display DataFrame
    display_df = filtered_df.copy()
    display_df = display_df.rename(columns={
        "timestamp": "Timestamp",
        "natural_query": "Natural Language Query",
        "sql_query": "Generated SQL",
        "status": "Execution Status",
        "error_msg": "Errors/Logs",
        "execution_time": "Latency (ms)"
    })
    
    # Hide id column
    if "id" in display_df.columns:
        display_df = display_df.drop(columns=["id"])
        
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Actions: Download and Clear History
    st.divider()
    col_dl, col_clr, _ = st.columns([1, 1, 3])

    csv_data = df.to_csv(index=False).encode('utf-8')
    col_dl.download_button(
        label="📥 Download History (CSV)",
        data=csv_data,
        file_name="query_execution_history.csv",
        mime="text/csv",
        use_container_width=True
    )

    if col_clr.button("🔥 Clear Complete History", type="secondary", use_container_width=True):
        if clear_query_history():
            st.success("🎉 Query history cleared successfully!")
            st.rerun()
        else:
            st.error("Failed to clear query history.")
            
    # Re-run a selected query from history
    st.subheader("🔁 Quick Re-run Query")
    query_options = filtered_df["sql_query"].tolist()
    if query_options:
        selected_sql = st.selectbox("Select SQL query to re-run:", query_options)
        if st.button("🚀 Re-execute Selected", type="primary"):
            with st.spinner("Re-executing query..."):
                success, result, latency, err = execute_sql_query(selected_sql)
            if success:
                st.success(f"Executed successfully in {latency:.2f} ms")
                if isinstance(result, pd.DataFrame):
                    st.dataframe(result, use_container_width=True)
                else:
                    st.info(result)
            else:
                st.error(f"Execution Error: {err}")
