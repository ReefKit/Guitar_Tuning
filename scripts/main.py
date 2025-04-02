import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import click
import sqlite3
from config import DB_FILE
from db_manager import (
    add_song,
    import_songs_from_csv,
    list_closeness_keys,
    list_all_tunings,
    list_all_songs,
    find_songs_by_tuning,
    find_songs_by_name,
    update_tuning_name
)
from export.graph import fetch_tunings_and_relationships, build_graph, export_graph, get_clusters, export_clusters
from tuning_analysis import compute_all_closeness

# -------------------- CLI Setup --------------------

@click.group(help="Guitar Tuning CLI Tool")
def cli():
    pass


# -------------------- Song Import Commands --------------------

@cli.command(help="Import songs from a CSV file.")
@click.argument("csv_file", type=click.Path(exists=True))
def import_csv(csv_file):
    with sqlite3.connect(DB_FILE) as conn:
        import_songs_from_csv(conn, csv_file)
    click.echo(f"✅ Imported songs from {csv_file}")


@cli.command(name="add-song", help="Add a single song to the database.")
@click.option("--name", prompt="Song name", help="The name of the song.")
@click.option("--artist", prompt="Artist", help="The artist of the song.")
@click.option("--tuning", prompt="Tuning", help="Tuning (e.g., E A D G B E).")
def add_song_cli(name, artist, tuning):
    with sqlite3.connect(DB_FILE) as conn:
        add_song(conn, name, artist, tuning)
    click.echo(f"✅ Added song: '{name}' by {artist} ({tuning})")


# -------------------- Song Lookup Commands --------------------

@cli.group(help="Commands for listing and searching songs.")
def song():
    pass


@song.command("list", help="List all songs in the database.")
def list_songs():
    with sqlite3.connect(DB_FILE) as conn:
        songs = list_all_songs(conn)
        if not songs:
            click.echo("No songs found.")
        else:
            click.echo("Songs:")
            for sid, name, artist, tuning in songs:
                click.echo(f"  ID {sid}: '{name}' by {artist} ({tuning})")


@song.command("find-by-tuning", help="Find songs by tuning.")
@click.argument("tuning")
def find_by_tuning(tuning):
    with sqlite3.connect(DB_FILE) as conn:
        matches = find_songs_by_tuning(conn, tuning)
        if not matches:
            click.echo(f"No songs found with tuning: {tuning}")
        else:
            click.echo(f"Songs with tuning {tuning}:")
            for sid, name, artist in matches:
                click.echo(f"  ID {sid}: '{name}' by {artist}")


@song.command("find-by-name", help="Search songs by name or artist (partial match).")
@click.argument("query")
def find_by_name(query):
    with sqlite3.connect(DB_FILE) as conn:
        matches = find_songs_by_name(conn, query)
        if not matches:
            click.echo(f"No matches found for: {query}")
        else:
            click.echo(f"Songs matching '{query}':")
            for sid, name, artist, tuning in matches:
                click.echo(f"  ID {sid}: '{name}' by {artist} ({tuning})")


# -------------------- Tuning Analysis Commands --------------------

@cli.command(help="Analyze tuning closeness and store relationships in the database.")
@click.option("--max-changed", type=int, required=True, help="Max number of changed strings.")
@click.option("--max-pitch", type=int, required=True, help="Max pitch change per string.")
@click.option("--max-total", type=int, required=True, help="Max total pitch change.")
def analyze(max_changed, max_pitch, max_total):
    with sqlite3.connect(DB_FILE) as conn:
        compute_all_closeness(conn, max_changed, max_pitch, max_total)
    click.echo("✅ Tuning closeness analysis complete.")


# -------------------- Utility Commands --------------------

@cli.command(help="List all stored closeness keys.")
def show_closeness_keys():
    with sqlite3.connect(DB_FILE) as conn:
        keys = list_closeness_keys(conn)
        if not keys:
            click.echo("No closeness keys found.")
        else:
            click.echo("Stored closeness keys:")
            for key in keys:
                click.echo(f"- ID {key[0]}: max_changed={key[1]}, max_pitch={key[2]}, max_total={key[3]}")


# -------------------- Tuning Utilities --------------------

@cli.group(help="Inspect or update tunings.")
def tuning():
    pass


@tuning.command("list", help="List all tunings in the database.")
def list_tunings():
    with sqlite3.connect(DB_FILE) as conn:
        tunings = list_all_tunings(conn)
        if not tunings:
            click.echo("No tunings found.")
        else:
            click.echo("Tunings:")
            for tid, tuning, name in tunings:
                label = f"{name} ({tuning})" if name else tuning
                click.echo(f"  ID {tid}: {label}")


@tuning.command("name", help="Update the name of a tuning by ID.")
@click.argument("tuning_id", type=int)
@click.argument("new_name", type=str)
def name_tuning(tuning_id, new_name):
    with sqlite3.connect(DB_FILE) as conn:
        update_tuning_name(conn, tuning_id, new_name)
    click.echo(f"✅ Updated tuning ID {tuning_id} with name: {new_name}")


# -------------------- Exporting Commands --------------------

@cli.command(name="export-graph", help="Export the tuning graph for a specific closeness key to a GraphML file.")
@click.option("--closeness-key-id", type=int, prompt="Closeness Key ID", help="The closeness key ID to export.")
@click.option("--output", default="export/tuning_graph.graphml", help="Output filepath (default: export/tuning_graph.graphml)")
def export_graph_cli(closeness_key_id, output):
    with sqlite3.connect(DB_FILE) as conn:
        nodes, edges = fetch_tunings_and_relationships(conn, closeness_key_id)
        if not edges:
            click.echo(f"⚠️ No tuning relationships found for closeness key ID {closeness_key_id}")
            if not nodes:
                click.echo("⚠️ No tunings found either — maybe the DB is empty?")
            return
        graph = build_graph(conn, nodes, edges, closeness_key_id)
        export_graph(graph, output)
    click.echo(f"✅ Exported tuning graph to: {output}")

@cli.command(name="export-clusters", help="Export each tuning cluster to its own GraphML file.")
@click.option("--closeness-key-id", type=int, prompt="Closeness Key ID", help="The closeness key ID to analyze.")
@click.option("--out-dir", default="export/clusters", help="Output directory (default: export/clusters)")
def export_clusters_cli(closeness_key_id, out_dir):
    with sqlite3.connect(DB_FILE) as conn:
        nodes, edges = fetch_tunings_and_relationships(conn, closeness_key_id)
        if not edges:
            click.echo(f"⚠️ No tuning relationships found for closeness key ID {closeness_key_id}")
            return
        graph = build_graph(conn, nodes, edges, closeness_key_id)
        export_clusters(graph, out_dir)
        clusters = get_clusters(graph)
        click.echo(f"🔍 Found {len(clusters)} cluster(s):")
        for i, cluster in enumerate(clusters):
            click.echo(f"  - Cluster {i+1}: {len(cluster)} tuning(s)")

    click.echo(f"✅ Exported all clusters to directory: {out_dir}")


# -------------------- Entry Point --------------------

if __name__ == "__main__":
    cli()
