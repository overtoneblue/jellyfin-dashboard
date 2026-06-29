from configparser import ConfigParser

# import sqlite3
import psycopg


def config_parse(filename="database.ini", section="postgresql"):
    parser = ConfigParser()

    parser.read(filename)

    db = {}

    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]

    else:
        raise Exception("Missing Database Configuration Information")

    return db


def setup_db() -> psycopg.Connection:
    # conn = sqlite3.connect("data/movies.db")

    dbinfo = config_parse()

    conn = psycopg.connect(**dbinfo)
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
        four_k_available INTEGER DEFAULT NULL,
        last_checked TIMESTAMPTZ,
        manually_reviewed INTEGER DEFAULT 0,
        blacklisted INTEGER DEFAULT 0
    )
    """
    )
    conn.commit()

    return conn
