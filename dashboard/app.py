import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px  
import streamlit.components.v1 as components 
from sqlalchemy import create_engine
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
except:
    logo_img = "👁️" 


st.set_page_config(page_title="Sauron Eye", layout="wide", page_icon=logo_img)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { color: #FF4B4B !important; }
    div[data-testid="stMetricValue"] { color: #FFA500 !important; }
    /* Force iframes to clear when hidden */
    iframe { display: block; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    return create_engine(db_url)

try:
    engine = get_db_connection()
except:
    st.error("Database Error.")
    st.stop()

@st.cache_data(ttl=60)
def load_data():
    try:
        query = "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 2000"
        df = pd.read_sql(query, engine)
        if 'amount' in df.columns:
            df['Risk Label'] = df['amount'].apply(lambda x: "🐋 Whale" if x > 4000 else ("🦐 Shrimp" if x < 10 else "👤 User"))
        if 'tx_type' not in df.columns: df['tx_type'] = 'Unknown'
        else: df['tx_type'] = df['tx_type'].fillna('Unknown')
        return df
    except:
        return pd.DataFrame(columns=['sender', 'amount', 'timestamp', 'tx_hash', 'tx_type', 'details', 'Risk Label'])

with st.sidebar:
    st.image(logo_img, use_container_width=True)
    selected_page = st.radio("Navigate", 
        ["Network Overview", " Cluster Inspector", "⚡ Protocol Activity", "AI Analyst"]
    )
    st.divider()
    components.html("""<a class="twitter-timeline" data-height="300" data-theme="dark" href="https://twitter.com/babylonlabs_io?ref_src=twsrc%5Etfw">Tweets</a><script async src="https://platform.twitter.com/widgets.js"></script>""", height=300)
    
    st.divider()
    if st.button("RESET & SEED DATA"):
        try:
            from seed_crime_data import run_seed 
            run_seed()
            st.cache_data.clear()
            st.success("Reset Done!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

c1, c2 = st.columns([1, 15])
with c1: st.image(logo_img, width=60)
with c2: st.markdown("# SAURON EYE")
st.caption("The All-Seeing Lens for Babylon Chain")
st.divider()

df = load_data()

if selected_page == "Network Overview":
    st.subheader("Network Status")
    if not df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Transactions", len(df))
        m2.metric("Volume", f"{df['amount'].sum():,} BBN")
        m3.metric("Whales", len(df[df['Risk Label'] == "🐋 Whale"]))
        st.dataframe(df.head(15), use_container_width=True)
    else:
        st.warning("No Data.")

elif selected_page == "Cluster Inspector":
    st.subheader("Wallet Forensics")
    if not df.empty:
        senders = df['sender'].unique().tolist() if 'sender' in df.columns else []
        target = st.selectbox("Select Suspect:", senders)
        
        if target:
            c_map, c_stats = st.columns([3, 1])
            with c_map:
                html = generate_cluster_map(df.head(1000), target)
                components.html(html, height=600, scrolling=True) 
            with c_stats:
                st.write(f"**Target:** `{target[:10]}...`")
                if st.button("AI Deep Analysis"):
                    if api_key:
                        agent = AnalyticsAgent(api_key=api_key)
                        with st.spinner("Analyzing..."):
                            st.info(agent.analyze_wallet_deep_dive(target))
                    else:
                        st.error("No API Key")
    else:
        st.warning("No Data.")

elif selected_page == "⚡ Protocol Activity":
    st.subheader("Protocol Events")
    
    if not df.empty and 'tx_type' in df.columns:
        type_counts = df['tx_type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            fig_pie = px.pie(
                type_counts, 
                values='Count', 
                names='Type', 
                title="Transaction Distribution", 
                hole=0.4, 
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_b:
            st.markdown("### Key Metrics")
            btc_stakes = len(df[df['tx_type'] == "BTC_Stake"])
            votes = len(df[df['tx_type'] == "Governance_Vote"])
            transfers = len(df[df['tx_type'] == "Transfer"])
            
            st.metric("BTC Delegations", btc_stakes)
            st.metric("Governance Votes", votes)
            st.metric("Transfers", transfers)

        st.divider()
        st.subheader(" Live Event Log")
        st.dataframe(df[['timestamp', 'tx_type', 'sender']].head(20), use_container_width=True)
    else:
        st.info("No protocol data found.")

elif selected_page == "AI Analyst":
    st.subheader("Ask Sauron")
    q = st.chat_input("Ask about the chain...")
    if q:
        st.chat_message("user").write(q)
        if api_key:
            agent = AnalyticsAgent(api_key=api_key)
            st.chat_message("assistant").write(agent.ask(q))
        else:
            st.error("No API Key.")