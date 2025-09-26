import streamlit as st
import pickle
import pandas as pd
import requests
from streamlit_lottie import st_lottie
import json

# Load data
movie_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movie_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# TMDB API Configuration
import os
from dotenv import load_dotenv

load_dotenv()                  # loads .env in dev
API_KEY = os.environ.get("MOVIE_API_KEY")

# App layout
st.set_page_config(page_title="CineMatch", page_icon="🎬", layout="wide")

# Custom CSS for styling
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")  # You can create a style.css file for additional styling


# Load Lottie animation
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)


import time
from functools import lru_cache

@lru_cache(maxsize=1000)
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    try:
        time.sleep(0.4)
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")

        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
        else:
            return "https://via.placeholder.com/500x750?text=No+Poster"
    except requests.exceptions.RequestException as e:
        st.warning(f"Poster not available for movie ID {movie_id}")
        return "https://via.placeholder.com/500x750?text=Poster+Unavailable"


# Fetch movie poster with error handling
# def fetch_poster(movie_id):
#     try:
#         time.sleep(0.5)
#         url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
#         response = requests.get(url)
#         response.raise_for_status()  # Raises an HTTPError for bad responses
#         data = response.json()
#
#         if 'poster_path' in data and data['poster_path']:
#             return f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
#         return "https://via.placeholder.com/500x750?text=No+Poster+Available"
#     except Exception as e:
#         st.error(f"Error fetching poster: {e}")
#         return "https://via.placeholder.com/500x750?text=Error+Loading+Poster"


# Enhanced recommendation function
def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        if movie_index >= similarity.shape[0]:
            st.error("Movie index out of bounds. Please try another movie.")
            return [], []

        distances = similarity[movie_index]
        movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_movies = []
        recommended_movies_posters = []
        recommended_movies_ids = []
        recommended_movies_overviews = []

        for i in movie_list:
            movie_id = movies.iloc[i[0]].id
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_movies_posters.append(fetch_poster(movie_id))
            recommended_movies_ids.append(movie_id)
            recommended_movies_overviews.append(movies.iloc[i[0]].overview[:150] + "...")

        return recommended_movies, recommended_movies_posters, recommended_movies_ids, recommended_movies_overviews
    except Exception as e:
        st.error(f"Error in recommendation: {e}")
        return [], [], [], []




# Header with animation
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎬 CineMatch")
    st.markdown("### Your Personal Movie Recommendation Engine")
with col2:
    lottie_movie = load_lottiefile("movie.json")  # Add a Lottie animation file
    st_lottie(lottie_movie, height=100, key="movie")

# Search section with custom styling
st.markdown("""
    <style>
    .search-box {
        background-color: #0e1117;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    selected_movie_name = st.selectbox(
        "🔍 Search for a movie to get recommendations",
        movies['title'].values,
        index=0,
        help="Type or select a movie title"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Recommendation button with animation
if st.button("🎥 Get Recommendations", use_container_width=True):
    with st.spinner('Finding your perfect movie matches...'):
        names, posters, ids, overviews = recommend(selected_movie_name)

    if names:
        st.success("Here are your recommendations!")

        # Display selected movie
        st.subheader(f"Because you liked: {selected_movie_name}")
        selected_id = movies[movies['title'] == selected_movie_name].iloc[0].id
        selected_poster = fetch_poster(selected_id)
        st.image(selected_poster, width=300)

        # Display recommendations in a grid
        st.subheader("You might also enjoy these movies:")

        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.image(posters[i], use_container_width=True)
                st.markdown(f"**{names[i]}**")
                st.caption(overviews[i])

                # Add a button to get more info
                with st.expander("More Info"):
                    st.write(f"**Overview:** {movies[movies['title'] == names[i]].iloc[0].overview}")
                    genre_data = movies[movies['title'] == names[i]].iloc[0].genres
                    if isinstance(genre_data, list):
                        st.write(f"**Genres:** {', '.join(genre_data)}")
                    else:
                        st.write("**Genres:** Not available")

                    # Add a link to TMDB
                    st.markdown(f"[View on TMDB](https://www.themoviedb.org/movie/{ids[i]})", unsafe_allow_html=True)

        # Add a rating feature
        st.markdown("---")
        st.subheader("Rate these recommendations")
        rating = st.slider("How accurate are these recommendations?", 1, 5, 3)
        if st.button("Submit Rating"):
            st.success(f"Thanks for your {rating}-star rating!")

    else:
        st.warning("Couldn't generate recommendations. Please try another movie.")

# Additional features in sidebar
with st.sidebar:
    st.header("🎭 Discover More")
    st.markdown("""
    - 🎞️ Browse by Genre
    - 🏆 Top Rated Movies
    - 🆕 Recently Released
    - 🎭 Actors/Directors
    """)

    st.markdown("---")
    st.header("🔍 Advanced Filters")
    genre_filter = st.multiselect(
        "Filter by Genre",
        ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance"]
    )
    year_filter = st.slider(
        "Release Year",
        1950, 2023, (2000, 2023)
    )

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 10px;">
        <p>© 2025 CineMatch | Made with ❤️ for movie lovers</p>
    </div>
""", unsafe_allow_html=True)
