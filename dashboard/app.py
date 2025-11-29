import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import streamlit.components.v1 as components 
from dotenv import load_dotenv
from PIL import Image
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_agent.backend import AnalyticsAgent 
from analytics.graph_algo import SuspiciousBehaviorDetector 
from analytics.visuals import generate_cluster_map 

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

logo_path = "dashboard/assets/sauroneye.png" 
try:
    logo_img = Image.open(logo_path)
except FileNotFoundError:
    logo_img = "👁️" 

st.set_page_config(
    page_title="Sauron Eye", 
    layout="wide", 
    page_icon=logo_img 
)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* Title Styling */
    .title-text {
        font-size: 2rem !important;
        color: #FF4B4B !important; 
        text-shadow: 0px 0px 15px rgba(255, 75, 75, 0.4); 
        font-weight: 750;
        margin-bottom: 0px;
    }
    
    div[data-testid="stMetricValue"] { font-size: 2.5rem !important; color: #FFA500 !important; }
    iframe { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 15]) 
with col1:
    st.image(logo_img, width=100) 
with col2:
    st.markdown('<h2 class="title-text">SAURON EYE</h2>', unsafe_allow_html=True)

st.caption("The All-Seeing Lens for Babylon Chain")
st.divider()

with st.sidebar:
    st.header("Babylon Live")
    twitter_embed = """
    <a class="twitter-timeline" data-width="300" data-height="600" data-theme="dark" href="https://twitter.com/babylonlabs_io?ref_src=twsrc%5Etfw">Tweets by babylonlabs_io</a> 
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    """
    components.html(twitter_embed, height=600, scrolling=True)
    st.divider()
    st.header("Admin (Demo Mode)")
    if st.button("RESET & SEED DATA"):
        with st.spinner("Planting evidence..."):
            try:
                from seed_crime_data import run_seed 
                
                run_seed()
                st.success("Data Reset! Reload the page.")
                st.cache_data.clear() 
            except Exception as e:
                st.error(f"Seeding failed: {e}")

@st.cache_resource
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    return create_engine(db_url)

engine = get_db_connection()

@st.cache_data(ttl=60)
def load_data():
    try:
        query = "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 2000"
        df = pd.read_sql(query, engine)
        
        df['Risk Label'] = df['amount'].apply(lambda x: "🐋 Whale" if x > 4000 else ("🦐 Shrimp" if x < 10 else "👤 User"))
        
        if 'tx_type' not in df.columns:
            df['tx_type'] = 'Unknown'
        else:
            df['tx_type'] = df['tx_type'].fillna('Unknown')
            
        return df
    except Exception:
        return pd.DataFrame(columns=['sender', 'amount', 'timestamp', 'tx_hash', 'tx_type', 'details', 'Risk Label'])

tab1, tab2, tab3, tab4 = st.tabs(["Network Overview", "Cluster Map (Inspector)", "AI Analyst", "⚡ Protocol Activity"])


with tab1:
    df = load_data()
    
    if df.empty:
        st.warning(" Database is empty or not initialized.")
        st.info("Please go to the **Sidebar**, scroll down to **Admin**, and click **' RESET & SEED DATA'** to initialize the database.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", len(df))
        col1.metric("Total Volume", f"{df['amount'].sum():,} BBN")
        col3.metric("Whales Detected", len(df[df['Risk Label'] == "🐋 Whale"]))

        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_vol = df.groupby('date')['amount'].sum().reset_index()
        fig = px.bar(daily_vol, x='date', y='amount', title="Daily Transaction Volume", color_discrete_sequence=['#FF4B4B'])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Live Feed")
        st.dataframe(df[['timestamp', 'tx_hash', 'sender', 'amount', 'Risk Label']].head(10), use_container_width=True)
        
        st.subheader("Transaction Types")
        if 'tx_type' in df.columns:
            type_counts = df['tx_type'].value_counts()
            st.bar_chart(type_counts)


with tab2:
    st.header("Wallet Cluster Inspector")
    
    if not df.empty and 'sender' in df.columns:
        all_senders = df['sender'].unique().tolist()
    else:
        all_senders = []

    target_address = st.selectbox("Select Target Address:", options=all_senders)
    
    if target_address:
        col_map, col_stats = st.columns([3, 1])
        
        cluster_df = df.head(500)
        
        with col_map:
            if not cluster_df.empty:
                html_map = generate_cluster_map(cluster_df, target_address)
                components.html(html_map, height=600)
            else:
                st.warning("No connections found for this address.")

        with col_stats:
            st.markdown("### Risk Profile")
            
            detector = SuspiciousBehaviorDetector()
            filtered_df = df[df['sender'] == target_address] 
            for _, row in filtered_df.iterrows():
                detector.add_transaction(row['sender'], "unknown", row['amount'], row['timestamp'])
            
            fan_outs = detector.detect_fan_out(min_recipients=1)
            
            if len(fan_outs) > 0:
                st.error("Fan-Out Detected")
                st.metric("Risk Score", "90/100")
            else:
                st.success("Normal Behavior")
                st.metric("Risk Score", "10/100")
                
            st.divider()
            
            if st.button("✨ AI Deep Analysis"):
                if not api_key:
                    st.error("No API Key")
                else:
                    with st.spinner("Profiling..."):
                        agent = AnalyticsAgent(api_key=api_key)
                        analysis = agent.analyze_wallet_deep_dive(target_address)
                        st.info(analysis)

with tab3:
    st.header("Ask Sauron")
    agent = AnalyticsAgent(api_key=api_key)
    query = st.chat_input("Ask a question...")
    
    if query:
        with st.chat_message("user"): st.write(query)
        with st.chat_message("assistant"):
            if not api_key: st.error("No API Key")
            else:
                with st.spinner("Thinking..."):
                    st.write(agent.ask(query))


with tab4:
    st.header("⚡ Protocol Activity Breakdown")
    
    if not df.empty and 'tx_type' in df.columns:
        type_counts = df['tx_type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            fig_pie = px.pie(type_counts, values='Count', names='Type', title="Transaction Distribution", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie)
            
        with col_b:
            st.markdown("### Key Metrics")
        
            btc_stakes = df[df['tx_type'] == "BTC_Stake"]
            votes = df[df['tx_type'] == "Governance_Vote"]
            delegations = df[df['tx_type'] == "Delegate"]
            
            st.metric("BTC Delegations (Staking)", len(btc_stakes))
            st.metric("Governance Votes", len(votes))
            st.metric("Validator Delegations", len(delegations))

        st.subheader("Deep Dive Log")
        st.caption("Inspect raw metadata (BTC PKs, Validator addresses, etc.)")
        
        display_cols = ['timestamp', 'tx_hash', 'tx_type', 'details']
        final_cols = [c for c in display_cols if c in df.columns]
        
        st.dataframe(df[final_cols], use_container_width=True)
    else:
        st.info("No transaction type data available yet. Run the updated indexer to capture types.")