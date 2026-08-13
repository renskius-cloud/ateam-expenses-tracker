import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ATeam Expenses Tracker",
    page_icon="💳",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💳 ATeam Credit Card & Expenses Tracker")

# --- CONNECT TO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    cards_df = conn.read(worksheet="Cards")
    tx_df = conn.read(worksheet="Transactions")
    inst_df = conn.read(worksheet="Installments")
    try:
        outside_df = conn.read(worksheet="Outside_CC")
    except:
        outside_df = pd.DataFrame(columns=["Date", "Category", "Description", "Amount"])
    return cards_df, tx_df, inst_df, outside_df

cards_df, tx_df, inst_df, outside_df = load_data()

# --- 1. TOP SECTION: BILLING SELECTOR ---
col_lbl, col_m, col_y = st.columns([2, 2, 2])
with col_lbl:
    st.subheader("📅 Select Billing Period")

months_list = ["January", "February", "March", "April", "May", "June", 
               "July", "August", "September", "October", "November", "December"]

with col_m:
    selected_month_str = st.selectbox("Month", months_list, index=7)

with col_y:
    selected_year = st.selectbox("Year", [2025, 2026, 2027], index=1)

# Toggle state for Display #2
if "show_display_2" not in st.session_state:
    st.session_state.show_display_2 = False

# Summary Cards / Filter Triggers
m1, m2 = st.columns(2)
with m1:
    if st.button(f"🗓️ Due for {selected_month_str} 15th — Click to Toggle Breakdown", type="primary"):
        st.session_state.show_display_2 = not st.session_state.show_display_2
with m2:
    if st.button(f"🗓️ Due for {selected_month_str} 30th — Click to Toggle Breakdown", type="primary"):
        st.session_state.show_display_2 = not st.session_state.show_display_2

st.divider()

# --- DISPLAY #2 (CLICKABLE EXPANDABLE BREAKDOWN) ---
if st.session_state.show_display_2:
    st.info(f"📋 **Display #2:** Statement Breakdown for **{selected_month_str} {selected_year}**")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("##### 🛒 Current Period Transactions")
        st.dataframe(tx_df, use_container_width=True)
    with col_d2:
        st.markdown("##### 🔄 Active Installments Breakdown")
        st.dataframe(inst_df, use_container_width=True)
    st.divider()

# --- 2. MAIN CC DASHBOARD & STATUS ---
st.subheader("📊 Credit Card Dashboard & Status")
st.dataframe(cards_df, use_container_width=True)

# --- ENTRY FORMS ---
st.subheader("📝 Quick Log Entry")
tab1, tab2, tab3 = st.tabs(["➕ Log CC Daily Expense", "🔄 Register CC Installment", "🛒 Log Outside CC (Utang ni Daddy)"])

with tab1:
    with st.form("form_cc_tx", clear_on_submit=True):
        c1, c2 = st.columns(2)
        f_date = c1.date_input("Purchase Date")
        f_card = c2.selectbox("Credit Card", cards_df["Card"].dropna().unique() if not cards_df.empty else ["No Cards"])
        f_cat = c1.selectbox("Category", ["🛒 Groceries", "🍽️ Dining", "💡 Utilities", "🛍️ Shopping", "📦 Misc"])
        f_amt = c2.number_input("Amount (PHP)", min_value=0.0, step=50.0)
        f_notes = st.text_input("Notes")
        if st.form_submit_button("Save Daily Expense"):
            new_row = pd.DataFrame([{"Date": str(f_date), "Card": f_card, "Category": f_cat, "Amount": f_amt, "Notes": f_notes}])
            updated_tx = pd.concat([tx_df, new_row], ignore_index=True)
            conn.update(worksheet="Transactions", data=updated_tx)
            st.success("Successfully saved daily expense!")
            st.cache_data.clear()

with tab2:
    with st.form("form_cc_inst", clear_on_submit=True):
        c1, c2 = st.columns(2)
        fi_date = c1.date_input("Start Date")
        fi_card = c2.selectbox("Credit Card", cards_df["Card"].dropna().unique() if not cards_df.empty else ["No Cards"])
        fi_item = st.text_input("Item Description")
        i1, i2, i3 = st.columns(3)
        fi_prin = i1.number_input("Total Principal", min_value=0.0)
        fi_tenor = i2.number_input("Tenor (Months)", min_value=1, value=12)
        fi_monthly = i3.number_input("Monthly Due", min_value=0.0)
        if st.form_submit_button("Register Installment"):
            new_inst = pd.DataFrame([{"StartDate": str(fi_date), "Item": fi_item, "Card": fi_card, "Principal": fi_prin, "Tenor": fi_tenor, "Monthly": fi_monthly}])
            updated_inst = pd.concat([inst_df, new_inst], ignore_index=True)
            conn.update(worksheet="Installments", data=updated_inst)
            st.success("Successfully registered installment!")
            st.cache_data.clear()

with tab3:
    with st.form("form_outside_cc", clear_on_submit=True):
        st.caption("📌 **Note:** Excluded from Credit Card statement totals. For Daddy/Mommy tracking only.")
        o1, o2 = st.columns(2)
        fo_date = o1.date_input("Date")
        fo_cat = o2.selectbox("Category", ["Market / Ulam", "Baon", "Personal Loan", "Other Cash Expense"])
        fo_desc = st.text_input("Description / Item")
        fo_amt = st.number_input("Amount (PHP)", min_value=0.0, step=50.0)
        if st.form_submit_button("Log Outside CC Expense"):
            new_out = pd.DataFrame([{"Date": str(fo_date), "Category": fo_cat, "Description": fo_desc, "Amount": fo_amt}])
            updated_out = pd.concat([outside_df, new_out], ignore_index=True)
            conn.update(worksheet="Outside_CC", data=updated_out)
            st.success("Successfully logged outside expense!")
            st.cache_data.clear()

st.divider()

# --- 3. BOTTOM TRACKING PANELS ---
b_left, b_right = st.columns(2)

with b_left:
    st.subheader("🤝 Loans Summary (Tatay & Kuya Jaypard)")
    if not inst_df.empty and "Item" in inst_df.columns:
        loans_mask = inst_df["Item"].str.contains("Tatay|Jaypard|MBOA", case=False, na=False)
        st.dataframe(inst_df[loans_mask], use_container_width=True)
    else:
        st.info("No active loan records found.")

with b_right:
    st.subheader("📜 Utang ni Daddy kay Mommy (Outside CC)")
    st.caption("Monitoring List for Cash, Market, Baon & Other Non-CC Expenses")
    st.dataframe(outside_df, use_container_width=True)
    
    if not outside_df.empty and "Amount" in outside_df.columns:
        total_utang = pd.to_numeric(outside_df["Amount"], errors="coerce").sum()
        st.metric("Total Outside Cash Expenses", f"₱{total_utang:,.2f}")
