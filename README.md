# claude_xkiro_backend

A proxy backend that connects Claude Desktop to free AI models via the [xKiro](https://xkiro.com) API.

## Features

- Routes Claude Desktop requests through a local proxy to xKiro's free API
- Model mapping: each Claude model selector maps to a different free model
- Easy setup with batch scripts

## Quick Start

1. Clone this repo
2. Copy `.env.example` to `.env` and add your xKiro API key
3. Run `setup.bat` to install dependencies
4. Run `start-proxy.bat` to start the proxy
5. Configure Claude Desktop to point to `http://127.0.0.1:3000`

## Setup via PowerShell (Step by Step)

Open PowerShell and run these commands one by one:

### Step 1: Navigate to the project folder
```powershell
cd C:\Users\ASUS\claude-desktop-config
```
> This moves you into the project directory where all your files are.

### Step 2: Initialize a new Git repository
```powershell
git init
```
> This creates a hidden `.git` folder and turns your project into a Git repository.

### Step 3: Add a `.gitignore` file
```powershell
# Create .gitignore to prevent sensitive files (like .env with API keys) from being pushed
echo ".env" >> .gitignore
```
> ⚠️ **Important**: Always add `.gitignore` BEFORE committing, so your API keys in `.env` never get pushed to GitHub.

### Step 4: Create the README file
```powershell
echo "# claude_xkiro_backend" >> README.md
```
> This creates the `README.md` file that GitHub displays on your repo page.

### Step 5: Stage all files for commit
```powershell
git add .
```
> `git add .` stages **all** files except those listed in `.gitignore` (like `.env`). You can also use `git add README.md` to add specific files only.

### Step 6: Set your Git identity (first time only)
```powershell
git config user.name "laljith-gamer"
git config user.email "laljith-gamer@users.noreply.github.com"
```
> Git needs to know who is making the commit. You only need to do this once per repo (or use `--global` to set it for all repos).

### Step 7: Commit the files
```powershell
git commit -m "first commit"
```
> This saves a snapshot of your staged files with the message "first commit".

### Step 8: Rename the branch to `main`
```powershell
git branch -M main
```
> Git defaults to `master`, but GitHub uses `main`. The `-M` flag force-renames your branch to match.

### Step 9: Add the remote GitHub repository
```powershell
git remote add origin https://github.com/laljith-gamer/claude_xkiro_backend.git
```
> This links your local repo to the GitHub repo so Git knows where to push.

### Step 10: Push to GitHub
```powershell
git push -u origin main
```
> This uploads all your committed files to GitHub. The `-u` flag sets `origin main` as the default, so future pushes only need `git push`.

---

## Files

| File | Description |
|------|-------------|
| `proxy.py` | Main proxy server |
| `models.json` | Model configuration and mappings |
| `setup.bat` | Install Python dependencies |
| `start-proxy.bat` | Start the proxy server |
| `stop-proxy.bat` | Stop the proxy server |
| `switch-model.bat` | Switch between AI models |
| `claude_desktop_config.json` | Claude Desktop configuration |

## License

MIT
