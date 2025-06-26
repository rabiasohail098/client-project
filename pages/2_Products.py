# pages/2_Products.py

import streamlit as st
import pandas as pd
from database import Item
from utils.session import initialize_session
initialize_session()

db = st.session_state['db']


def manage_products():
    st.title("Product Management")
    session = db.get_session()

    # --- Initialize session state for product management persistence ---
    if 'add_item_name_value' not in st.session_state:
        st.session_state.add_item_name_value = ""
    if 'add_item_qty_value' not in st.session_state:
        st.session_state.add_item_qty_value = 0
    if 'add_item_cost_value' not in st.session_state:
        st.session_state.add_item_cost_value = 0.0
    if 'add_item_selling_value' not in st.session_state:
        st.session_state.add_item_selling_value = 0.0
    
    # For Edit/Delete tab's selectbox
    if 'selected_product_key_edit_value' not in st.session_state:
        st.session_state.selected_product_key_edit_value = None
    # --- End session state initialization ---

    try:
        tab1, tab2, tab3 = st.tabs(["View Products", "Add Product", "Edit/Delete Product"]) 
        
        with tab1:
            st.subheader("All Products")
            products = session.query(Item).order_by(Item.id.asc()).all()
            
            if products:
                data = [{
                    "ID": p.id,
                    "Name": p.name,
                    "Quantity": p.quantity,
                    "Cost Price": f"PKR {p.cost_price:.2f}",
                    "Selling Price": f"PKR {p.selling_price:.2f}"
                } for p in products]
                st.dataframe(pd.DataFrame(data))
            else:
                st.info("No products found")
        
        with tab2:
            st.subheader("Add New Product")
            with st.form("add_product_form"):
                # Use st.session_state to store and retrieve values
                name = st.text_input("Product Name", value=st.session_state.add_item_name_value, key="add_item_name")
                quantity = st.number_input("Initial Quantity", value=st.session_state.add_item_qty_value, min_value=0, step=1, key="add_item_qty")
                cost_price = st.number_input("Cost Price", value=st.session_state.add_item_cost_value, min_value=0.0, step=0.01, key="add_item_cost")
                selling_price = st.number_input("Selling Price", value=st.session_state.add_item_selling_value, min_value=0.0, step=0.01, key="add_item_selling")
                
                if st.form_submit_button("Add Product"):
                    if name and quantity >= 0 and cost_price >= 0 and selling_price >= 0:
                        new_product = Item(
                            name=name,
                            quantity=quantity,
                            cost_price=cost_price,
                            selling_price=selling_price
                        )
                        session.add(new_product)
                        session.commit()
                        st.success("Product added successfully!")
                        # Clear form fields after successful submission by resetting session state values
                        st.session_state.add_item_name_value = ""
                        st.session_state.add_item_qty_value = 0
                        st.session_state.add_item_cost_value = 0.0
                        st.session_state.add_item_selling_value = 0.0
                        st.rerun()
                    else:
                        st.error("Please fill all product fields correctly.")
                
                # Update session state for non-form submission inputs (if any)
                # For inputs within a form, their 'key' makes their value accessible via st.session_state[key]
                # If you want to persist values even if the user refreshes mid-entry without submitting,
                # you would typically set the value on_change. For forms, the above approach is common.
                # However, for the 'add_item_name_value' etc., the `value=` argument in the widget itself
                # ensures persistence.
                st.session_state.add_item_name_value = name # Update if user changes input
                st.session_state.add_item_qty_value = quantity
                st.session_state.add_item_cost_value = cost_price
                st.session_state.add_item_selling_value = selling_price
                
        with tab3:
            st.subheader("Edit or Delete Product Details and Stock")
            products = session.query(Item).order_by(Item.id.asc()).all()

            if products:
                product_options = {f"{p.name} (ID: {p.id}) - Current Qty: {p.quantity}": p.id for p in products}
                
                # Get the index of the previously selected product if it exists in current options
                current_product_keys = list(product_options.keys())
                default_index = 0
                if st.session_state.selected_product_key_edit_value in current_product_keys:
                    default_index = current_product_keys.index(st.session_state.selected_product_key_edit_value)
                elif products: # If the previously selected product was deleted, select the first available one
                    st.session_state.selected_product_key_edit_value = current_product_keys[0]
                    default_index = 0
                else: # No products left
                    st.session_state.selected_product_key_edit_value = None
                

                # Use st.session_state to store the selected value and set the default index
                selected_product_key_edit = st.selectbox(
                    "Select Product to Edit/Delete", 
                    options=current_product_keys, 
                    index=default_index, # Set the default selection
                    key="select_product_edit_delete"
                )
                
                # Update session state with the current selection for persistence
                st.session_state.selected_product_key_edit_value = selected_product_key_edit

                # Get the item ID from the selected key (must be done after selectbox has a value)
                if selected_product_key_edit and st.session_state.selected_product_key_edit_value: # Make sure a product is actually selected
                    item_id = product_options[st.session_state.selected_product_key_edit_value] # Use session state value for consistency
                    item_to_edit = session.query(Item).get(item_id)

                    with st.form(f"edit_product_form_{item_id}"):
                        edited_name = st.text_input("Product Name", value=item_to_edit.name, key=f"edit_item_name_{item_id}")
                        edited_quantity = st.number_input("Quantity", value=item_to_edit.quantity, min_value=0, step=1, key=f"edit_item_qty_{item_id}")
                        edited_cost_price = st.number_input("Cost Price", value=item_to_edit.cost_price, min_value=0.0, step=0.01, key=f"edit_item_cost_{item_id}")
                        edited_selling_price = st.number_input("Selling Price", value=item_to_edit.selling_price, min_value=0.0, step=0.01, key=f"edit_item_selling_{item_id}")
                        
                        col_update, col_delete = st.columns(2)
                        with col_update:
                            if st.form_submit_button("Update Product Details"):
                                item_to_edit.name = edited_name
                                item_to_edit.quantity = edited_quantity
                                item_to_edit.cost_price = edited_cost_price
                                item_to_edit.selling_price = edited_selling_price
                                session.commit()
                                st.success("Product details and stock updated successfully!")
                                st.rerun()
                        with col_delete:
                            if st.form_submit_button("Delete Product"):
                                if st.checkbox("Confirm deletion?", key=f"confirm_delete_item_{item_id}"):
                                    session.delete(item_to_edit)
                                    session.commit()
                                    st.success("Product deleted successfully!")
                                    # Clear selected item from session state after deletion
                                    st.session_state.selected_product_key_edit_value = None 
                                    st.rerun()
                else:
                    st.info("Please select a product to edit or delete.")
            else:
                st.info("No products available to edit or delete.")
    finally:
        session.close()

if st.session_state.logged_in:
    manage_products()
else:
    st.warning("Please log in to manage products.")