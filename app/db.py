import sqlite3


def setup_db() -> sqlite3.Connection:
    conn = sqlite3.connect("data/movies.db")
    cursor = conn.cursor()

    _ = cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS movies (
        tmdb_id INTEGER PRIMARY KEY,
        radarr_movie_id INTEGER,
        name TEXT NOT NULL,
        year INTEGER,
        height INTEGER,
        width INTEGER,
        four_k_available INTEGER,
        last_checked TEXT,
        manually_reviewed INTEGER DEFAULT 0,
        blacklisted INTEGER DEFAULT 0
    )
    """
    )
    conn.commit()

    return conn
