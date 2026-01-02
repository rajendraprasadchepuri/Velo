import streamlit as st
import os

def add_logo():
    # Get absolute path to logo
    # This file is in src/, so go up one level to root, then assets/logo.png
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    logo_path = os.path.join(root_dir, "assets", "logo_processed.png")
    
    if not os.path.exists(logo_path):
        st.error(f"Logo not found at {logo_path}")
        return

    # Use usage of st.logo for sidebar logo
    # This places it above the navigation
    try:
        st.logo(logo_path, icon_image=None)
        # Inject CSS to increase logo size beyond default
        st.markdown(
            """
            <style>
                [data-testid="stLogo"] {
                    height: 5rem !important;
                    width: auto !important;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
    except AttributeError:
        # Fallback for older streamlit versions
        st.sidebar.image(logo_path, width=200)
