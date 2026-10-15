import os
import streamlit as st
from database.auth import authenticate_user, register_user

def show_landing_page(authenticated: bool = False):
    """Renders the VoiceSQL Studio Landing Page explaining the website, its capabilities, and workspace access."""
    
    # ========================================================
    # TOP HEADER & BRAND BAR
    # ========================================================
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px; padding: 10px 0 20px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); border-radius: 14px; font-size: 24px; box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35); border: 1px solid rgba(255, 255, 255, 0.25);">
                ⚡
            </div>
            <div>
                <div style="font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: -0.03em; line-height: 1.1;">
                    VoiceSQL Studio
                </div>
                <div style="font-size: 13px; color: #64748B; font-weight: 500;">
                    AI Voice-to-SQL Analytics & Predictive Studio
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <div style="background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 20px; padding: 5px 14px; font-size: 12px; font-weight: 700; color: #4338CA;">
                🎙️ Voice Dictation Active
            </div>
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 20px; padding: 5px 14px; font-size: 12px; font-weight: 700; color: #15803D;">
                ⚡ Zero-Code SQL
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
                    Your workspace is ready. You can query with your voice, explore visual charts, and run What-If machine learning predictions.
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
            if st.button("📊 View Analytics Dashboard", use_container_width=True):
                st.session_state["nav_override"] = "Analytics"
                st.rerun()
        with col_act3:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.pop("authenticated", None)
                st.session_state.pop("current_user", None)
                st.rerun()
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # ========================================================
    # HERO SECTION: WHAT THIS WEBSITE IS
    # ========================================================
    st.markdown("""
    <div style="text-align: center; max-width: 880px; margin: 0 auto 30px auto; padding: 10px 10px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 30px; padding: 4px 14px; font-size: 12px; font-weight: 700; color: #4F46E5; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">
            🚀 Welcome to VoiceSQL Studio
        </div>
        <h1 style="font-size: 42px; font-weight: 800; color: #0F172A; margin: 0 0 16px 0; letter-spacing: -0.04em; line-height: 1.15;">
            Talk to Any Database with Your <span style="background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Voice & Everyday Language</span>
        </h1>
        <p style="font-size: 17px; color: #475569; margin: 0 auto 10px auto; line-height: 1.6; max-width: 760px;">
            <b>VoiceSQL Studio</b> is an intelligent, voice-first analytics platform designed to bridge the gap between people and databases. Instead of writing complex SQL queries by hand, simply <b>speak or type in plain English or Tanglish</b>—the AI automatically understands your intent, generates precise SQL, renders interactive charts, and runs predictive machine learning forecasts.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ========================================================
    # 4 CORE CAPABILITIES OF THIS WEBSITE
    # ========================================================
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 18px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 28px; margin-bottom: 10px;">🎙️</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Voice & Speech Input</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Speak naturally using your browser's microphone in <b>English or Tanglish</b>. Real-time speech-to-text with audio waveform feedback.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_f2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 18px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 28px; margin-bottom: 10px;">⚡</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Zero-Code Text-to-SQL</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Dynamic semantic vector embeddings map everyday words (like "earnings" or "box office") directly to database columns and execute safe SQL in milliseconds.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_f3:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 18px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 28px; margin-bottom: 10px;">📊</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Instant Smart Charts</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Query results automatically render the best visualization: <b>Scatter plots with Pearson correlation (r)</b>, grouped <b>Bar charts</b>, <b>Line trends</b>, or <b>Pie breakdowns</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_f4:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 18px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 28px; margin-bottom: 10px;">🔮</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">AutoML & What-If</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Ask forward-looking questions like <i>"What if the budget is 200M for Sci-Fi?"</i> and get instant ML forecasts with Explainable AI (XAI) feature impact reasoning.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)

    # ========================================================
    # MAIN WORKSPACE ACCESS (AUTHENTICATION CARDS)
    # ========================================================
    if not authenticated and not st.session_state.get("authenticated", False):
        col_portal_l, col_portal_c, col_portal_r = st.columns([1, 2.3, 1])
        with col_portal_c:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 14px;">
                <h3 style="font-size: 22px; font-weight: 800; color: #0F172A; margin: 0 0 4px 0;">
                    Get Started with Studio Workspace
                </h3>
                <p style="font-size: 13.5px; color: #64748B; margin: 0;">
                    Sign in with your account or use 1-Click Instant Demo login to explore immediately.
                </p>
            </div>
            """, unsafe_allow_html=True)

            tab_in, tab_up, tab_sec = st.tabs(["🔑 Sign In", "📝 Create Account", "🔒 Account & Data Security"])

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
                st.markdown("<div style='font-size: 12px; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 8px; text-align: center;'>⚡ Fast 1-Click Access</div>", unsafe_allow_html=True)
                col_demo, col_guest = st.columns(2)
                with col_demo:
                    if st.button("⚡ Instant Demo Login", use_container_width=True, help="1-Click login as demo / demo123 with sample datasets"):
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
                            "role": "user",
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
                    st.caption("Create your isolated workspace to upload custom datasets and save query history.")
                    
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
            # TAB 3: STORAGE TRANSPARENCY & DATA PRIVACY
            # ----------------------------------------------------
            with tab_sec:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown("""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px; padding: 16px; font-size: 13px; color: #334155; line-height: 1.6;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
                        <span>🔒</span> How Your Account and Data Are Secured
                    </div>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li><b>Role-Based Access Control (RBAC):</b> System and authentication tables are guarded. Regular users and the AI query engine cannot view, browse, or export account credentials.</li>
                        <li><b>Salted SHA-256 Hashing:</b> Passwords are <b>never saved in plain text</b>. They are hashed with a 16-byte cryptographically secure random salt so no one can reconstruct your original password.</li>
                        <li><b>Data Privacy & Isolation:</b> Any CSV files you upload are tagged to your private account and isolated from other users.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #E2E8F0; margin: 35px 0 25px 0;'>", unsafe_allow_html=True)

    # ========================================================
    # HOW IT WORKS: 3 SIMPLE STEPS
    # ========================================================
    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px;">
        <div style="display: inline-flex; align-items: center; gap: 6px; background: #F1F5F9; border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 8px;">
            Workflow
        </div>
        <h3 style="font-size: 24px; font-weight: 800; color: #0F172A; margin: 0 0 6px 0;">
            How VoiceSQL Studio Works in 3 Simple Steps
        </h3>
        <p style="font-size: 14px; color: #64748B; margin: 0 auto; max-width: 600px;">
            From spoken question to actionable business insight in seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="width: 36px; height: 36px; border-radius: 10px; background: #EFF6FF; color: #2563EB; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 14px;">1</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Ask or Speak Naturally</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Click the microphone button to talk in English or Tanglish, or type what you want to know: e.g. <i>"Show top 5 movies by revenue"</i> or <i>"Sci-Fi movies with budget over 100M"</i>.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="width: 36px; height: 36px; border-radius: 10px; background: #F5F3FF; color: #7C3AED; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 14px;">2</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Semantic SQL Generation</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                The AI maps your natural words to exact database columns, generates verified SQL, and executes it securely against the database in milliseconds.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s3:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="width: 36px; height: 36px; border-radius: 10px; background: #ECFDF5; color: #059669; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 14px;">3</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Instant Charts & Forecasts</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                View the results as clean data tables, interactive Scatter / Bar charts with Pearson correlation coefficients, or run What-If machine learning simulations.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ========================================================
    # SAMPLE QUESTIONS SHOWCASE
    # ========================================================
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h4 style="font-size: 18px; font-weight: 700; color: #0F172A; margin: 0 0 4px 0;">
            💡 Example Questions You Can Ask
        </h4>
        <p style="font-size: 13.5px; color: #64748B; margin: 0;">
            Here are some examples of what you can ask once you sign in to the studio:
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
            <div style="font-size: 13.5px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "Show top 5 movies by box office revenue"
            </div>
            <div style="font-size: 12px; color: #64748B;">
                ⚡ Automatically generates SQL ranking and interactive bar charts.
            </div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;">
            <div style="font-size: 13.5px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "Which director has the highest average movie rating?"
            </div>
            <div style="font-size: 12px; color: #64748B;">
                ⚡ Executes multi-table relational JOINs across directors and movies.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_q2:
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
            <div style="font-size: 13.5px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "Compare budget vs box office for Sci-Fi movies"
            </div>
            <div style="font-size: 12px; color: #64748B;">
                ⚡ Auto-detects relationship question and plots a <b>Scatter Plot</b> with Pearson correlation (<b>r</b>).
            </div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;">
            <div style="font-size: 13.5px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">
                💬 "What if the budget is 200M for an Action movie?"
            </div>
            <div style="font-size: 12px; color: #64748B;">
                ⚡ Runs an AutoML regression forecast with Explainable AI reasoning.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ========================================================
    # WHO IS VOICESQL STUDIO FOR?
    # ========================================================
    st.markdown("<hr style='border-color: #E2E8F0; margin: 35px 0 25px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px;">
        <h3 style="font-size: 22px; font-weight: 800; color: #0F172A; margin: 0 0 6px 0;">
            Who is VoiceSQL Studio Built For?
        </h3>
        <p style="font-size: 14px; color: #64748B; margin: 0 auto; max-width: 600px;">
            Designed for anyone who needs fast data insights without technical friction.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px; height: 100%;">
            <div style="font-size: 24px; margin-bottom: 8px;">💼</div>
            <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Business & Product Teams</div>
            <div style="font-size: 12.5px; color: #64748B; line-height: 1.5;">
                Get immediate answers from corporate databases without waiting for data engineers to write custom SQL scripts.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_u2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px; height: 100%;">
            <div style="font-size: 24px; margin-bottom: 8px;">🎙️</div>
            <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Hands-Free Voice Querying</div>
            <div style="font-size: 12.5px; color: #64748B; line-height: 1.5;">
                Ask questions out loud while in meetings or multitasking. Supports natural voice phrasing in English and Tanglish.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_u3:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px; height: 100%;">
            <div style="font-size: 24px; margin-bottom: 8px;">👩‍💻</div>
            <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Data Analysts & Students</div>
            <div style="font-size: 12.5px; color: #64748B; line-height: 1.5;">
                Inspect auto-generated SQL code, test hypothesis simulations, and evaluate correlation coefficients across custom uploaded CSV datasets.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)

def show_login_page():
    """Alias for backwards compatibility with app.py."""
    show_landing_page(authenticated=False)
