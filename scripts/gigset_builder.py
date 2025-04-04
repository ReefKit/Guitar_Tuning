"""
gigset_builder.py

This script generates an interactive HTML graph of tunings and their relationships using PyVis.
Each node is a tuning, with a hoverable tooltip showing its associated songs.
The goal is to visually explore connected tunings and begin building a gigset plan.
Future extensions include click-to-build paths, constraint warnings, and gigset export.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pyvis.network import Network
import networkx as nx
import sqlite3
from scripts.db_manager import get_songs_by_tuning_id
from export.graph import fetch_tunings_and_relationships, build_graph
from scripts.config import DB_FILE

def build_interactive_gigset_graph(conn, closeness_key_id: int, output_file: str = "export/interactive_gigset.html"):
    """
    Builds and displays an interactive graph of tunings using PyVis.
    Nodes show the tuning and list of songs using it.

    Args:
        conn: Active SQLite connection
        closeness_key_id: ID of the tuning closeness rule to visualize
        output_file: Path to save the generated HTML file
    """
    nodes, edges = fetch_tunings_and_relationships(conn, closeness_key_id)
    G = build_graph(conn, nodes, edges, closeness_key_id)
    print("🧪 Sanity check: dumping 5 edge pitch_vectors from graph:")
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        if i >= 5: break
        print(f"  {u} -> {v}: pitch_vector = {data.get('pitch_vector')}")


    # Initialize PyVis network
    net = Network(height="800px", width="100%", bgcolor="#1e1e1e", font_color="white")
    net.toggle_physics(True)

    # Add nodes with songs in tooltips
    for node_id in G.nodes:
        data = G.nodes[node_id]
        songs = get_songs_by_tuning_id(conn, node_id)
        tuning_label = data['tuning']
        songs_label = "\n".join(songs) if songs else "(No songs)"

        net.add_node(
            node_id,
            label=tuning_label,  # default view
            color="#00bfff",
            shape="dot",
            size=15 + len(songs)*2,
            tuning_label=tuning_label,
            songs_label=songs_label
        )

    # Add edges with pitch vector stored directly as a top-level custom attribute
    for source, target, edge_data in G.edges(data=True):
        pitch_vector_str = ','.join(map(str, edge_data["pitch_vector"])) if isinstance(edge_data["pitch_vector"], list) else edge_data["pitch_vector"]
        net.add_edge(
            source,
            target,
            color="#aaaaaa",
            pitch_vector=pitch_vector_str
        )


    # Save HTML to string so we can inject JavaScript for click selection and label toggle
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    net.show_buttons(filter_=['physics'])
    net.save_graph(output_file)

    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Ensure the HTML content has the proper DOCTYPE and structure
    if not html.startswith('<!DOCTYPE html>'):
        html = "<!DOCTYPE html>" + html  # Add DOCTYPE at the start if missing

    # Inject JavaScript into the HTML
    js_file_path = os.path.join(os.path.dirname(__file__), "static", "graph_interactivity.js")
    with open(js_file_path, 'r', encoding='utf-8') as f_js:
        js_script = f"<script>{f_js.read()}</script>"

    # Replace the closing body tag with the injected JS
    html = html.replace("</body>", js_script + "</body>")

    # Write the updated HTML back to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Interactive gigset graph with selection and label toggle saved to {output_file}")


if __name__ == "__main__":
    # Entry point to launch the graph from terminal
    closeness_key_id = int(input("Enter closeness_key_id to use: "))
    with sqlite3.connect(DB_FILE) as conn:
        build_interactive_gigset_graph(conn, closeness_key_id)
