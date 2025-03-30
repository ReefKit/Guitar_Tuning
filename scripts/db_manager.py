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
from config import DB_FILE  # Import DB path

# -------------------- Core Database Functions --------------------

def add_tuning(tuning: str, conn: sqlite3.Connection) -> int:
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

def add_song(name: str, artist: str, tuning: str, conn: sqlite3.Connection) -> None:
    """
    Inserts a song into the database, ensuring its tuning exists.
    Skips duplicates if song with same name, artist, and tuning_id exists.
    """
    cursor = conn.cursor()

    # Ensure the tuning exists
    tuning_id = add_tuning(tuning, conn)

    try:
        # Insert the song
        cursor.execute(
            "INSERT INTO songs (name, artist, tuning_id) VALUES (?, ?, ?)",
            (name, artist, tuning_id)
        )
    except sqlite3.IntegrityError:
        print(f"⚠️  Skipped duplicate song: {name} by {artist}")

def bulk_add_songs(songs: list[tuple[str, str, str]], conn: sqlite3.Connection) -> None:
    """
    Adds multiple songs efficiently with one transaction.
    
    Args:
        songs (list): List of (name, artist, tuning) tuples.
        conn (sqlite3.Connection): Database connection object.
    """
    cursor = conn.cursor()
    inserted_count = 0

    for name, artist, tuning in songs:
        tuning_id = add_tuning(tuning, conn)
        try:
            cursor.execute(
                "INSERT INTO songs (name, artist, tuning_id) VALUES (?, ?, ?)",
                (name, artist, tuning_id)
            )
            inserted_count += 1
        except sqlite3.IntegrityError:
            print(f"⚠️  Skipped duplicate song: {name} by {artist}")

    print(f"✅ Bulk added {inserted_count} new songs.")

def import_songs_from_csv(csv_file: str, conn: sqlite3.Connection) -> None:
    """
    Reads a CSV file and inserts songs into the database.

    Args:
        csv_file (str): Path to the CSV file.
        conn (sqlite3.Connection): Database connection.
    """
    df = pd.read_csv(csv_file)

    # Ensure columns match expected format
    required_cols = {"name", "artist", "tuning"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV must contain columns: {missing}")

    songs = [(row["name"], row["artist"], row["tuning"]) for _, row in df.iterrows()]
    bulk_add_songs(songs, conn)

def insert_closeness_key(
    max_changed_strings: int,
    max_pitch_change: int,
    max_total_difference: int,
    conn: sqlite3.Connection
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

    return cursor.lastrowid

def insert_tuning_relationship(
    tuning_id: int,
    close_tuning_id: int,
    closeness_score: float,
    closeness_key_id: int,
    conn: sqlite3.Connection
) -> None:
    """
    Inserts a relationship between two tunings, including a closeness score and key.

    Args:
        tuning_id (int): ID of the source tuning.
        close_tuning_id (int): ID of the related tuning.
        closeness_score (float): Computed closeness score.
        closeness_key_id (int): ID of the applied closeness rule.
        conn (sqlite3.Connection): Active DB connection.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tuning_relationships (tuning_id, close_tuning_id, closeness_score, closeness_key_id)
            VALUES (?, ?, ?, ?)
            """,
            (tuning_id, close_tuning_id, closeness_score, closeness_key_id)
        )
    except sqlite3.IntegrityError:
        print(f"⚠️  Skipped duplicate relationship: {tuning_id} ↔ {close_tuning_id}")