import sys
import os
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components 
from sqlalchemy import create_engine
from dotenv import load_dotenv
from PIL import Image

# --- PATH SETUP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_agent.backend import AnalyticsAgent 
from analytics.graph_algo import SuspiciousBehaviorDetector 
from analytics.visuals import generate_cluster_map 

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# --- LOAD LOGO ---
logo_path = "dashboard/assets/sauroneye.png" 
try:
    logo_img = Image.open(logo_path)
except:
    logo_img = "👁️" 

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sauron Eye", layout="wide", page_icon=logo_img)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { color: #FF4B4B !important; }
    div[data-testid="stMetricValue"] { color: #FFA500 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    return create_engine(db_url)

try:
    engine = get_db_connection()
except:
    st.error("❌ Database connection failed. Check Railway variables.")
    st.stop()

# --- DATA LOADER ---
@st.cache_data(ttl=60)
def load_data():
    try:
        query = "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 2000"
        df = pd.read_sql(query, engine)
        
        # Add Columns if missing
        if 'amount' in df.columns:
            df['Risk Label'] = df['amount'].apply(lambda x: "🐋 Whale" if x > 4000 else ("🦐 Shrimp" if x < 10 else "👤 User"))
        
        if 'tx_type' not in df.columns: df['tx_type'] = 'Unknown'
        else: df['tx_type'] = df['tx_type'].fillna('Unknown')
        
        return df
    except:
        # Return empty structure to prevent crashes
        return pd.DataFrame(columns=['sender', 'amount', 'timestamp', 'tx_hash', 'tx_type', 'details', 'Risk Label'])

# --- SIDEBAR NAVIGATION (THE FIX) ---
with st.sidebar:
    st.write("🔴 **VERSION 2.0 (LIVE)**") # <--- Add this line
    st.image(logo_img, use_container_width=True)
    st.image(logo_img, use_container_width=True)
    
    # NAVIGATION MENU
    selected_page = st.radio("Navigate", 
        ["📊 Network Overview", "🕸️ Cluster Inspector", "⚡ Protocol Activity", "🤖 AI Analyst"]
    )
    
    st.divider()
    st.caption("Babylon Live Feed")
    components.html("""<a class="twitter-timeline" data-height="300" data-theme="dark" href="https://twitter.com/babylonlabs_io?ref_src=twsrc%5Etfw">Tweets</a><script async src="https://platform.twitter.com/widgets.js"></script>""", height=300)
    
    st.divider()
    if st.button("🔴 RESET & SEED DATA"):
        try:
            from seed_crime_data import run_seed 
            run_seed()
            st.cache_data.clear()
            st.success("Reset Done!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- MAIN PAGE HEADER ---
c1, c2 = st.columns([1, 15])
with c1: st.image(logo_img, width=60)
with c2: st.markdown("# SAURON EYE")
st.caption("The All-Seeing Lens for Babylon Chain")
st.divider()

# --- PAGE LOGIC (MUTUALLY EXCLUSIVE) ---
df = load_data()

if selected_page == "📊 Network Overview":
    st.subheader("Network Status")
    if df.empty:
        st.warning("Database empty. Use the Sidebar button to Seed Data.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Transactions", len(df))
        m2.metric("Volume", f"{df['amount'].sum():,} BBN")
        m3.metric("Whales", len(df[df['Risk Label'] == "🐋 Whale"]))
        
        st.dataframe(df.head(15), use_container_width=True)

elif selected_page == "🕸️ Cluster Inspector":
    st.subheader("Wallet Forensics")
    if df.empty:
        st.warning("No data available.")
    else:
        senders = df['sender'].unique().tolist() if 'sender' in df.columns else []
        target = st.selectbox("Select Suspect:", senders)
        
        if target:
            c_map, c_stats = st.columns([3, 1])
            with c_map:
                # Limit to 1000 to catch the funding transaction
                html = generate_cluster_map(df.head(1000), target)
                components.html(html, height=600)
            with c_stats:
                st.write(f"**Target:** `{target[:10]}...`")
                if st.button("AI Deep Analysis"):
                    if not api_key: st.error("No API Key")
                    else:
                        with st.spinner("Analyzing..."):
                            agent = AnalyticsAgent(api_key=api_key)
                            st.info(agent.analyze_wallet_deep_dive(target))

elif selected_page == "⚡ Protocol Activity":
    st.subheader("Protocol Events")
    if not df.empty and 'tx_type' in df.columns:
        counts = df['tx_type'].value_counts()
        c1, c2 = st.columns(2)
        c1.bar_chart(counts)
        c2.dataframe(df[['timestamp', 'tx_type', 'sender']].head(20), use_container_width=True)
    else:
        st.info("No protocol data found.")

elif selected_page == "🤖 AI Analyst":
    st.subheader("Ask Sauron")
    q = st.chat_input("Ask about the chain...")
    if q:
        st.chat_message("user").write(q)
        if api_key:
            agent = AnalyticsAgent(api_key=api_key)
            st.chat_message("assistant").write(agent.ask(q))
        else:
            st.error("No API Key found.")