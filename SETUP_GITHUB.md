# Setting Up GitHub Repository - Step by Step Guide

## Step 1: Initialize Git Repository (Already Done)
✅ Git repository has been initialized in your project directory.

## Step 2: Create .gitignore (Already Done)
✅ A `.gitignore` file has been created to exclude:
- Virtual environments (venv/)
- Database files (db.sqlite3)
- Python cache files (__pycache__/)
- Environment variables (.env)
- IDE files (.vscode/, .idea/)
- And more...

## Step 3: Add Files to Git

Run these commands in your terminal (from the project root):

```bash
cd /Users/landenramsey/Downloads/spotify_recommender

# Add all files (respecting .gitignore)
git add .

# Check what will be committed
git status

# Commit the files
git commit -m "Initial commit: Spotify Recommender Django application"
```

## Step 4: Create GitHub Repository

1. **Go to GitHub**: Open https://github.com in your browser
2. **Sign in** to your GitHub account (or create one if you don't have one)
3. **Create New Repository**:
   - Click the "+" icon in the top right
   - Select "New repository"
   - Repository name: `spotify-recommender` (or any name you prefer)
   - Description: "Django web application for personalized Spotify music recommendations"
   - **Set to Public** (for public repository)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
   - Click "Create repository"

## Step 5: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/spotify-recommender.git

# Rename branch to main (if needed)
git branch -M main

# Push your code to GitHub
git push -u origin main
```

## Step 6: Verify on GitHub

1. Go to your GitHub repository page
2. You should see all your files
3. The README.md should display automatically

## Important Notes

### Before Pushing - Check for Sensitive Data

**IMPORTANT**: Make sure you haven't committed any sensitive information:

1. **Check views.py** - Make sure it has placeholder values:
   ```python
   SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_client_id_here')
   SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'your_client_secret_here')
   ```

2. **Never commit**:
   - Actual Spotify Client ID
   - Actual Spotify Client Secret
   - `.env` files with credentials
   - `db.sqlite3` with user data

3. **If you accidentally committed sensitive data**:
   - Remove it from git history before pushing
   - Or use environment variables (which is already set up)

### Recommended: Update README

Before pushing, you might want to add a note in README.md about setting up environment variables instead of hardcoding credentials.

## Troubleshooting

### If you get "remote origin already exists":
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/spotify-recommender.git
```

### If you get authentication errors:
- Use GitHub Personal Access Token instead of password
- Or set up SSH keys for GitHub

### If you need to update .gitignore later:
```bash
# After updating .gitignore
git rm -r --cached .
git add .
git commit -m "Update .gitignore"
```

## Next Steps After Pushing

1. **Add a description** to your GitHub repository
2. **Add topics/tags**: django, python, spotify-api, music-recommendations, web-app
3. **Consider adding**:
   - License file (MIT, Apache, etc.)
   - Contributing guidelines
   - Issue templates
   - GitHub Actions for CI/CD (optional)

## Quick Command Summary

```bash
# Navigate to project
cd /Users/landenramsey/Downloads/spotify_recommender

# Check status
git status

# Add files
git add .

# Commit
git commit -m "Initial commit: Spotify Recommender Django application"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/spotify-recommender.git

# Push to GitHub
git push -u origin main
```

