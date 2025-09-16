# examine_data.py
import pandas as pd

def run_quick_eda(df):
    """
    Prints quick EDA summaries to console (useful when button clicked in app).
    """
    print("=== QUICK EDA ===")
    print("Shape:", df.shape)
    print("\nColumns and dtypes:")
    print(df.dtypes)
    print("\nMissing value counts:")
    print(df.isna().sum())
    print("\nRating distribution:")
    print(df["rating"].value_counts().sort_index())
    if "genres" in df.columns:
        unique_genres = set(sum(df["genres"].dropna().astype(str).str.split("|").tolist(), []))
        print(f"\nUnique genres (sample): {sorted(list(unique_genres))[:30]} (total {len(unique_genres)})")
    if "year" in df.columns:
        print("\nYear range:", df["year"].min(), "-", df["year"].max())
    # Print basic stats by movie
    movie_stats = df.groupby(["movie_id", "title"]).rating.agg(["count","mean"]).reset_index().sort_values("count", ascending=False)
    print("\nTop 10 movies by # ratings (console):")
    print(movie_stats.head(10).to_string(index=False))
    print("=== END EDA ===")
