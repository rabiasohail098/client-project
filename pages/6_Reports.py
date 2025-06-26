# pages/6_Reports.py

import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
from database import Item, Transaction

db = st.session_state['db']

# Helper function for creating transaction summary PDF 
def create_transaction_pdf(data_frame, start, end):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Transaction Summary Report", 0, 1, 'C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"From {start.strftime('%d-%m-%Y')} to {end.strftime('%d-%m-%Y')}", 0, 1, 'C') 
        pdf.ln(10)

        # Column widths - --- CORRECTED THIS LINE ---
        # Old: col_widths = [18, 20, 25, 25, 25, 22, 20, 20] # 8 elements
        col_widths = [14, 10, 15, 23, 50, 11, 12, 15, 12] # New: 9 elements to match 9 headers
        headers = ["Trans ID", "Bill No", "Date", "Customer", "Address", "Mode", "Issued", "Received", "Balance"] # 9 elements

        # Header
        pdf.set_font("Arial", 'B', 8)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
        pdf.ln()

        # Data
        pdf.set_font("Arial", '', 7)
        for _, row in data_frame.iterrows():
            # Ensure the order matches the headers
            pdf.cell(col_widths[0], 8, str(row["Transaction ID"]), 1, 0, 'C')
            pdf.cell(col_widths[1], 8, str(row["Bill No"]), 1, 0, 'C')
            pdf.cell(col_widths[2], 8, row["Date"].split(' ')[0], 1, 0, 'C') 
            pdf.cell(col_widths[3], 8, row["Customer Name"], 1, 0, 'C')
            pdf.cell(col_widths[4], 8, row["Customer Address"], 1, 0, 'C') 
            pdf.cell(col_widths[5], 8, row["Payment Mode"], 1, 0, 'C')
            pdf.cell(col_widths[6], 8, row["Issue Amount"].replace("PKR ", ""), 1, 0, 'C')
            pdf.cell(col_widths[7], 8, row["Received Amount"].replace("PKR ", ""), 1, 0, 'C')
            pdf.cell(col_widths[8], 8, row["Balance Amount"].replace("PKR ", ""), 1, 0, 'C')
            pdf.ln()

        # Summary
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        total_issued = data_frame['Issue Amount Numeric'].sum()
        total_received = data_frame['Received Amount Numeric'].sum()
        total_balance = data_frame['Balance Amount Numeric'].sum()
        
        pdf.cell(0, 10, f"Total Issued: PKR {total_issued:.2f}", 0, 1, 'R')
        pdf.cell(0, 10, f"Total Received: PKR {total_received:.2f}", 0, 1, 'R')
        pdf.cell(0, 10, f"Total Balance: PKR {total_balance:.2f}", 0, 1, 'R')

        buffer = BytesIO()
        buffer.write(pdf.output(dest='B')) 
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def show_reports():
    st.title("Inventory Reports")
    session = st.session_state['db'].get_session() 
    try:
        report_type = st.selectbox("Select Report", ["Stock Levels", "Low Stock", "Transaction Summary"], key="main_reports_select")
        
        if report_type == "Stock Levels":
            st.subheader("Current Stock Levels")
            items = session.query(Item).order_by(Item.quantity.asc()).all() 
            
            if items:
                data = [{
                    "ID": i.id,
                    "Name": i.name,
                    "Quantity": i.quantity,
                    "Cost Price": f"PKR {i.cost_price:.2f}",
                    "Selling Price": f"PKR {i.selling_price:.2f}"
                } for i in items]
                df = pd.DataFrame(data)
                st.dataframe(df)
                st.bar_chart(df.set_index('Name')['Quantity'])
            else:
                st.info("No products found")
        
        elif report_type == "Low Stock":
            st.subheader("Low Stock Items (Quantity <= 5)")
            items = session.query(Item).filter(Item.quantity <= 5).order_by(Item.quantity.asc()).all()
            
            if items:
                data = [{
                    "ID": i.id,
                    "Name": i.name,
                    "Quantity": i.quantity,
                    "Reorder Level": 5
                } for i in items]
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                critical = [i for i in items if i.quantity == 0]
                if critical:
                    st.warning(f"Critical: {len(critical)} items out of stock!")
            else:
                st.success("No low stock items!")
        
        elif report_type == "Transaction Summary":
            st.subheader("Transaction Summary")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.today().replace(month=1, day=1).date(), key="report_start_trans")
            with col2:
                end_date = st.date_input("End Date", value=datetime.today().date(), key="report_end_trans")
            
            if st.button("Generate Transaction Summary"):
                transactions = session.query(Transaction).filter(
                    Transaction.date >= datetime.combine(start_date, datetime.min.time()),
                    Transaction.date <= datetime.combine(end_date, datetime.max.time())
                ).order_by(Transaction.date.asc()).all() 
                
                if transactions:
                    summary = pd.DataFrame([{
                        "Transaction ID": t.id,
                        "Bill No": t.bill_no,
                        "Date": t.date.strftime("%d-%m-%Y %H:%M"), 
                        "Customer Name": t.party_name,
                        "Customer Address": t.address, 
                        "Payment Mode": t.mode,
                        "Issue Amount": f"PKR {t.issue_amount:.2f}",
                        "Received Amount": f"PKR {t.received:.2f}",
                        "Balance Amount": f"PKR {t.balance:.2f}"
                    } for t in transactions])
                    
                    st.dataframe(summary)
                    
                    summary['Issue Amount Numeric'] = summary['Issue Amount'].str.replace('PKR ', '').astype(float)
                    summary['Received Amount Numeric'] = summary['Received Amount'].str.replace('PKR ', '').astype(float)
                    summary['Balance Amount Numeric'] = summary['Balance Amount'].str.replace('PKR ', '').astype(float)

                    st.subheader("Summary by Payment Mode")
                    mode_summary = summary.groupby('Payment Mode').agg(
                        Count=('Payment Mode', 'count'),
                        Total_Amount=('Issue Amount Numeric', 'sum')
                    ).reset_index()
                    st.dataframe(mode_summary)
                    
                    st.subheader("Transaction Distribution by Mode")
                    st.bar_chart(mode_summary.set_index('Payment Mode')['Total_Amount'])

                    st.markdown("---")
                    st.subheader("Generate Printout (PDF)") 

                    transaction_pdf_output = create_transaction_pdf(summary, start_date, end_date)
                    if transaction_pdf_output: 
                        st.download_button(
                            label="Print Transaction Summary (PDF)", 
                            data=transaction_pdf_output,
                            file_name=f"transaction_summary_{start_date.strftime('%d%m%Y')}_to_{end_date.strftime('%d%m%Y')}.pdf", 
                            mime="application/pdf",
                            key="download_transaction_pdf_button"
                        )
                    else:
                        st.error("Failed to generate PDF for the transaction summary.") 
                else:
                    st.info("No transactions in selected period") 
    finally:
        session.close()

if st.session_state.logged_in:
    show_reports()
else:
    st.warning("Please log in to view reports.")