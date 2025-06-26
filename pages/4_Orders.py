# pages/4_Orders.py

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import joinedload
from database import Customer, Item, Order, OrderItem, Transaction
from utils.session import initialize_session
initialize_session()

db = st.session_state['db']



def manage_orders():
    st.title("Order Management")
    session = db.get_session()
    try:
        tab1, tab2 = st.tabs(["Create New Order", "View All Orders"])

        with tab1:
            st.subheader("Create a New Sales Order")
            customers = session.query(Customer).order_by(Customer.id.asc()).all()
            products = session.query(Item).filter(Item.quantity > 0).order_by(Item.id.asc()).all()

            if not customers:
                st.warning("Please add some customers first from 'Customers' page.")
                return
            if not products:
                st.warning("Please add some products with available stock first from 'Products' page.")
                return

            customer_options = {f"{c.name} (ID: {c.id})": c.id for c in customers}
            selected_customer_key = st.selectbox("Select Customer", options=list(customer_options.keys()), key="order_customer_select")
            selected_customer_id = customer_options[selected_customer_key]

            st.markdown("---")
            st.subheader("Add Items to Order")

            if 'current_order_items' not in st.session_state:
                st.session_state.current_order_items = []

            product_choices = {f"{p.name} (Available: {p.quantity}, Price: PKR {p.selling_price:.2f})": p.id for p in products}
            
            if product_choices:
                selected_product_key = st.selectbox("Select Product to Add", options=list(product_choices.keys()), key="add_item_to_order_product")
                selected_product_id = product_choices[selected_product_key]
                
                selected_product = session.query(Item).get(selected_product_id)

                qty_to_add = st.number_input(
                    f"Quantity (Max: {selected_product.quantity})", 
                    min_value=1, 
                    max_value=selected_product.quantity, 
                    step=1, 
                    key="add_item_to_order_qty"
                )

                if st.button("Add Product to Order List", key="add_product_to_order_list"):
                    existing_item_index = -1
                    for i, item_data in enumerate(st.session_state.current_order_items):
                        if item_data['item_id'] == selected_product_id:
                            existing_item_index = i
                            break

                    if existing_item_index != -1:
                        if st.session_state.current_order_items[existing_item_index]['quantity'] + qty_to_add > selected_product.quantity:
                            st.error(f"Cannot add {qty_to_add} more. Only {selected_product.quantity - st.session_state.current_order_items[existing_item_index]['quantity']} available for {selected_product.name}.")
                        else:
                            st.session_state.current_order_items[existing_item_index]['quantity'] += qty_to_add
                            st.session_state.current_order_items[existing_item_index]['total_price'] += (selected_product.selling_price * qty_to_add)
                            st.success(f"{qty_to_add} x {selected_product.name} added to order list.")
                    else:
                        st.session_state.current_order_items.append({
                            "item_id": selected_product_id,
                            "name": selected_product.name,
                            "quantity": qty_to_add,
                            "selling_price_at_order": selected_product.selling_price,
                            "cost_price_at_order": selected_product.cost_price, 
                            "total_price": selected_product.selling_price * qty_to_add
                        })
                        st.success(f"{qty_to_add} x {selected_product.name} added to order list.")
            else:
                st.info("No products with available stock to add.")


            if st.session_state.current_order_items:
                st.subheader("Current Order Items:")
                order_df = pd.DataFrame(st.session_state.current_order_items)
                order_df['Selling Price'] = order_df['selling_price_at_order'].apply(lambda x: f"PKR {x:.2f}")
                order_df['Total Price'] = order_df['total_price'].apply(lambda x: f"PKR {x:.2f}")
                st.dataframe(order_df[['name', 'quantity', 'Selling Price', 'Total Price']])

                total_order_amount = sum(item['total_price'] for item in st.session_state.current_order_items)
                st.markdown(f"### Total Order Amount: **PKR {total_order_amount:.2f}**")

                st.markdown("---")
                st.subheader("Payment Details")
                payment_mode = st.selectbox("Payment Mode", ["Cash", "Credit", "Cheque"], key="order_payment_mode")
                
                cheque_no = None
                if payment_mode == "Cheque":
                    cheque_no = st.text_input("Cheque Number", key="order_cheque_no")
                
                order_status = st.selectbox("Order Status", ["Pending", "Completed", "Cancelled"], key="order_status_select")


                amount_received = st.number_input("Amount Received", min_value=0.0, value=total_order_amount, step=0.01, key="order_amount_received")
                balance_amount = total_order_amount - amount_received
                st.info(f"Balance Amount: PKR {balance_amount:.2f}")

                if st.button("Finalize Order", key="finalize_order_button"):
                    if not st.session_state.current_order_items:
                        st.error("Please add items to the order before finalizing.")
                    else:
                        all_stock_available = True
                        for item_data in st.session_state.current_order_items:
                            product_in_stock = session.query(Item).get(item_data['item_id'])
                            if product_in_stock and product_in_stock.quantity < item_data['quantity']:
                                st.error(f"Error: Not enough stock for {product_in_stock.name}. Available: {product_in_stock.quantity}, Requested: {item_data['quantity']}")
                                all_stock_available = False
                                break
                        
                        if not all_stock_available:
                            session.rollback() 
                            st.stop()

                        new_order = Order(
                            customer_id=selected_customer_id,
                            total_amount=total_order_amount,
                            date=datetime.utcnow(),
                            status=order_status
                        )
                        session.add(new_order)
                        session.flush() 

                        for item_data in st.session_state.current_order_items:
                            order_item = OrderItem(
                                order_id=new_order.id,
                                item_id=item_data['item_id'],
                                quantity=item_data['quantity'],
                                price=item_data['selling_price_at_order']
                            )
                            session.add(order_item)

                            product_in_stock = session.query(Item).get(item_data['item_id'])
                            if product_in_stock:
                                product_in_stock.quantity -= item_data['quantity']

                        customer_details = session.query(Customer).get(selected_customer_id)
                        customer_name_for_transaction = customer_details.name if customer_details else "N/A"
                        customer_address_for_transaction = customer_details.address if customer_details else "N/A"

                        new_transaction = Transaction(
                            bill_no=str(new_order.id), 
                            date=datetime.utcnow(),
                            customer_id=selected_customer_id,
                            party_name=customer_name_for_transaction,
                            address=customer_address_for_transaction,
                            mode=payment_mode,
                            cheque_no=cheque_no,
                            issue_amount=total_order_amount,
                            received=amount_received,
                            balance=balance_amount
                        )
                        session.add(new_transaction)
                        
                        session.commit()
                        st.success(f"Order {new_order.id} finalized successfully!")
                        st.session_state.current_order_items = []
                        st.rerun()
            else:
                st.info("Add products to create an order.")


        with tab2:
            st.subheader("All Sales Orders")
            orders_with_details = session.query(Order).options(
                joinedload(Order.customer),
                joinedload(Order.order_items).joinedload(OrderItem.item)
            ).order_by(Order.date.asc()).all() 

            if orders_with_details:
                order_data = []
                for order in orders_with_details:
                    items_str = ", ".join([f"{oi.item.name} ({oi.quantity}x)" for oi in order.order_items])
                    
                    transaction = session.query(Transaction).filter_by(bill_no=str(order.id)).first()

                    order_data.append({
                        "Order ID": order.id,
                        "Date": order.date.strftime("%d-%m-%Y %H:%M"), 
                        "Customer Name": order.customer.name if order.customer else "N/A",
                        "Items": items_str,
                        "Total Amount": f"PKR {order.total_amount:.2f}",
                        "Status": order.status,
                        "Payment Mode": transaction.mode if transaction else "N/A",
                        "Amount Received": f"PKR {transaction.received:.2f}" if transaction else "PKR 0.00",
                        "Balance": f"PKR {transaction.balance:.2f}" if transaction else f"PKR {order.total_amount:.2f}"
                    })
                st.dataframe(pd.DataFrame(order_data))
            else:
                st.info("No orders found.")
    finally:
        session.close()

if st.session_state.logged_in:
    manage_orders()
else:
    st.warning("Please log in to manage orders.")