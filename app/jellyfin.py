import logging
import os
import sqlite3
from typing import Any
import psycopg
import requests

from .radarr import contact_radarr

from .config import JELLYFIN_URL, JELLYFIN_API_KEY


def fetch_jellyfin_movies() -> dict[str, Any] | None:
    headers = {
        "Authorization": f'MediaBrowser Token="{JELLYFIN_API_KEY}"',
        "Accept": "application/json",
    }

    url = f"{JELLYFIN_URL}/Items"

    params = {
        "recursive": "true",
        "includeItemTypes": "Movie",
        "isHd": "true",
        "fields": "MediaStreams,Path,ProviderIds",
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()
    except (ValueError, requests.exceptions.RequestException) as e:
        logging.error(f"Failed to contact jellyfin for movie data with exception: {e}")
        return None

    return data


def parse_streams(movie: dict) -> tuple[int, int] | tuple[None, None]:
    movie_key = movie["ProviderIds"]["Tmdb"]
    res_height, res_width = (None, None)
    for stream in movie["MediaStreams"]:
        accepted_codecs = ("hevc", "h264")
        if stream.get("Codec") in accepted_codecs:
            try:
                res_height = stream["Height"]
                res_width = stream["Width"]
            except (TypeError, KeyError, ValueError) as e:
                logging.warning(
                    "Skipping stream for movie_key=%s name=%s because of %s: %s",
                    movie_key,
                    movie["Name"],
                    type(e).__name__,
                    e,
                )

    return (res_height, res_width)


def organize_movies(data: dict, conn: psycopg.Connection):
    for movie in data["Items"]:
        movie_key = movie["ProviderIds"]["Tmdb"]
        res_height, res_width = parse_streams(movie)

        if not res_height or not res_width:
            logging.warning(
                f"Skipping movie {int(movie_key)}: {movie['Name']}, missing height and or width"
            )
            continue
        if res_height <= 1080 and res_width <= 1920:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tmdb_id, radarr_movie_id FROM movies WHERE tmdb_id = %s",
                (int(movie_key),),
            )
            row = cursor.fetchone()
            if not row:
                radarr_movie_id = contact_radarr(int(movie_key))
                cursor.execute(
                    """
                    INSERT INTO movies (tmdb_id, radarr_movie_id, year, name, height, width)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        int(movie_key),
                        radarr_movie_id,
                        movie["ProductionYear"],
                        movie["Name"],
                        res_height,
                        res_width,
                    ),
                )
                logging.info(f"Adding movie {movie['Name']} to HD movies list")
            elif row[0] and row[1]:
                logging.info(f"This movie {movie['Name']} is completely indexed")
            elif row[0] and not row[1]:
                radarr_movie_id = contact_radarr(int(movie_key))
                cursor.execute(
                    "UPDATE movies SET radarr_movie_id = %s WHERE tmdb_id = %s",
                    (radarr_movie_id, int(movie_key)),
                )
                logging.info(
                    "Updating movie %s with its radarr_movie_id %s",
                    movie["Name"],
                    radarr_movie_id,
                )

    conn.commit()
