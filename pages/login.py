import streamlit as st
from database.auth import authenticate_user, register_user

def show_login_page():
    """Renders the VoiceSQL Studio Login & Registration Portal."""
    
    # Outer layout container
    col_l, col_center, col_r = st.columns([1, 2.2, 1])

    with col_center:
        # Brand Header Card
        st.markdown("""
        <div style="text-align: center; padding: 25px 0 15px 0;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); border-radius: 18px; font-size: 32px; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.4); margin-bottom: 12px; border: 1px solid rgba(255, 255, 255, 0.2);">
                ⚡
            </div>
            <h1 style="font-size: 32px; font-weight: 800; color: #0F172A; margin: 0 0 6px 0; letter-spacing: -0.03em;">
                VoiceSQL Studio
            </h1>
            <p style="font-size: 15px; color: #64748B; margin: 0 0 20px 0;">
                AI-Powered Voice-to-Database Multi-User Workspace
            </p>
        </div>
        """, unsafe_allow_html=True)

        tab_signin, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # ========================================================
        # TAB 1: SIGN IN
        # ========================================================
        with tab_signin:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.form("signin_form", clear_on_submit=False):
                st.subheader("Welcome Back")
                st.caption("Sign in to query your custom datasets and explore relational databases.")

                login_ident = st.text_input(
                    "Username or Email",
                    placeholder="e.g. demo or demo@voicesql.com",
                    key="login_username_input"
                )
                login_pwd = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password_input"
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
                        with st.spinner("Authenticating account..."):
                            ok, res = authenticate_user(login_ident, login_pwd)
                        if ok:
                            st.session_state["authenticated"] = True
                            st.session_state["current_user"] = res
                            st.success(f"🎉 Welcome back, {res.get('full_name', res.get('username'))}!")
                            st.rerun()
                        else:
                            st.error(f"❌ {res}")

            st.markdown("<hr style='border-color: #E2E8F0; margin: 20px 0;'>", unsafe_allow_html=True)
            
            # Quick 1-Click Access for Evaluators / Reviewers
            st.markdown("##### ⚡ Quick Access Options")
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                if st.button("⚡ Instant Demo Login", use_container_width=True, help="Logs in with demo / demo123 automatically"):
                    with st.spinner("Logging into demo account..."):
                        ok, res = authenticate_user("demo", "demo123")
                    if ok:
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = res
                        st.success("✅ Signed in as Demo Explorer!")
                        st.rerun()
                    else:
                        st.error(f"❌ {res}")

            with col_d2:
                if st.button("👤 Continue as Guest", use_container_width=True, help="Explore without an account"):
                    guest_user = {
                        "user_id": 0,
                        "username": "guest",
                        "email": "guest@voicesql.com",
                        "full_name": "Guest Visitor",
                        "created_at": "Active Session"
                    }
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = guest_user
                    st.success("✅ Exploring as Guest!")
                    st.rerun()

        # ========================================================
        # TAB 2: SIGN UP
        # ========================================================
        with tab_signup:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.form("signup_form", clear_on_submit=False):
                st.subheader("Create a New Account")
                st.caption("Each user gets an isolated workspace to upload datasets and run voice queries.")

                reg_fullname = st.text_input("Full Name", placeholder="e.g. Harini Dharmaraj")
                reg_username = st.text_input("Username", placeholder="e.g. harini")
                reg_email = st.text_input("Email Address", placeholder="e.g. harini@example.com")
                reg_password = st.text_input("Password", type="password", placeholder="At least 6 characters")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")

                submit_signup = st.form_submit_button(
                    "✨ Register & Create Workspace",
                    type="primary",
                    use_container_width=True
                )

                if submit_signup:
                    if not reg_username.strip() or not reg_email.strip() or not reg_password:
                        st.warning("⚠️ Please fill in all required fields.")
                    elif reg_password != reg_confirm:
                        st.error("❌ Passwords do not match. Please re-enter.")
                    else:
                        with st.spinner("Creating your workspace..."):
                            ok, msg = register_user(reg_username, reg_email, reg_password, reg_fullname)
                        if ok:
                            st.success(f"🎉 {msg}")
                            # Automatically log them in!
                            auth_ok, user_data = authenticate_user(reg_username, reg_password)
                            if auth_ok:
                                st.session_state["authenticated"] = True
                                st.session_state["current_user"] = user_data
                                st.rerun()
                        else:
                            st.error(f"❌ {msg}")
