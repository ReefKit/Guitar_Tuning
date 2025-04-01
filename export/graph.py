import sqlite3
import networkx as nx
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# -------------------- Graph Export Logic --------------------

def fetch_tunings_and_relationships(conn: sqlite3.Connection, closeness_key_id: int):
    """
    Fetches tunings and relationships for a specific closeness key.

    Returns:
        nodes: List of (id, tuning, name)
        edges: List of (tuning_id_1, tuning_id_2)
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, tuning, COALESCE(name, '')
        FROM tunings
    """)
    nodes = cursor.fetchall()

    cursor.execute("""
        SELECT tuning_id, close_tuning_id
        FROM tuning_relationships
        WHERE closeness_key_id = ?
    """, (closeness_key_id,))
    edges = cursor.fetchall()

    if not edges:
        print(f"⚠️ No relationships found for closeness_key_id={closeness_key_id}")

    return nodes, edges

def build_graph(nodes, edges, closeness_key_id: int) -> nx.Graph:
    """
    Constructs a NetworkX graph from tuning nodes and closeness edges.

    Returns:
        A NetworkX Graph object.
    """
    G = nx.Graph()

    for tuning_id, tuning, name in nodes:
        G.add_node(tuning_id, tuning=tuning, name=name, key=closeness_key_id)

    for tuning_id_1, tuning_id_2 in edges:
        G.add_edge(tuning_id_1, tuning_id_2)

    return G

def export_graph(graph: nx.Graph, filepath: str):
    """
    Exports the graph to a file (GraphML format) for use in Gephi.

    Args:
        graph: NetworkX graph
        filepath: Output path for exported graph
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        nx.write_graphml(graph, filepath)
    except Exception as e:
        print(f"❌ Failed to export graph: {e}")
