import streamlit as st

st.title("4K Upgrade Checker")

conn = st.connection(
    "movies_db",
    type="sql",
    url="sqlite:///data/movies.db",
)

df = conn.query(
    """
    SELECT tmdb_id, name, year, height, width, four_k_available, last_checked
    FROM movies
    WHERE four_k_available = 1
    ORDER BY name
"""
)

st.dataframe(df, use_container_width=True)
