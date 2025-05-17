# ==============================================================================
# STREAMLIT APP - PICK YOUR PREFERENCE TAB ----
# ==============================================================================
# streamlit run src/app/app_tab_1.py

# ------------------------------------------------------------------------------
# SETUP ----
# ------------------------------------------------------------------------------

# Import Libraries ----
import streamlit as st
import pandas as pd
import datetime
import os

# ------------------------------------------------------------------------------
# APP CONFIGURATION ----
# ------------------------------------------------------------------------------

# --- Page Configuration ---
st.set_page_config(
    page_title            = "Pick Your Preference",
    page_icon             = "🎧",
    layout                = "centered",
    initial_sidebar_state = "expanded"
)

# --- Paths ---
css_path = "src/app/style.css"
data_path = "data/dev/"

# --- Load Custom CSS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css(css_path) # Adjust path as necessary


# --- Session State Initialization ---
def initialize_session_state():
    if "filters_applied" not in st.session_state:
        st.session_state.filters_applied = False
    if "filtered_sets" not in st.session_state:
        st.session_state.filtered_sets = pd.DataFrame()
    # Initialize filter defaults
    if "selected_djs" not in st.session_state:
        st.session_state.selected_djs = []
    if "selected_genres" not in st.session_state:
        st.session_state.selected_genres = []
    if "date_range" not in st.session_state:
        st.session_state.date_range = (datetime.date(2020, 1, 1), datetime.date.today()) # Default date range
    if "play_count_range" not in st.session_state:
        st.session_state.play_count_range = (0, 10000) # Placeholder, adjust based on data
    if "fav_count_range" not in st.session_state:
        st.session_state.fav_count_range = (0, 1000) # Placeholder, adjust based on data
    if "energy_range" not in st.session_state:
        st.session_state.energy_range = (0, 10) # Placeholder, adjust based on data
    if "bpm_range" not in st.session_state:
        st.session_state.bpm_range = (60, 180) # Placeholder, adjust based on data

initialize_session_state()

# --- Data Loading and Preprocessing ---
@st.cache_data
def load_data(csv_path = os.path.join(data_path, "dj_shows_test.csv")): # Placeholder for dataset path
    try:
        df = pd.read_csv(csv_path)
        # --- Preprocessing Steps ---
        # Convert string tags to list
        if "show_tags_cleaned" in df.columns:
            df["show_tags_cleaned"] = df["show_tags_cleaned"].apply(
                lambda x: [tag.strip() for tag in x.strip("[]").replace("'", "").split(",")] if isinstance(x, str) else []
            )
        else:
            st.warning("Column 'show_tags_cleaned' not found. Genre filtering might not work as expected.")
            df["show_tags_cleaned"] = [[] for _ in range(len(df))]


        # Standardize date formats
        if "date_uploaded" in df.columns:
            df["date_uploaded"] = pd.to_datetime(df["date_uploaded"], errors='coerce').dt.date
        else:
            st.warning("Column 'date_uploaded' not found. Date filtering might not work as expected.")
            df["date_uploaded"] = pd.NaT

        # Fill missing numeric values for sliders to prevent errors
        numeric_cols_ranges = {
            "play_count": (0, 10000),
            "fav_count": (0, 1000),
            "energy_min": (0, 10),
            "energy_max": (0, 10),
            "bpm_min": (60, 180),
            "bpm_max": (60, 180)
        }
        for col, (default_min, _) in numeric_cols_ranges.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default_min)
            else:
                st.warning(f"Column '{col}' not found. Related filters might not work as expected.")
                df[col] = default_min # Add column with default if missing

        return df
    except FileNotFoundError:
        st.error(f"Error: The dataset file was not found at '{csv_path}'. Please ensure the file exists.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred while loading or preprocessing the data: {e}")
        return pd.DataFrame()

# Load data
df_sets = load_data() # Ensure you have a CSV file in 'data/dj_sets.csv' or update path

# --- Helper Functions ---
def get_unique_values(data_frame, column_name):
    if column_name in data_frame.columns and not data_frame[column_name].empty:
        return sorted(list(data_frame[column_name].explode().astype(str).dropna().unique()))
    return []

all_djs = get_unique_values(df_sets, "name")
all_genres = get_unique_values(df_sets, "show_tags_cleaned")

if "bachata" in all_genres:
    all_genres.remove("bachata")

if "salsa" in all_genres:
    all_genres.remove("salsa")


