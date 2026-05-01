import logging
import sqlite3

from app.radarr import query_movie, contact_radarr
from app.jellyfin import organize_movies, fetch_jellyfin_movies

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


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


def main():

    conn = setup_db()

    data = fetch_jellyfin_movies()
    if data is None:
        logging.error("fetch_jellyfin_movies returned None")
        return

    organize_movies(data, conn)

    query_movie(conn)


if __name__ == "__main__":
    main()
