# streamlit_app.py
import streamlit as st
import pandas as pd
from data import load_cleaned_data
from recommendation_logic import recommend_destinations
from urllib.parse import quote_plus
from github import Github
import io
import tempfile
import streamlit.components.v1 as components

# PAGE CONFIG
st.set_page_config(page_title="Travel Planning Assistant", layout="wide")

# Inject FontAwesome + styles
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

# Load data
df = load_cleaned_data()

if "ratings_df" not in st.session_state:
    st.session_state["ratings_df"] = df.copy()

TRIP_TYPES = ["culture", "adventure", "nature", "beaches",
              "cuisine", "wellness", "urban", "seclusion"]

# Ensure trip-type columns exist
for col in TRIP_TYPES:
    if col not in st.session_state["ratings_df"].columns:
        st.session_state["ratings_df"][col] = 0

# Utility: Static star display

def display_stars_html(rating, max_stars=5):
    full_star = '<i class="fas fa-star star"></i>'
    empty_star = '<i class="far fa-star star"></i>'
    rating = int(round(rating))
    stars_html = full_star * rating + empty_star * (max_stars - rating)
    st.markdown(stars_html, unsafe_allow_html=True)

# Big interactive star HTML + JS 
def interactive_star_rating_html(key, max_stars=5, default=0):
    """
    Renders an interactive star widget using raw HTML + JS.
    NOTE: This purely affects front-end visuals. To keep server-side values deterministic,
    we pair it with a Streamlit input (radio/slider) that actually stores the rating
    in st.session_state under the same key (see star_rating_half below).
    """
    html_code = f"""
    <div id="{key}" style="display:flex; align-items:center;">
        {''.join([f'<span class="star" data-value="{i}">&#9733;</span>' for i in range(1, max_stars+1)])}
    </div>
    <script>
    (function(){{
        const container = document.getElementById("{key}");
        const stars = container.querySelectorAll(".star");
        let selected = {default};

        function updateStars(val){{
            stars.forEach(s => {{
                if (parseInt(s.dataset.value) <= val) {{
                    s.style.color = "gold";
                }} else {{
                    s.style.color = "#ccc";
                }}
            }});
        }}

        updateStars(selected);

        stars.forEach(star => {{
            star.style.cursor = "pointer";
            star.addEventListener("mouseover", function() {{
                updateStars(parseInt(this.dataset.value));
            }});
            star.addEventListener("mouseout", function() {{
                updateStars(selected);
            }});
            star.addEventListener("click", function() {{
                selected = parseInt(this.dataset.value);
                updateStars(selected);
                // Post a message to parent window in case you want to handle it externally.
                // Streamlit doesn't automatically convert window.postMessage into server-side state.
                window.parent.postMessage({{key:"{key}", value:selected}}, "*");
            }});
        }});
    }})();
    </script>
    """
    components.html(html_code, height=60)

    return st.session_state.get(key, default)


# A server-side rating input that reliably sets st.session_state
def star_rating_half(key, default=0.0):
    """
    A Streamlit radio input that stores a 0.5-step rating in st.session_state[key].
    We show the interactive HTML above it for user experience, but this radio
    is the authoritative value saved on the server.
    """
    if key not in st.session_state:
        st.session_state[key] = default

    options = [i * 0.5 for i in range(11)]  # 0.0 .. 5.0 step 0.5
    # Find the index of current value
    try:
        index = options.index(st.session_state[key])
    except ValueError:
        index = 0

    # Show the interactive visual widget
    interactive_star_rating_html(key, max_stars=5, default=int(round(st.session_state[key])))

    # The radio stores the real value
    rating = st.radio("", options=options, index=index, horizontal=True, key=f"radio_{key}")
    st.session_state[key] = rating

    # Render bigger stars to reflect the numeric rating
    stars_html = ""
    for i in range(1, 6):
        if rating >= i:
            stars_html += f'<span style="font-size:32px; color:gold;">&#9733;</span>'
        elif rating >= i - 0.5:
            stars_html += f'<span style="font-size:32px; color:gold;">&#9734;</span>'
        else:
            stars_html += f'<span style="font-size:32px; color:#ccc;">&#9733;</span>'
    st.markdown(stars_html, unsafe_allow_html=True)

    return rating

# SIDEBAR NAV
st.sidebar.title("Pages:")
section = st.sidebar.radio("Choose Section:", ["Travel Planning Assistant", "Add Travel Rating"])

