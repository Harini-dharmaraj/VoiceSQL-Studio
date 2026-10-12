import os
import streamlit as st
import pandas as pd
from database.db_connection import get_db_connection
from database.execute_query import execute_sql_query
from utils.config_manager import load_config

def show_database_page():
    st.title("🗄️ Database Management")
    st.caption("Inspect database tables, review schema columns, or upload custom CSV datasets.")
    st.divider()

    config = load_config()
    db_engine = config.get("db_type", "SQLite")
    db_name = "demo.db (SQLite)" if db_engine == "SQLite" else f"{config.get('mysql_database', 'voice_to_sql')} (MySQL)"
    
    db_online = False
    db_error = ""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        db_online = True
    except Exception as e:
        db_online = False
        db_error = str(e)

    # Status & Management Header
    col1, col2, col3, col4 = st.columns([2.5, 1.8, 2.5, 2.2])
    with col1:
        st.markdown(f"**Target Database:** `{db_name}`")
    with col2:
        if db_online:
            st.markdown("🟢 **Status:** Connected & Ready")
        else:
            st.markdown("🔴 **Status:** Offline / Disconnected")
    with col3:
        if st.button("🎬 Seed IMDb Movies Data", use_container_width=True, type="primary"):
            from database.seed_movies import generate_and_seed_movies
            with st.spinner("Seeding IMDb Movies, Directors, and Actors..."):
                ok, seed_msg = generate_and_seed_movies()
            if ok:
                st.success("✅ " + seed_msg)
                st.rerun()
            else:
                st.error(f"❌ {seed_msg}")
    with col4:
        if st.button("📦 Seed Classic Tables", use_container_width=True):
            from database.db_connection import init_database
            with st.spinner("Restoring sample tables..."):
                ok, seed_msg = init_database()
            if ok:
                st.success("✅ Sample database restored!")
                st.rerun()
            else:
                st.error(f"❌ {seed_msg}")

    if not db_online:
        st.warning(f"⚠️ Unable to connect to database: {db_error}. Please check database settings in the Settings tab.")
        return

    st.divider()

    tab_browse, tab_upload = st.tabs(["📋 Browse Database Tables", "📤 Upload Custom CSV Dataset"])

    # ========================================================
    # TAB 1: BROWSE TABLES
    # ========================================================
    with tab_browse:
        tables = _get_all_tables(config)

        if not tables:
            st.info("No tables found. Click 'Re-seed Default Sample Data' above or upload a CSV in the next tab.")
            return

        # Show user's active datasets
        user = st.session_state.get("current_user", {})
        user_id = user.get("user_id", 0)
        from database.auth import get_user_datasets
        my_datasets = get_user_datasets(user_id) if user_id else []
        if my_datasets:
            ds_tags = ", ".join([f"`{d['table_name']}` ({d['row_count']} rows)" for d in my_datasets])
            st.markdown(f"""
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 10px 14px; margin-bottom: 14px; font-size: 13px; color: #166534;">
                📁 <b>Your Uploaded Datasets (@{user.get('username', 'user')}):</b> {ds_tags}
            </div>
            """, unsafe_allow_html=True)

        selected_table = st.selectbox("Select Table to View:", sorted(tables))

        schema_df, total_rows = _get_table_info(selected_table, config)

        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.markdown(f"#### 📋 `{selected_table}` Table")
        with col_t2:
            st.metric(label="Total Records", value=f"{total_rows}")

        # Table data rows
        success, result, latency, err = execute_sql_query(f"SELECT * FROM {selected_table};")
        if success and isinstance(result, pd.DataFrame):
            st.dataframe(result, use_container_width=True)
            
            col_d1, col_d2, _ = st.columns([1, 1, 2])
            with col_d1:
                csv = result.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download CSV",
                    data=csv,
                    file_name=f"{selected_table}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_d2:
                # Protect core and system tables from accidental deletion
                protected_tables = [
                    "departments", "employees", "projects", "employee_projects", 
                    "query_history", "movies", "directors", "actors", "movie_cast", 
                    "reviews", "users", "user_datasets", "sqlite_sequence"
                ]
                is_core = selected_table.lower() in protected_tables
                if not is_core:
                    if st.button(f"🗑️ Delete `{selected_table}`", use_container_width=True):
                        _drop_table(selected_table)
                        st.success(f"Table `{selected_table}` deleted.")
                        st.rerun()

        # View columns schema
        with st.expander(f"🔍 View `{selected_table}` Columns & Data Types", expanded=False):
            st.dataframe(schema_df, use_container_width=True, hide_index=True)

    # ========================================================
    # TAB 2: UPLOAD & INSERT CUSTOM DATASETS
    # ========================================================
    with tab_upload:
        st.subheader("📤 Insert & Manage Your Own Data")
        st.caption("Upload your own CSV or Excel spreadsheets, seed instant business datasets, or build custom tables to query them with your voice in Voice Studio.")

        upload_mode = st.radio(
            "Choose How You Want to Add Your Data:",
            ["📁 Upload File (CSV or Excel)", "⚡ 1-Click Instant Datasets", "✏️ Interactive Table Builder"],
            horizontal=True
        )

        # ----------------------------------------------------
        # OPTION 1: FILE UPLOADER (CSV & EXCEL)
        # ----------------------------------------------------
        if upload_mode == "📁 Upload File (CSV or Excel)":
            st.markdown("##### 📁 Upload CSV or Excel Spreadsheet")
            uploaded_file = st.file_uploader(
                "Choose a CSV or Excel file (.csv, .xlsx, .xls) to import into the database:",
                type=["csv", "xlsx", "xls"],
                help="Your file will be converted into a queryable SQL table instantly."
            )

            if uploaded_file is not None:
                try:
                    fname = uploaded_file.name.lower()
                    if fname.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)

                    default_name = os.path.splitext(uploaded_file.name)[0].lower().replace(" ", "_").replace("-", "_")

                    st.write(f"📊 **File Preview:** `{uploaded_file.name}` ({len(df_upload)} records, {len(df_upload.columns)} columns)")
                    st.dataframe(df_upload.head(6), use_container_width=True)

                    col_name, col_import = st.columns([2, 1])
                    with col_name:
                        custom_table_name = st.text_input("Database Table Name:", value=default_name)
                    with col_import:
                        st.write("")
                        st.write("")
                        import_clicked = st.button("🚀 Import Table into Database", type="primary", use_container_width=True)

                    if import_clicked:
                        table_clean = custom_table_name.strip().lower().replace(" ", "_")
                        if not table_clean:
                            st.warning("Please provide a valid table name.")
                        else:
                            with st.spinner(f"Creating table `{table_clean}` and importing {len(df_upload)} records..."):
                                success_imp, err_imp = _import_df_to_database(df_upload, table_clean, config)
                            if success_imp:
                                from database.auth import record_user_dataset
                                user = st.session_state.get("current_user", {})
                                user_id = user.get("user_id", 0)
                                if user_id:
                                    record_user_dataset(user_id, table_clean, display_name=uploaded_file.name, row_count=len(df_upload))
                                st.success(f"🎉 Successfully created table `{table_clean}` with {len(df_upload)} records linked to @{user.get('username', 'user')}!")
                                st.markdown(f"""
                                <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 12px 16px; margin: 12px 0;">
                                    <b>🎙️ Ready for Voice Studio!</b> Try asking with your voice or typing:
                                    <ul>
                                        <li><i>"Show all records from {table_clean}"</i></li>
                                        <li><i>"How many {table_clean} are there?"</i></li>
                                        <li><i>"Show top 5 {table_clean}"</i></li>
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                                st.rerun()
                            else:
                                st.error(f"❌ Import failed: {err_imp}")

                except Exception as ex:
                    st.error(f"❌ Failed to parse uploaded file: {ex}")

        # ----------------------------------------------------
        # OPTION 2: 1-CLICK INSTANT DATASETS
        # ----------------------------------------------------
        elif upload_mode == "⚡ 1-Click Instant Datasets":
            st.markdown("##### ⚡ Instant Ready-to-Use Business Datasets")
            st.write("Visitors can test the Voice Studio on various industry datasets with a single click:")

            col_ds1, col_ds2 = st.columns(2)
            with col_ds1:
                st.markdown("""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                    <div style="font-weight: 700; font-size: 16px; margin-bottom: 4px;">🎬 IMDb Movies & Streaming</div>
                    <div style="font-size: 13px; color: #64748B; margin-bottom: 8px;">
                        30 blockbuster movies, 12 award-winning directors, 15 top actors, cast junctions, and critic reviews.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🎬 Load IMDb Movies Dataset", use_container_width=True, type="primary"):
                    from database.seed_movies import generate_and_seed_movies
                    with st.spinner("Seeding IMDb Movies, Directors, and Reviews..."):
                        ok, seed_msg = generate_and_seed_movies()
                    if ok:
                        st.success("✅ " + seed_msg)
                        st.rerun()
                    else:
                        st.error(f"❌ {seed_msg}")

                st.markdown("""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-top: 14px; margin-bottom: 4px;">
                    <div style="font-weight: 700; font-size: 16px; margin-bottom: 4px;">🛒 E-Commerce & Retail</div>
                    <div style="font-size: 13px; color: #64748B; margin-bottom: 8px;">
                        Customers, product catalogs, customer orders, and sales revenue items.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🛒 Load E-Commerce Sales Dataset", use_container_width=True):
                    from database.seed_ecommerce import generate_and_seed_ecommerce
                    with st.spinner("Seeding E-Commerce data..."):
                        ok_ecom, msg_ecom = generate_and_seed_ecommerce()
                    if ok_ecom:
                        st.success(f"✅ {msg_ecom}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg_ecom}")

            with col_ds2:
                st.markdown("""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 4px;">
                    <div style="font-weight: 700; font-size: 16px; margin-bottom: 4px;">🏥 Healthcare & Patients</div>
                    <div style="font-size: 13px; color: #64748B; margin-bottom: 8px;">
                        Doctors, patient demographics, clinical diagnoses, and billing admissions.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🏥 Load Healthcare & Hospital Dataset", use_container_width=True):
                    from database.seed_healthcare_500 import generate_and_seed_healthcare
                    with st.spinner("Seeding Healthcare data..."):
                        ok_hc, msg_hc = generate_and_seed_healthcare()
                    if ok_hc:
                        st.success(f"✅ {msg_hc}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg_hc}")

                st.markdown("""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-top: 14px; margin-bottom: 4px;">
                    <div style="font-weight: 700; font-size: 16px; margin-bottom: 4px;">🎓 University & Students</div>
                    <div style="font-size: 13px; color: #64748B; margin-bottom: 8px;">
                        Student records, course enrollments, grade point averages, and majors.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🎓 Load University Education Dataset", use_container_width=True):
                    # Check if datasets/students.csv exists
                    if os.path.exists("datasets/students.csv"):
                        df_st = pd.read_csv("datasets/students.csv")
                        _import_df_to_database(df_st, "students", config)
                        if os.path.exists("datasets/courses.csv"):
                            df_co = pd.read_csv("datasets/courses.csv")
                            _import_df_to_database(df_co, "courses", config)
                        st.success("✅ University students and courses loaded successfully!")
                        st.rerun()
                    else:
                        st.info("Creating students dataset...")
                        df_sample_st = pd.DataFrame([
                            {"student_id": 1, "student_name": "Alice Chen", "major": "Computer Science", "gpa": 3.9, "graduation_year": 2025},
                            {"student_id": 2, "student_name": "Bob Miller", "major": "Data Science", "gpa": 3.5, "graduation_year": 2026},
                            {"student_id": 3, "student_name": "Charlie Davis", "major": "Cybersecurity", "gpa": 3.8, "graduation_year": 2025},
                            {"student_id": 4, "student_name": "Diana Prince", "major": "Artificial Intelligence", "gpa": 4.0, "graduation_year": 2024},
                            {"student_id": 5, "student_name": "Ethan Hunt", "major": "Software Engineering", "gpa": 3.2, "graduation_year": 2027}
                        ])
                        _import_df_to_database(df_sample_st, "students", config)
                        st.success("✅ University students dataset created successfully!")
                        st.rerun()

        # ----------------------------------------------------
        # OPTION 3: INTERACTIVE TABLE BUILDER
        # ----------------------------------------------------
        elif upload_mode == "✏️ Interactive Table Builder":
            st.markdown("##### ✏️ Create Custom Table In-Browser")
            st.caption("Design your own schema and enter records directly without uploading files.")

            col_tb_name, col_tb_rows = st.columns([2, 1])
            with col_tb_name:
                builder_table_name = st.text_input("New Table Name:", value="custom_data")
            with col_tb_rows:
                num_init_rows = st.number_input("Number of Initial Rows:", min_value=1, max_value=20, value=3)

            col_names_input = st.text_input(
                "Column Names (comma separated):",
                value="item_name, category, price, quantity",
                help="Specify the column names you want in your table."
            )

            raw_cols = [c.strip().replace(" ", "_") for c in col_names_input.split(",") if c.strip()]
            if raw_cols:
                # Default starter data grid
                template_data = {c: [f"Sample {i+1}" if "name" in c or "cat" in c else (i + 1) * 10 for i in range(int(num_init_rows))] for c in raw_cols}
                df_template = pd.DataFrame(template_data)

                st.markdown("**Enter or Edit Table Rows:**")
                edited_df = st.data_editor(df_template, use_container_width=True, num_rows="dynamic")

                if st.button("💾 Save & Create Table", type="primary", use_container_width=True):
                    table_clean = builder_table_name.strip().lower().replace(" ", "_")
                    if not table_clean:
                        st.warning("Please provide a valid table name.")
                    else:
                        with st.spinner(f"Creating table `{table_clean}`..."):
                            success_bld, err_bld = _import_df_to_database(edited_df, table_clean, config)
                        if success_bld:
                            st.success(f"🎉 Created table `{table_clean}` with {len(edited_df)} records!")
                            st.info("💡 You can now speak in the **Voice Studio** to query this data!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error creating table: {err_bld}")


def _get_all_tables(config):
    """Retrieve list of user tables from active database."""
    tables = []
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if config["db_type"] == "SQLite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [r[0] for r in cursor.fetchall()]
        else:
            cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{config['mysql_database']}';")
            tables = [r[0] for r in cursor.fetchall()]
    except Exception:
        tables = []
    finally:
        cursor.close()
        conn.close()
    return tables


def _get_table_info(selected_table, config):
    """Fetch columns metadata and total row count for a given table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if config["db_type"] == "SQLite":
            cursor.execute(f"PRAGMA table_info({selected_table});")
            col_data = cursor.fetchall()
            schema_df = pd.DataFrame(col_data, columns=["cid", "Column Name", "Data Type", "Not Null", "Default Value", "Primary Key"])
            schema_df = schema_df[["Column Name", "Data Type", "Primary Key", "Not Null"]]
        else:
            cursor.execute(f"SELECT column_name, data_type, is_nullable, column_key FROM information_schema.columns WHERE table_schema = '{config['mysql_database']}' AND table_name = '{selected_table}';")
            col_data = cursor.fetchall()
            schema_df = pd.DataFrame(col_data, columns=["Column Name", "Data Type", "Nullable", "Key"])
        
        cursor.execute(f"SELECT COUNT(*) FROM {selected_table};")
        total_rows = cursor.fetchone()[0]
    except Exception:
        schema_df = pd.DataFrame()
        total_rows = 0
    finally:
        cursor.close()
        conn.close()
    return schema_df, total_rows


def _drop_table(table_name):
    """Drop a user-created table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def _import_df_to_database(df: pd.DataFrame, table_name: str, config: dict):
    """Safely import DataFrame into SQLite or MySQL without external ORM dependencies."""
    conn = get_db_connection()
    try:
        if config["db_type"] == "SQLite":
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            return True, None
        else:
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            
            # Map pandas dtypes to MySQL types
            col_defs = []
            for col, dtype in zip(df.columns, df.dtypes):
                clean_col = col.strip().replace(" ", "_")
                if pd.api.types.is_integer_dtype(dtype):
                    col_defs.append(f"`{clean_col}` INT")
                elif pd.api.types.is_float_dtype(dtype):
                    col_defs.append(f"`{clean_col}` DOUBLE")
                elif pd.api.types.is_bool_dtype(dtype):
                    col_defs.append(f"`{clean_col}` BOOLEAN")
                else:
                    col_defs.append(f"`{clean_col}` TEXT")
                    
            create_query = f"CREATE TABLE `{table_name}` ({', '.join(col_defs)});"
            cursor.execute(create_query)

            # Insert rows in batches
            col_names = [f"`{col.strip().replace(' ', '_')}`" for col in df.columns]
            placeholders = ", ".join(["%s"] * len(col_names))
            insert_query = f"INSERT INTO `{table_name}` ({', '.join(col_names)}) VALUES ({placeholders})"

            rows = [tuple(None if pd.isna(v) else v for v in row) for row in df.values]
            cursor.executemany(insert_query, rows)
            conn.commit()
            cursor.close()
            return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
