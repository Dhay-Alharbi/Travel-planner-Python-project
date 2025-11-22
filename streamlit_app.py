import streamlit as st
import pandas as pd
from data import load_cleaned_data
from recommendation_logic import recommend_destinations
from urllib.parse import quote_plus
from github import Github
import io
import tempfile

#Page Config
st.set_page_config(page_title="Travel Planning Assistant", layout="wide")

#Styles
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
<style>
.star { 
    color: gold; 
    margin-right: 8px; 
    font-size:28px;  
    cursor:pointer; 
    transition: color 0.2s; 
}
.recommendation-card { 
    border-radius: 8px; 
    padding: 15px; 
    margin-bottom: 10px; 
    background-color: #f9f9f9; 
    box-shadow: 1px 1px 4px rgba(0,0,0,0.1); 
}
</style>
""", unsafe_allow_html=True)

#Sidebar Navigation
st.sidebar.title("Pages:")
section = st.sidebar.radio("Choose Section:", ["Travel Planning Assistant", "Add Travel Rating"])

#Load Data
df = load_cleaned_data()
if "ratings_df" not in st.session_state:
    st.session_state["ratings_df"] = df.copy()

TRIP_TYPES = ["culture", "adventure", "nature", "beaches",
              "cuisine", "wellness", "urban", "seclusion"]

# Ensure missing trip type columns exist
for col in TRIP_TYPES:
    if col not in st.session_state["ratings_df"].columns:
        st.session_state["ratings_df"][col] = 0

#Static star display
def display_stars_html(rating, max_stars=5):
    full_star = '<i class="fas fa-star star"></i>'
    empty_star = '<i class="far fa-star star"></i>'
    rating = int(rating)
    stars_html = full_star * rating + empty_star * (max_stars - rating)
    st.markdown(stars_html, unsafe_allow_html=True)

# Section 1: Travel Planning Assistant

if section == "Travel Planning Assistant":
    st.markdown("<div style='text-align:center; font-size:32px; font-weight:700;'>🌍 Travel Planning Assistant</div>", unsafe_allow_html=True)

    budget_levels = {
        "Budget": (50, 150),
        "Mid-range": (150, 350),
        "Luxury": (350, 1000)
    }

    budget_options = [
        f"{lvl} ({low}-{high}+)" if high >= 1000 else f"{lvl} ({low}-{high})"
        for lvl, (low, high) in budget_levels.items()
    ]

    budget_choice_str = st.selectbox("Select your Budget Level:", budget_options)
    budget_level = budget_choice_str.split(" (")[0]

    selected_types = st.multiselect("Select your Trip Types:", TRIP_TYPES)

    if st.button("Get Recommendations"):
        if not selected_types:
           st.warning("⚠️ Please select budget level.")

        elif not selected_types:
            st.warning("⚠️ Please select at least one trip type.")
        else:
            recs = recommend_destinations(df, budget_level, selected_types)
            st.session_state["recommendations"] = recs.sort_values(by="score", ascending=False)

    if "recommendations" in st.session_state:
        recs = st.session_state["recommendations"]
        st.markdown(f"<div style='font-size:24px; font-weight:600;'>🏖️ Top Destinations for You:</div>", unsafe_allow_html=True)

        # Show results
        for idx, row in recs.iterrows():
            st.markdown("---")
            st.markdown(f"**{idx+1}. {row['city']}, {row['country']}**")
            st.markdown(f"**Region:** {row['region']}")
            st.markdown(f"**Description:** {row['short_description']}")
            display_stars_html(row["score"])

            search_url = f"https://www.google.com/search?q={quote_plus(row['city'])}+{quote_plus(row['country'])}"
            st.markdown(f"[Search More]({search_url})")

# Section 2: Add Travel Rating + View All Ratings
if section == "Add Travel Rating":
    st.markdown("<div style='text-align:center; font-size:32px; font-weight:bold;'>✏️ Add Travel Rating</div>", unsafe_allow_html=True)

    city = st.text_input("City").strip()
    country = st.text_input("Country").strip()
    region = st.text_input("Region").strip()
    short_description = st.text_area("Short Description").strip()
    budget_level_input = st.selectbox("Budget Level", ["Budget", "Mid-range", "Luxury"])

    st.markdown("<h3>⭐ Rate each Trip Type</h3>", unsafe_allow_html=True)

    scores = {}
    for t in TRIP_TYPES:
        scores[t] = st.slider(f"{t.capitalize()} Rating", 0.0, 5.0, 0.0, 0.5)
        
    is_valid = lambda x: bool(x and x.strip())

    if st.button("Add Rating"):
        if not is_valid(city):
            st.error("❌ City cannot be empty")
    
        elif not is_valid(country):
            st.error("❌ Country cannot be empty")
    
        elif not is_valid(region):
            st.error("❌ Region cannot be empty")
                
        else:
            try:
                token = st.secrets["GITHUB_TOKEN"]
                repo_name = st.secrets["REPO_NAME"]
                file_path = st.secrets["FILE_PATH"]

                g = Github(token)
                repo = g.get_repo(repo_name)

                contents = repo.get_contents(file_path)
                df_ratings = pd.read_excel(io.BytesIO(contents.decoded_content))

                if city.lower() in df_ratings["city"].str.lower().values:
                    st.warning(f"⚠️ The city {city} already exists.")
                else:
                    new_row = {
                        "city": city,
                        "country": country,
                        "region": region,
                        "short_description": short_description,
                        "budget_level": budget_level_input
                    }
                    for t in TRIP_TYPES:
                        new_row[t] = float(scores[t])

                    df_ratings = pd.concat([df_ratings, pd.DataFrame([new_row])], ignore_index=True)

                    with tempfile.NamedTemporaryFile() as tmp:
                        df_ratings.to_excel(tmp.name, index=False)
                        with open(tmp.name, "rb") as f:
                            repo.update_file(file_path, f"Add rating for {city}", f.read(), contents.sha)

                    st.session_state["ratings_df"] = df_ratings
                    st.success(f"✅ Added new rating for {city}")

            except Exception as e:
                st.error(f"Failed to add rating: {e}")

    st.markdown("---")
    st.markdown("<h3>🏖️ All Travel Ratings</h3>", unsafe_allow_html=True)

    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        file_path = st.secrets["FILE_PATH"]

        g = Github(token)
        repo = g.get_repo(repo_name)

        contents = repo.get_contents(file_path)
        df_ratings = pd.read_excel(io.BytesIO(contents.decoded_content))

        st.dataframe(df_ratings)
    except Exception as e:
        st.error(f"Failed to load ratings: {e}")

