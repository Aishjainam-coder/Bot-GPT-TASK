# Steps to Push Project to GitHub

## Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click "+" → "New repository"
3. Repository name: `bot-gpt` (or your choice)
4. Description: "BOT GPT - Conversational AI Backend"
5. Set to **Public**
6. **Don't** initialize with README, .gitignore, or license
7. Click "Create repository"

## Step 2: Initialize Git (if not already done)

Open PowerShell in your project folder and run:

```powershell
# Check if git is initialized
git status

# If not initialized, run:
git init
```

## Step 3: Add All Files

```powershell
# Add all files
git add .

# Check what will be committed
git status
```

## Step 4: Create Initial Commit

```powershell
git commit -m "Initial commit: BOT GPT backend implementation"
```

## Step 5: Add Remote Repository

```powershell
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/bot-gpt.git

# Verify remote
git remote -v
```

## Step 6: Push to GitHub

```powershell
# Push to main branch
git branch -M main
git push -u origin main
```

**If prompted for credentials:**
- Use your GitHub username
- Use a Personal Access Token (not password)
  - Get token: GitHub → Settings → Developer settings → Personal access tokens → Generate new token
  - Select scope: `repo`

## Step 7: Verify

1. Go to your GitHub repository
2. Check all files are uploaded
3. Verify README.md displays correctly
4. Check .github/workflows/ci.yml is present

## Complete Command Sequence

```powershell
# 1. Initialize (if needed)
git init

# 2. Add files
git add .

# 3. Commit
git commit -m "Initial commit: BOT GPT backend implementation"

# 4. Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/bot-gpt.git

# 5. Push
git branch -M main
git push -u origin main
```

## Troubleshooting

### If files are too large:
```powershell
# Remove large files (if any)
git rm --cached bot_gpt.db
git rm --cached bot-gpt-submission.zip

# Add to .gitignore
echo "*.db" >> .gitignore
echo "*.zip" >> .gitignore
```

### If push fails:
```powershell
# Pull first (if repository has files)
git pull origin main --allow-unrelated-histories

# Then push
git push -u origin main
```

### If authentication fails:
- Use Personal Access Token instead of password
- Or use SSH: `git remote set-url origin git@github.com:USERNAME/bot-gpt.git`

## After Pushing

1. **Copy repository URL** for submission form
2. **Verify all files** are present
3. **Test CI/CD** (if enabled) - check Actions tab
4. **Update README** if needed

---

**Your project is now on GitHub! 🚀**

