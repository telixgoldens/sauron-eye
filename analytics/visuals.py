import networkx as nx
from pyvis.network import Network
import pandas as pd
import os

def generate_cluster_map(df, center_address):
    """
    Generates a Bubblemaps-style interactive graph.
    """
    try:
        # 1. Initialize Graph
        G = nx.Graph()
        
        # 2. Add Center Node (The Suspect)
        G.add_node(center_address, title=f"TARGET\n{center_address}", color="#FF4B4B", size=30, label="TARGET")
        
        # 3. Add Edges (Safeguard against missing columns)
        if 'sender' in df.columns and 'amount' in df.columns:
            # Aggregate transactions to avoid duplicate lines
            grouped = df.groupby('sender')['amount'].sum().reset_index()
            
            for _, row in grouped.iterrows():
                sender = row['sender']
                total_vol = row['amount']
                
                # Don't link target to itself
                if sender != center_address:
                    # Color Logic: Whales vs Shrimps
                    color = "#FFA500" if total_vol > 1000 else "#97C2FC"
                    size = 15 if total_vol > 1000 else 8
                    label = "Whale" if total_vol > 1000 else None
                    
                    # Tooltip
                    title_text = f"Address: {sender}\nVolume: {total_vol} BBN"
                    
                    G.add_node(sender, title=title_text, color=color, size=size, label=label)
                    G.add_edge(center_address, sender, weight=total_vol, color="rgba(255, 255, 255, 0.3)")

        # 4. Configure Pyvis Network
        # CRITICAL FIX: cdn_resources='in_line' ensures JS works in Streamlit Cloud
        net = Network(height="600px", width="100%", bgcolor="#0E1117", font_color="white", cdn_resources='in_line')
        net.from_nx(G)
        
        # Physics Engine
        net.force_atlas_2based(
            gravity=-50, 
            central_gravity=0.01, 
            spring_length=100, 
            spring_strength=0.08, 
            damping=0.4, 
            overlap=0
        )
        
        # 5. Save and Read (Railway-Safe Path)
        # We use a static name in the current folder to avoid path permission issues
        file_name = "network_graph.html"
        net.save_graph(file_name)
        
        # Read the file content into a string
        with open(file_name, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 6. Inject Click Event (JavaScript)
        # This allows clicking a node to open the explorer
        js_click = """
        <script type="text/javascript">
        network.on("click", function (params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                window.open("https://babylon.explorers.guru/account/" + nodeId, "_blank");
            }
        });
        </script>
        </body>
        """
        html_content = html_content.replace("</body>", js_click)
        
        # Cleanup
        if os.path.exists(file_name):
            os.remove(file_name)
            
        return html_content

    except Exception as e:
        return f"<div style='color:red; padding:20px;'><h3>⚠️ Graph Error</h3><p>{str(e)}</p></div>"