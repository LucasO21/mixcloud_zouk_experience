# ==============================================================================
# STREAMLIT APP (HOME PAGE) ----
# ==============================================================================

# Import Libraries ----
import streamlit as st
import random
import yaml
import uuid
import os
import sys
from pathlib import Path
import pandas as pd
from src.app.app_tab_1 import load_data, get_unique_values


# ------------------------------------------------------------------------------
# APP SETUP ----
# ------------------------------------------------------------------------------

# Set Page Config ----
st.set_page_config(
    page_title = "Zouk Music DJ Set Recommender",
    page_icon = "🎧",
    layout = "wide",
    initial_sidebar_state = "collapsed"
)


# Custom CSS
def apply_custom_css():
    st.markdown("""
    <style>
        /* Main app styling */
        .main-title {
            font-size: 3rem !important;
            font-weight: 800 !important;
            margin-bottom: 0 !important;
            color: #FF4B4B;
        }
        .subtitle {
            font-size: 1.5rem !important;
            font-weight: 400 !important;
            color: #888888;
            margin-top: 0 !important;
        }
        .block-container {
            padding-top: 2rem !important;
        }

        /* Card styling */
        .card {
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }
        .card:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-5px);
        }
        .card-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #212529;
        }
        .card-text {
            color: #495057;
            margin-bottom: 1rem;
        }

        /* Button styling */
        .custom-button {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(90deg, #FF4B4B 0%, #FF9A8B 100%);
            color: white !important;
            border-radius: 30px;
            font-weight: 600;
            text-align: center;
            margin: 10px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s ease;
            border: none;
            width: 100%;
        }
        .alt-button {
            background: linear-gradient(90deg, #4B6EFF 0%, #8BA9FF 100%);
        }
        .custom-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        /* Chat interface styling */
        .chat-message {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            flex-direction: row;
            align-items: flex-start;
        }
        .chat-message.user {
            background-color: #F0F2F6;
        }
        .chat-message.bot {
            background-color: #EAEEF7;
        }
        .chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
            background-color: #ccc;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .user .chat-avatar {
            background-color: #4B6EFF;
            color: white;
        }
        .bot .chat-avatar {
            background-color: #FF4B4B;
            color: white;
        }
        .chat-text {
            flex: 1;
        }

        /* Set cards */
        .set-card {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 5px solid #FF4B4B;
            background-color: #f8f9fa;
        }
        .set-card-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        .set-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin: 8px 0;
        }
        .set-tag {
            background-color: #e9ecef;
            border-radius: 15px;
            padding: 3px 10px;
            font-size: 0.8rem;
            color: #495057;
        }

        /* Icons and stats */
        .set-stats {
            display: flex;
            gap: 15px;
            margin-top: 10px;
            color: #6c757d;
            font-size: 0.9rem;
        }
        .stat {
            display: flex;
            align-items: center;
            gap: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize app state ----
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
# Initialize djs and sets if not already present
if 'djs' not in st.session_state or 'sets' not in st.session_state:
    df_temp_sets = load_data()
    if not df_temp_sets.empty:
        st.session_state.sets = df_temp_sets
        st.session_state.djs = get_unique_values(df_temp_sets, "name")
    else:
        st.session_state.sets = pd.DataFrame()
        st.session_state.djs = []

# Apply custom CSS
apply_custom_css()

# Function to display welcome screen
def display_welcome():
    col1, col2, col3 = st.columns([1, 6, 1])

    with col2:
        st.markdown("<h1 class='main-title'>MixRecommend</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Discover your next favorite DJ set</p>", unsafe_allow_html=True)

        st.markdown("""
        <div class='card'>
            <div class='card-title'>Welcome to MixRecommend!</div>
            <div class='card-text'>
                MixRecommend helps you discover amazing DJ sets on Mixcloud based on your mood and preferences.
                Whether you want to find something energetic for your workout, chill tracks for relaxation,
                or explore new genres, we've got you covered.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<h3>How would you like to discover music today?</h3>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("""
            <div onclick="document.getElementById('decide_preference_button').click()" class='card'>
                <div class='card-title'>Decide Your Preference</div>
                <div class='card-text'>
                    Use filters to specify exactly what you're looking for - whether it's mood, genre,
                    or energy level. Perfect if you know what kind of music you want.
                </div>
                <div class='custom-button'>Choose This</div>
            </div>
            """, unsafe_allow_html=True)

            # Hidden button that will be clicked by the JavaScript
            if st.button('Decide Your Preference', key='decide_preference_button'):
                st.session_state.active_tab = 'decide_preference'
                st.rerun()

        with col_b:
            st.markdown("""
            <div onclick="document.getElementById('ai_recommend_button').click()" class='card'>
                <div class='card-title'>AI Recommendation</div>
                <div class='card-text'>
                    Chat with our AI assistant and get personalized recommendations based on your
                    conversation. Great for discovering new sounds or if you're not sure what you want.
                </div>
                <div class='custom-button alt-button'>Choose This</div>
            </div>
            """, unsafe_allow_html=True)

            # Hidden button that will be clicked by the JavaScript
            if st.button('AI Recommendation', key='ai_recommend_button'):
                st.session_state.active_tab = 'ai_recommend'
                st.rerun()

# Function to display decide preference tab
def display_decide_preference():
    st.markdown("<h1>Decide Your Preference</h1>", unsafe_allow_html=True)

    # Add "back to welcome" button
    if st.button("← Back to Welcome", key="back_from_preference"):
        st.session_state.active_tab = None
        st.rerun()

    st.markdown("<p>This is where you'll be able to filter through sets based on your preferences.</p>", unsafe_allow_html=True)

    # Placeholder for filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.selectbox("Mood", ["All Moods", "Chill", "Energetic", "Dark", "Uplifting", "Melancholic"])
    with col2:
        st.selectbox("Genre", ["All Genres", "Afrobeats", "House", "Techno", "Zouk", "Hip Hop"])
    with col3:
        st.slider("Popularity", 0, 10000, (0, 10000))

    # Search button
    st.button("Find Sets", key="find_sets")

