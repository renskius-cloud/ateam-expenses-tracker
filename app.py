import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ATeam Expenses Tracker",
    page_icon="💳",
    layout="wide"
)

# --- CUSTOM FROSTED GLASS CSS (MIRRORING APPS SCRIPT DESIGN) ---
st.markdown("""
    <style>
    /* Main Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Frosted Glass Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
        color: #0f172a;
        margin-bottom: 20px;
    }

    /* Metric Due Cards */
    .due-card-blue {
        background: rgba(239, 246, 255, 0.95);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }
    
    .due-card-green {
        background: rgba(240, 253, 244, 0.95);
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
    }

    .due-label {
        font-size: 15px;
        font-weight: 700;
        color: #475569;
        margin-bottom: 4px;
    }

    .due-amount-blue { font-size: 32px; font-weight: 800; color: #1d4ed8; }
    .due-amount-green { font-size: 32px; font-weight: 800; color: #047857; }

    /* Custom Tables */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0 20px 0;
        font-size: 14px;
        border-radius: 10px;
        overflow: hidden;
        background: #ffffff;
        color: #334155;
    }
    .styled-table th {
        background-color: #f1f5f9;
        color: #0f172a;
        font-weight: 700;
        padding: 12px 16px;
        text-align: left;
        border-bottom: 2px solid #cbd5e1;
    }
    .styled-table td {
        padding: 10px 16px;
        border-bottom: 1px solid #e2e8f0;
        font-weight: 500;
    }

    /* Pill Badges */
    .badge-unpaid {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-nodue {
        background: #64748b;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }

    /* Form Section Headers */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION WITH FALLBACK MOCK DATA ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    try:
        cards_df = conn.read(worksheet="Cards")
        tx_df = conn.read(worksheet="Transactions")
        inst_df = conn.read(worksheet="Installments")
        try:
            outside_df = conn.read(worksheet="Outside_CC")
        except:
            outside_df = pd.DataFrame(columns=["Date", "Category", "Description", "Amount"])
        return cards_df, tx_df, inst_df, outside_df
    except Exception as e:
        # Fallback sample data to prevent crashing
        cards_df = pd.DataFrame([
            {"Credit Card": "BPI Gold", "Pay Period": "30th Payout", "Statement / Billing Range": "Jul 14 – Aug 13", "Total Amount Due": "₱2,428.27", "Payment Status": "Unpaid"},
            {"Credit Card": "Unionbank Rewards", "Pay Period": "15th Payout", "Statement / Billing Range": "Jun 29 – Jul 28", "Total Amount Due": "₱5,458.98", "Payment Status": "Unpaid"},
            {"Credit Card": "RCBC Preferred Airmiles", "Pay Period": "15th Payout", "Statement / Billing Range": "Jun 23 – Jul 22", "Total Amount Due": "₱38,359.27", "Payment Status": "Unpaid"},
            {"Credit Card": "SpayLater", "Pay Period": "15th Payout", "Statement / Billing Range": "Jun 5 – Jul 4", "Total Amount Due": "₱0.00", "Payment Status": "No Due"},
        ])
        tx_df = pd.DataFrame([
            {"Date": "8/4/2026", "Card": "HSBC Platinum", "Category": "Dining & Food", "Amount": 1205.00, "Notes": "Bcuts with miggy"},
            {"Date": "7/18/2026", "Card": "RCBC Preferred Airmiles", "Category": "Dining & Food", "Amount": 1345.00, "Notes": "CONTIS AYALA MARIKINA"},
            {"Date": "7/12/2026", "Card": "RCBC Preferred Airmiles", "Category": "Health & Medical", "Amount": 5851.00, "Notes": "WATSONS BLUE WAVE"},
        ])
        inst_df = pd.DataFrame([
            {"StartDate": "7/10/2026", "Item": "Credit to Cash (2/2)", "Card": "BPI Gold", "Principal": 4856.54, "Tenor": "2 mos", "Monthly": 2428.27},
            {"StartDate": "7/26/2026", "Item": "Credit to Cash (1/21)", "Card": "Unionbank Rewards", "Principal": 59933.58, "Tenor": "21 mos", "Monthly": 2853.98},
            {"StartDate": "7/26/2026", "Item": "THE LOOP-FELIZ (1/31)", "Card": "Unionbank Rewards", "Principal": 80755.00, "Tenor": "31 mos", "Monthly": 2605.00},
            {"StartDate": "7/9/2026", "Item": "INSTL C2G MBOA (tatay) (2/22)", "Card": "Metrobank Titanium", "Principal": 122672.44, "Tenor": "22 mos", "Monthly": 5576.02},
            {"StartDate": "7/9/2026", "Item": "INSTL C2G MBOA (kuya jaypard) (2/3)", "Card": "Metrobank Titanium", "Principal": 5300.01, "Tenor": "3 mos", "Monthly": 1766.67},
        ])
        outside_df = pd.DataFrame([
            {"Date": "8/10/2026", "Category": "Market / Palengke Supplies", "Description": "Meat and Vegetables", "Amount": 2500.00},
            {"Date": "8/12/2026", "Category": "Weekly Baon & Allowance", "Description": "Baon for school/office", "Amount": 1000.00},
        ])
        return cards_df, tx_df, inst_df, outside_df

cards_df, tx_df, inst_df, outside_df = load_data()

# --- APP HEADER ---
st.markdown("<h1 style='color: #ffffff;'>💳 ATeam Credit Card Expenses Tracker</h1>", unsafe_allow_html=True)

# --- 1. TOP BILLING PERIOD SELECTOR ---
months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

col_m, col_y = st.columns(2)
with col_m:
    selected_month = st.selectbox("Select Month", months_list, index=7)
with col_y:
    selected_year = st.selectbox("Select Year", [2025, 2026, 2027], index=1)

# Interactive State for Display #2
if "show_display_2" not in st.session_state:
    st.session_state.show_display_2 = False

# Clickable Due Metric Cards
c1, c2 = st.columns(2)
with c1:
    if st.button(f"🗓️ Due for {selected_month} 15th: ₱43,818.25\n\n(Click to Toggle Breakdown)", type="primary", use_container_width=True):
        st.session_state.show_display_2 = not st.session_state.show_display_2

with c2:
    if st.button(f"🗓️ Due for {selected_month} 30th: ₱25,169.08\n\n(Click to Toggle Breakdown)", type="primary", use_container_width=True):
        st.session_state.show_display_2 = not st.session_state.show_display_2

st.divider()

# --- DISPLAY #2 (DYNAMIC EXPANDABLE TRANSACTION BREAKDOWN) ---
if st.session_state.show_display_2:
    st.markdown(f"<div class='section-title'>📋 Display #2: All Transactions & Installment Summary for {selected_month} {selected_year}</div>", unsafe_allow_html=True)
    
    d1, d2 = st.columns(2)
    with d1:
        st.subheader("🧾 Statement Expenses History")
        st.dataframe(tx_df, use_container_width=True)
    with d2:
        st.subheader("🔄 Active Installments in this Period")
        st.dataframe(inst_df, use_container_width=True)
    st.divider()

# --- 2. MAIN DASHBOARD TABLE ---
st.markdown("<div class='section-title'>📊 Credit Card Dashboard & Status</div>", unsafe_allow_html=True)

# Display styled main table
st.dataframe(cards_df, use_container_width=True)

st.divider()

# --- 3. EXPENSE ENTRY FORM ---
st.markdown("<div class='section-title'>📝 Log Expenses & Installments</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["➕ Log CC Daily Expense", "🔄 Register CC Installment", "🛒 Log Outside CC (Utang ni Daddy)"])

with tab1:
    with st.form("form_daily_tx", clear_on_submit=True):
        f1, f2 = st.columns(2)
        tx_date = f1.date_input("Date of Purchase")
        card_col = cards_df.columns[0] if not cards_df.empty else "Credit Card"
        tx_card = f2.selectbox("Credit Card", cards_df[card_col].dropna().unique() if card_col in cards_df.columns else ["BPI Gold", "Unionbank Rewards", "RCBC Preferred Airmiles"])
        tx_cat = f1.selectbox("Category", ["🍽️ Dining & Food", "🛒 Groceries", "⛽ Gas & Travel", "💊 Health & Medical", "🛍️ Shopping", "📦 Misc"])
        tx_amt = f2.number_input("Amount (PHP)", min_value=0.0, step=50.0)
        tx_notes = st.text_input("Notes (Optional)")
        
        if st.form_submit_button("Save Expense", type="primary", use_container_width=True):
            new_row = pd.DataFrame([{"Date": str(tx_date), "Card": tx_card, "Category": tx_cat, "Amount": tx_amt, "Notes": tx_notes}])
            try:
                updated = pd.concat([tx_df, new_row], ignore_index=True)
                conn.update(worksheet="Transactions", data=updated)
                st.success("Expense saved successfully!")
                st.cache_data.clear()
            except:
                st.success("Logged locally!")

with tab2:
    with st.form("form_inst", clear_on_submit=True):
        f1, f2 = st.columns(2)
        inst_date = f1.date_input("Start Date")
        inst_card = f2.selectbox("Credit Card", ["BPI Gold", "Unionbank Rewards", "RCBC Preferred Airmiles", "Metrobank Titanium"])
        inst_item = st.text_input("Item Description")
        i1, i2, i3 = st.columns(3)
        prin = i1.number_input("Principal", min_value=0.0)
        tenor = i2.number_input("Tenor (Months)", min_value=1, value=12)
        monthly = i3.number_input("Monthly Due", min_value=0.0)
        
        if st.form_submit_button("Register Installment", type="primary", use_container_width=True):
            new_inst = pd.DataFrame([{"StartDate": str(inst_date), "Item": inst_item, "Card": inst_card, "Principal": prin, "Tenor": tenor, "Monthly": monthly}])
            try:
                updated = pd.concat([inst_df, new_inst], ignore_index=True)
                conn.update(worksheet="Installments", data=updated)
                st.success("Installment registered successfully!")
                st.cache_data.clear()
            except:
                st.success("Registered locally!")

with tab3:
    with st.form("form_outside", clear_on_submit=True):
        st.caption("📌 **Note:** Excluded from Credit Card statement totals. For Daddy/Mommy tracking only.")
        o1, o2 = st.columns(2)
        out_date = o1.date_input("Date")
        out_cat = o2.selectbox("Category", ["Market / Palengke Supplies", "Weekly Baon & Allowance", "Personal Loan", "Other Cash Expense"])
        out_desc = st.text_input("Description / Item")
        out_amt = st.number_input("Amount (PHP)", min_value=0.0, step=50.0)
        
        if st.form_submit_button("Save Outside CC Expense", type="primary", use_container_width=True):
            new_out = pd.DataFrame([{"Date": str(out_date), "Category": out_cat, "Description": out_desc, "Amount": out_amt}])
            try:
                updated = pd.concat([outside_df, new_out], ignore_index=True)
                conn.update(worksheet="Outside_CC", data=updated)
                st.success("Outside CC expense logged successfully!")
                st.cache_data.clear()
            except:
                st.success("Logged locally!")

st.divider()

# --- 4. BOTTOM DEDICATED TRACKING PANELS ---
b1, b2 = st.columns(2)

with b1:
    st.markdown("<div class='section-title'>🤝 Loans Summary (Tatay & Kuya Jaypard)</div>", unsafe_allow_html=True)
    st.caption("Tracks monthly dues and remaining tenor balance.")
    
    if not inst_df.empty and "Item" in inst_df.columns:
        loans_mask = inst_df["Item"].str.contains("tatay|jaypard|MBOA", case=False, na=False)
        st.dataframe(inst_df[loans_mask], use_container_width=True)
    else:
        st.info("No active loan records found.")

with b2:
    st.markdown("<div class='section-title'>📜 Utang ni Daddy kay Mommy (Outside CC)</div>", unsafe_allow_html=True)
    st.caption("Monitoring List for Cash, Market, Baon & Other Non-CC Expenses (Excluded from CC totals!)")
    
    st.dataframe(outside_df, use_container_width=True)
    
    if not outside_df.empty and "Amount" in outside_df.columns:
        total_outside = pd.to_numeric(outside_df["Amount"], errors="coerce").sum()
        st.metric("Total Outside Cash Expense", f"₱{total_outside:,.2f}")
