# pages/3_Customers.py

import streamlit as st
import pandas as pd
from database import Customer
from utils.session import initialize_session
initialize_session()

db = st.session_state['db']



def manage_customers():
    st.title("Customer Management")
    session = db.get_session()

    # --- Initialize session state for customer management persistence ---
    if 'add_cust_name_value' not in st.session_state:
        st.session_state.add_cust_name_value = ""
    if 'add_cust_phone_value' not in st.session_state:
        st.session_state.add_cust_phone_value = ""
    if 'add_cust_address_value' not in st.session_state:
        st.session_state.add_cust_address_value = ""

    # For Update/Delete tab's selectbox
    if 'selected_customer_key_value' not in st.session_state:
        st.session_state.selected_customer_key_value = None
    # --- End session state initialization ---

    try:
        tab1, tab2, tab3 = st.tabs(["View Customers", "Add Customer", "Update/Delete Customer"])
        
        with tab1:
            st.subheader("All Customers")
            customers = session.query(Customer).order_by(Customer.id.asc()).all()
            
            if customers:
                data = [{
                    "ID": c.id,
                    "Name": c.name,
                    "Phone": c.phone,
                    "Address": c.address
                } for c in customers]
                st.dataframe(pd.DataFrame(data))
            else:
                st.info("No customers found")
        
        with tab2:
            st.subheader("Add New Customer")
            with st.form("add_customer_form"):
                # Use st.session_state for initial values
                name = st.text_input("Customer Name", value=st.session_state.add_cust_name_value, key="add_cust_name")
                phone = st.text_input("Phone Number", value=st.session_state.add_cust_phone_value, key="add_cust_phone")
                address = st.text_area("Address", value=st.session_state.add_cust_address_value, key="add_cust_address")
                
                if st.form_submit_button("Add Customer"):
                    if name and phone and address:
                        new_customer = Customer(
                            name=name,
                            phone=phone,
                            address=address
                        )
                        session.add(new_customer)
                        session.commit()
                        st.success("Customer added successfully!")
                        # Clear form fields after successful submission
                        st.session_state.add_cust_name_value = ""
                        st.session_state.add_cust_phone_value = ""
                        st.session_state.add_cust_address_value = ""
                        st.rerun()
                    else:
                        st.error("Please fill all customer fields.")
                
                # Update session state for non-form submission inputs (if any)
                st.session_state.add_cust_name_value = name
                st.session_state.add_cust_phone_value = phone
                st.session_state.add_cust_address_value = address
                
        with tab3:
            st.subheader("Update or Delete Customer")
            customers = session.query(Customer).order_by(Customer.id.asc()).all()
            
            if customers:
                customer_options = {f"{c.name} (ID: {c.id})": c.id for c in customers}
                
                # Get the index of the previously selected customer if it exists in current options
                current_customer_keys = list(customer_options.keys())
                default_index = 0
                if st.session_state.selected_customer_key_value in current_customer_keys:
                    default_index = current_customer_keys.index(st.session_state.selected_customer_key_value)
                elif customers: # If previous was deleted, or no prev selected, pick first
                    st.session_state.selected_customer_key_value = current_customer_keys[0]
                    default_index = 0
                else: # No customers left
                    st.session_state.selected_customer_key_value = None

                selected_customer_key = st.selectbox(
                    "Select Customer to Update/Delete", 
                    options=current_customer_keys, 
                    index=default_index, # Set default selection
                    key="select_customer_update"
                )
                
                # Update session state with the current selection for persistence
                st.session_state.selected_customer_key_value = selected_customer_key
                
                if selected_customer_key and st.session_state.selected_customer_key_value: # Make sure a customer is actually selected
                    cust_id = customer_options[st.session_state.selected_customer_key_value] # Use session state value
                    customer_to_edit = session.query(Customer).get(cust_id)
                    
                    with st.form(f"edit_customer_form_{cust_id}"):
                        edited_name = st.text_input("Customer Name", value=customer_to_edit.name, key=f"edit_cust_name_{cust_id}")
                        edited_phone = st.text_input("Phone Number", value=customer_to_edit.phone, key=f"edit_cust_phone_{cust_id}")
                        edited_address = st.text_area("Address", value=customer_to_edit.address, key=f"edit_cust_address_{cust_id}")
                        
                        col_update, col_delete = st.columns(2)
                        with col_update:
                            if st.form_submit_button("Update Customer"):
                                customer_to_edit.name = edited_name
                                customer_to_edit.phone = edited_phone
                                customer_to_edit.address = edited_address
                                session.commit()
                                st.success("Customer updated successfully!")
                                st.rerun()
                        with col_delete:
                            if st.form_submit_button("Delete Customer"):
                                if st.checkbox("Confirm deletion?", key=f"confirm_delete_customer_{cust_id}"):
                                    session.delete(customer_to_edit)
                                    session.commit()
                                    st.success("Customer deleted successfully!")
                                    # Clear selected item from session state after deletion
                                    st.session_state.selected_customer_key_value = None
                                    st.rerun()
                else:
                    st.info("Please select a customer to edit or delete.")
            else:
                st.info("No customers available to update or delete.")
    finally:
        session.close()

if st.session_state.logged_in:
    manage_customers()
else:
    st.warning("Please log in to manage customers.")