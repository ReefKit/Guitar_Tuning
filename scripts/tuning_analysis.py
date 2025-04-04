"""
tuning_analysis.py

Performs analysis on tunings, including calculating closeness relationships,
storing results in the database, and batch processing using configurable thresholds.
"""

import sqlite3
from db_manager import (
    insert_tuning_relationship,
    insert_closeness_key
)
from tuning_utils import (
    are_tunings_close,
    get_pitch_vector
)
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

def get_closeness_thresholds(conn: sqlite3.Connection, closeness_key_id: int) -> tuple[int, int, int]:
    """
    Returns the thresholds (max_changed_strings, max_pitch_change, max_total_difference)
    for a given closeness_key_id.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT max_changed_strings, max_pitch_change, max_total_difference
        FROM closeness_keys WHERE id = ?
    """, (closeness_key_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Closeness key ID {closeness_key_id} not found.")
    return tuple(row)


def compute_all_closeness(
    conn: sqlite3.Connection,
    max_changed: int = None,
    max_pitch: int = None,
    max_total: int = None,
    closeness_key_id: int = None
) -> None:
    """
    Compares all pairs of tunings and stores close pairs in the database,
    including the per-string pitch vector required to move from one tuning
    to the other under optimal transposition.

    This function can either:
    - Accept a closeness_key_id directly (reusing existing thresholds), or
    - Accept threshold values to insert a new closeness key.

    Args:
        conn (sqlite3.Connection): Database connection.
        max_changed (int, optional): Max number of strings allowed to change.
        max_pitch (int, optional): Max semitone shift allowed per string.
        max_total (int, optional): Max total semitone shift across all strings.
        closeness_key_id (int, optional): Existing closeness key ID to reuse.

    Raises:
        ValueError: If neither a closeness_key_id nor all 3 threshold values are provided.
    """
    if closeness_key_id is None:
        if max_changed is None or max_pitch is None or max_total is None:
            raise ValueError("Either provide a closeness_key_id or all 3 threshold values.")
        closeness_key_id = insert_closeness_key(conn, max_changed, max_pitch, max_total)

    tunings = get_all_tunings(conn)

    for (id1, tuning1), (id2, tuning2) in tqdm(
        combinations(tunings, 2),
        desc="Analyzing tuning pairs",
        total=len(tunings) * (len(tunings) - 1) // 2
    ):
        is_close, shift = are_tunings_close(tuning1, tuning2, max_changed, max_pitch, max_total)
        if is_close:
            pitch_vector = get_pitch_vector(tuning1, tuning2, shift)
            pitch_vector_str = ",".join(map(str, pitch_vector))
            insert_tuning_relationship(conn, id1, id2, closeness_key_id, pitch_vector=pitch_vector_str)





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