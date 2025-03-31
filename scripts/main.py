import click
import sqlite3
from config import DB_FILE
from db_manager import (
    add_song,
    add_tuning,
    import_songs_from_csv,
    list_closeness_keys,
    list_all_tunings,
    list_all_songs,
    find_songs_by_tuning,
    find_songs_by_name,
    update_tuning_name
)
from tuning_analysis import compute_all_closeness

# -------------------- CLI Setup --------------------

@click.group()
def cli():
    """Guitar Tuning CLI Tool"""
    pass


# -------------------- Song Import Commands --------------------

@cli.command()
@click.argument("csv_file", type=click.Path(exists=True))
def import_csv(csv_file):
    """Import songs from a CSV file."""
    with sqlite3.connect(DB_FILE) as conn:
        import_songs_from_csv(csv_file, conn)
    click.echo(f"Imported songs from {csv_file}")


@cli.command(name="add-song")
@click.option("--name", prompt="Song name", help="The name of the song.")
@click.option("--artist", prompt="Artist", help="The artist of the song.")
@click.option("--tuning", prompt="Tuning", help="Tuning (e.g., E A D G B E).")
def add_song_cli(name, artist, tuning):
    """Add a single song to the database."""
    with sqlite3.connect(DB_FILE) as conn:
        tuning_id = add_tuning(tuning, conn)
        add_song(name, artist, tuning, conn)
    click.echo(f"Added '{name}' by {artist} with tuning: {tuning}")


# -------------------- Song Lookup Commands --------------------

@cli.group()
def song():
    """Inspect or search songs."""
    pass


@song.command("list")
def list_songs():
    """List all songs in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        songs = list_all_songs(conn)
        if not songs:
            click.echo("No songs found.")
        else:
            for sid, name, artist, tuning in songs:
                click.echo(f"  ID {sid}: '{name}' by {artist} ({tuning})")


@song.command("find-by-tuning")
@click.argument("tuning")
def find_by_tuning(tuning):
    """Find songs by tuning."""
    with sqlite3.connect(DB_FILE) as conn:
        matches = find_songs_by_tuning(tuning, conn)
        if not matches:
            click.echo(f"No songs found with tuning: {tuning}")
        else:
            for sid, name, artist in matches:
                click.echo(f"  ID {sid}: '{name}' by {artist}")


@song.command("find-by-name")
@click.argument("query")
def find_by_name(query):
    """Search songs by name or artist (partial match)."""
    with sqlite3.connect(DB_FILE) as conn:
        matches = find_songs_by_name(query, conn)
        if not matches:
            click.echo(f"No matches found for: {query}")
        else:
            for sid, name, artist, tuning in matches:
                click.echo(f"  ID {sid}: '{name}' by {artist} ({tuning})")


# -------------------- Tuning Analysis Commands --------------------

@cli.command()
@click.option("--max-changed", type=int, required=True, help="Max number of changed strings.")
@click.option("--max-pitch", type=int, required=True, help="Max pitch change per string.")
@click.option("--max-total", type=int, required=True, help="Max total pitch change.")
def analyze(max_changed, max_pitch, max_total):
    """Analyze tuning closeness and store relationships in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        compute_all_closeness(conn, max_changed, max_pitch, max_total)
    click.echo("Tuning closeness analysis complete.")


# -------------------- Utility Commands --------------------

@cli.command()
def show_closeness_keys():
    """List all stored closeness keys."""
    with sqlite3.connect(DB_FILE) as conn:
        keys = list_closeness_keys(conn)
        if not keys:
            click.echo("No closeness keys found.")
        else:
            click.echo("Stored closeness keys:")
            for key in keys:
                click.echo(f"- ID {key[0]}: max_changed={key[1]}, max_pitch={key[2]}, max_total={key[3]}")


# -------------------- Tuning Utilities --------------------

@cli.group()
def tuning():
    """Inspect or update tunings."""
    pass


@tuning.command("list")
def list_tunings():
    """List all tunings in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        tunings = list_all_tunings(conn)
        if not tunings:
            click.echo("No tunings found.")
        else:
            click.echo("Tunings:")
            for tid, tuning, name in tunings:
                label = f" (name: {name})" if name else ""
                click.echo(f"  ID {tid}: {tuning}{label}")


@tuning.command("name")
@click.argument("tuning_id", type=int)
@click.argument("new_name", type=str)
def name_tuning(tuning_id, new_name):
    """Update the name of a tuning by ID."""
    with sqlite3.connect(DB_FILE) as conn:
        update_tuning_name(tuning_id, new_name, conn)
    click.echo(f"Updated tuning ID {tuning_id} with name: {new_name}")


# -------------------- Entry Point --------------------

if __name__ == "__main__":
    cli()
