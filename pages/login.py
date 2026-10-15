import os
import streamlit as st
from database.auth import authenticate_user, register_user

def show_landing_page(authenticated: bool = False):
    """Renders a clean, elegant landing page with clear product description, user registration, and sign in."""

    # ========================================================
    # TOP HEADER & BRAND BAR
    # ========================================================
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px; padding: 10px 0 20px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 46px; height: 46px; background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); border-radius: 12px; font-size: 22px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35); border: 1px solid rgba(255, 255, 255, 0.2);">
                ⚡
            </div>
            <div>
                <div style="font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: -0.03em; line-height: 1.1;">
                    VoiceSQL Studio
                </div>
                <div style="font-size: 13px; color: #64748B; font-weight: 500;">
                    AI Voice-to-SQL Analytics & Data Intelligence Platform
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <div style="background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 20px; padding: 5px 14px; font-size: 12px; font-weight: 700; color: #4338CA;">
                🎙️ Browser Voice Input Active
            </div>
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 20px; padding: 5px 14px; font-size: 12px; font-weight: 700; color: #15803D;">
                📁 Dynamic Dataset Uploads
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ========================================================
    # HERO SECTION: ABOUT VOICESQL STUDIO
    # ========================================================
    st.markdown("""
    <div style="text-align: center; max-width: 840px; margin: 0 auto 24px auto; padding: 10px 10px 0 10px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 30px; padding: 5px 16px; font-size: 12px; font-weight: 700; color: #4F46E5; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.05em;">
            🚀 Intelligent Database Querying with Your Voice
        </div>
        <h1 style="font-size: 40px; font-weight: 800; color: #0F172A; margin: 0 0 14px 0; letter-spacing: -0.04em; line-height: 1.2;">
            Talk to Any Database with Your <span style="background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Voice & Everyday Language</span>
        </h1>
        <p style="font-size: 16.5px; color: #475569; margin: 0 auto 20px auto; line-height: 1.6; max-width: 740px;">
            <b>VoiceSQL Studio</b> allows you to upload any CSV or Excel spreadsheet and query your data naturally using your voice or plain English. The AI automatically maps your words to database columns, generates precise SQL, executes it safely, and displays instant interactive charts without writing code.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ========================================================
    # 3 CORE HIGHLIGHTS
    # ========================================================
    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 26px; margin-bottom: 10px;">📤</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Upload Custom Datasets</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Upload your own CSV or Excel spreadsheets into your isolated workspace. Tables are created and indexed dynamically.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_h2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 26px; margin-bottom: 10px;">🎙️</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Voice & Speech Input</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Click the microphone to ask questions in English or Tanglish. Real-time audio waveform feedback with spoken audio synthesis.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_h3:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; height: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 26px; margin-bottom: 10px;">📊</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Zero-Code SQL & Charts</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Instant SQL execution with automatic bar charts, scatter plots with Pearson correlation, and predictive What-If simulations.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # ========================================================
    # AUTHENTICATION PORTAL (SIGN IN & REGISTER)
    # ========================================================
    col_p_l, col_p_c, col_p_r = st.columns([1, 2.4, 1])
    with col_p_c:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 14px;">
            <h3 style="font-size: 22px; font-weight: 800; color: #0F172A; margin: 0 0 4px 0;">
                Access Studio Workspace
            </h3>
            <p style="font-size: 13.5px; color: #64748B; margin: 0;">
                Sign in to your account or register a new workspace to start querying your data.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tab_signin, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # ----------------------------------------------------
        # TAB 1: SIGN IN
        # ----------------------------------------------------
        with tab_signin:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            with st.form("signin_form_clean", clear_on_submit=False):
                login_ident = st.text_input(
                    "Username or Email",
                    placeholder="Enter your username or email address",
                    key="clean_login_user"
                )
                login_pwd = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your account password",
                    key="clean_login_pwd"
                )

                submit_login = st.form_submit_button(
                    "🚀 Sign In to Workspace",
                    type="primary",
                    use_container_width=True
                )

                if submit_login:
                    if not login_ident.strip() or not login_pwd:
                        st.warning("⚠️ Please provide both your username/email and password.")
                    else:
                        with st.spinner("Authenticating credentials..."):
                            ok, res = authenticate_user(login_ident, login_pwd)
                        if ok:
                            st.session_state["authenticated"] = True
                            st.session_state["current_user"] = res
                            st.success(f"🎉 Welcome back, {res.get('full_name', res.get('username'))}!")
                            st.rerun()
                        else:
                            st.error(f"❌ {res}")

            st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin-top: 14px; font-size: 12px; color: #64748B; line-height: 1.4;">
                🛡️ <b>Administrator Login:</b> System Administrator can sign in using <code>admin</code> / <code>admin123</code> to access live user action & audit logs.
            </div>
            """, unsafe_allow_html=True)

        # ----------------------------------------------------
        # TAB 2: REGISTER NEW ACCOUNT
        # ----------------------------------------------------
        with tab_register:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            with st.form("signup_form_clean", clear_on_submit=False):
                st.caption("Create your isolated workspace to upload custom datasets and query with your voice.")
                
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
                    "✨ Create Account & Open Workspace",
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
                        with st.spinner("Creating account & setting up workspace..."):
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
            From uploaded spreadsheet to voice-driven business insight in seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="width: 36px; height: 36px; border-radius: 10px; background: #EFF6FF; color: #2563EB; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 14px;">1</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Upload Your Dataset</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                In the <b>Database Manager</b>, upload your CSV or Excel file. VoiceSQL Studio dynamically creates tables and indexes column data types.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="width: 36px; height: 36px; border-radius: 10px; background: #F5F3FF; color: #7C3AED; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 14px;">2</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Speak or Type Questions</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                Click the microphone button to talk in English or Tanglish, or type what you want to know. The AI maps your words directly to your columns.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s3:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="width: 36px; height: 36px; border-radius: 10px; background: #ECFDF5; color: #059669; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 14px;">3</div>
            <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Instant Charts & Forecasts</div>
            <div style="font-size: 13px; color: #64748B; line-height: 1.5;">
                View the results as clean data tables, interactive Scatter / Bar charts with correlation analysis, or run What-If machine learning simulations.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)

def show_login_page():
    """Alias for backwards compatibility with app.py."""
    show_landing_page(authenticated=False)
