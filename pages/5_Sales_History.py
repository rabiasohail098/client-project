# pages/5_Sales_History.py

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import cast, String as AlchemyString
from sqlalchemy.orm import joinedload
from fpdf import FPDF
from io import BytesIO
from database import Customer, Item, Order, OrderItem, Transaction

db = st.session_state['db']

# Helper function for creating sales PDF
def create_pdf(data_frame, total_rev, total_prof, start, end):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Sales Report", 0, 1, 'C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"From {start.strftime('%d-%m-%Y')} to {end.strftime('%d-%m-%Y')}", 0, 1, 'C')
        pdf.ln(10)

        # Column widths
        col_widths = [15, 15, 20, 20, 20, 25, 12, 16, 16, 15, 15] 
        headers = ["Bill No", "Order ID", "Date", "Customer Name", "Customer Phone", "Product Name", "Qty", "Item Total", "Order Total", "Paid", "Balance"]

        # Header
        pdf.set_font("Arial", 'B', 8)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
        pdf.ln()

        # Data
        pdf.set_font("Arial", '', 7)
        for _, row in data_frame.iterrows():
            pdf.cell(col_widths[0], 8, str(row["Bill No"]), 1, 0, 'C')
            pdf.cell(col_widths[1], 8, str(row["Order ID"]), 1, 0, 'C')
            pdf.cell(col_widths[2], 8, row["Order Date"].split(' ')[0], 1, 0, 'C') 
            pdf.cell(col_widths[3], 8, row["Customer Name"], 1, 0, 'C')
            pdf.cell(col_widths[4], 8, row["Customer Phone"], 1, 0, 'C')
            pdf.cell(col_widths[5], 8, row["Product Name"], 1, 0, 'C')
            pdf.cell(col_widths[6], 8, str(row["Quantity Sold"]), 1, 0, 'C')
            pdf.cell(col_widths[7], 8, row["Total Item Revenue"].replace("PKR ", ""), 1, 0, 'C')
            pdf.cell(col_widths[8], 8, row["Order Total Amount"].replace("PKR ", ""), 1, 0, 'C')
            pdf.cell(col_widths[9], 8, row["Amount Received"].replace("PKR ", ""), 1, 0, 'C')
            pdf.cell(col_widths[10], 8, row["Balance Amount"].replace("PKR ", ""), 1, 0, 'C')
            pdf.ln()

        # Summary
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Total Revenue: PKR {total_rev:.2f}", 0, 1, 'R')
        pdf.cell(0, 10, f"Total Profit: PKR {total_prof:.2f}", 0, 1, 'R')

        buffer = BytesIO()
        buffer.write(pdf.output(dest='B')) 
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def show_sales_history():
    st.title("Comprehensive Sales History")
    session = st.session_state['db'].get_session() 
    try:
        st.subheader("Filter Sales Data")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.today().replace(day=1).date(), key="sales_hist_start")
        with col2:
            end_date = st.date_input("End Date", value=datetime.today().date(), key="sales_hist_end")

        customer_list = session.query(Customer).order_by(Customer.name.asc()).all()
        customer_options = {"All Customers": None}
        customer_options.update({c.name: c.id for c in customer_list})
        selected_customer_name = st.selectbox("Filter by Customer", options=list(customer_options.keys()), key="sales_hist_customer")
        selected_customer_id = customer_options[selected_customer_name]

        product_list = session.query(Item).order_by(Item.name.asc()).all()
        product_options = {"All Products": None}
        product_options.update({i.name: i.id for i in product_list})
        selected_product_name = st.selectbox("Filter by Product", options=list(product_options.keys()), key="sales_hist_product")
        selected_product_id = product_options[selected_product_name]

        payment_mode_options = ["All", "Cash", "Credit", "Cheque"]
        selected_payment_mode = st.selectbox("Filter by Payment Mode", options=payment_mode_options, key="sales_hist_payment_mode")

        if st.button("Generate Sales Report", key="generate_sales_report_button"):
            query = session.query(
                Order, Customer, OrderItem, Item, Transaction
            ).join(
                Customer, Order.customer_id == Customer.id
            ).join(
                OrderItem, Order.id == OrderItem.order_id
            ).join(
                Item, OrderItem.item_id == Item.id
            ).outerjoin(
                Transaction, cast(Order.id, AlchemyString) == Transaction.bill_no
            ).filter(
                Order.date >= datetime.combine(start_date, datetime.min.time()),
                Order.date <= datetime.combine(end_date, datetime.max.time())
            )

            if selected_customer_id:
                query = query.filter(Customer.id == selected_customer_id)
            if selected_product_id:
                query = query.filter(Item.id == selected_product_id)
            if selected_payment_mode != "All":
                query = query.filter(Transaction.mode == selected_payment_mode.lower())

            sales_records = query.order_by(Order.date.asc()).all() 

            if sales_records:
                detailed_sales_data = []
                for order, customer, order_item, item, transaction in sales_records:
                    profit_on_item = (order_item.price - item.cost_price) * order_item.quantity
                    
                    detailed_sales_data.append({
                        "Bill No": transaction.bill_no if transaction else "N/A",
                        "Order ID": order.id,
                        "Order Date": order.date.strftime("%d-%m-%Y %H:%M:%S"),
                        "Customer Name": customer.name,
                        "Customer Phone": customer.phone, 
                        "Customer Address": customer.address, 
                        "Product Name": item.name,
                        "Quantity Sold": order_item.quantity,
                        "Total Item Revenue": f"PKR {order_item.quantity * order_item.price:.2f}",
                        "Order Total Amount": f"PKR {order.total_amount:.2f}",
                        "Payment Mode": transaction.mode if transaction else "N/A",
                        "Amount Received": f"PKR {transaction.received:.2f}" if transaction else "PKR 0.00",
                        "Balance Amount": f"PKR {transaction.balance:.2f}" if transaction else f"PKR {order.total_amount:.2f}",
                        "Profit (Internal)": profit_on_item 
                    })
                
                df_sales = pd.DataFrame(detailed_sales_data)
                
                display_cols = [
                    "Bill No", "Order ID", "Order Date", "Customer Name", "Customer Phone", 
                    "Customer Address", "Product Name", "Quantity Sold", "Total Item Revenue", 
                    "Order Total Amount", "Payment Mode", "Amount Received", "Balance Amount"
                ]
                st.dataframe(df_sales[display_cols])

                total_revenue = df_sales['Total Item Revenue'].str.replace('PKR ', '').astype(float).sum()
                total_profit = df_sales['Profit (Internal)'].sum() 
                
                st.markdown(f"### Summary for Selected Period:")
                st.info(f"Total Revenue: **PKR {total_revenue:.2f}**")
                st.success(f"Total Profit: **PKR {total_profit:.2f}**")
                
                st.subheader("Revenue and Profit by Date")
                df_sales['Total Item Revenue_Numeric'] = df_sales['Total Item Revenue'].str.replace('PKR ', '').astype(float)
                df_sales['Profit on Item_Numeric'] = df_sales['Profit (Internal)'] 
                df_sales['Order Date_Daily'] = pd.to_datetime(df_sales['Order Date'], format="%d-%m-%Y %H:%M:%S").dt.date 
                
                daily_summary = df_sales.groupby('Order Date_Daily').agg(
                    Total_Revenue=('Total Item Revenue_Numeric', 'sum'),
                    Total_Profit=('Profit on Item_Numeric', 'sum')
                ).reset_index()

                daily_summary['Total_Revenue'] = pd.to_numeric(daily_summary['Total_Revenue'])
                daily_summary['Total_Profit'] = pd.to_numeric(daily_summary['Total_Profit'])

                st.line_chart(daily_summary.set_index('Order Date_Daily')[['Total_Revenue', 'Total_Profit']])

                st.markdown("---")
                st.subheader("Generate Printout (PDF)") 

                pdf_output = create_pdf(df_sales, total_revenue, total_profit, start_date, end_date)
                # --- ADDED CHECK HERE ---
                if pdf_output: 
                    st.download_button(
                        label="Download Sales Report (PDF)",
                        data=pdf_output,
                        file_name=f"sales_report_{start_date.strftime('%d%m%Y')}_to_{end_date.strftime('%d%m%Y')}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate PDF for the sales report.") # Optional more specific error
            else:
                st.info("No sales records found for the selected criteria.")
    finally:
        session.close()

if st.session_state.logged_in:
    show_sales_history()
else:
    st.warning("Please log in to view sales history.")