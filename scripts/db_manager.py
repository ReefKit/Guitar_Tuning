"""
db_manager.py

Handles SQLite database interactions, including:
- Adding tunings & songs
- Importing data from CSV
- Efficiently managing database connections

Usage:
    from db_manager import add_song, import_songs_from_csv
"""

import sqlite3
import pandas as pd

# -------------------- Core Database Functions --------------------

def add_tuning(conn: sqlite3.Connection, tuning: str) -> int:
    """
    Inserts a tuning into the database if it doesn't exist.
    Returns the tuning_id.
    """
    cursor = conn.cursor()

    # Check if tuning exists
    cursor.execute("SELECT id FROM tunings WHERE tuning = ?", (tuning,))
    result = cursor.fetchone()

    if result:
        return result[0]  # Tuning already exists

    # Insert new tuning
    cursor.execute("INSERT INTO tunings (tuning) VALUES (?)", (tuning,))
    return cursor.lastrowid  # Get the new tuning ID

def add_song(conn: sqlite3.Connection, name: str, artist: str, tuning: str) -> None:
    """
    Inserts a song into the database, ensuring its tuning exists.
    Skips duplicates if song with same name, artist, and tuning_id exists.
    """
    cursor = conn.cursor()

    # Ensure the tuning exists
    tuning_id = add_tuning(conn, tuning)

    try:
        # Insert the song
        cursor.execute(
            "INSERT INTO songs (name, artist, tuning_id) VALUES (?, ?, ?)",
            (name, artist, tuning_id)
        )
    except sqlite3.IntegrityError:
        print(f"⚠️  Skipped duplicate song: {name} by {artist}")

def bulk_add_songs(conn: sqlite3.Connection, songs: list[tuple[str, str, str]]) -> None:
    """
    Adds multiple songs efficiently with one transaction.
    
    Args:
        songs (list): List of (name, artist, tuning) tuples.
        conn (sqlite3.Connection): Database connection object.
    """
    cursor = conn.cursor()
    inserted_count = 0

    for name, artist, tuning in songs:
        tuning_id = add_tuning(conn, tuning)
        try:
            cursor.execute(
                "INSERT INTO songs (name, artist, tuning_id) VALUES (?, ?, ?)",
                (name, artist, tuning_id)
            )
            inserted_count += 1
        except sqlite3.IntegrityError:
            print(f"⚠️  Skipped duplicate song: {name} by {artist}")

    conn.commit()
    print(f"✅ Bulk added {inserted_count} new songs.")

def import_songs_from_csv(conn: sqlite3.Connection, csv_file: str) -> None:
    """
    Reads a CSV file and inserts songs into the database.

    Args:
        csv_file (str): Path to the CSV file.
        conn (sqlite3.Connection): Database connection.
    """
    df = pd.read_csv(csv_file)

    # Ensure columns match expected format
    required_columns = {"name", "artist", "tuning"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"CSV must contain columns: {missing_columns}")

    songs = [(row["name"].strip(), row["artist"].strip(), row["tuning"].strip()) for _, row in df.iterrows()]
    bulk_add_songs(conn, songs)

def insert_closeness_key(
    conn: sqlite3.Connection,
    max_changed_strings: int,
    max_pitch_change: int,
    max_total_difference: int
) -> int:
    """
    Inserts a closeness key into the database if it doesn't already exist,
    and returns its ID.

    Args:
        max_changed_strings (int): Max number of strings allowed to change.
        max_pitch_change (int): Max pitch difference allowed per string.
        max_total_difference (int): Max total pitch change allowed across all strings.

    Returns:
        int: The ID of the closeness key.
    """
    cursor = conn.cursor()

    # Check if this key already exists
    cursor.execute(
        """
        SELECT id FROM closeness_keys
        WHERE max_changed_strings = ? AND max_pitch_change = ? AND max_total_difference = ?
        """,
        (max_changed_strings, max_pitch_change, max_total_difference)
    )
    result = cursor.fetchone()

    if result:
        return result[0]  # Reuse existing ID

    # Otherwise, insert new key
    cursor.execute(
        """
        INSERT INTO closeness_keys (max_changed_strings, max_pitch_change, max_total_difference)
        VALUES (?, ?, ?)
        """,
        (max_changed_strings, max_pitch_change, max_total_difference)
    )

    conn.commit()
    return cursor.lastrowid

