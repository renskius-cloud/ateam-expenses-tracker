import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

# 1. PAGE SETUP
st.set_page_config(
    page_title="ATeam Expenses & CC Tracker",
    page_icon="💳",
    layout="wide"
)

# 2. GOOGLE SHEETS CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_all_data():
    cards_df = conn.read(worksheet="Cards")
    tx_df = conn.read(worksheet="Transactions")
    inst_df = conn.read(worksheet="Installments")
    try:
        daddy_df = conn.read(worksheet="Daddy")
    except Exception:
        daddy_df = pd.DataFrame(columns=["Date", "Items", "Amount", "Notes"])
    try:
        payments_df = conn.read(worksheet="Payments")
    except Exception:
        payments_df = pd.DataFrame(columns=["Month", "Year", "Card", "Status", "Timestamp"])
    return cards_df, tx_df, inst_df, daddy_df, payments_df

try:
    cards_df, tx_df, inst_df, daddy_df, payments_df = load_all_data()
except Exception as e:
    st.error(f"⚠️ Error loading Google Sheets: {e}")
    st.stop()


# 3. HELPER FUNCTIONS FOR CUTOFF & BILLING CALCULATIONS
def parse_day(val):
    """Extracts numeric day from string like '22nd of the month' or integer 22."""
    if pd.isna(val):
        return 1
    val_str = str(val).lower().replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
    nums = [int(s) for s in val_str.split() if s.isdigit()]
    return nums[0] if nums else 1

def calculate_billing_payout(tx_date, cutoff_day, pay_period):
    """
    Determines the exact payout month & year for a transaction based on cutoff day.
    Example: Cutoff 22nd, Pay Period 15th.
    Purchased Jul 23 -> Misses Jul 22 cutoff -> Billed in Aug statement -> Due on Sept 15 Payout.
    """
    if pd.isna(tx_date):
        return None, None
    
    if isinstance(tx_date, str):
        tx_date = pd.to_datetime(tx_date, errors="coerce")
    
    if pd.isna(tx_date):
        return None, None

    year = tx_date.year
    month = tx_date.month
    day = tx_date.day

    # If transaction date is after cutoff day, move to next billing month
    if day > cutoff_day:
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Add payout delay (15th payout is due in month + 1 after cutoff month)
    # e.g., Cutoff Jul 22 -> Next cutoff Aug 22 -> Due Sept 15
    if "15" in str(pay_period):
        month += 1
        if month > 12:
            month = 1
            year += 1

    return month, year


# 4. SIDEBAR NAVIGATION
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["💳 Credit Cards", "📜 Daddy List"])


