import streamlit as st
import bcrypt
from database import Database, User

# --- Initialize database only once ---
if 'db' not in st.session_state:
    st.session_state['db'] = Database('sqlite:///inventory.db')
    st.session_state['db'].create_tables()

db = st.session_state['db']

# --- Persistent Authentication State ---
st.session_state.logged_in = st.session_state.get('logged_in', False)
st.session_state.current_user = st.session_state.get('current_user', None)

# --- Global CSS ---
st.markdown(
    """
    <style>
    .st-ag-grid table, .ag-root-wrapper, .ag-grid-wrapper {
        width: 100% !important;
    }
    .ag-header-cell-label, .ag-cell-value {
        text-align: center !important;
    }
    [data-testid="stDataFrame"] th, 
    [data-testid="stDataFrame"] td {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Utility Functions ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- Login/Signup Page ---
def login_page():
    st.title("Inventory Management System - Login/Signup")
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        st.subheader("Login to your account")

        # Preserve form inputs
        st.session_state.login_username_value = st.session_state.get('login_username_value', "")
        st.session_state.login_password_value = st.session_state.get('login_password_value', "")

        username = st.text_input("Username", value=st.session_state.login_username_value, key="login_username",
                                 on_change=lambda: st.session_state.__setitem__('login_username_value', st.session_state.login_username))
        password = st.text_input("Password", type="password", value=st.session_state.login_password_value, key="login_password",
                                 on_change=lambda: st.session_state.__setitem__('login_password_value', st.session_state.login_password))

        if st.button("Login", key="login_button"):
            session = db.get_session()
            user = session.query(User).filter_by(username=username).first()
            session.close()

            if user and check_password(password, user.password):
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.success("Logged in successfully!")
                # Clear form fields
                st.session_state.login_username_value = ""
                st.session_state.login_password_value = ""
                st.rerun()
            else:
                st.error("Invalid username or password")

    with signup_tab:
        st.subheader("Create a new account")

        st.session_state.signup_username_value = st.session_state.get('signup_username_value', "")
        st.session_state.new_password_value = st.session_state.get('new_password_value', "")
        st.session_state.confirm_password_value = st.session_state.get('confirm_password_value', "")

        new_username = st.text_input("New Username", value=st.session_state.signup_username_value, key="signup_username",
                                     on_change=lambda: st.session_state.__setitem__('signup_username_value', st.session_state.signup_username))
        new_password = st.text_input("New Password", type="password", value=st.session_state.new_password_value, key="new_password",
                                     on_change=lambda: st.session_state.__setitem__('new_password_value', st.session_state.new_password))
        confirm_password = st.text_input("Confirm Password", type="password", value=st.session_state.confirm_password_value, key="confirm_password",
                                         on_change=lambda: st.session_state.__setitem__('confirm_password_value', st.session_state.confirm_password))

        if st.button("Sign Up", key="signup_button"):
            if not new_username or not new_password or not confirm_password:
                st.error("All fields are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match!")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                session = db.get_session()
                existing_user = session.query(User).filter_by(username=new_username).first()
                if existing_user:
                    st.error("Username already exists. Please choose a different one.")
                    session.close()
                else:
                    hashed_pw = hash_password(new_password)
                    new_user = User(username=new_username, password=hashed_pw)
                    session.add(new_user)
                    session.commit()
                    session.close()
                    st.success("Account created successfully! You can now log in.")
                    # Clear fields
                    st.session_state.signup_username_value = ""
                    st.session_state.new_password_value = ""
                    st.session_state.confirm_password_value = ""
                    st.rerun()

# --- Main App Flow ---
if not st.session_state.logged_in:
    login_page()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.current_user}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        # Optional: clear other session keys
        keys_to_clear = [key for key in st.session_state.keys() if key.startswith(('add_item_', 'edit_item_', 'select_product_', 'add_cust_', 'edit_cust_', 'select_customer_'))]
        for key in keys_to_clear:
            del st.session_state[key]
        st.rerun()
