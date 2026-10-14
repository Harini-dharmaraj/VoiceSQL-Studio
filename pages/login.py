import os
import streamlit as st
from database.auth import authenticate_user, register_user
from database.db_connection import get_db_connection
from utils.config_manager import load_config

def get_live_system_metrics():
    """Extract real-time, non-mock system telemetry directly from the active database."""
    config = load_config()
    db_type = config.get("db_type", "SQLite")
    
    if db_type == "SQLite":
        target_name = "database/demo.db"
    else:
        target_name = f"{config.get('mysql_host', 'localhost')}:{config.get('mysql_port', 3306)}/{config.get('mysql_database', 'voicesql')}"

    ai_provider = config.get("ai_provider", "Offline Rules")
    gemini_key = config.get("gemini_api_key", "").strip()
    openai_key = config.get("openai_api_key", "").strip()

    if ai_provider in ["Google Gemini", "Gemini"]:
        ai_engine = "Google Gemini" if gemini_key else "Offline Rules Engine"
        ai_model = "gemini-2.5-flash" if gemini_key else "Local Vector + Regex Parser"
    elif ai_provider in ["OpenAI", "ChatGPT"]:
        ai_engine = "OpenAI GPT" if openai_key else "Offline Rules Engine"
        ai_model = "gpt-4o-mini" if openai_key else "Local Vector + Regex Parser"
    else:
        ai_engine = "Offline Rules Engine"
        ai_model = "Local Vector + Regex Parser"

    metrics = {
        "db_type": db_type,
        "db_target": target_name,
        "db_connected": False,
        "tables": [],
        "total_records": 0,
        "queries_count": 0,
        "queries_success": 0,
        "users_count": 0,
        "ai_engine": ai_engine,
        "ai_model": ai_model,
        "error": None
    }

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        metrics["db_connected"] = True

        if db_type == "SQLite":
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            raw_tables = [r[0] for r in cur.fetchall()]
        else:
            cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{config.get('mysql_database', '')}';")
            raw_tables = [r[0] for r in cur.fetchall()]

        data_rows = 0
        table_list = []
        for t in raw_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                cnt = cur.fetchone()[0]
                if db_type == "SQLite":
                    cur.execute(f"PRAGMA table_info({t});")
                    col_names = [col[1] for col in cur.fetchall()]
                    cols = len(col_names)
                else:
                    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='{config.get('mysql_database', '')}' AND table_name='{t}';")
                    col_names = [col[0] for col in cur.fetchall()]
                    cols = len(col_names)

                table_list.append({
                    "name": t,
                    "rows": cnt,
                    "cols": cols,
                    "col_names": col_names[:6]  # first 6 sample columns
                })
                if t not in ["sqlite_sequence", "query_history"]:
                    data_rows += cnt
            except Exception:
                pass

        metrics["tables"] = table_list
        metrics["total_records"] = data_rows

        try:
            cur.execute("SELECT COUNT(*) FROM query_history;")
            metrics["queries_count"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM query_history WHERE UPPER(status) = 'SUCCESS';")
            metrics["queries_success"] = cur.fetchone()[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM users;")
            metrics["users_count"] = cur.fetchone()[0]
        except Exception:
            pass

        cur.close()
        conn.close()
    except Exception as e:
        metrics["error"] = str(e)

    return metrics

def show_landing_page(authenticated: bool = False):
    """Renders the VoiceSQL Studio Landing Page with 100% Real Database Telemetry & Portal."""
    metrics = get_live_system_metrics()

    # ========================================================
    # TOP HEADER & BRAND BAR
    # ========================================================
    db_badge_color = "#10B981" if metrics["db_connected"] else "#EF4444"
    db_status_text = "Connected" if metrics["db_connected"] else "Offline"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px; padding: 10px 0 24px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); border-radius: 14px; font-size: 24px; box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35); border: 1px solid rgba(255, 255, 255, 0.25);">
                ⚡
            </div>
            <div>
                <div style="font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: -0.03em; line-height: 1.1;">
                    VoiceSQL Studio
                </div>
                <div style="font-size: 13px; color: #64748B; font-weight: 500;">
                    Next-Gen AI Voice-to-SQL Analytics & Predictive Workspace
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 20px; padding: 5px 12px; font-size: 12px; font-weight: 600; color: #334155; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <span style="width: 8px; height: 8px; border-radius: 50%; background: {db_badge_color}; display: inline-block;"></span>
                {metrics['db_type']}: {db_status_text}
            </div>
            <div style="background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 20px; padding: 5px 12px; font-size: 12px; font-weight: 600; color: #475569;">
                🧠 {metrics['ai_engine']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # If user is already authenticated and visits this landing page:
    if authenticated or st.session_state.get("authenticated", False):
        user = st.session_state.get("current_user", {})
        u_name = user.get("username", "Guest")
        f_name = user.get("full_name", u_name)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 1.5px solid #93C5FD; border-radius: 16px; padding: 18px 24px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
            <div>
                <div style="font-size: 17px; font-weight: 700; color: #1E3A8A; margin-bottom: 2px;">
                    👋 Welcome back, {f_name} (@{u_name})!
                </div>
                <div style="font-size: 13px; color: #3B82F6;">
                    Your workspace is active. You have full access to voice dictation, SQL execution, and AutoML forecasting.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        col_act1, col_act2, col_act3 = st.columns([1.2, 1, 1])
        with col_act1:
            if st.button("🎙️ Open Voice Studio", type="primary", use_container_width=True):
                st.session_state["nav_override"] = "Voice Assistant"
                st.rerun()
        with col_act2:
            if st.button("🗄️ Explore Database Manager", use_container_width=True):
                st.session_state["nav_override"] = "Database"
                st.rerun()
        with col_act3:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.pop("authenticated", None)
                st.session_state.pop("current_user", None)
                st.rerun()
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # ========================================================
    # HERO SECTION
    # ========================================================
    st.markdown("""
    <div style="text-align: center; max-width: 860px; margin: 0 auto 30px auto; padding: 10px 10px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 30px; padding: 4px 14px; font-size: 12px; font-weight: 700; color: #4F46E5; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">
            ✨ Production-Grade Voice Data Intelligence
        </div>
        <h1 style="font-size: 42px; font-weight: 800; color: #0F172A; margin: 0 0 14px 0; letter-spacing: -0.04em; line-height: 1.15;">
            Talk to Your Database with <span style="background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Voice & SQL</span>
        </h1>
        <p style="font-size: 17px; color: #475569; margin: 0 auto 20px auto; line-height: 1.6; max-width: 720px;">
            Convert spoken voice commands and natural language into instant SQL queries, dynamic schema vector embeddings, real-time charts, and explainable ML predictions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ========================================================
    # LIVE TELEMETRY METRIC CARDS (100% REAL DATA, NO MOCK DATA)
    # ========================================================
    st.markdown("<div style='margin-bottom: 8px; font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; text-align: center;'>Live Database & Engine Telemetry • No Mock Data</div>", unsafe_allow_html=True)
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    success_rate = f"{(metrics['queries_success'] / metrics['queries_count'] * 100):.0f}%" if metrics['queries_count'] > 0 else "100%"
    
    with col_m1:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 100%;">
            <div style="font-size: 12px; font-weight: 600; color: #64748B; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                <span>🗄️</span> Active Database
            </div>
            <div style="font-size: 20px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">
                {metrics['db_type']}
            </div>
            <div style="font-size: 11px; color: #10B981; font-weight: 600; word-break: break-all;">
                🟢 {metrics['db_target']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 100%;">
            <div style="font-size: 12px; font-weight: 600; color: #64748B; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                <span>📊</span> Connected Schema
            </div>
            <div style="font-size: 20px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">
                {len(metrics['tables'])} Tables
            </div>
            <div style="font-size: 11px; color: #6366F1; font-weight: 600;">
                {metrics['total_records']:,} Total Live Records
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_m3:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 100%;">
            <div style="font-size: 12px; font-weight: 600; color: #64748B; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                <span>⚡</span> Live Queries Executed
            </div>
            <div style="font-size: 20px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">
                {metrics['queries_count']} Recorded
            </div>
            <div style="font-size: 11px; color: #059669; font-weight: 600;">
                {success_rate} Success Rate ({metrics['queries_success']} OK)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_m4:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 100%;">
            <div style="font-size: 12px; font-weight: 600; color: #64748B; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                <span>🧠</span> Active AI Provider
            </div>
            <div style="font-size: 20px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">
                {metrics['ai_engine']}
            </div>
            <div style="font-size: 11px; color: #8B5CF6; font-weight: 600;">
                {metrics['ai_model']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # ========================================================
    # MAIN WORKSPACE ACCESS & PORTAL (AUTHENTICATION CARDS)
    # ========================================================
    if not authenticated and not st.session_state.get("authenticated", False):
        col_portal_l, col_portal_c, col_portal_r = st.columns([1, 2.4, 1])
        with col_portal_c:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 12px;">
                <h3 style="font-size: 22px; font-weight: 800; color: #0F172A; margin: 0 0 4px 0;">
                    Access Studio Workspace
                </h3>
                <p style="font-size: 13.5px; color: #64748B; margin: 0;">
                    Sign in to your isolated dataset environment or register a new workspace.
                </p>
            </div>
            """, unsafe_allow_html=True)

            tab_in, tab_up, tab_sec = st.tabs(["🔑 Sign In", "📝 Create Account", "🔒 Data & Storage Security"])

            # ----------------------------------------------------
            # TAB 1: SIGN IN
            # ----------------------------------------------------
            with tab_in:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                with st.form("signin_form_main", clear_on_submit=False):
                    login_ident = st.text_input(
                        "Username or Email",
                        placeholder="e.g. demo or demo@voicesql.com",
                        key="login_user_input_field"
                    )
                    login_pwd = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your account password",
                        key="login_pwd_input_field"
                    )

                    col_btn1, col_btn2 = st.columns([1.5, 1])
                    with col_btn1:
                        submit_login = st.form_submit_button(
                            "🚀 Sign In to Studio",
                            type="primary",
                            use_container_width=True
                        )

                    if submit_login:
                        if not login_ident.strip() or not login_pwd:
                            st.warning("⚠️ Please provide both your username/email and password.")
                        else:
                            with st.spinner("Verifying credentials..."):
                                ok, res = authenticate_user(login_ident, login_pwd)
                            if ok:
                                st.session_state["authenticated"] = True
                                st.session_state["current_user"] = res
                                st.success(f"🎉 Welcome back, {res.get('full_name', res.get('username'))}!")
                                st.rerun()
                            else:
                                st.error(f"❌ {res}")

                st.markdown("<hr style='border-color: #E2E8F0; margin: 16px 0;'>", unsafe_allow_html=True)
                
                # 1-Click Fast Pass Options
                st.markdown("<div style='font-size: 12px; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 8px;'>⚡ 1-Click Instant Evaluation</div>", unsafe_allow_html=True)
                col_demo, col_guest = st.columns(2)
                with col_demo:
                    if st.button("⚡ Instant Demo Login", use_container_width=True, help="1-Click login as demo / demo123 with preloaded datasets"):
                        with st.spinner("Accessing demo workspace..."):
                            ok, res = authenticate_user("demo", "demo123")
                        if ok:
                            st.session_state["authenticated"] = True
                            st.session_state["current_user"] = res
                            st.success("✅ Logged in as Demo Explorer!")
                            st.rerun()
                        else:
                            st.error(f"❌ {res}")

                with col_guest:
                    if st.button("👤 Continue as Guest", use_container_width=True, help="Explore workspace without saving persistent state"):
                        guest_user = {
                            "user_id": 0,
                            "username": "guest",
                            "email": "guest@voicesql.com",
                            "full_name": "Guest Visitor",
                            "created_at": "Active Session"
                        }
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = guest_user
                        st.success("✅ Continuing as Guest!")
                        st.rerun()

            # ----------------------------------------------------
            # TAB 2: REGISTER NEW ACCOUNT
            # ----------------------------------------------------
            with tab_up:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                with st.form("signup_form_main", clear_on_submit=False):
                    st.caption("Each account gets an isolated workspace to upload custom CSV datasets and run voice queries.")
                    
                    reg_fullname = st.text_input("Full Name", placeholder="e.g. Harini Dharmaraj")
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        reg_username = st.text_input("Username", placeholder="e.g. harini")
                    with col_u2:
                        reg_email = st.text_input("Email Address", placeholder="e.g. harini@example.com")
                    
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        reg_password = st.text_input("Password", type="password", placeholder="Min 6 characters")
                    with col_p2:
                        reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-type password")

                    submit_signup = st.form_submit_button(
                        "✨ Register & Open Workspace",
                        type="primary",
                        use_container_width=True
                    )

                    if submit_signup:
                        u_clean = reg_username.strip().lower()
                        e_clean = reg_email.strip().lower()

                        if not u_clean or len(u_clean) < 3:
                            st.warning("⚠️ Username must be at least 3 characters long.")
                        elif not e_clean or "@" not in e_clean or "." not in e_clean:
                            st.warning("⚠️ Please provide a valid email address (e.g. name@domain.com).")
                        elif not reg_password or len(reg_password) < 6:
                            st.warning("⚠️ Password must be at least 6 characters long.")
                        elif reg_password != reg_confirm:
                            st.error("❌ Passwords do not match. Please verify both password fields.")
                        else:
                            with st.spinner("Registering user & provisioning workspace..."):
                                ok, msg = register_user(u_clean, e_clean, reg_password, reg_fullname)
                            if ok:
                                st.success(f"🎉 {msg}")
                                # Automatic login
                                auth_ok, user_data = authenticate_user(u_clean, reg_password)
                                if auth_ok:
                                    st.session_state["authenticated"] = True
                                    st.session_state["current_user"] = user_data
                                    st.rerun()
                            else:
                                st.error(f"❌ {msg}")

            # ----------------------------------------------------
            # TAB 3: STORAGE TRANSPARENCY (SECURITY & USER DETAILS)
            # ----------------------------------------------------
            with tab_sec:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px; padding: 16px; font-size: 13px; color: #334155; line-height: 1.6;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
                        <span>🔒</span> Where are your user details stored?
                    </div>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li><b>Database File:</b> <code>{metrics['db_target']}</code> ({metrics['db_type']})</li>
                        <li><b>User Table:</b> <code>users</code> (Stores <code>user_id</code>, <code>username</code>, <code>email</code>, <code>full_name</code>, <code>created_at</code>)</li>
                        <li><b>Password Security:</b> Passwords are <b>NEVER</b> stored in plain text. They are hashed using <b>SHA-256 with a 16-byte cryptographically secure random salt</b> (<code>secrets.token_hex(16)</code>) stored as <code>salt:sha256_hash</code>.</li>
                        <li><b>Dataset Isolation:</b> Uploaded CSVs are tracked in <code>user_datasets</code> and mapped strictly to your <code>user_id</code>.</li>
                        <li><b>Current Registered Users:</b> <code>{metrics['users_count']}</code> active accounts in local database.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #E2E8F0; margin: 35px 0 25px 0;'>", unsafe_allow_html=True)

    # ========================================================
    # LIVE DATABASE SCHEMA EXPLORER (100% REAL DATA)
    # ========================================================
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h3 style="font-size: 22px; font-weight: 800; color: #0F172A; margin: 0 0 6px 0;">
            🗄️ Live Connected Database Schema
        </h3>
        <p style="font-size: 14px; color: #64748B; margin: 0;">
            Below are the actual tables and record counts actively running in your database right now. No hardcoded or mock data.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if metrics["tables"]:
        # Group tables into 3 columns
        cols = st.columns(3)
        for idx, t in enumerate(metrics["tables"]):
            c = cols[idx % 3]
            sample_cols = ", ".join(t["col_names"]) if t["col_names"] else "None"
            with c:
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-size: 14px; font-weight: 700; color: #1E293B;">📋 {t['name']}</span>
                        <span style="background: #EEF2FF; color: #4338CA; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px;">{t['rows']:,} rows</span>
                    </div>
                    <div style="font-size: 11.5px; color: #64748B; margin-bottom: 6px;">
                        <b>{t['cols']} Columns:</b> <span style="color: #475569;">{sample_cols}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ No user tables detected yet. Initializing default sample dataset...")

    # ========================================================
    # VERIFIED SAMPLE VOICE PROMPTS
    # ========================================================
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h4 style="font-size: 18px; font-weight: 700; color: #0F172A; margin: 0 0 4px 0;">
            🎙️ Try These Natural Voice Questions
        </h4>
        <p style="font-size: 13.5px; color: #64748B; margin: 0;">
            Speak or type any of these real questions once signed in to experience instant SQL conversion and chart rendering:
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
            <div style="font-size: 13px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "Show top 5 movies by box office revenue"
            </div>
            <div style="font-size: 11.5px; color: #64748B;">
                ⚡ Auto-generates: <code>SELECT title, box_office_millions FROM movies ORDER BY box_office_millions DESC LIMIT 5;</code>
            </div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;">
            <div style="font-size: 13px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "Which director has the highest average movie rating?"
            </div>
            <div style="font-size: 11.5px; color: #64748B;">
                ⚡ Auto-generates: <code>SELECT d.name, AVG(m.rating) FROM directors d JOIN movies m ... GROUP BY d.name;</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_q2:
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
            <div style="font-size: 13px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "Compare budget vs box office for Sci-Fi movies"
            </div>
            <div style="font-size: 11.5px; color: #64748B;">
                ⚡ Auto-renders: <b>Scatter Plot Relationship Chart</b> with Pearson Correlation (<b>r</b>).
            </div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;">
            <div style="font-size: 13px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "Predict box office if budget is 200M for Action movie"
            </div>
            <div style="font-size: 11.5px; color: #64748B;">
                ⚡ Auto-executes: <b>AutoML Regression Forecast</b> with Explainable AI (XAI) feature breakdown.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ========================================================
    # CORE SYSTEM ARCHITECTURE
    # ========================================================
    st.markdown("<hr style='border-color: #E2E8F0; margin: 35px 0 25px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px;">
        <h3 style="font-size: 22px; font-weight: 800; color: #0F172A; margin: 0 0 6px 0;">
            ⚡ End-to-End VoiceSQL Intelligence Architecture
        </h3>
        <p style="font-size: 14px; color: #64748B; margin: 0 auto; max-width: 650px;">
            Engineered for high-precision, low-latency, and zero-hallucination database interactions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="font-size: 26px; margin-bottom: 10px;">🎙️</div>
            <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">1. Voice Dictation</div>
            <div style="font-size: 12.5px; color: #64748B; line-height: 1.5;">
                Native browser Web Speech API captures real-time speech in English, Tamil, and Tanglish with live waveform feedback.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_a2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="font-size: 26px; margin-bottom: 10px;">🔍</div>
            <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">2. Schema Grounding</div>
            <div style="font-size: 12.5px; color: #64748B; line-height: 1.5;">
                Vector cosine similarity matches colloquial phrases ("earnings", "cost") to technical schema columns (<code>box_office_millions</code>).
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_a3:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="font-size: 26px; margin-bottom: 10px;">📊</div>
            <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">3. Smart Charts</div>
            <div style="font-size: 12.5px; color: #64748B; line-height: 1.5;">
                Auto-selects optimal visualization (Scatter correlation, grouped Bar, Line, or Pie) depending on SQL query result dimensions.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_a4:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="font-size: 26px; margin-bottom: 10px;">🤖</div>
            <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">4. AutoML & What-If</div>
            <div style="font-size: 12.5px; color: #64748B; line-height: 1.5;">
                Trains on-the-fly regression models to answer "What-If" queries and predict future metrics with Explainable AI reasoning.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)

def show_login_page():
    """Alias for backwards compatibility with app.py."""
    show_landing_page(authenticated=False)
