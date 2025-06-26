# pages/3_Customers.py

import streamlit as st
import pandas as pd
from database import Customer

db = st.session_state['db']

def manage_customers():
    st.title("Customer Management")
    session = db.get_session()
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
                name = st.text_input("Customer Name", key="add_cust_name")
                phone = st.text_input("Phone Number", key="add_cust_phone")
                address = st.text_area("Address", key="add_cust_address")
                
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
                        st.rerun()
                    else:
                        st.error("Please fill all customer fields.")
        
        with tab3:
            st.subheader("Update or Delete Customer")
            customers = session.query(Customer).order_by(Customer.id.asc()).all()
            
            if customers:
                customer_options = {f"{c.name} (ID: {c.id})": c.id for c in customers}
                selected_customer_key = st.selectbox("Select Customer to Update/Delete", options=list(customer_options.keys()), key="select_customer_update")
                
                if selected_customer_key:
                    cust_id = customer_options[selected_customer_key]
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
                                session.delete(customer_to_edit)
                                session.commit()
                                st.success("Customer deleted successfully!")
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