# Section: Travel Planning Assistant
if section == "Travel Planning Assistant":
    st.markdown("<div style='text-align:center; font-size:32px; font-weight:700;'>🌍 Travel Planning Assistant</div>", unsafe_allow_html=True)

    budget_levels = {"": (0, 0), "Budget": (50, 150), "Mid-range": (150, 350), "Luxury": (350, 1000)}
    budget_options = [f"{lvl} ({low}-{high})" if lvl else "" for lvl, (low, high) in budget_levels.items()]

    # Keep an empty default option so user must pick explicitly
    budget_choice_str = st.selectbox("Select your Budget Level:", budget_options, index=0)
    # Extract text before the space-parenthesis, handle empty selection
    budget_level = budget_choice_str.split(" (")[0] if budget_choice_str else ""

    selected_types = st.multiselect("Select your Trip Types:", TRIP_TYPES)

    if st.button("Get Recommendations"):

        # Use if / elif / else for validation & action
        if not selected_types:
            st.warning("⚠️ Please select at least one trip type.")

        elif not budget_level or budget_level.strip() == "":
            st.warning("⚠️ Please select a budget level.")

        else:
            try:
                recommendations = recommend_destinations(df, budget_level, selected_types)
                if recommendations.empty:
                    st.warning("⚠️ No destinations found for your selections.")
                else:
                    st.session_state["recommendations"] = recommendations.sort_values(by="score", ascending=False).reset_index(drop=True)
            except Exception as e:
                st.error(f"Failed to get recommendations: {e}")

    # Display recommendations if present
    if "recommendations" in st.session_state and not st.session_state["recommendations"].empty:
        recs = st.session_state["recommendations"]
        # show top (include ties)
        if len(recs) > 5:
            top5_score = recs.iloc[4]["score"]
            recs = recs[recs["score"] >= top5_score].reset_index(drop=True)

        st.markdown(f"<div style='font-size:24px; font-weight:600;'>🏖️ Top {len(recs)} Destination Recommendations for You:</div>", unsafe_allow_html=True)

        for idx, row in recs.iterrows():
            st.markdown("---")
            st.markdown(f"**{idx+1}. {row['city']}, {row['country']}**")
            st.markdown(f"**Region:** {row.get('region','')}")
            st.markdown(f"**Description:** {row.get('short_description','')}")
            display_stars_html(row["score"])
            search_url = f"https://www.google.com/search?q={quote_plus(str(row['city']))}+{quote_plus(str(row['country']))}"
            st.markdown(f"[Search More]({search_url})")

# Section: Add Travel Rating
if section == "Add Travel Rating":
    st.markdown("<div style='text-align:center; font-size:32px; font-weight:bold;'>✏️ Add Travel Rating</div>", unsafe_allow_html=True)

    city = st.text_input("City").strip()
    country = st.text_input("Country").strip()
    region = st.text_input("Region").strip()
    short_description = st.text_area("Short Description").strip()

    budget_level_input = st.selectbox("Budget Level", ["Budget", "Mid-range", "Luxury"])

    st.markdown("<h3>⭐ Rate each Trip Type</h3>", unsafe_allow_html=True)

    # Lambda validation
    is_valid = lambda x: bool(x and x.strip())

    # We'll store ratings in st.session_state keys "star_<type>"
    scores = {}
    for t in TRIP_TYPES:
        scores[t] = star_rating_half(f"star_{t}")  # interactive + radio input

    if st.button("Add Rating"):
        # Enforce city, country, region required
        if not is_valid(city):
            st.error("❌ City cannot be empty")

        elif not is_valid(country):
            st.error("❌ Country cannot be empty")

        elif not is_valid(region):
            st.error("❌ Region cannot be empty")

        else:
            try:
                # --- GitHub secrets ---
                token = st.secrets["GITHUB_TOKEN"]
                repo_name = st.secrets["REPO_NAME"]
                file_path = st.secrets["FILE_PATH"]

                g = Github(token)
                repo = g.get_repo(repo_name)

                # Load Excel from GitHub
                contents = repo.get_contents(file_path)
                df_ratings = pd.read_excel(io.BytesIO(contents.decoded_content))

                # Check if city exists (case-insensitive)
                existing = df_ratings[df_ratings['city'].str.lower() == city.lower()]
                if not existing.empty:
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

                    # Save to Excel in memory and update GitHub
                    with tempfile.NamedTemporaryFile() as tmp:
                        df_ratings.to_excel(tmp.name, index=False, engine='openpyxl')
                        with open(tmp.name, "rb") as f:
                            repo.update_file(file_path, f"Add rating for {city}", f.read(), contents.sha)

                    st.session_state['ratings_df'] = df_ratings
                    st.success(f"✅ Added new rating for {city}")

            except Exception as e:
                st.error(f"Failed to add rating: {e}")

    # --- View All Ratings ---
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
