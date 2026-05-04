from datetime import datetime, timedelta
from time import perf_counter
import time
from typing import Any
import requests
import logging
import sqlite3
from .config import RADARR_URL, RADARR_API_KEY

RADARR_HEADERS = {
    "X-Api-Key": f"{RADARR_API_KEY}",
    "Accept": "application/json",
}
ACCEPTED_4K_QUALITIES = ("Bluray-2160p", "WEBDL-2160p", "Remux-2160p")
MIN_4K_RELEASE_MATCHES = 5
STALE_DAYS = 7
REQUEST_DELAY_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 30


def count_4k_releases(release_info: list[dict[str, Any]]) -> int:
    count = 0
    for release in release_info:
        try:
            quality = release["quality"]["quality"]["name"]
        except (KeyError, TypeError) as e:
            logging.warning(
                f"Error parsing radarr json unable to find quality name exception: {e}"
            )
            continue

        if quality in ACCEPTED_4K_QUALITIES:
            count += 1

    return count


def get_movies_for_release_check(
    conn: sqlite3.Connection, n: int | None = None
) -> list[tuple[int, str]]:
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=STALE_DAYS)).isoformat()
    query = """
    SELECT radarr_movie_id, name
    FROM movies
    WHERE radarr_movie_id IS NOT NULL
    AND (
        four_k_available IS NULL
        OR (
        four_k_available = 0
        AND last_checked < ?
        )
    )
    ORDER BY
    four_k_available IS NOT NULL,
    last_checked
    """
    params = (cutoff,)
    if n is not None:
        query += " LIMIT ?"
        params = params + (n,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return rows


def fetch_radarr_releases(
    radarr_movie_id: int, movie_name: str
) -> list[dict[str, Any]] | None:
    time.sleep(REQUEST_DELAY_SECONDS)
    release_info_url = f"{RADARR_URL}/api/v3/release"
    release_info_params = {"movieId": radarr_movie_id}
    try:
        release_info_resp = requests.get(
            release_info_url,
            headers=RADARR_HEADERS,
            params=release_info_params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        release_info = release_info_resp.json()
        return release_info
    except (requests.exceptions.RequestException, ValueError) as e:
        logging.warning(
            f"Radarr query failed for {radarr_movie_id}: {movie_name} exception: {e}"
        )
    return None


def query_movie(conn: sqlite3.Connection, n: int | None = None) -> None:
    cursor = conn.cursor()
    rows = get_movies_for_release_check(conn, n)
    for row in rows:
        radarr_movie_id = row[0]
        movie_name = row[1]
        if radarr_movie_id:
            start = perf_counter()
            release_info = fetch_radarr_releases(radarr_movie_id, movie_name)
            count = count_4k_releases(release_info)
            if count >= MIN_4K_RELEASE_MATCHES:
                state = 1
                logging.info(f"4k Upgrade found for {movie_name}")
            else:
                state = 0
                logging.info(f"4k Upgrade not found for {movie_name}")
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
            elapsed = perf_counter() - start
            logging.info("%s radarr_query took %.2fs", movie_name, elapsed)
        else:
            logging.warning("Could not retrieve radarr_movie_id for a movie.")


def contact_radarr(movie_tmdbid: int) -> int | None:
    request_id_url = f"{RADARR_URL}/api/v3/movie"
    request_id_params = {"tmdbId": f"{movie_tmdbid}"}
    try:
        request_id_resp = requests.get(
            request_id_url,
            headers=RADARR_HEADERS,
            params=request_id_params,
            timeout=REQUEST_TIMEOUT_SECONDS,
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
