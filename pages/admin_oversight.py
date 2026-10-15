import streamlit as st
import pandas as pd
from database.auth import get_all_users_for_admin, get_all_user_datasets_for_admin, update_user_role, delete_user_by_admin
from database.history import get_query_history

def show_admin_oversight_page():
    user = st.session_state.get("current_user", {})
    if user.get("role") != "admin":
        st.error("⛔ Access Denied: This portal is strictly restricted to System Administrators.")
        st.stop()

    st.title("🛡️ Administrator: User Action & Oversight")
    st.caption("Monitor registered users, inspect uploaded datasets, and audit live user queries and actions.")
    st.divider()

    # Load administrative data
    all_users = get_all_users_for_admin()
    all_datasets = get_all_user_datasets_for_admin()
    all_queries = get_query_history(limit=500, username=None)

    # Top KPI Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Registered Users", len(all_users))
    with col_m2:
        st.metric("Uploaded Datasets", len(all_datasets))
    with col_m3:
        st.metric("Total User Queries", len(all_queries))
    with col_m4:
        admin_count = sum(1 for u in all_users if u.get("role") == "admin")
        st.metric("Administrators", admin_count)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    tab_users, tab_datasets, tab_activity = st.tabs([
        "👥 Registered User Accounts",
        "📁 User Uploaded Datasets",
        "📜 Live User Action & Query Audit"
    ])

    # ========================================================
    # TAB 1: USER ACCOUNTS
    # ========================================================
    with tab_users:
        st.subheader("👥 Registered User Accounts")
        st.caption("Inspect user accounts and manage access permissions. Passwords are securely hashed and hidden.")

        if all_users:
            users_df = pd.DataFrame(all_users)
            display_df = users_df.rename(columns={
                "user_id": "User ID",
                "username": "Username",
                "email": "Email Address",
                "full_name": "Full Name",
                "role": "Role",
                "created_at": "Registration Date",
                "total_datasets": "Datasets Count"
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("<hr style='border-color: #E2E8F0; margin: 20px 0;'>", unsafe_allow_html=True)
            st.markdown("#### ⚙️ User Role & Account Actions")

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                with st.expander("👑 Change User Role (Admin / User)", expanded=False):
                    target_user = st.selectbox(
                        "Select User:",
                        options=all_users,
                        format_func=lambda u: f"ID {u['user_id']} - @{u['username']} ({u['full_name']}) [{u['role'].upper()}]",
                        key="admin_role_select_box"
                    )
                    new_role = st.selectbox(
                        "Assign Role:",
                        ["admin", "user"],
                        index=0 if target_user.get("role") == "admin" else 1,
                        key="admin_new_role_box"
                    )
                    if st.button("Update Role", type="primary", key="btn_apply_role"):
                        ok_r, msg_r = update_user_role(target_user["user_id"], new_role)
                        if ok_r:
                            st.success(msg_r)
                            st.rerun()
                        else:
                            st.error(msg_r)

            with col_u2:
                with st.expander("🗑️ Delete User Account", expanded=False):
                    delete_options = [u for u in all_users if u["user_id"] != user.get("user_id")]
                    if delete_options:
                        del_target = st.selectbox(
                            "Select User to Delete:",
                            options=delete_options,
                            format_func=lambda u: f"ID {u['user_id']} - @{u['username']} ({u['email']})",
                            key="admin_delete_user_box"
                        )
                        st.warning("⚠️ Deleting an account permanently deletes their registered data.")
                        if st.button(f"Permanently Delete @{del_target['username']}", type="secondary", key="btn_confirm_delete"):
                            ok_d, msg_d = delete_user_by_admin(del_target["user_id"])
                            if ok_d:
                                st.success(msg_d)
                                st.rerun()
                            else:
                                st.error(msg_d)
                    else:
                        st.info("No other user accounts to delete.")
        else:
            st.info("No users registered yet.")

    # ========================================================
    # TAB 2: USER UPLOADED DATASETS
    # ========================================================
    with tab_datasets:
        st.subheader("📁 Custom Datasets Uploaded by Users")
        st.caption("Overview of all dynamic CSV and Excel spreadsheets uploaded across user workspaces.")

        if all_datasets:
            ds_df = pd.DataFrame(all_datasets)
            ds_display = ds_df.rename(columns={
                "dataset_id": "Dataset ID",
                "username": "Uploaded By (@User)",
                "email": "User Email",
                "table_name": "Database Table",
                "display_name": "Display Name",
                "row_count": "Total Records",
                "created_at": "Upload Timestamp"
            })
            st.dataframe(ds_display, use_container_width=True, hide_index=True)
        else:
            st.info("No user datasets uploaded yet. Users can upload CSVs under Database Manager.")

    # ========================================================
    # TAB 3: LIVE USER ACTION & QUERY AUDIT
    # ========================================================
    with tab_activity:
        st.subheader("📜 Live User Query & Action Audit Log")
        st.caption("Real-time feed of all natural language and voice queries executed by users, generated SQL, and latency.")

        if not all_queries.empty:
            q_filter = st.text_input("🔍 Filter Activity by Username, Question, or SQL:", value="")
            filtered_q = all_queries.copy()
            if q_filter.strip():
                k = q_filter.lower()
                filtered_q = filtered_q[
                    filtered_q["natural_query"].str.lower().str.contains(k, na=False) |
                    filtered_q["sql_query"].str.lower().str.contains(k, na=False) |
                    filtered_q["username"].str.lower().str.contains(k, na=False)
                ]

            q_display = filtered_q.rename(columns={
                "timestamp": "Timestamp",
                "username": "User (@)",
                "natural_query": "Spoken / Natural Question",
                "sql_query": "Generated SQL Query",
                "status": "Status",
                "execution_time": "Latency (ms)",
                "error_msg": "Error (if any)"
            })
            if "id" in q_display.columns:
                q_display = q_display.drop(columns=["id"])

            st.dataframe(q_display, use_container_width=True, hide_index=True)
        else:
            st.info("No user query actions logged yet.")
