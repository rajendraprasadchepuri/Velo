# 🚀 Deploying to Streamlit Community Cloud

This guide will help you deploy your **Stock Analysis & Prediction App** to the internet for free using Streamlit Community Cloud.

## Prerequisites

1. A **GitHub Account** (Free).
2. **Git** installed on your computer.

---

## Step 1: Create a GitHub Repository

1. Go to [new repository on GitHub](https://github.com/new).
2. Repository Name: `stock-prediction-app` (or whatever you like).
3. **Public** or **Private** (Private is fine).
4. **Do NOT** initialize with README, .gitignore, or license (we have them local).
5. Click **Create repository**.

## Step 2: Push Code to GitHub

Open your terminal in VS Code (`Ctrl + ~`) and run these commands one by one:

```bash
# 1. Initialize Git
git init

# 2. Add all files
git add .

# 3. Commit changes
git commit -m "Initial commit of Stock Prediction App"

# 4. Rename branch to main
git branch -M main

# 5. Link to your new GitHub Repo (REPLACE URL with YOUR repo URL)
# Example: git remote add origin https://github.com/YOUR_USERNAME/stock-prediction-app.git
git remote add origin <PASTE_YOUR_GITHUB_REPO_URL_HERE>

# 6. Push to GitHub
git push -u origin main
```

## Step 3: Deploy on Streamlit Cloud

1. Go to [Streamlit Community Cloud](https://streamlit.io/cloud) and sign up/login with GitHub.
2. Click **"New app"**.
3. Select your repository (`stock-prediction-app`) and branch (`main`).
4. Main file path: `app.py`.
5. Click **"Deploy!"**.

## Step 4: Wait for Build

Streamlit will install the libraries from `requirements.txt`. This takes 2-3 minutes.
Once done, your app will be live at `https://<your-app-name>.streamlit.app`! 🎈

## Troubleshooting

- **"ModuleNotFoundError"**: Ensure the library is listed in `requirements.txt`.
- **"Error installing packages"**: Check the logs in the Streamlit dashboard.
