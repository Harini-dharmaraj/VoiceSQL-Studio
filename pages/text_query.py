import streamlit as st
import pandas as pd
from sql_generator.generate_sql import generate_sql
from sql_generator.validator import validate_sql
from database.execute_query import execute_sql_query
from database.history import log_query

def show_text_query_page():
    st.title("⌨️ Natural Language Text Query")
    st.caption("Ask questions in plain English to retrieve data from your database instantly.")
    st.divider()

    # Preset suggestions
    st.markdown("""
    <div style="font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">
        💡 POPULAR QUESTIONS
    </div>
    """, unsafe_allow_html=True)
    
    suggestions = [
        ("👥 All Employees", "Show all employees"),
        ("💰 Highest Earner", "Find the employee with the highest salary"),
        ("💻 Engineering Team", "List all engineering department employees"),
        ("📊 Project Budgets", "What is the total budget for all projects?"),
    ]

    if "text_query_input" not in st.session_state:
        st.session_state.text_query_input = ""

    cols = st.columns(len(suggestions))
    for col, (label, prompt) in zip(cols, suggestions):
        if col.button(label, key=f"sug_{label}", use_container_width=True):
            st.session_state.text_query_input = prompt
            st.rerun()

    # Query Input Area
    user_query = st.text_area(
        "Enter your query in plain English",
        value=st.session_state.text_query_input,
        placeholder="Example: Find employees in Sales department who earn more than 60,000...",
        height=100,
        label_visibility="collapsed"
    )

    col_run, col_clear, _ = st.columns([1, 1, 3])
    run_clicked = col_run.button("⚡ Run Query", type="primary", use_container_width=True)
    clear_clicked = col_clear.button("🔄 Reset", use_container_width=True)

    if clear_clicked:
        st.session_state.text_query_input = ""
        st.session_state.pop("last_generated_sql", None)
        st.session_state.pop("text_query_result", None)
        st.rerun()

    if run_clicked:
        query_text = user_query.strip()
        if not query_text:
            st.warning("⚠️ Please enter a question or click one of the suggested prompts above.")
        else:
            with st.spinner("🤖 Translating and querying database..."):
                generated_sql = generate_sql(query_text)
                is_valid = validate_sql(generated_sql)
            
            st.session_state.last_generated_sql = generated_sql
            st.session_state.last_natural_query = query_text
            st.session_state.sql_validated = is_valid

            if is_valid:
                with st.spinner("Retrieving data..."):
                    success, df_or_msg, latency, err = execute_sql_query(generated_sql)
                
                status_str = "Success" if success else "Failed"
                log_query(
                    natural_query=query_text,
                    sql_query=generated_sql,
                    status=status_str,
                    error_msg=err,
                    execution_time=latency
                )
                st.session_state.text_query_result = (success, df_or_msg, latency, err)
            else:
                st.session_state.text_query_result = None

    if "last_generated_sql" in st.session_state:
        st.divider()
        if st.session_state.get("sql_validated", False):
            if "text_query_result" in st.session_state and st.session_state.text_query_result is not None:
                success, df_or_msg, latency, err = st.session_state.text_query_result
                if success:
                    st.subheader("📊 Query Results")
                    if isinstance(df_or_msg, pd.DataFrame):
                        col_m1, col_m2 = st.columns([3, 1])
                        with col_m1:
                            st.caption(f"Retrieved **{len(df_or_msg)} records** in **{latency:.1f} ms**")
                        with col_m2:
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

                    with st.expander("🔍 View Technical SQL Query (Optional)", expanded=False):
                        st.code(st.session_state.last_generated_sql, language="sql")
                else:
                    st.error(f"❌ Database execution error: {err}")
                    with st.expander("🔍 View Generated SQL", expanded=True):
                        st.code(st.session_state.last_generated_sql, language="sql")
        else:
            st.error("❌ Safety Block: Unsafe query detected. Execution was blocked for security.")
