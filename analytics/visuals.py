import networkx as nx
from pyvis.network import Network
import pandas as pd
import tempfile
import os

def generate_cluster_map(df, center_address):
    """
    Generates a Bubblemaps-style interactive graph.
    Nodes are CLICKABLE -> Opens Babylon Explorer.
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
            
            title_text = f"Address: {sender}\nVolume: {total_vol} BBN\n(Click to view on Explorer)"
            
            G.add_node(sender, title=title_text, color=color, size=size, label=label)
            
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
    
    js_click_event = """
    <script type="text/javascript">
    network.on("click", function (params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            // Open Babylon Explorer in new tab
            window.open("https://babylon.explorers.guru/account/" + nodeId, "_blank");
        }
    });
    </script>
    """
    
    try:
        path = os.path.join(tempfile.gettempdir(), "graph.html")
        net.save_graph(path)
        
        with open(path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        html_content = html_content.replace("</body>", f"{js_click_event}</body>")
        
        return html_content
        
    except Exception as e:
        return f"<div>Error: {e}</div>"