# ==========================================
# PAGE 1: CREDIT CARDS
# ==========================================
if page == "💳 Credit Cards":
    st.title("💳 Credit Cards Tracker")

    # --- Billing Period Selection ---
    col_m, col_y = st.columns(2)
    months_map = {
        "January": 1, "February": 2, "March": 3, "April": 4, 
        "May": 5, "June": 6, "July": 7, "August": 8, 
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    months_reverse = {v: k for k, v in months_map.items()}

    with col_m:
        sel_month_name = st.selectbox("Select Billing Month", list(months_map.keys()), index=8) # Default Sept
        sel_month = months_map[sel_month_name]
    with col_y:
        sel_year = st.selectbox("Select Billing Year", [2025, 2026, 2027], index=1)

    # --- Calculate Statement Dues based on Cutoff Rules ---
    # Merge Card details with Transactions
    tx_df_calc = tx_df.copy()
    if not tx_df_calc.empty and "Card" in tx_df_calc.columns:
        tx_df_calc = tx_df_calc.merge(cards_df, left_on="Card", right_on="Card Name", how="left")
        
        # Parse Cutoff Day
        tx_df_calc["Cutoff_Day"] = tx_df_calc["Billing Period"].apply(parse_day)
        tx_df_calc["Tx_Date"] = pd.to_datetime(tx_df_calc["Date"], errors="coerce")
        
        # Calculate Payout Month & Year
        tx_df_calc[["Payout_Month", "Payout_Year"]] = tx_df_calc.apply(
            lambda row: pd.Series(calculate_billing_payout(row["Tx_Date"], row["Cutoff_Day"], row["Pay Period"])),
            axis=1
        )
        
        # Clean Amount column to float
        tx_df_calc["Clean_Amount"] = (
            tx_df_calc["Amount"].astype(str)
            .str.replace("₱", "", regex=False)
            .str.replace(",", "", regex=False)
            .astype(float)
        )
        
        # Filter for selected period
        current_period_tx = tx_df_calc[
            (tx_df_calc["Payout_Month"] == sel_month) & 
            (tx_df_calc["Payout_Year"] == sel_year)
        ]
    else:
        current_period_tx = pd.DataFrame()

    # Calculate Totals for 15th & 30th
    if not current_period_tx.empty:
        due_15th = current_period_tx[current_period_tx["Pay Period"].astype(str).str.contains("15")]["Clean_Amount"].sum()
        due_30th = current_period_tx[current_period_tx["Pay Period"].astype(str).str.contains("30")]["Clean_Amount"].sum()
    else:
        due_15th = 0.0
        due_30th = 0.0

    # --- Clickable Summary Buttons ---
    st.markdown("#### 🗓️ Payout Dues Summary")
    c1, c2 = st.columns(2)
    
    if "filter_payout" not in st.session_state:
        st.session_state.filter_payout = "All"

    with c1:
        if st.button(f"🗓️ Due for {sel_month_name} 15th: ₱{due_15th:,.2f}", use_container_width=True, type="primary"):
            st.session_state.filter_payout = "15th"
    with c2:
        if st.button(f"🗓️ Due for {sel_month_name} 30th: ₱{due_30th:,.2f}", use_container_width=True, type="primary"):
            st.session_state.filter_payout = "30th"

    st.divider()

    # --- Credit Cards Master Table ---
    st.markdown("### 📊 Credit Cards Status")
    st.dataframe(cards_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- Transactions for the Selected Period ---
    st.markdown(f"### 📑 Transactions for {sel_month_name} {sel_year}")
    
    if not current_period_tx.empty:
        display_tx = current_period_tx
        if st.session_state.filter_payout != "All":
            display_tx = display_tx[display_tx["Pay Period"].astype(str).str.contains(st.session_state.filter_payout)]
        
        st.dataframe(
            display_tx[["Date", "Card", "Category", "Amount", "Notes", "Pay Period"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No transactions found for this billing period.")

    st.divider()

    # --- CC Entry Forms ---
    st.markdown("### 📝 Add New CC Entry")
    t1, t2 = st.tabs(["➕ Daily Expense", "🔄 Installment"])
    
    card_opts = cards_df["Card Name"].dropna().unique().tolist() if "Card Name" in cards_df.columns else []

    with t1:
        with st.form("form_daily_expense", clear_on_submit=True):
            f1, f2 = st.columns(2)
            d_date = f1.date_input("Date")
            d_card = f2.selectbox("Card", card_opts)
            f3, f4 = st.columns(2)
            d_cat = f3.selectbox("Category", ["Dining & Food", "Groceries", "Utilities & Bills", "Health & Medical", "Gas & Travel", "Shopping & Clothes", "Miscellaneous"])
            d_amt = f4.number_input("Amount (PHP)", min_value=0.0, step=50.0)
            d_notes = st.text_input("Notes")

            if st.form_submit_button("Save Expense", type="primary", use_container_width=True):
                new_row = pd.DataFrame([{
                    "Date": d_date.strftime("%m/%d/%Y"),
                    "Card": d_card,
                    "Category": d_cat,
                    "Amount": f"₱{d_amt:,.2f}",
                    "Notes": d_notes
                }])
                updated = pd.concat([tx_df, new_row], ignore_index=True)
                conn.update(worksheet="Transactions", data=updated)
                st.success("Expense added successfully!")
                st.cache_data.clear()
                st.rerun()

    with t2:
        with st.form("form_inst_expense", clear_on_submit=True):
            f1, f2 = st.columns(2)
            i_owner = f1.selectbox("Owner", ["A-Team", "Tatay", "Kuya Jaypard", "Daddy"])
            i_card = f2.selectbox("Card", card_opts, key="inst_card")
            i_item = st.text_input("Item Description")
            p1, p2, p3 = st.columns(3)
            i_prin = p1.number_input("Principal (PHP)", min_value=0.0)
            i_tenor = p2.number_input("Tenor (Months)", min_value=1, value=12)
            i_monthly = p3.number_input("Monthly Payment (PHP)", min_value=0.0)
            i_start = st.date_input("Start Date")

            if st.form_submit_button("Register Installment", type="primary", use_container_width=True):
                new_inst = pd.DataFrame([{
                    "Owner": i_owner,
                    "Item": i_item,
                    "Card": i_card,
                    "Principal": f"₱{i_prin:,.2f}",
                    "Tenor": i_tenor,
                    "Monthly_Payment": f"₱{i_monthly:,.2f}",
                    "Start_Date": i_start.strftime("%m/%d/%Y")
                }])
                updated = pd.concat([inst_df, new_inst], ignore_index=True)
                conn.update(worksheet="Installments", data=updated)
                st.success("Installment registered successfully!")
                st.cache_data.clear()
                st.rerun()


# ==========================================
# PAGE 2: DADDY LIST
# ==========================================
elif page == "📜 Daddy List":
    st.title("📜 Utang ni Daddy kay Mommy Tracker")
    st.caption("Dedicated tracking view for non-CC/cash expenses, market runs, and personal cash items.")

    # Total Dues Metric
    if not daddy_df.empty and "Amount" in daddy_df.columns:
        clean_daddy_amt = (
            daddy_df["Amount"].astype(str)
            .str.replace("₱", "", regex=False)
            .str.replace(",", "", regex=False)
            .astype(float)
        )
        total_daddy_due = clean_daddy_amt.sum()
        st.metric("Total Outstanding Balance", f"₱{total_daddy_due:,.2f}")

    st.divider()

    # Daddy Transactions Table
    st.markdown("### 📋 Expenses List")
    st.dataframe(daddy_df, use_container_width=True, hide_index=True)

    st.divider()

    # Daddy Entry Form
    st.markdown("### ➕ Add Entry for Daddy")
    with st.form("form_daddy_entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_date = c1.date_input("Date")
        d_amt = c2.number_input("Amount (PHP)", min_value=0.0, step=50.0)
        d_item = st.text_input("Item Description / Expense")
        d_notes = st.text_input("Notes (Optional)")

        if st.form_submit_button("Save Entry", type="primary", use_container_width=True):
            new_entry = pd.DataFrame([{
                "Date": d_date.strftime("%m/%d/%Y"),
                "Items": d_item,
                "Amount": f"₱{d_amt:,.2f}",
                "Notes": d_notes
            }])
            updated = pd.concat([daddy_df, new_entry], ignore_index=True)
            conn.update(worksheet="Daddy", data=updated)
            st.success("Entry added successfully!")
            st.cache_data.clear()
            st.rerun()
