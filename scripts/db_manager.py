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

# -------------------- Database Connection Manager --------------------

class Database:
    """Manages a single SQLite connection."""
    
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.conn = None
    
    def __enter__(self):
        """Opens a database connection."""
        self.conn = sqlite3.connect(self.db_file)
        return self.conn  # Allows usage with `with Database() as conn:`
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Closes the connection when exiting the context."""
        if self.conn:
            self.conn.commit()  # Commit changes before closing
            self.conn.close()

# -------------------- Core Database Functions --------------------

def add_tuning(tuning):
    """
    Inserts a tuning into the database if it doesn't exist.
    Returns the tuning_id.
    """
    with Database() as conn:
        cursor = conn.cursor()
        
        # Check if tuning exists
        cursor.execute("SELECT id FROM tunings WHERE tuning = ?", (tuning,))
        result = cursor.fetchone()

        if result:
            return result[0]  # Tuning already exists
        
        # Insert new tuning
        cursor.execute("INSERT INTO tunings (tuning) VALUES (?)", (tuning,))
        return cursor.lastrowid  # Get the new tuning ID

def add_song(name, artist, tuning):
    """
    Inserts a song into the database, ensuring its tuning exists.
    """
    with Database() as conn:
        cursor = conn.cursor()
        
        # Ensure the tuning exists
        tuning_id = add_tuning(tuning)
        
        # Insert the song
        cursor.execute("INSERT INTO songs (name, artist, tuning_id) VALUES (?, ?, ?)", 
                       (name, artist, tuning_id))

def import_songs_from_csv(csv_file):
    """
    Reads a CSV file and inserts songs into the database.
    """
    df = pd.read_csv(csv_file)

    # Ensure columns match expected format
    if not all(col in df.columns for col in ["name", "artist", "tuning"]):
        raise ValueError("CSV must contain 'name', 'artist', and 'tuning' columns.")

    with Database() as conn:
        cursor = conn.cursor()
        inserted_count = 0

        for _, row in df.iterrows():
            name, artist, tuning = row["name"], row["artist"], row["tuning"]

            # Ensure tuning exists
            tuning_id = add_tuning(tuning)

            # Insert the song
            cursor.execute(
                "INSERT INTO songs (name, artist, tuning_id) VALUES (?, ?, ?)",
                (name, artist, tuning_id)
            )
            inserted_count += 1

        print(f"Imported {inserted_count} songs successfully.")

def insert_closeness_key(max_changed_strings, max_pitch_change, max_total_difference):
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
    with Database() as conn:
        cursor = conn.cursor()

        # Check if this key already exists
        cursor.execute("""
            SELECT id FROM closeness_keys
            WHERE max_changed_strings = ? AND max_pitch_change = ? AND max_total_difference = ?
        """, (max_changed_strings, max_pitch_change, max_total_difference))
        result = cursor.fetchone()

        if result:
            return result[0]  # Reuse existing ID

        # Otherwise, insert new key
        cursor.execute("""
            INSERT INTO closeness_keys (max_changed_strings, max_pitch_change, max_total_difference)
            VALUES (?, ?, ?)
        """, (max_changed_strings, max_pitch_change, max_total_difference))

        return cursor.lastrowid
