# How to Push to GitHub

The project is ready to push to GitHub. The GitHub token provided appears to be invalid or expired.

## Option 1: Push with a New Token

1. Generate a new Personal Access Token on GitHub:
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" (classic)
   - Give it a name: "MQTT Remapper Upload"
   - Select scopes: `repo` (full control)
   - Click "Generate token"
   - Copy the token immediately (you won't see it again)

2. Push to GitHub:

```bash
cd /path/to/mqtt-input-remapper
git remote set-url origin https://YOUR_NEW_TOKEN@github.com/Qutaiba-Khader/mqtt-input-remapper.git
git push -u origin main
```

## Option 2: Push with SSH

1. Set up SSH key if you haven't:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add to GitHub: https://github.com/settings/keys
```

2. Push to GitHub:

```bash
cd /path/to/mqtt-input-remapper
git remote set-url origin git@github.com:Qutaiba-Khader/mqtt-input-remapper.git
git push -u origin main
```

## Option 3: Manual Upload

1. Download the zip file from this conversation
2. Extract it locally
3. Create repository on GitHub
4. Follow GitHub's instructions to push

## What's Already Done

✅ Git repository initialized
✅ All files committed
✅ Remote added (just needs valid token)
✅ Ready to push with `git push -u origin main`

## Verify Everything After Push

```bash
# Clone your repo
git clone https://github.com/Qutaiba-Khader/mqtt-input-remapper.git

# Test installation
cd mqtt-input-remapper
sudo bash scripts/install.sh
```
