import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_agent.backend import AnalyticsAgent 
from analytics.graph_algo import SuspiciousBehaviorDetector 

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Sauron Eye", layout="wide")
st.title("Sauron Eye (Babylon Chain Analytics)")
# --- CUSTOM CSS FOR "SAURON EYE" THEME ---
st.markdown("""
    <style>
    /* Main Background (Optional: Streamlit handles dark mode, but this enforces it) */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Bigger Header Text */
    h1 {
        font-size: 3.5rem !important;
        color: #FF4B4B !important; /* Sauron Red/Orange */
        text-align: center;
        text-shadow: 0px 0px 10px rgba(255, 75, 75, 0.5);
    }
    
    h2, h3 {
        font-size: 2rem !important;
        border-bottom: 2px solid #333;
        padding-bottom: 10px;
    }
    
    /* Bigger Metric Numbers */
    div[data-testid="stMetricValue"] {
        font-size: 3rem !important;
        color: #FFA500 !important; /* Gold/Fire */
    }
    
    /* Bigger Body Text & Table Text */
    p, .stDataFrame, div[data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem !important;
    }
    
    /* Warning/Error Boxes Bigger */
    .stAlert {
        font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    return create_engine(db_url)

engine = get_db_connection()

@st.cache_data(ttl=60) 
def load_data():
    """Load recent transactions for the Overview"""
    query = "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 2000"
    df = pd.read_sql(query, engine)
    
    def get_label(amount):
        if amount > 4000: return "🐋 Whale"
        if amount < 10: return "🦐 Shrimp"
        return "👤 User"
    
    df['Risk Label'] = df['amount'].apply(get_label)
    return df

tab1, tab2, tab3 = st.tabs(["Network Overview", "Wallet Inspector", "AI Analyst"])

with tab1:
    df = load_data()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", len(df))
    col1.metric("Total Volume", f"{df['amount'].sum():,} BBN")
    col2.metric("Active Addresses", df['sender'].nunique())
    col3.metric("Whale Count", len(df[df['Risk Label'] == "🐋 Whale"]))

    st.subheader("Transaction History")
    if not df.empty:
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_vol = df.groupby('date')['amount'].sum().reset_index()
        fig = px.bar(daily_vol, x='date', y='amount', title="Daily Transaction Volume")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Live Feed")
    st.dataframe(df[['timestamp', 'tx_hash', 'sender', 'amount', 'Risk Label']].head(20))

with tab2:
    st.header("🔎 Address Investigation")
    
    all_senders = df['sender'].unique().tolist()
    target_address = st.selectbox("Select or Type Address to Inspect:", options=all_senders)
    
    if target_address:
        wallet_df = df[df['sender'] == target_address]
        if not wallet_df.empty:
            detector = SuspiciousBehaviorDetector()
            for _, row in wallet_df.iterrows():
                detector.add_transaction(row['sender'], "simulated_receiver", row['amount'], row['timestamp'])
            
            fan_outs = detector.detect_fan_out(min_recipients=5) 
            
            st.markdown(f"### Profile: `{target_address}`")
            
            w_col1, w_col2, w_col3 = st.columns(3)
            total_sent = wallet_df['amount'].sum()
            w_col1.metric("Tx Count", len(wallet_df))
            w_col2.metric("Total Volume", f"{total_sent:,} BBN")
            
            risk_score = 0
            tags = []
            
            if len(fan_outs) > 0: 
                risk_score += 50
                tags.append("Fan-Out Behavior")
            if total_sent > 10000: 
                risk_score += 20
                tags.append(" Whale")
            
            w_col3.metric("Risk Score", f"{risk_score}/100", delta_color="inverse" if risk_score > 0 else "normal")
            
            st.write(" **Compliance Tags:** " + (", ".join(tags) if tags else " Clean"))
            
            if fan_outs:
                st.error(f" Detected {len(fan_outs)} suspicious 'Fan Out' events (sending to many addresses quickly).")
                st.write(fan_outs)
            
            st.divider()
            st.caption("Recent Activity")
            st.dataframe(wallet_df)

            st.divider()
            st.subheader("AI Forensic Report")
            
            if st.button(f"Analyze {target_address[:8]}... with AI"):
                if not api_key:
                    st.error("Need OpenAI Key in .env")
                else:
                    with st.spinner("Consulting forensic database..."):
                        agent = AnalyticsAgent(api_key=api_key)
                        try:
                            analysis = agent.analyze_wallet_deep_dive(target_address)
                            st.markdown("Investigator's Findings")
                            st.info(analysis)
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")

        else:
            st.warning("No transactions found for this address.")

with tab3:
    st.header("Ask the Data")
    
    agent = AnalyticsAgent(api_key=api_key)

    query = st.chat_input("Ask a question about the blockchain data...")
    
    if query:
        with st.chat_message("user"):
            st.write(query)
            
        with st.chat_message("assistant"):
            if not api_key:
                st.error("Please add OPENAI_API_KEY to .env to use this feature.")
            else:
                with st.spinner("Analyzing chain data..."):
                    try:
                        response = agent.ask(query)
                        st.write(response)
                    except Exception as e:
                        st.error(f"Error: {e}")