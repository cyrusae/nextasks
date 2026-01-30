# Discord Bot Setup Guide

## Create the Bot Application

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it: `Nextcloud Tasks Bot` (or whatever you prefer)
4. Click "Create"

## Configure Bot Settings

1. In the left sidebar, click "Bot"
2. Click "Add Bot" → "Yes, do it!"
3. Under "Privileged Gateway Intents", enable:
   - ✅ MESSAGE CONTENT INTENT (needed for DM natural language in v1.1)
   - ✅ SERVER MEMBERS INTENT (optional, but useful)
4. Under "Bot Permissions", note these for later (we'll set during invite):
   - Send Messages
   - Use Slash Commands
   - Read Message History

## Get Your Bot Token

1. Still on the "Bot" page, under "TOKEN" section
2. Click "Reset Token" (if this is a new bot, it might say "Copy")
3. **CRITICAL:** Copy this token and save it securely
   - You'll need it in a moment
   - Never commit this to git
   - Never share it publicly
   - If leaked, reset it immediately

## Generate Invite Link

1. In left sidebar, click "OAuth2" → "URL Generator"
2. Under "SCOPES", check:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Under "BOT PERMISSIONS", check:
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Read Message History
   - ✅ Embed Links (for rich embeds)
4. Copy the generated URL at the bottom
5. Open that URL in a browser
6. Select your test Discord server (or create a new one for testing)
7. Click "Authorize"

## Verify Bot Joined

1. Open Discord
2. Check your test server - bot should appear in member list (offline for now)
3. Create a test channel like `#bot-testing` if you don't have one

## Save Your Token Securely

For now, we'll use a `.env` file locally (never commit this!):

```bash
# In your bot project directory
echo "DISCORD_TOKEN=your_token_here" > .env
echo ".env" >> .gitignore
```

You're ready! The bot exists but isn't running yet. Let's write the code.