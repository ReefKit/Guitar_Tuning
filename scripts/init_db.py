"""
init_db.py

This script initializes the SQLite database by executing the schema defined in 'schema.sql'.
It ensures that all necessary tables are created before the application interacts with the database.

Usage:
    Run this script once to initialize the database:
        python init_db.py
"""

import sqlite3
import config

# Constants
SCHEMA_FILE = config.SCHEMA_FILE
DB_FILE = config.DB_FILE

def initialize_database():
    """
    Reads and executes the schema.sql file to create the database structure.
    
    - Connects to SQLite (creates 'songs.db' if it doesn't exist).
    - Reads 'schema.sql' and executes the SQL commands.
    - Commits the changes and closes the connection.

    Raises:
        Exception: If there is an issue reading the schema file or executing SQL commands.
    """
    try:
        # Connect to the SQLite database (creates file if it doesn’t exist)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Read schema file
        with open(SCHEMA_FILE, "r") as file:
            schema = file.read()

        # Execute schema SQL commands
        cursor.executescript(schema)

        # Commit changes and close connection
        conn.commit()
        conn.close()

        print("Database initialized successfully!")

    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    initialize_database()