def get_min_max_values(data_frame, column_name, default_min=0, default_max=100):
    if column_name in data_frame.columns and not data_frame[column_name].dropna().empty:
        return (int(data_frame[column_name].min()), int(data_frame[column_name].max()))
    return (default_min, default_max)

play_count_min_max = get_min_max_values(df_sets, "play_count", 0, 10000)
fav_count_min_max = get_min_max_values(df_sets, "fav_count", 0, 1000)
energy_min_max = get_min_max_values(df_sets, "energy_min", 0, 10) # Assuming energy_min for range
bpm_min_max = get_min_max_values(df_sets, "bpm_min", 60, 180) # Assuming bpm_min for range


# Update session state defaults if data loaded successfully
if not df_sets.empty:
    if "play_count_range" not in st.session_state or st.session_state.play_count_range == (0,10000):
         st.session_state.play_count_range = play_count_min_max
    if "fav_count_range" not in st.session_state or st.session_state.fav_count_range == (0,1000):
        st.session_state.fav_count_range = fav_count_min_max
    if "energy_range" not in st.session_state or st.session_state.energy_range == (0,10): # Assuming energy_min for range
        st.session_state.energy_range = energy_min_max
    if "bpm_range" not in st.session_state or st.session_state.bpm_range == (60,180): # Assuming bpm_min for range
        st.session_state.bpm_range = bpm_min_max
    if "date_range" not in st.session_state or st.session_state.date_range == (datetime.date(2020, 1, 1), datetime.date.today()):
        min_date_data = df_sets["date_uploaded"].dropna().min()
        max_date_data = df_sets["date_uploaded"].dropna().max()
        if pd.notna(min_date_data) and pd.notna(max_date_data):
            st.session_state.date_range = (min_date_data, max_date_data)


# --- Filter Logic ---
def apply_filters(df):
    filtered_df = df.copy()

    # DJ/Artist Filter
    if st.session_state.selected_djs:
        filtered_df = filtered_df[filtered_df["name"].isin(st.session_state.selected_djs)]

    # Genre/Tag Filter (partial matching)
    if st.session_state.selected_genres:
        filtered_df = filtered_df[
            filtered_df["show_tags_cleaned"].apply(
                lambda tags: any(selected_genre.lower() in tag.lower() for tag in tags for selected_genre in st.session_state.selected_genres) if isinstance(tags, list) else False
            )
        ]

    # Date Range Filter
    start_date, end_date = st.session_state.date_range
    if "date_uploaded" in filtered_df.columns:
        filtered_df["date_uploaded_comp"] = pd.to_datetime(filtered_df["date_uploaded"], errors='coerce').dt.date
        filtered_df = filtered_df[
            (filtered_df["date_uploaded_comp"] >= start_date) &
            (filtered_df["date_uploaded_comp"] <= end_date)
        ]
        filtered_df = filtered_df.drop(columns=["date_uploaded_comp"])


    # Play Count Filter
    min_plays, max_plays = st.session_state.play_count_range
    if "play_count" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["play_count"] >= min_plays) & (filtered_df["play_count"] <= max_plays)
        ]

    # Favorites Count Filter
    min_favs, max_favs = st.session_state.fav_count_range
    if "fav_count" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["fav_count"] >= min_favs) & (filtered_df["fav_count"] <= max_favs)
        ]

    # Energy Level Filter (assumes 'energy_min' and 'energy_max' columns exist)
    min_energy, max_energy = st.session_state.energy_range
    if "energy_min" in filtered_df.columns and "energy_max" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["energy_min"] <= max_energy) & (filtered_df["energy_max"] >= min_energy)
        ]
    elif "energy_min" in filtered_df.columns: # Fallback if only one energy column
         filtered_df = filtered_df[(filtered_df["energy_min"] >= min_energy) & (filtered_df["energy_min"] <= max_energy)]


    # BPM Filter (assumes 'bpm_min' and 'bpm_max' columns exist)
    min_bpm, max_bpm = st.session_state.bpm_range
    if "bpm_min" in filtered_df.columns and "bpm_max" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["bpm_min"] <= max_bpm) & (filtered_df["bpm_max"] >= min_bpm)
        ]
    elif "bpm_min" in filtered_df.columns: # Fallback if only one BPM column
        filtered_df = filtered_df[(filtered_df["bpm_min"] >= min_bpm) & (filtered_df["bpm_min"] <= max_bpm)]

    # Tags Filter
    if "show_tags_cleaned" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["show_tags_cleaned"].apply(
                lambda tags: any(tag in all_genres for tag in tags)
            )
        ]



    st.session_state.filtered_sets = filtered_df
    st.session_state.filters_applied = True
    return filtered_df

