import streamlit as st
import bcrypt
from database import Database, User # Only User needed for auth in main_app
from datetime import datetime # Needed for some default values in date_input in pages

# Initialize database (only once)
db = Database('sqlite:///inventory.db')
db.create_tables()

# Store db instance in session state for access in pages
if 'db' not in st.session_state:
    st.session_state['db'] = db

# Initialize session state for authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# --- Global CSS for table alignment ---
st.markdown(
    """
    <style>
    /* Target data cells (td) and header cells (th) specifically within st.dataframe's AgGrid structure */
    /* Streamlit uses AgGrid, so we target its internal classes for better specificity. */
    .st-ag-grid table, .ag-root-wrapper, .ag-grid-wrapper {
        width: 100% !important; /* Ensure the table itself can use full width */
    }
    .ag-header-cell-label, .ag-cell-value {
        text-align: center !important; /* Force text to center */
    }
    /* Fallback for general table alignment if AgGrid classes are missed by some components */
    [data-testid="stDataFrame"] th, 
    [data-testid="stDataFrame"] td {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Authentication Functions ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def login_page():
    st.title("Inventory Management System - Login/Signup")

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            session = db.get_session()
            user = session.query(User).filter_by(username=username).first()
            session.close()

            if user and check_password(password, user.password):
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.success("Logged in successfully!")
                # Streamlit automatically redirects to default page after login
                st.rerun() 
            else:
                st.error("Invalid username or password")

    with signup_tab:
        st.subheader("Create a new account")
        new_username = st.text_input("New Username", key="signup_username")
        new_password = st.text_input("New Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

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
                    st.success("Account created successfully! You can now log in.")
                    session.close()
                    # No need to change current_page, just show success and rerun
                    st.rerun()

# Main app flow
if not st.session_state.logged_in:
    login_page()
else:
    # This block runs after successful login.
    # Streamlit will automatically show pages from the 'pages' directory.
    st.sidebar.write(f"Logged in as: **{st.session_state.current_user}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        # Clear any page-specific session state if necessary upon logout
        if 'current_order_items' in st.session_state:
            del st.session_state.current_order_items
        st.rerun()