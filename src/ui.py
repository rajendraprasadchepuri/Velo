import streamlit as st
import os

def add_logo():
    # Get absolute path to logo
    # This file is in src/, so go up one level to root, then assets/logo.png
    # Path Resolution
    # Assuming script is run from root (Velo/), assets is in Velo/assets
    # But ui.py is in Velo/src/ui.py
    
    # Robust Path Finding
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Velo root
    logo_path = os.path.join(base_dir, "assets", "logo_processed.png")
    
    if not os.path.exists(logo_path):
        # Try finding it relative to CWD if running from root
        cwd_path = os.path.join(os.getcwd(), "assets", "logo_processed.png")
        if os.path.exists(cwd_path):
            logo_path = cwd_path
        else:
            # Fallback to original logo if processed missing
             orig_path = os.path.join(base_dir, "assets", "logo.png")
             if os.path.exists(orig_path):
                 logo_path = orig_path
             else:
                 st.toast(f"Logo not found. Checked: {logo_path}", icon="⚠️")
                 return

    try:
        # Use Streamlit's native logo feature (top left sidebar)
        st.logo(logo_path, icon_image=logo_path)
    except Exception as e:
        # Fallback for sidebar image
        st.sidebar.image(logo_path, use_column_width=True)
        
    # Inject CSS to ensure visibility if theme is dark/light
    st.markdown(
        """
        <style>
            [data-testid="stLogo"] {
                height: 5.5rem !important;
                width: auto !important;
                max-width: 100% !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