def insert_tuning_relationship(
    conn: sqlite3.Connection,
    tuning_id: int,
    close_tuning_id: int,
    closeness_key_id: int,
    pitch_vector: str
) -> None:
    """
    Inserts a relationship between two tunings for a given closeness key,
    including the per-string pitch vector used to move from one to the other.

    Args:
        tuning_id (int): ID of the first tuning.
        close_tuning_id (int): ID of the second tuning.
        closeness_key_id (int): ID of the applied closeness rule.
        pitch_vector (str): Comma-separated string of pitch differences (e.g., "2,0,0,0,0,0").
        conn (sqlite3.Connection): Active DB connection.
    """
    cursor = conn.cursor()

    original_pair = (tuning_id, close_tuning_id)
    sorted_pair = tuple(sorted(original_pair))

    # Flip pitch vector if we reversed direction
    if original_pair != sorted_pair:
        pitch_vector = ','.join(str(-int(x)) for x in pitch_vector.split(','))

    tuning_id, close_tuning_id = sorted_pair

    try:
        cursor.execute(
            """
            INSERT INTO tuning_relationships 
                (tuning_id, close_tuning_id, closeness_key_id, pitch_vector)
            VALUES (?, ?, ?, ?)
            """,
            (tuning_id, close_tuning_id, closeness_key_id, pitch_vector)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠️ Skipped duplicate relationship: {tuning_id} ↔ {close_tuning_id}")


def list_closeness_keys(conn: sqlite3.Connection) -> list[tuple[int, int, int, int]]:
    """
    Lists all stored closeness keys in the database.

    Args:
        conn: SQLite connection.

    Returns:
        List of tuples: (id, max_changed_strings, max_pitch_change, max_total_difference)
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, max_changed_strings, max_pitch_change, max_total_difference FROM closeness_keys")
    return cursor.fetchall()

def list_all_tunings(conn: sqlite3.Connection) -> list[tuple[int, str, str]]:
    """
    Returns all tunings as (id, tuning_string, name).
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, tuning, COALESCE(name, '') FROM tunings ORDER BY id")
    return cursor.fetchall()


def update_tuning_name(conn: sqlite3.Connection, tuning_id: int, new_name: str) -> None:
    """
    Updates the name of a tuning given its ID.
    """
    cursor = conn.cursor()
    cursor.execute("UPDATE tunings SET name = ? WHERE id = ?", (new_name, tuning_id))
    conn.commit()

def list_all_songs(conn: sqlite3.Connection) -> list[tuple[int, str, str, str]]:
    """
    Returns all songs in the database as (id, name, artist, tuning_string).
    """
    cursor = conn.cursor()
    cursor.execute('''
        SELECT songs.id, songs.name, songs.artist, tunings.tuning
        FROM songs
        JOIN tunings ON songs.tuning_id = tunings.id
        ORDER BY songs.artist, songs.name
    ''')
    return cursor.fetchall()

def find_songs_by_tuning(conn: sqlite3.Connection, tuning: str) -> list[tuple[int, str, str]]:
    """
    Returns all songs using the given tuning string.

    Args:
        tuning (str): The exact tuning string (e.g., "D A D G A D").

    Returns:
        List of (song_id, name, artist)
    """
    cursor = conn.cursor()
    cursor.execute('''
        SELECT songs.id, songs.name, songs.artist
        FROM songs
        JOIN tunings ON songs.tuning_id = tunings.id
        WHERE tunings.tuning = ?
        ORDER BY songs.artist, songs.name
    ''', (tuning,))
    return cursor.fetchall()

def find_songs_by_name(conn: sqlite3.Connection, query: str) -> list[tuple[int, str, str, str]]:
    """
    Returns songs where the name or artist matches a partial case-insensitive query.

    Args:
        query (str): Partial name or artist to search.

    Returns:
        List of (song_id, name, artist, tuning_string)
    """
    wildcard = f"%{query}%"
    cursor = conn.cursor()
    cursor.execute('''
        SELECT songs.id, songs.name, songs.artist, tunings.tuning
        FROM songs
        JOIN tunings ON songs.tuning_id = tunings.id
        WHERE songs.name LIKE ? OR songs.artist LIKE ?
        ORDER BY songs.artist, songs.name
    ''', (wildcard, wildcard))
    return cursor.fetchall()

def get_songs_by_tuning_id(conn: sqlite3.Connection, tuning_id: int) -> list[str]:
    """
    Returns a list of song titles (with artist) using a given tuning ID.

    Args:
        tuning_id (int): ID of the tuning.

    Returns:
        List[str]: A list like ["Song A by Artist1", "Song B by Artist2"]
    """
    cursor = conn.cursor()
    cursor.execute('''
        SELECT songs.name, songs.artist
        FROM songs
        WHERE songs.tuning_id = ?
        ORDER BY songs.artist, songs.name
    ''', (tuning_id,))
    return [f"{name} by {artist}" for name, artist in cursor.fetchall()]
