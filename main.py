import logging
from time import perf_counter
from app.db import setup_db
from app.radarr import process_release_checks, contact_radarr
from app.jellyfin import organize_movies, fetch_jellyfin_movies

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    conn = setup_db()
    start = perf_counter()

    data = fetch_jellyfin_movies()
    if data is None:
        logging.error("fetch_jellyfin_movies returned None")
        return
    logging.info("fetch_jellyfin_movies() took %.2fs", perf_counter() - start)

    start = perf_counter()
    organize_movies(data, conn)
    logging.info("organize_movies() took %.2fs", perf_counter() - start)

    start = perf_counter()
    process_release_checks(conn)
    logging.info("process_release_checks() took %.2fs", perf_counter() - start)


if __name__ == "__main__":
    main()