# --- Reset Filters ---
def reset_filters():
    st.session_state.selected_djs = []
    st.session_state.selected_genres = []

    # Reset to data-derived min/max or initial defaults
    min_date_data = df_sets["date_uploaded"].dropna().min() if "date_uploaded" in df_sets.columns and not df_sets["date_uploaded"].dropna().empty else datetime.date(2020, 1, 1)
    max_date_data = df_sets["date_uploaded"].dropna().max() if "date_uploaded" in df_sets.columns and not df_sets["date_uploaded"].dropna().empty else datetime.date.today()
    st.session_state.date_range = (min_date_data if pd.notna(min_date_data) else datetime.date(2020,1,1), max_date_data if pd.notna(max_date_data) else datetime.date.today())

    st.session_state.play_count_range = play_count_min_max
    st.session_state.fav_count_range = fav_count_min_max
    st.session_state.energy_range = energy_min_max
    st.session_state.bpm_range = bpm_min_max

    st.session_state.filters_applied = False
    st.session_state.filtered_sets = pd.DataFrame()
    st.rerun()

# --- Helper function to display sets ---
def display_sets_section(title, sets_df, empty_message="No sets to display in this section.", success_message=None):
    st.subheader(title)
    if success_message:
        st.success(success_message)

    if not sets_df.empty:
        for index, row in sets_df.iterrows():
            card_html = f"""
            <div class="set-card">
                <div class="card-header">
                    <h4>{row.get('name', 'N/A')} - {row.get('title', 'Untitled Set')}</h4>
                </div>
                <div class="card-body">
                    <div class="tags-section">
                        {''.join([f'<span class="tag">{tag}</span>' for tag in row.get('show_tags_cleaned', [])[:5]])}
                    </div>
                    <div class="stats-section">
                        <span><strong>Plays:</strong> {row.get('play_count', 'N/A'):,}</span>
                        <span><strong>Favs:</strong> {row.get('fav_count', 'N/A'):,}</span>
                        <span><strong>Uploaded:</strong> {row.get('date_uploaded', 'N/A')}</span>
                    </div>
                </div>
                <div class="card-footer">
                    <a href="{row.get('show_url', '#' )}" target="_blank" class="listen-button">
                        Listen on Mixcloud
                    </a>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            st.markdown("---") # Separator
    else:
        st.info(empty_message)

# --- UI Layout ---
st.title("🎧 Pick Your Preference")
st.subheader("Discover new music sets based on your preferences.")
st.markdown("---")

# --- Sidebar for Filters ---
with st.sidebar:
    st.header("🔍 Filters")

    with st.expander("👤 Artist & Genre", expanded=True):
        st.session_state.selected_djs = st.multiselect(
            "Select DJ/Artist (max 5)",
            options        = all_djs,
            # default        = st.session_state.selected_djs,
            default        = all_djs,
            max_selections = 5,
            key            = "djs_multiselect"
        )
        st.session_state.selected_genres = st.multiselect(
            "Select Genre/Tag (max 5)",
            options        = all_genres,
            # default        = st.session_state.selected_genres,
            default        = all_genres[:5], # Default to first 5 genres
            max_selections = 5,
            key            = "genres_multiselect"
        )

    with st.expander("📅 Date & Popularity", expanded=True):
        # Date Range
        min_date_overall = df_sets["date_uploaded"].dropna().min() if "date_uploaded" in df_sets.columns and not df_sets["date_uploaded"].dropna().empty else datetime.date(2000, 1, 1)
        max_date_overall = df_sets["date_uploaded"].dropna().max() if "date_uploaded" in df_sets.columns and not df_sets["date_uploaded"].dropna().empty else datetime.date.today()

        # Ensure default range is valid
        current_start_date, current_end_date = st.session_state.date_range
        if not (isinstance(current_start_date, datetime.date) and isinstance(current_end_date, datetime.date)):
            current_start_date, current_end_date = min_date_overall, max_date_overall
        else:
            if current_start_date < min_date_overall: current_start_date = min_date_overall
            if current_end_date > max_date_overall: current_end_date = max_date_overall
            if current_start_date > current_end_date : current_start_date = current_end_date


        if min_date_overall <= max_date_overall :
            st.session_state.date_range = st.date_input(
                "Select Upload Date Range",
                value=(current_start_date, current_end_date),
                min_value=min_date_overall,
                max_value=max_date_overall,
                key="date_range_picker"
            )
        else:
            st.warning("Not enough date data to create a valid range. Please check your dataset.")
            # Fallback to a default if data is insufficient
            st.session_state.date_range = st.date_input(
                "Select Date Range",
                value=(datetime.date(2020,1,1), datetime.date.today()),
                key="date_range_picker_fallback"
            )


        # Play Count
        st.session_state.play_count_range = st.slider(
            "Play Count Range",
            min_value=play_count_min_max[0],
            max_value=play_count_min_max[1],
            value=st.session_state.play_count_range,
            key="play_count_slider"
        )
        # Favorites Count
        st.session_state.fav_count_range = st.slider(
            "Favorites Count Range",
            min_value=fav_count_min_max[0],
            max_value=fav_count_min_max[1],
            value=st.session_state.fav_count_range,
            key="fav_count_slider"
        )

    with st.expander("⚡️ Energy & BPM", expanded=True):
        # Energy Level
        st.session_state.energy_range = st.slider(
            "Energy Level Range",
            min_value=energy_min_max[0],
            max_value=energy_min_max[1],
            value=st.session_state.energy_range,
            key="energy_slider",
            help = "Filtering on Energy Level will reduce the number of sets shown, as only few sets have Energy data."
        )
        # BPM
        st.session_state.bpm_range = st.slider(
            "BPM Range",
            min_value=bpm_min_max[0],
            max_value=bpm_min_max[1],
            value=st.session_state.bpm_range,
            key="bpm_slider",
            help = "Filtering on BPM will reduce the number of sets shown, as only few sets have BPM data."
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 Apply Filters", use_container_width=True, type="primary"):
            apply_filters(df_sets)
    with col2:
        if st.button("🔁 Reset Filters", use_container_width=True):
            reset_filters()

# --- Display Sets ---
# --- Display User's Picks (Filtered Results) ---
if st.session_state.filters_applied:
    if not df_sets.empty:
        if not st.session_state.filtered_sets.empty:
            display_sets_section(
                title="⭐ Your Picks",
                sets_df=st.session_state.filtered_sets,
                success_message=f"Found {len(st.session_state.filtered_sets)} sets matching your criteria."
            )
        else:
            st.subheader("⭐ Your Picks")
            st.warning("No sets match your current filter criteria. Try adjusting your filters.")
    else:
        # This case should ideally not be reached if df_sets is empty and filters applied,
        # but as a fallback for "Your Picks" when main data is missing.
        st.subheader("⭐ Your Picks")
        st.error("Dataset is currently unavailable, so we can't show your picks.")

# st.markdown("---") # Separator between sections if both are shown

# --- Display Our Picks (Sample Sets) ---
if not df_sets.empty:
    sample_size = min(3, len(df_sets))
    our_picks_df = df_sets.sample(n=sample_size, random_state=1) if sample_size > 0 else pd.DataFrame()
    display_sets_section(
        title="🎶 Our Picks",
        success_message = "Here are a few sets we think you might enjoy. Your picks will appear above ☝️ once you apply filters.",
        sets_df=our_picks_df,
        empty_message="No sample sets to display (dataset might be smaller than expected or empty)."
    )
else:
    # This message is specifically for "Our Picks" if the main dataset failed to load
    st.subheader("🎶 Our Picks")
    st.error("Dataset is empty or could not be loaded. Cannot display 'Our Picks'.")


# --- Info Box ---
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div class="info-box">
        <strong>How to Use:</strong>
        <ol>
            <li>Select your preferred DJs, genres, and other criteria in the filter sections.</li>
            <li>Click "Apply Filters" to see matching sets.</li>
            <li>Use "Reset Filters" to start over.</li>
            <li>Click "Listen on Mixcloud" on any card to open the set.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True
)

# --- Potential Future Enhancements ---
with st.sidebar.expander("🚀 Future Ideas"):
    st.markdown("- Audio previews within the app")
    st.markdown("- User accounts & personal favorite lists")
    st.markdown("- More advanced recommendation engine")

st.markdown(
    """
    <style>
        /* Add some spacing below the main content before any footer or end-of-page elements */
        .stApp > footer {
            margin-top: 50px;
        }
    </style>
    """, unsafe_allow_html=True
)