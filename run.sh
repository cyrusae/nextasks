# Nextcloud Tasks Discord Bot

Discord bot for managing Nextcloud Tasks via CalDAV. Provides mobile-friendly task management through Discord's excellent mobile app.

## Current Version: v0.1 MVP

**Features:**
- ✅ `/task-add <title>` - Create task due today at 11:59 PM
- ✅ `/task-list` - Show today's incomplete tasks
- ✅ `/task-complete <id>` - Mark task complete by ID
- ✅ `/task-help` - Show command help

**Coming in v1.0:**
- Custom due dates and times
- Rich embeds with interactive buttons
- Task filtering (today/tomorrow/week/overdue)
- Task deletion

## Quick Start

### The Really Quick Way (with uv)

```bash
# Clone project
git clone <repo-url> nextcloud-tasks-bot
cd nextcloud-tasks-bot

# Install dependencies
uv sync  # Creates .venv and installs everything

# Configure
cp .env.template .env
nano .env  # Add your Discord token and Nextcloud credentials

# Run!
./run.sh  # Or: uv run src/bot.py
```

### The Detailed Way

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Nextcloud instance with Tasks app installed
- Discord account and server for testing

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### 2. Clone and Setup

```bash
# If starting fresh
cd ~/projects  # or wherever you keep projects
git clone <repo-url> nextcloud-tasks-bot
cd nextcloud-tasks-bot

# Create virtual environment and install dependencies (one command!)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Or even simpler with uv sync (if using pyproject.toml in future)
# uv sync
```

### 2. Configure Discord Bot

Follow the instructions in `discord_bot_setup.md` to:
1. Create bot in Discord Developer Portal
2. Get bot token
3. Invite bot to your test server

### 3. Configure Nextcloud

1. Create dedicated bot user in Nextcloud (recommended: username `taskbot`)
2. Install Tasks app if not already installed
3. Generate app-specific password:
   - Settings → Security → Devices & sessions
   - "Create new app password"
   - Name it "Discord Bot"
   - Copy the password (you'll only see it once)

### 4. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit with your values
nano .env  # or your preferred editor
```

Fill in:
- `DISCORD_TOKEN` - From Discord Developer Portal
- `NEXTCLOUD_URL` - Your Nextcloud URL (e.g., https://nextcloud.dawnfire.casa)
- `NEXTCLOUD_USER` - Bot username (e.g., taskbot)
- `NEXTCLOUD_PASSWORD` - App-specific password from Nextcloud

### 5. Run the Bot

```bash
# Activate venv if not already (uv creates .venv by default)
source .venv/bin/activate

# Run bot
python src/bot.py

# Or run directly with uv (no activation needed!)
uv run src/bot.py
```

You should see:
```
🚀 Starting Nextcloud Tasks Bot v0.1...
✅ Connected to Nextcloud successfully
✅ Slash commands synced
🤖 Logged in as YourBotName (ID: ...)
🎉 Bot is ready!
```

### 6. Test in Discord

In your Discord server:

```
/task-add Buy groceries
/task-list
/task-complete 1
```

Check your Nextcloud Tasks web interface - the task should appear there too!

## Usage Examples

### Adding Tasks

```
/task-add Buy groceries
/task-add Call dentist
/task-add Review pull requests
```

All tasks are due today at 11:59 PM (v0.1 limitation, fixed in v1.0).

### Viewing Tasks

```
/task-list
```

Shows all incomplete tasks due today, numbered 1, 2, 3, etc.

### Completing Tasks

```
/task-complete 1
```

Marks task #1 from your last `/task-list` as complete. The task will disappear from future lists and show as completed in Nextcloud.

### Getting Help

```
/task-help
```

Shows all available commands.

## Architecture

```
Discord Bot (bot.py)
    ↓
CalDAV Client (caldav_client.py)
    ↓
Nextcloud CalDAV API (/remote.php/dav/)
    ↓
Nextcloud Tasks (VTODO storage)
```

**Key Design Decisions:**
- Tasks are stored as VTODO components in CalDAV
- Bot uses a dedicated Nextcloud user account for security
- Task numbers (1, 2, 3) are cached between `/task-list` and `/task-complete` calls
- All operations run asynchronously to avoid blocking Discord

## Troubleshooting

### Bot won't start - "Missing required environment variables"

Make sure `.env` file exists and contains all four variables:
```bash
cat .env
```

### Bot won't start - "Failed to connect to Nextcloud"

1. Check `NEXTCLOUD_URL` is correct (include https://)
2. Verify `NEXTCLOUD_USER` exists in Nextcloud
3. Make sure `NEXTCLOUD_PASSWORD` is an app password, not your main password
4. Test manually:
   ```bash
   curl -u "taskbot:your_app_password" https://nextcloud.dawnfire.casa/remote.php/dav/
   ```

### Slash commands don't appear in Discord

1. Wait 5-10 minutes (Discord can be slow to sync)
2. Try restarting Discord client
3. Make sure bot was invited with `applications.commands` scope
4. Check bot logs for "Slash commands synced" message

### "Invalid task number" when completing tasks

Task cache is cleared between bot restarts. Run `/task-list` again to refresh the cache.

### Tasks appear in Nextcloud but not in `/task-list`

Currently only shows tasks due today. If you added a task without a due date in Nextcloud, it won't appear. In v1.0, this will be more flexible.

## Development

### Project Structure

```
nextcloud-tasks-bot/
├── src/
│   ├── bot.py              # Main Discord bot
│   ├── caldav_client.py    # CalDAV/Nextcloud interface
│   └── (more in v1.0+)
├── k8s/                    # Kubernetes manifests (for deployment)
├── tests/                  # Unit tests (coming soon)
├── requirements.txt        # Python dependencies
├── .env.template          # Environment template
├── .gitignore
└── README.md
```

### Running in Development

```bash
# With activation
source .venv/bin/activate
python src/bot.py

# Or directly with uv (simpler!)
uv run src/bot.py
```

Watch the logs for detailed information about what the bot is doing.

### Adding Features

For v1.0 features, see `nextcloud_tasks_bot_roadmap.md` for the plan.

## Deployment to K8s

(Documentation coming when ready to deploy)

Will include:
- Dockerfile
- Kubernetes manifests
- Secrets management
- Health checks

## Roadmap

See `nextcloud_tasks_bot_roadmap.md` for detailed feature roadmap.

**Upcoming versions:**
- **v1.0** - Custom due dates, rich embeds, interactive buttons, task filtering
- **v1.1** - Natural language parsing (DMs), proactive reminders, Ollama integration
- **v2.0** - Multi-user support, recurring tasks, subtasks, advanced features

## Contributing

This is currently a personal project for household use. If you're in the household:
- Martin, Tea, Ellie - feel free to suggest features or report bugs!
- Pull requests welcome once v1.0 is stable

## License

Personal use project (no formal license yet).

## Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Uses [python-caldav](https://github.com/python-caldav/caldav) for Nextcloud integration
- Inspired by frustration with iOS CalDAV task support 😤