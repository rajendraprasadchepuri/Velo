# Deployment Instructions

Since the `git` command is not available in the internal terminal, you need to manually push your code to GitHub from your own terminal (PowerShell or Command Prompt).

## 1. Initialize/Connect Repository
In your terminal, navigate to the project folder and run:

```powershell
git remote add origin https://github.com/rajendraprasadchepuri/Velo.git
```
*(If it says "remote origin already exists", that is fine, proceed to the next step)*

## 2. Save and Push Changes
Run these commands to save the new MTF Strategy and Logo changes:

```powershell
git add .
git commit -m "Added MTF Strategy page and Logo"
git branch -M main
git push -u origin main
```

## 3. Deploy
Once the command finishes successfully, go back to your Streamlit Cloud dashboard and try deploying again. It should now see your latest code.
