import networkx as nx
from pyvis.network import Network
import pandas as pd
import tempfile
import os

def generate_cluster_map(df, center_address):
    """
    Generates a Bubblemaps-style interactive graph.
    """
    G = nx.Graph()
    
    G.add_node(center_address, title=f"TARGET\n{center_address}", color="#FF4B4B", size=40, label="TARGET")
    
    grouped = df.groupby('sender')['amount'].sum().reset_index()
    
    for _, row in grouped.iterrows():
        sender = row['sender']
        total_vol = row['amount']
        
        if sender != center_address:
            
            if total_vol > 1000:
                color = "#FFA500" 
                size = 20
                label = "Bot/Whale"
            else:
                color = "#97C2FC" 
                size = 10
                label = None
            
            
            G.add_node(sender, title=f"{sender}\nVol: {total_vol}", color=color, size=size, label=label)
            
            width = 3 if total_vol > 1000 else 1
            G.add_edge(center_address, sender, weight=total_vol, color="rgba(255, 255, 255, 0.2)", width=width)

    net = Network(height="600px", width="100%", bgcolor="#0E1117", font_color="white")
    net.from_nx(G)
    net.force_atlas_2based(
        gravity=-100,      
        central_gravity=0.05, 
        spring_length=200, 
        spring_strength=0.05,
        damping=0.9
    )
    
    try:
        path = os.path.join(tempfile.gettempdir(), "graph.html")
        net.save_graph(path)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<div>Error: {e}</div>"
    """
    Generates a Bubblemaps-style interactive graph.
    Nodes = Wallets (Size based on volume)
    Edges = Transactions (Thickness based on amount)
    """
    G = nx.Graph()

    G.add_node(center_address, title=center_address, color="#FF4B4B", size=30, label="TARGET")
    
    for _, row in df.iterrows():
        if row['sender'] != center_address:
            sender = row['sender']
            amount = row['amount']
        
            color = "#FFA500" if amount > 5000 else "#97C2FC"
            size = 15 if amount > 5000 else 8
            
            G.add_node(sender, title=f"{sender}\nVol: {amount}", color=color, size=size)
            G.add_edge(center_address, sender, weight=amount, color="rgba(200, 200, 200, 0.5)")

    net = Network(height="600px", width="100%", bgcolor="#0E1117", font_color="white")
    net.from_nx(G)
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0)
    
    try:
        path = os.path.join(tempfile.gettempdir(), "graph.html")
        net.save_graph(path)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<div>Error generating graph: {e}</div>"