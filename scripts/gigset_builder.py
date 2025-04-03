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

    # Initialize PyVis network
    net = Network(height="800px", width="100%", bgcolor="#1e1e1e", font_color="white")
    net.toggle_physics(True)

    # Add nodes with songs in tooltips
    for node_id in G.nodes:
        data = G.nodes[node_id]
        songs = get_songs_by_tuning_id(conn, node_id)
        tuning_label = data['tuning']
        tooltip = "<br>".join(songs) if songs else "(No songs)"
        node_label = tuning_label  # default to tuning string
        net.add_node(
            node_id,
            label=node_label,
            title=tooltip,
            color="#00bfff",
            shape="dot",
            size=15 + len(songs)*2
        )

    # Add edges based on tuning relationships
    for source, target in G.edges:
        net.add_edge(source, target, color="#aaaaaa")

    # Save HTML to string so we can inject JavaScript for click selection and label toggle
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    net.show_buttons(filter_=['physics'])
    net.save_graph(output_file)

    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()

    js_script = '''
    <script>
    var selectedNodes = new Set();
    var showSongs = false;

    function toggleNodeSelection(params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            var node = this.body.nodes[nodeId];
            if (selectedNodes.has(nodeId)) {
                selectedNodes.delete(nodeId);
                node.setOptions({color: '#00bfff'});
            } else {
                selectedNodes.add(nodeId);
                node.setOptions({color: '#ff69b4'});
            }
        }
    }

    function showSelected() {
        alert("Selected tunings: " + Array.from(selectedNodes).join(", "));
    }

    function toggleLabels() {
        showSongs = !showSongs;
        network.body.data.nodes.get().forEach(function(node) {
            var nodeObj = network.body.nodes[node.id];
            if (showSongs) {
                if (node.title && node.title !== "(No songs)") {
                    var songList = node.title.replace(/<br>/g, ", ");
                    nodeObj.setOptions({label: node.label + "\n(" + songList + ")"});
                }
            } else {
                var tuningOnly = node.label.split("\n")[0];
                nodeObj.setOptions({label: tuningOnly});
            }
        });
    }

    network.on("click", toggleNodeSelection);

    var btn = document.createElement("button");
    btn.innerHTML = "Show Selected Tunings";
    btn.style.position = "absolute";
    btn.style.top = "10px";
    btn.style.left = "10px";
    btn.style.zIndex = 9999;
    btn.onclick = showSelected;
    document.body.appendChild(btn);

    var toggleBtn = document.createElement("button");
    toggleBtn.innerHTML = "Toggle Song Labels";
    toggleBtn.style.position = "absolute";
    toggleBtn.style.top = "50px";
    toggleBtn.style.left = "10px";
    toggleBtn.style.zIndex = 9999;
    toggleBtn.onclick = toggleLabels;
    document.body.appendChild(toggleBtn);
    </script>
    '''

    html = html.replace("</body>", js_script + "</body>")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Interactive gigset graph with selection and label toggle saved to {output_file}")

if __name__ == "__main__":
    # Entry point to launch the graph from terminal
    closeness_key_id = int(input("Enter closeness_key_id to use: "))
    with sqlite3.connect(DB_FILE) as conn:
        build_interactive_gigset_graph(conn, closeness_key_id)
