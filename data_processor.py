# data_processor.py
import pandas as pd
import numpy as np
from datetime import datetime

def load_and_clean_data(path="data/movie_ratings.csv"):
    """
    Load CSV and perform basic cleaning:
      - parse timestamps (if present)
      - ensure year/decade types
      - clean genres formatting (pipe-separated)
      - drop duplicates
    Returns the cleaned dataframe (no genre explode).
    """
    df = pd.read_csv(path)
    # Basic types
    if "timestamp" in df.columns:
        # try common timestamp formats
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s', errors='coerce')
        except Exception:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
    # rating_year fallback
    if "rating_year" not in df.columns and "timestamp" in df.columns:
        df["rating_year"] = df["timestamp"].dt.year
    # ensure year numeric
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors='coerce')
    if "decade" in df.columns:
        df["decade"] = df["decade"].astype(str)
    # fill missing genres with empty string
    if "genres" in df.columns:
        df["genres"] = df["genres"].fillna("").astype(str)
        # normalize delimiter (some datasets use '|' or '|' already; ensure consistent)
        df["genres"] = df["genres"].str.replace(" ", "", regex=False)
        df["genres"] = df["genres"].str.replace(",", "|", regex=False)  # if someone used commas
    # drop exact duplicates
    df = df.drop_duplicates()
    # ensure age numeric
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors='coerce')
    return df

def explode_genres(df, genres_col="genres"):
    """
    Explodes the genres column into single-genre rows.
    Returns a new dataframe where each row has exactly one genre in 'genres' column.
    Also creates a 'genres_list' column with the original list.
    """
    df = df.copy()
    # Keep original genres_list for multi-genre movies
    df["genres_list"] = df[genres_col].apply(lambda s: [g for g in s.split("|") if g])
    # explode
    df_exploded = df.explode("genres_list")
    df_exploded = df_exploded.rename(columns={"genres_list": "genres"})
    # For movies that had no genre, fill with 'Unknown'
    df_exploded["genres"] = df_exploded["genres"].fillna("Unknown")
    return df_exploded

def add_age_group(df, bin_size=10):
    """
    Adds an 'age_group' column for easier grouping (like 0-9,10-19,...).
    """
    df = df.copy()
    min_age = int(np.nanmin(df["age"].dropna())) if "age" in df.columns else 0
    max_age = int(np.nanmax(df["age"].dropna())) if "age" in df.columns else 100
    bins = list(range(0, max_age + bin_size, bin_size))
    labels = [f"{b}-{b+bin_size-1}" for b in bins[:-1]]
    df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=False)
    return df

def top_movies(df, min_ratings=50, top_n=5):
    """
    Returns the top_n movies with at least min_ratings (by mean rating then by n_ratings).
    """
    grouped = df.groupby(["movie_id", "title"]).agg(mean_rating=("rating","mean"), n_ratings=("rating","count")).reset_index()
    res = grouped[grouped.n_ratings >= min_ratings].sort_values(["mean_rating","n_ratings"], ascending=[False, False]).head(top_n)
    return res
