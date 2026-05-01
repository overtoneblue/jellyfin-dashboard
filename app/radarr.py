from datetime import datetime
import os
import time
import requests
import logging
import sqlite3
from .config import RADARR_URL, RADARR_API_KEY

RADARR_HEADERS = {
    "X-Api-Key": f"{RADARR_API_KEY}",
    "Accept": "application/json",
}


def query_movie(conn: sqlite3.Connection, n: int | None = None):
    cursor = conn.cursor()
    query = "SELECT radarr_movie_id, name FROM movies WHERE four_k_available IS NULL"
    params = ()
    if n is not None:
        query += " LIMIT ?"
        params = (n,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    for row in rows:
        radarr_movie_id = row[0]
        movie_name = row[1]
        if radarr_movie_id:
            time.sleep(5.00)
            release_info_url = f"{RADARR_URL}/api/v3/release"
            release_info_params = {"movieId": radarr_movie_id}
            try:
                release_info_resp = requests.get(
                    release_info_url,
                    headers=RADARR_HEADERS,
                    params=release_info_params,
                    timeout=30,
                )

                release_info = release_info_resp.json()
            except (requests.exceptions.RequestException, ValueError) as e:
                logging.warning(
                    f"Radarr query failed for {radarr_movie_id}: {movie_name} exception: {e}"
                )
                continue
            count = 0
            for release in release_info:
                try:
                    quality = release["quality"]["quality"]["name"]
                except (KeyError, TypeError) as e:
                    logging.warning(
                        f"Error parsing radarr json unable to find quality name exception: {e}"
                    )
                    continue

                accepted_qualites = ("Bluray-2160p", "WEBDL-2160p", "Remux-2160p")
                if quality in accepted_qualites:
                    count += 1
            if count >= 3:
                state = 1
                logging.info(f"4k Upgrade found for {movie_name}")
            else:
                state = 0
            last_checked = datetime.now().isoformat()
            cursor.execute(
                "UPDATE movies SET four_k_available = ?, last_checked = ? WHERE radarr_movie_id = ?",
                (
                    state,
                    last_checked,
                    radarr_movie_id,
                ),
            )
            conn.commit()

        else:
            logging.warning("Could not retrieve radarr_movie_id for a movie.")


def contact_radarr(movie_tmdbid: int) -> int | None:
    request_id_url = f"{RADARR_URL}/api/v3/movie"
    request_id_params = {"tmdbId": f"{movie_tmdbid}"}
    try:
        request_id_resp = requests.get(
            request_id_url, headers=RADARR_HEADERS, params=request_id_params, timeout=30
        )
        movie_data = request_id_resp.json()
        radarr_movie_id = movie_data[0]["id"]

    except (
        IndexError,
        ValueError,
        KeyError,
        requests.exceptions.RequestException,
    ) as e:
        logging.error(
            f"Failed to contact radarr for movie {movie_tmdbid}, with error: {e}"
        )
        return None
    return radarr_movie_id
