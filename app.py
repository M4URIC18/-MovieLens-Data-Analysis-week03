# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from data_processor import load_and_clean_data, explode_genres, add_age_group
from helper_Functions import zip_to_state
from examine_data import run_quick_eda

st.set_page_config(layout="wide", page_title="MovieLens Ratings Dashboard")

@st.cache_data
def load_data(path="data/movie_ratings.csv"):
    df = load_and_clean_data(path)
    df_exp = explode_genres(df, genres_col="genres")
    df_exp = add_age_group(df_exp)
    # add state (may be slow, cache)
    if "state" not in df_exp.columns:
        df_exp["state"] = df_exp["zip_code"].apply(lambda z: zip_to_state(str(z)))
    return df, df_exp

df, df_exp = load_data()

st.title("MovieLens (200k) — Ratings Dashboard")
st.write("Interactive dashboard to analyze MovieLens ratings. Use filters in the sidebar to slice the data.")

# Sidebar filters
st.sidebar.header("Filters")
ages = st.sidebar.slider("Age range", int(df.age.min()), int(df.age.max()), (18, 40))
genders = st.sidebar.multiselect("Gender", options=sorted(df.gender.unique()), default=list(df.gender.unique()))
occupations = st.sidebar.multiselect("Occupation (sample)", options=sorted(df.occupation.unique()), default=[])
genres_filter = st.sidebar.multiselect("Genres", options=sorted(set(sum(df["genres"].str.split("|").tolist(), []))), default=[])
min_ratings = st.sidebar.slider("Minimum # ratings for movie lists", 10, 500, 50)

# apply filters to exploded dataframe
mask = (df_exp["age"].between(ages[0], ages[1])) & (df_exp["gender"].isin(genders))
if occupations:
    mask &= df_exp["occupation"].isin(occupations)
if genres_filter:
    mask &= df_exp["genres"].apply(lambda g: any(gg in g.split("|") for gg in genres_filter))
filtered = df_exp[mask].copy()

st.markdown("### Dataset snapshot")
with st.expander("Show raw (filtered) data"):
    st.dataframe(filtered.sample(min(500, len(filtered))) if len(filtered) > 0 else filtered)

# 1. Genre breakdown (counts)
st.header("1) Breakdown of genres for rated movies")
genre_counts = filtered.groupby("genres")["movie_id"].nunique().sort_values(ascending=False).reset_index()
# When exploded, genres are single strings (we used explode_genres)
fig1 = px.bar(genre_counts, x="genres", y="movie_id", labels={"movie_id":"# movies (rated)", "genres":"Genre"}, title="Number of unique movies per genre (in filtered data)")
st.plotly_chart(fig1, use_container_width=True)

# 2. Which genres have the highest viewer satisfaction (mean rating)
st.header("2) Viewer satisfaction by genre (mean rating)")
genre_rating = filtered.groupby("genres").agg(mean_rating=("rating","mean"), n_ratings=("rating","count")).reset_index()
genre_rating = genre_rating.sort_values("mean_rating", ascending=False)
fig2 = px.scatter(genre_rating, x="n_ratings", y="mean_rating", size="n_ratings", hover_name="genres",
                  labels={"n_ratings":"# Ratings", "mean_rating":"Mean Rating"}, title="Mean rating vs #ratings per genre")
st.plotly_chart(fig2, use_container_width=True)
st.write("Top genres by mean rating (min 50 ratings):")
st.dataframe(genre_rating[genre_rating.n_ratings>=50].sort_values("mean_rating", ascending=False).head(10))

# 3. How mean rating changes across movie release years
st.header("3) Mean rating across movie release years")
year_stats = filtered.groupby("year").agg(mean_rating=("rating","mean"), n_ratings=("rating","count")).reset_index()
year_stats = year_stats[year_stats.n_ratings >= 5]  # small smoothing filter
fig3 = px.line(year_stats.sort_values("year"), x="year", y="mean_rating", markers=True, labels={"year":"Release Year", "mean_rating":"Mean Rating"}, title="Mean rating by movie release year")
st.plotly_chart(fig3, use_container_width=True)

# 4. Top rated movies with minimum ratings (50 and 150)
st.header("4) Best-rated movies (with minimum number of ratings)")
movie_stats = filtered.groupby(["movie_id", "title"]).agg(mean_rating=("rating","mean"), n_ratings=("rating","count")).reset_index()
top_50 = movie_stats[movie_stats.n_ratings >= 50].sort_values(["mean_rating","n_ratings"], ascending=[False, False]).head(5)
top_150 = movie_stats[movie_stats.n_ratings >= 150].sort_values(["mean_rating","n_ratings"], ascending=[False, False]).head(5)

col1, col2 = st.columns(2)
with col1:
    st.subheader(f"Top 5 movies with ≥ {min_ratings} ratings")
    st.dataframe(movie_stats[movie_stats.n_ratings >= min_ratings].sort_values(["mean_rating","n_ratings"], ascending=[False,False]).head(10))
with col2:
    st.subheader("Top 5 movies with ≥150 ratings")
    st.dataframe(top_150)

# Extra Credit: rating change by viewer age for selected genres
st.header("Extra: How rating changes as viewer age increases (by genre)")
all_genres = genre_rating.sort_values("n_ratings", ascending=False).genres.tolist()
selected_genres = st.multiselect("Pick genres to inspect (age vs rating)", options=all_genres, default=all_genres[:4])

if selected_genres:
    # build age bins and compute mean rating per age for each genre
    age_bins = list(range(10, 101, 5))
    age_labels = [f"{a}-{a+4}" for a in age_bins[:-1]]
    df_age = filtered.copy()
    df_age["age_group"] = pd.cut(df_age["age"], bins=age_bins, labels=age_labels, right=False)
    rows = []
    for g in selected_genres:
        tmp = df_age[df_age["genres"]==g].groupby("age_group").agg(mean_rating=("rating","mean"), n=("rating","count")).reset_index()
        tmp["genre"] = g
        rows.append(tmp)
    if rows:
        df_plot = pd.concat(rows)
        fig_age = px.line(df_plot, x="age_group", y="mean_rating", color="genre", markers=True,
                          labels={"age_group":"Viewer age group", "mean_rating":"Mean rating"}, title="Mean rating by viewer age group for selected genres")
        st.plotly_chart(fig_age, use_container_width=True)

# Plot: #ratings vs mean rating per genre (correlation)
st.header("Plot: Number of ratings vs Mean rating per genre")
fig_corr = px.scatter(genre_rating, x="n_ratings", y="mean_rating", hover_name="genres", title="Number of ratings vs Mean rating (per genre)")
st.plotly_chart(fig_corr, use_container_width=True)
st.write("Pearson correlation between #ratings and mean rating: ", np.round(genre_rating.n_ratings.corr(genre_rating.mean_rating), 3))

# Run quick EDA in separate tab
if st.sidebar.button("Run quick EDA (console)"):
    with st.spinner("Running quick EDA..."):
        run_quick_eda(df)

st.info("Note: Movies can belong to multiple genres. Exploding genres counts them multiple times for preference profiling but not for market-share.")

st.markdown("---")
st.markdown("Built with ❤️ — change filters to re-run analyses. Data is cached for performance.")
