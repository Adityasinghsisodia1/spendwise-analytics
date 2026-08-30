"""Expense Tracker Dashboard — Streamlit app.

Log expenses by category, filter by month, and see spending trends at a
glance (category breakdown + monthly history) without touching a
spreadsheet. Data persists in a local SQLite file between runs.
"""

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

import db
import export

st.set_page_config(page_title="Expense Tracker Dashboard", page_icon="💰", layout="wide")

db.init_db()

st.title("💰 Expense Tracker Dashboard")

# --- Sidebar: add a new expense -------------------------------------------
with st.sidebar:
    st.header("Add Expense")
    with st.form("add_expense_form", clear_on_submit=True):
        expense_date = st.date_input("Date", value=date.today())
        category = st.selectbox("Category", db.CATEGORIES)
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("Add Expense", use_container_width=True)

        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                db.add_expense(expense_date, category, description.strip(), amount)
                st.success(f"Added {category} expense of ${amount:,.2f}")
                st.rerun()

# --- Filters ----------------------------------------------------------------
available_months = db.get_available_months()
col_month, col_category = st.columns(2)

with col_month:
    month_choice = st.selectbox("Month", ["All"] + available_months)
selected_month = None if month_choice == "All" else month_choice

with col_category:
    category_choice = st.selectbox("Category", ["All"] + db.CATEGORIES)
selected_category = None if category_choice == "All" else category_choice

expense_rows = [dict(row) for row in db.list_expenses(selected_month, selected_category)]
expenses_df = pd.DataFrame(expense_rows)

# --- KPI summary --------------------------------------------------------
total_spent = expenses_df["amount"].sum() if not expenses_df.empty else 0.0
transaction_count = len(expenses_df)
average_expense = (total_spent / transaction_count) if transaction_count else 0.0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Spent", f"${total_spent:,.2f}")
kpi2.metric("Transactions", transaction_count)
kpi3.metric("Average Expense", f"${average_expense:,.2f}")

# --- Charts -----------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Spending by Category")
    category_totals = db.get_category_totals(selected_month)
    if category_totals:
        category_df = pd.DataFrame([dict(row) for row in category_totals])
        fig = px.pie(category_df, names="category", values="total", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses logged yet for this filter.")

with chart_col2:
    st.subheader("Monthly Trend")
    monthly_totals = db.get_monthly_totals()
    if monthly_totals:
        monthly_df = pd.DataFrame([dict(row) for row in monthly_totals])
        fig = px.bar(monthly_df, x="month", y="total", labels={"month": "Month", "total": "Total Spent"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense history yet.")

# --- Expense table + delete + export ----------------------------------------
st.subheader("Expenses")

if expense_rows:
    for row in expense_rows:
        cols = st.columns([2, 2, 4, 2, 1])
        cols[0].write(row["expense_date"])
        cols[1].write(row["category"])
        cols[2].write(row["description"] or "—")
        cols[3].write(f"${row['amount']:,.2f}")
        if cols[4].button("🗑️", key=f"delete_{row['id']}"):
            db.delete_expense(row["id"])
            st.rerun()

    excel_bytes = export.build_excel(expense_rows)
    st.download_button(
        "Export to Excel",
        data=excel_bytes,
        file_name="expenses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("No expenses match this filter yet — add one from the sidebar.")
