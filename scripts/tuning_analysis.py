"""
tuning_analysis.py

Performs analysis on tunings, including calculating closeness relationships,
storing results in the database, and batch processing using configurable thresholds.
"""

import sqlite3
from config import DB_FILE
from db_manager import (
    insert_tuning_relationship,
    insert_closeness_key
)
from tuning_utils import are_tunings_close
from tqdm import tqdm
from itertools import combinations

# -------------------- Analysis Functions --------------------

def get_all_tunings(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    """
    Retrieves all tunings from the database.

    Args:
        conn: SQLite database connection.

    Returns:
        List of (tuning_id, tuning_string)
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, tuning FROM tunings")
    return cursor.fetchall()



def compute_all_closeness(conn: sqlite3.Connection, max_changed: int, max_pitch: int, max_total: int) -> None:
    """
    Compares all pairs of tunings and stores close pairs in the database.

    Args:
        conn: SQLite database connection.
        max_changed: Max number of strings allowed to change.
        max_pitch: Max semitone shift allowed on each string.
        max_total: Max total semitone shift across all strings.
    """
    tunings = get_all_tunings(conn)
    closeness_key_id = insert_closeness_key(conn, max_changed, max_pitch, max_total)

    for (id1, tuning1), (id2, tuning2) in tqdm(combinations(tunings, 2), desc="Analyzing tuning pairs", total=len(tunings)*(len(tunings)-1)//2):
        if are_tunings_close(tuning1, tuning2, max_changed, max_pitch, max_total):
            insert_tuning_relationship(conn, id1, id2, closeness_key_id)



def get_close_tunings(conn: sqlite3.Connection, tuning_id: int, closeness_key_id: int) -> list[int]:
    """
    Retrieves a list of tuning IDs that are close to a given tuning under a closeness rule.

    Args:
        tuning_id: The tuning to find close neighbors for.
        closeness_key_id: ID of the closeness rule used.
        conn: SQLite database connection.

    Returns:
        List of tuning IDs that are close to the input tuning.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            CASE
                WHEN tuning_id = ? THEN close_tuning_id
                ELSE tuning_id
            END
        FROM tuning_relationships
        WHERE closeness_key_id = ?
        AND (tuning_id = ? OR close_tuning_id = ?)

    """, (tuning_id, closeness_key_id, tuning_id, tuning_id))

    rows = cursor.fetchall()
    return [row[0] for row in rows]