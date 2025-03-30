-- Table for songs
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    artist TEXT NOT NULL,
    tuning_id INTEGER NOT NULL,  -- Link to tunings table
    FOREIGN KEY (tuning_id) REFERENCES tunings (id)
);

-- Table for named tunings
CREATE TABLE IF NOT EXISTS tunings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tuning TEXT NOT NULL UNIQUE,  -- Example: "D A D G B E"
    name TEXT  -- Optional: "Drop D"
);

-- Table defining a set of closeness criteria
CREATE TABLE IF NOT EXISTS closeness_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    max_changed_strings INTEGER NOT NULL,
    max_pitch_change INTEGER NOT NULL,
    max_total_difference INTEGER NOT NULL,
    UNIQUE (max_changed_strings, max_pitch_change, max_total_difference)
);

-- Table for relationships between "close" tunings, based on a closeness key
CREATE TABLE IF NOT EXISTS tuning_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tuning_id INTEGER NOT NULL,           -- Reference to tunings.id
    close_tuning_id INTEGER NOT NULL,     -- Another tuning
    closeness_key_id INTEGER NOT NULL,    -- Reference to closeness_keys.id
    FOREIGN KEY (tuning_id) REFERENCES tunings (id),
    FOREIGN KEY (close_tuning_id) REFERENCES tunings (id),
    FOREIGN KEY (closeness_key_id) REFERENCES closeness_keys (id),
    UNIQUE (tuning_id, close_tuning_id, closeness_key_id)  -- Prevents duplicate edges per key
);
