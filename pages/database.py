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
        if st.button("🏥 Seed 550+ Healthcare Data", use_container_width=True, type="primary"):
            from database.seed_healthcare_500 import generate_and_seed_healthcare_500
            with st.spinner("Seeding 550+ Hospital EHR records..."):
                ok, seed_msg = generate_and_seed_healthcare_500()
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
                # Protect core tables from accidental deletion
                is_core = selected_table in ["departments", "employees", "projects", "employee_projects", "query_history"]
                if not is_core:
                    if st.button(f"🗑️ Delete `{selected_table}`", use_container_width=True):
                        _drop_table(selected_table)
                        st.success(f"Table `{selected_table}` deleted.")
                        st.rerun()

        # View columns schema
        with st.expander(f"🔍 View `{selected_table}` Columns & Data Types", expanded=False):
            st.dataframe(schema_df, use_container_width=True, hide_index=True)

    # ========================================================
    # TAB 2: UPLOAD CUSTOM DATASET (CSV)
    # ========================================================
    with tab_upload:
        st.subheader("📤 Add Your Own Dataset")
        st.caption("Upload any CSV file to instantly create a new database table and query it using your voice.")

        uploaded_file = st.file_uploader("Choose a CSV file to import into the database:", type=["csv"])

        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                default_name = os.path.splitext(uploaded_file.name)[0].lower().replace(" ", "_").replace("-", "_")

                st.write(f"📊 **File Preview:** `{uploaded_file.name}` ({len(df_upload)} rows, {len(df_upload.columns)} columns)")
                st.dataframe(df_upload.head(5), use_container_width=True)

                col_name, col_import = st.columns([2, 1])
                with col_name:
                    custom_table_name = st.text_input("Database Table Name:", value=default_name)
                with col_import:
                    st.write("")
                    st.write("")
                    import_clicked = st.button("🚀 Import as New Table", type="primary", use_container_width=True)

                if import_clicked:
                    table_clean = custom_table_name.strip().lower().replace(" ", "_")
                    if not table_clean:
                        st.warning("Please provide a valid table name.")
                    else:
                        with st.spinner(f"Creating table `{table_clean}` and importing {len(df_upload)} records..."):
                            success_imp, err_imp = _import_df_to_database(df_upload, table_clean, config)
                        if success_imp:
                            st.success(f"🎉 Successfully created table `{table_clean}` with {len(df_upload)} records!")
                            st.info("💡 You can now speak in the **Voice Studio** to query this data!")
                            st.rerun()
                        else:
                            st.error(f"❌ Import failed: {err_imp}")

            except Exception as ex:
                st.error(f"❌ Failed to parse CSV: {ex}")


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
