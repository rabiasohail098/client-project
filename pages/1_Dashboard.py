# pages/1_Dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import func, cast, String as AlchemyString
from sqlalchemy.orm import joinedload
from database import Customer, Item, Order, OrderItem, Transaction

# Get database instance from session state
db = st.session_state['db']

def show_dashboard():
    st.title("Inventory Dashboard")
    session = db.get_session()
    try:
        total_products = session.query(Item).count()
        total_items_sum = session.query(func.sum(Item.quantity)).scalar()
        total_items = total_items_sum if total_items_sum is not None else 0
        low_stock = session.query(Item).filter(Item.quantity <= 5).count()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Products", total_products)
        col2.metric("Total Items in Stock", total_items)
        col3.metric("Low Stock Items", low_stock)
        
        st.subheader("Recent Sales Transactions")
        sales_transactions = session.query(
            Order, Customer, OrderItem, Item, Transaction
        ).join(
            Customer, Order.customer_id == Customer.id
        ).join(
            OrderItem, Order.id == OrderItem.order_id
        ).join(
            Item, OrderItem.item_id == Item.id
        ).outerjoin(
            Transaction, cast(Order.id, AlchemyString) == Transaction.bill_no
        ).order_by(Order.date.desc()).limit(10).all()

        if sales_transactions:
            data = []
            for order, customer, order_item, item, transaction in sales_transactions:
                data.append({
                    "Order ID": order.id,
                    "Date": order.date.strftime("%d-%m-%Y %H:%M"),
                    "Customer Name": customer.name,
                    "Product Name": item.name,
                    "Quantity": order_item.quantity,
                    "Item Total": f"PKR {order_item.quantity * order_item.price:.2f}",
                    "Order Total Amount": f"PKR {order.total_amount:.2f}",
                    "Payment Mode": transaction.mode if transaction else "N/A",
                    "Amount Received": f"PKR {transaction.received:.2f}" if transaction else "PKR 0.00",
                    "Balance Amount": f"PKR {transaction.balance:.2f}" if transaction else f"PKR {order.total_amount:.2f}",
                })
            st.dataframe(pd.DataFrame(data))
        else:
            st.info("No recent sales transactions found.")
    finally:
        session.close()

if st.session_state.logged_in:
    show_dashboard()
else:
    st.warning("Please log in to access the dashboard.")