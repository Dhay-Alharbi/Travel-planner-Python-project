# streamlit_app_ui.py
import streamlit as st
import pandas as pd
from data import load_cleaned_data
from recommendation_logic import recommend_destinations
from urllib.parse import quote_plus
import streamlit.components.v1 as components
from github import Github
import io
import tempfile

# --- Page Config ---
st.set_page_config(page_title="🌍 Travel Planning Assistant", layout="wide")

# --- Inject FontAwesome + Custom CSS ---
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
<style>
    /* Star styles */
    .star { color: gold; margin-right: 8px; font-size:30px; cursor:pointer; transition: 0.2s; }
    .star:hover { transform: scale(1.2); }
    
    /* Card styles */
    .recommendation-card {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        background-color: #fdfdfd;
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
        transition: transform 0.2s;
    }
    .recommendation-card:hover {
        transform: scale(1.02);
    }

    /* Section titles */
    .section-title {
        font-size: 32px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-title {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
st.sidebar.title("📌 Navigation")
section = st.sidebar.radio("Choose Section:", ["Travel Planning Assistant", "Add Travel Rating", "All Travel Ratings"])

# --- Load dataset ---
df = load_cleaned_data()

if 'ratings_df' not in st.session_state:
    st.session_state['ratings_df'] = df.copy()

TRIP_TYPES = ["culture", "adventure", "nature", "beaches", "cuisine", "wellness", "urban", "seclusion"]

# Ensure trip type columns exist
for col in TRIP_TYPES:
    if col not in st.session_state['ratings_df'].columns:
        st.session_state['ratings_df'][col] = 0

# -----------------------
# Functions for Stars
# -----------------------
def display_stars_html(rating, max_stars=5):
    full_star = '<i class="fas fa-star star"></i>'
    empty_star = '<i class="far fa-star star"></i>'
    rating = int(rating)
    st.markdown(full_star*rating + empty_star*(max_stars-rating), unsafe_allow_html=True)

def interactive_star_rating_html(key, max_stars=5, default=0):
    html_code = f"""
    <div id="{key}">
        {''.join([f'<span class="star" data-value="{i}">&#9733;</span>' for i in range(1, max_stars+1)])}
    </div>
    <script>
        const container_{key} = document.getElementById("{key}");
        const stars_{key} = container_{key}.querySelectorAll(".star");
        let selected_{key} = {default};
        function updateStars(val){{
            stars_{key}.forEach(s => s.style.color = s.dataset.value <= val ? "gold" : "#ccc");
        }}
        updateStars(selected_{key});
        stars_{key}.forEach(star => {{
            star.addEventListener("click", function(){{
                selected_{key} = parseInt(this.dataset.value);
                updateStars(selected_{key});
                window.parent.postMessage({{key:"{key}", value:selected_{key}}}, "*");
            }});
        }});
    </script>
    """
    components.html(html_code, height=100)
    return st.session_state.get(key, default)

# ========================
# SECTION 1: Travel Planning Assistant
# ========================
if section == "Travel Planning Assistant":
    st.markdown("<div class='section-title'>🌍 Travel Planning Assistant</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        budget_levels = {"Budget": (50,150), "Mid-range": (150,350), "Luxury": (350,1000)}
        budget_options = [f"{lvl} ({low}-{high}+)" if high>=1000 else f"{lvl} ({low}-{high})" for lvl,(low,high) in budget_levels.items()]
        budget_choice_str = st.selectbox("Select your Budget Level:", budget_options)
        budget_level = budget_choice_str.split(" (")[0]

        selected_types = st.multiselect("Select your Trip Types:", TRIP_TYPES)

        if st.button("Get Recommendations"):
            if not selected_types:
                st.warning("⚠️ Please select at least one trip type.")
            else:
                recommendations = recommend_destinations(df, budget_level, selected_types)
                st.session_state['recommendations'] = recommendations.sort_values(by='score', ascending=False).reset_index(drop=True)

    with col2:
        if 'recommendations' in st.session_state:
            recs = st.session_state['recommendations']
            if len(recs) > 5:
                top5_score = recs.iloc[4]['score']
                recs = recs[recs['score'] >= top5_score].reset_index(drop=True)

            st.markdown(f"<div class='sub-title'>🏖️ Top {len(recs)} Destination Recommendations:</div>", unsafe_allow_html=True)
            for idx,row in recs.iterrows():
                st.markdown("<div class='recommendation-card'>", unsafe_allow_html=True)
                st.markdown(f"**{idx+1}. {row['city']}, {row['country']}**")
                st.markdown(f"**Region:** {row['region']}")
                st.markdown(f"**Description:** {row['short_description']}")
                display_stars_html(row['score'])
                search_url = f"https://www.google.com/search?q={quote_plus(row['city'])}+{quote_plus(row['country'])}"
                st.markdown(f"[🔍 Search More]({search_url})")
                st.markdown("</div>", unsafe_allow_html=True)

# ========================
# SECTION 2: Add Travel Rating
# ========================
if section == "Add Travel Rating":
    st.markdown("<div class='section-title'>✏️ Add Travel Rating</div>", unsafe_allow_html=True)
    with st.form("add_rating_form"):
        city = st.text_input("City").strip()
        country = st.text_input("Country").strip()
        region = st.text_input("Region").strip()
        short_description = st.text_area("Short Description").strip()
        budget_level_input = st.selectbox("Budget Level", ["Budget", "Mid-range", "Luxury"])
        st.markdown("<h3>⭐ Rate Each Trip Type</h3>", unsafe_allow_html=True)

        scores = {}
        for t in TRIP_TYPES:
            st.markdown(f"**{t.capitalize()}**")
            scores[t] = interactive_star_rating_html(f"star_{t}")

        submitted = st.form_submit_button("Add Rating")
        if submitted:
            if not city or not country or not region:
                st.error("❌ City, Country, and Region cannot be empty")
            else:
                try:
                    token = st.secrets["GITHUB_TOKEN"]
                    repo_name = st.secrets["REPO_NAME"]
                    file_path = st.secrets["FILE_PATH"]

                    g = Github(token)
                    repo = g.get_repo(repo_name)
                    contents = repo.get_contents(file_path)
                    df_ratings = pd.read_excel(io.BytesIO(contents.decoded_content))

                    existing = df_ratings[df_ratings['city'].str.lower() == city.lower()]
                    if not existing.empty:
                        st.warning(f"⚠️ The city {city} already exists.")
                    else:
                        new_row = {"city": city, "country": country, "region": region,
                                   "short_description": short_description, "budget_level": budget_level_input}
                        for t in TRIP_TYPES: new_row[t] = float(scores[t])
                        df_ratings = pd.concat([df_ratings, pd.DataFrame([new_row])], ignore_index=True)

                        with tempfile.NamedTemporaryFile() as tmp:
                            df_ratings.to_excel(tmp.name, index=False, engine='openpyxl')
                            with open(tmp.name, "rb") as f:
                                repo.update_file(file_path, f"Add rating for {city}", f.read(), contents.sha)

                        st.session_state['ratings_df'] = df_ratings
                        st.success(f"✅ Added new rating for {city}")
                except Exception as e:
                    st.error(f"Failed to add rating: {e}")

# ========================
# SECTION 3: All Travel Ratings
# ========================
if section == "All Travel Ratings":
    st.markdown("<div class='section-title'>🏖️ All Travel Ratings</div>", unsafe_allow_html=True)
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        file_path = st.secrets["FILE_PATH"]

        g = Github(token)
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(file_path)
        df_ratings = pd.read_excel(io.BytesIO(contents.decoded_content))
        st.dataframe(df_ratings, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load ratings: {e}")
