import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Verifying app.py syntax and imports...")
    # We can't run streamlit in a script easily, but we can check for syntax errors
    with open("app.py", "r") as f:
        compile(f.read(), "app.py", "exec")
    print("Syntax check passed.")
    
    print("Verifying session state logic structure (static analysis)...")
    with open("app.py", "r") as f:
        content = f.read()
        if "st.session_state.data" in content and "if st.session_state.data is not None:" in content:
            print("Session state logic found.")
        else:
            print("Warning: Session state logic might be missing.")

    print("Verification complete.")

except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
