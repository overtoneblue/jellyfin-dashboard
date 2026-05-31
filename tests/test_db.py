from datetime import datetime, timedelta
import sqlite3
from app.radarr import get_movies_for_release_check


def setup_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE movies (
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


def test_get_movies_for_release_check():
    conn = setup_test_db()
    cursor = conn.cursor()

    stale_date = (datetime.now() - timedelta(days=30)).isoformat()
    fresh_date = datetime.now().isoformat()

    movies = [
        # selected: never checked
        (1, 101, "Unchecked Movie", None, None),
        # selected: checked negative but stale
        (2, 102, "Stale Negative Movie", 0, stale_date),
        # skipped: checked negative but fresh
        (3, 103, "Fresh Negative Movie", 0, fresh_date),
        # skipped: already found 4K
        (4, 104, "Already Found 4K Movie", 1, stale_date),
        # skipped: no Radarr ID
        (5, None, "No Radarr ID Movie", None, None),
    ]

    cursor.executemany(
        """
        INSERT INTO movies (
            tmdb_id, radarr_movie_id, name, four_k_available, last_checked
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        movies,
    )

    conn.commit()

    rows = get_movies_for_release_check(conn)

    assert set(rows) == {
        (101, "Unchecked Movie"),
        (102, "Stale Negative Movie"),
    }
