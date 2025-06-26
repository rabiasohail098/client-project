# utils/session.py
import streamlit as st
from database import Database

def initialize_session():
    if 'db' not in st.session_state:
        st.session_state['db'] = Database('sqlite:///inventory.db')
        st.session_state['db'].create_tables()
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
