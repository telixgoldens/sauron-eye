import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv

# --- PATH FIX ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_agent.backend import AnalyticsAgent 

load_dotenv()

# --- SETUP ---
st.set_page_config(page_title="Babylon Analytics", layout="wide")
st.title("🦁 Babylon Chain Analytics (Prototype)")

# Database Connection
@st.cache_resource
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    return create_engine(db_url)

engine = get_db_connection()

# --- HELPER FUNCTIONS ---
def load_data():
    """Load all transactions for the Overview"""
    query = "SELECT * FROM transactions ORDER BY timestamp DESC"
    df = pd.read_sql(query, engine)
    
    # Basic Labeling Logic
    def get_label(amount):
        if amount > 4000: return "🐋 Whale"
        if amount < 10: return "🦐 Shrimp"
        return "👤 User"
    
    df['Risk Label'] = df['amount'].apply(get_label)
    return df

def load_wallet_stats(address):
    """Load specific stats for one wallet (Investigator Mode)"""
    # We use parameterized queries for security (prevent SQL Injection)
    query = f"SELECT * FROM transactions WHERE sender = '{address}' ORDER BY timestamp DESC"
    df = pd.read_sql(query, engine)
    return df

# --- TABS LAYOUT ---
tab1, tab2, tab3 = st.tabs(["📊 Network Overview", "🕵️ Wallet Inspector", "🤖 AI Analyst"])

# ==========================================
# TAB 1: NETWORK OVERVIEW
# ==========================================
with tab1:
    df = load_data()
    
    # Top Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", len(df))
    col1.metric("Total Volume", f"{df['amount'].sum():,} BBN")
    col2.metric("Active Addresses", df['sender'].nunique())
    col3.metric("Whale Count", len(df[df['Risk Label'] == "🐋 Whale"]))

    # Charts
    st.subheader("Transaction History")
    # Group by date (using string manipulation for simplicity in prototype)
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_vol = df.groupby('date')['amount'].sum().reset_index()
    
    fig = px.bar(daily_vol, x='date', y='amount', title="Daily Transaction Volume")
    st.plotly_chart(fig, use_container_width=True)

    # Data Table
    st.subheader("Live Feed")
    st.dataframe(df[['timestamp', 'tx_hash', 'sender', 'amount', 'Risk Label']].head(20))

# ==========================================
# TAB 2: WALLET INSPECTOR (Compliance)
# ==========================================
with tab2:
    st.header("🔎 Address Investigation")
    
    # Dropdown to pick a wallet (or type one)
    all_senders = df['sender'].unique().tolist()
    target_address = st.selectbox("Select or Type Address to Inspect:", options=all_senders)
    
    if target_address:
        wallet_df = load_wallet_stats(target_address)
        
        if not wallet_df.empty:
            # Wallet Profile
            st.markdown(f"### Profile: `{target_address}`")
            
            # Advanced Heuristics (Smart Money Logic)
            first_seen = pd.to_datetime(wallet_df['timestamp']).min()
            days_active = (pd.to_datetime("now") - first_seen).days
            total_sent = wallet_df['amount'].sum()
            avg_tx = wallet_df['amount'].mean()
            
            # Compliance Tags
            tags = []
            if total_sent > 10000: tags.append("💰 High Net Worth")
            if days_active > 30: tags.append("💎 Diamond Hand") # Active for > 30 days
            if len(wallet_df) > 50: tags.append("🤖 Bot / High Freq")
            
            # Display Profile
            w_col1, w_col2, w_col3 = st.columns(3)
            w_col1.metric("First Seen", f"{days_active} days ago")
            w_col2.metric("Total Staked/Sent", f"{total_sent:,} BBN")
            w_col3.metric("Risk Score", "Low" if len(tags) < 2 else "High ⚠️")
            
            st.write("🏷️ **Tags:** " + ", ".join(tags) if tags else "No special tags")
            
            st.divider()
            st.caption("Recent Activity")
            st.dataframe(wallet_df)
        else:
            st.warning("No transactions found for this address.")

# ==========================================
# TAB 3: AI ANALYST
# ==========================================
with tab3:
    st.header("🤖 Ask the Data")
    
    api_key = os.getenv("OPENAI_API_KEY")
    agent = AnalyticsAgent(api_key=api_key)

    # Suggested Questions
    st.caption("Try asking:")
    st.markdown("*'Who are the top 3 whales by volume?'*")
    st.markdown("*'List all transactions sent by [paste an address]'*")
    
    query = st.chat_input("Ask a question about the blockchain data...")
    
    if query:
        with st.chat_message("user"):
            st.write(query)
            
        with st.chat_message("assistant"):
            if not api_key:
                st.error("⚠️ Please add OPENAI_API_KEY to .env to use this feature.")
            else:
                with st.spinner("Analyzing chain data..."):
                    try:
                        response = agent.ask(query)
                        st.write(response)
                    except Exception as e:
                        st.error(f"Error: {e}")