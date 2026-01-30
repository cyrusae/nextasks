# Nextcloud Tasks Discord Bot - Project Roadmap

## Project Vision

A Discord bot that provides mobile-friendly task management by interfacing with Nextcloud Tasks via CalDAV. Solves the iOS friction problem (no native CalDAV task support) by leveraging Discord's excellent mobile app as the primary interface for quick task entry and management on the go.

## Core Problem Being Solved

**Current pain points:**
- iOS Reminders dropped CalDAV support in iOS 13
- Official Nextcloud mobile app doesn't support Tasks
- Third-party iOS task apps are expensive ($15-50) or have poor Nextcloud compatibility
- Quick task entry on mobile requires opening browser → logging into Nextcloud → navigating to Tasks app

**Solution:**
Discord bot provides instant task entry via slash commands or natural language, with Discord's push notifications for reminders. Works identically on iOS, Android, and desktop.

## Architecture Overview

### Three-Tier Approach

1. **Discord Bot (Task Entry/Management)**
   - Slash commands for power users (fast, predictable)
   - DM natural language for casual use (conversational, flexible)
   - Rich embeds with interactive buttons/reactions for task completion
   - Proactive reminders sent as DMs

2. **Bedroom Dashboard (Passive Display)**
   - Queries CalDAV for both VEVENT and VTODO
   - Read-only visual display of today's events + tasks
   - See separate problem statement: `nextcloud_tasks_dashboard_integration.md`

3. **Nextcloud Web Interface (Deep Management)**
   - Full-featured for complex operations (subtasks, notes, recurring tasks)
   - Occasionally used, not primary interface
   - All changes sync to bot/dashboard immediately

**Unified Backend:** All three use Nextcloud's CalDAV endpoint as single source of truth.

---

## Technical Stack

### Bot Framework
- **Language:** Python 3.11+
- **Discord Library:** discord.py (v2.x with slash command support)
- **CalDAV Client:** caldav library (same as dashboard integration)
- **Natural Language:** Ollama (already deployed on homelab) with lightweight model for date/intent parsing
- **Deployment:** Kubernetes (K3s cluster on Babbage)

### Infrastructure
- **Nextcloud:** Already running at `https://nextcloud.dawnfire.casa`
- **CalDAV Endpoint:** `/remote.php/dav/calendars/{username}/{calendar}/`
- **Ollama:** Local LLM for natural language parsing (avoids API costs)
- **Secrets Management:** Kubernetes secrets for Discord token, Nextcloud credentials

### Bot User Setup
- Create dedicated Nextcloud account: `taskbot` (or similar)
- Use app-specific password (not main password)
- Grant access only to relevant calendar(s)
- Cleaner audit logs, better security isolation

---

## Feature Set by Version

### v0.1 - MVP (Minimum Viable Product)
**Goal:** Prove the concept works, test core CalDAV integration

**Features:**
- ✅ `/task add <title>` - Create task due today at 11:59 PM
- ✅ `/task list` - Show today's incomplete tasks
- ✅ `/task complete <id>` - Mark task complete by ID
- ✅ Bot responds in channel with confirmation messages
- ✅ Basic error handling (connection failures, invalid input)

**Out of scope for v0.1:**
- No custom due dates yet (everything defaults to today)
- No natural language parsing
- No proactive reminders
- No rich embeds or buttons
- No multi-user support

**Success criteria:**
- Can add task via Discord → see it in Nextcloud web interface
- Can mark task complete in Nextcloud → bot reflects that in `/task list`
- Round-trip sync works reliably

**Estimated time:** 4-8 hours (including learning discord.py slash commands)

---

### v1.0 - Core Functionality
**Goal:** Make it genuinely useful for daily task management

**New features:**
- 📅 `/task add <title> due:<date/time>` - Parse common date formats
  - "today", "tomorrow", "friday", "next monday"
  - "2pm", "tomorrow 3pm", "jan 30"
  - ISO format: "2026-01-30"
- 📋 `/task list <filter>` - List by timeframe/status
  - `today` (default), `tomorrow`, `week`, `overdue`, `all`
- 🗑️ `/task delete <id>` - Remove task entirely
- 🎨 Rich embeds with color coding
  - Green for completed
  - Yellow for due today
  - Red for overdue
  - Blue for future tasks
- 🔘 Interactive buttons on task lists
  - "✅ Complete" button next to each task
  - Click button instead of typing `/task complete <id>`

**Technical improvements:**
- Better date parsing (dateutil library or similar)
- Task ID caching (map Discord message to CalDAV UID)
- Proper async/await patterns for CalDAV calls
- Logging for debugging

**Out of scope for v1.0:**
- Still no natural language (that's v1.1)
- No recurring tasks
- No subtasks
- No priority/categorization
- Single user only (bot account)

**Success criteria:**
- Can manage entire day's tasks from Discord mobile app
- Date parsing handles 90% of common expressions
- Interactive buttons work reliably
- Fast enough for real-world use (<2 second response time)

**Estimated time:** 8-12 hours (on top of v0.1)

---

### v1.1 - Natural Language & Intelligence
**Goal:** Make task entry feel effortless and conversational

**New features:**
- 💬 DM the bot with natural language
  - "remind me to buy groceries today"
  - "I need to call the dentist tomorrow at 2pm"
  - "add task: review pull request by friday"
- 🤖 Ollama integration for intent parsing
  - Extract task title, due date, priority from free-form text
  - Handle ambiguity gracefully ("did you mean today or tomorrow?")
  - Learn common phrasings over time (fine-tuning potential)
- 🔔 Proactive reminders
  - DM user when task is due (configurable timing)
  - "Your task 'Call dentist' is due in 30 minutes"
  - Snooze functionality (buttons to postpone)
- 📊 `/task stats` - Show completion rate, overdue count, trends

**Ollama prompt structure:**
```
System: You are a task parser. Extract structured data from natural language.
User: remind me to buy groceries today
Assistant: {"title": "Buy groceries", "due": "today", "priority": "normal"}
```

**Technical considerations:**
- Keep Ollama prompts minimal (lightweight model like phi-3 or mistral-7b)
- Fallback to strict parsing if Ollama fails/times out
- Cache common phrasings to avoid repeated LLM calls
- Rate limiting to prevent Ollama overload

**Out of scope for v1.1:**
- Multi-user support (still single bot account)
- Recurring tasks
- Subtasks
- Calendar integration (events stay separate for now)

**Success criteria:**
- 80%+ accuracy on natural language task creation
- <3 second response time including Ollama inference
- Reminders arrive reliably within 1 minute of due time
- Users prefer natural language over slash commands for quick adds

**Estimated time:** 12-16 hours (on top of v1.0)

---

### v2.0 - Multi-User & Advanced Features
**Goal:** Support household members, handle complex task scenarios

**New features:**
- 👥 Multi-user support
  - Each Discord user links their own Nextcloud account
  - `/task setup` command to securely store credentials
  - Encrypted credential storage in Kubernetes secrets
  - Bot knows which calendar to use per user
- 🔁 Recurring tasks
  - `/task add "Water plants" every:week due:sunday`
  - Handle RRULE in VTODO properly
  - Generate next instance when current is completed
- 📝 Task details
  - `/task edit <id> title:"New title"`
  - `/task edit <id> due:tomorrow`
  - Add notes/descriptions
  - Set priority (high/medium/low)
- 🗂️ Task lists/categories
  - Multiple calendars support
  - `/task list calendar:personal`
  - `/task list calendar:shared` (household tasks)
- 📋 Subtasks
  - `/task add-subtask <parent_id> "Subtask title"`
  - Hierarchical display in `/task list`

**Multi-user architecture:**
```
Discord User ID → Encrypted Nextcloud Credentials → User's CalDAV Calendar(s)
```

**Security considerations:**
- Never log Nextcloud passwords
- Use Kubernetes secret per user (not environment variables)
- Allow users to revoke bot access (`/task disconnect`)
- Audit logging for shared calendar modifications

**Out of scope for v2.0:**
- Integration with calendar events (VEVENT) - that's v3.0
- Location-based reminders
- File attachments

**Success criteria:**
- Martin, Cyrus, Tea, and Ellie can all use bot independently
- Shared "Household" task list works for coordination
- Recurring tasks generate correctly and don't duplicate
- Zero credential leakage in logs or error messages

**Estimated time:** 20-30 hours (substantial refactor for multi-user)

---

### v3.0 - Calendar Integration & Ecosystem
**Goal:** Blur the line between tasks and events, integrate with broader homelab

**Potential features (TBD):**
- 📅 Unified view of events (VEVENT) + tasks (VTODO)
  - `/schedule today` shows both calendar appointments and tasks
  - Tasks auto-schedule into free time slots
- 🏠 Home Assistant integration
  - Voice: "Alexa, ask TaskBot what's on my list today"
  - Physical buttons/NFC tags to complete tasks
  - Task completion triggers automations (e.g., laundry timer sets reminder)
- 🔗 Webhook support
  - Other services can create tasks via HTTP POST
  - IFTTT/Zapier integration potential
  - GitHub issues → Nextcloud tasks
- 🎮 Gamification
  - Streak tracking
  - Leaderboards (household task completion)
  - Achievement system
- 📱 iOS Shortcuts integration
  - Siri: "Add grocery shopping to my task list"
  - Shortcuts → Discord webhook → bot

**Highly speculative:** These depend on v2.0 working well and actual usage patterns.

---

## Implementation Phases

### Phase 1: Local Prototype (v0.1)
**Environment:** Development laptop, testing against production Nextcloud

**Steps:**
1. Set up Python venv with discord.py and caldav
2. Create Discord bot in Developer Portal, get token
3. Implement basic slash commands (add, list, complete)
4. Test CalDAV connection to Nextcloud
5. Verify round-trip: Discord → Nextcloud web interface
6. Handle errors gracefully (connection failures, malformed input)

**Deliverables:**
- Working bot running locally
- Can add/list/complete tasks
- Confidence that CalDAV integration works

**Blockers:**
- Need Discord bot token (quick setup)
- Need taskbot Nextcloud account with app password

**Estimated timeline:** 1-2 coding sessions

---

### Phase 2: Enhanced Commands (v1.0)
**Environment:** Still local, more sophisticated testing

**Steps:**
1. Add date parsing library (dateutil or similar)
2. Implement due date parsing in `/task add`
3. Add filtering to `/task list` (today/tomorrow/week/overdue)
4. Create rich Discord embeds with color coding
5. Add interactive buttons for task completion
6. Implement proper task ID → CalDAV UID mapping
7. Add comprehensive error handling
8. Write basic tests for date parsing logic

**Deliverables:**
- Bot handles realistic daily task management workflow
- Date parsing covers common formats
- Interactive buttons work reliably
- Polished UX (good embed formatting, helpful error messages)

**Blockers:**
- None, build on v0.1

**Estimated timeline:** 2-3 coding sessions

---

### Phase 3: Containerization & Deployment
**Environment:** K3s cluster on Babbage

**Steps:**
1. Write Dockerfile for bot
2. Create Kubernetes manifests (Deployment, Service, Secrets)
3. Set up secrets for Discord token and Nextcloud credentials
4. Configure resource limits (CPU/memory)
5. Deploy to K3s cluster
6. Test from mobile devices (iOS/Android)
7. Set up logging (kubectl logs, potential Loki integration)
8. Document deployment process

**Deliverables:**
- Bot running 24/7 in K3s cluster
- Auto-restarts on failure
- Secrets properly secured
- Accessible from any device

**Infrastructure:**
```yaml
# nextcloud-tasks-bot/
#   deployment.yaml
#   secrets.yaml (template, not committed)
#   configmap.yaml (for non-sensitive config)
#   service.yaml (if needed for health checks)
```

**Blockers:**
- None, K3s cluster already running

**Estimated timeline:** 1 coding session + monitoring/tweaking

---

### Phase 4: Natural Language (v1.1)
**Environment:** K3s cluster with Ollama integration

**Steps:**
1. Design Ollama prompt for task parsing
2. Choose appropriate model (phi-3 or mistral-7b recommended)
3. Implement DM listener for natural language input
4. Add fallback to strict parsing if Ollama fails
5. Implement proactive reminders (background task checks due dates)
6. Add `/task stats` command
7. Test accuracy of natural language parsing
8. Optimize for speed (caching, async calls)

**Deliverables:**
- Natural language task creation via DM
- Proactive reminders sent on schedule
- Stats command shows useful metrics
- Fast enough for real-world use

**Technical notes:**
- Use discord.py's `on_message` event for DMs
- Differentiate between commands and natural language
- Background task for reminder checking (asyncio.create_task)
- Ollama API call: `POST http://ollama-service:11434/api/generate`

**Blockers:**
- Ollama service must be accessible from bot pod (K8s networking)

**Estimated timeline:** 3-4 coding sessions

---

### Phase 5: Multi-User Support (v2.0)
**Environment:** K3s cluster, significant refactor

**Steps:**
1. Design credential storage schema (K8s secrets per user)
2. Implement `/task setup` flow (secure credential collection)
3. Refactor CalDAV calls to use per-user credentials
4. Add user context to all commands
5. Implement shared calendar support
6. Add recurring task handling (RRULE parsing)
7. Implement task editing commands
8. Add subtask support
9. Security audit (no credential leakage)
10. Test with multiple household members

**Deliverables:**
- Multi-user bot supporting Martin, Cyrus, Tea, Ellie
- Shared household task list
- Recurring tasks work correctly
- Task editing and subtasks functional
- Secure credential management

**Architecture changes:**
```python
# Before (v1.x): single hardcoded CalDAV client
client = DAVClient(url=NEXTCLOUD_URL, username=BOT_USER, password=BOT_PASS)

# After (v2.x): per-user clients
def get_caldav_client(discord_user_id):
    creds = fetch_user_credentials(discord_user_id)
    return DAVClient(url=NEXTCLOUD_URL, username=creds.username, password=creds.password)
```

**Blockers:**
- Requires v1.0/v1.1 to be working well first
- Substantial refactor, don't rush into this

**Estimated timeline:** 10-15 coding sessions (major undertaking)

---

## Development Workflow

### Version Control
```bash
# Repository structure
nextcloud-tasks-bot/
├── src/
│   ├── bot.py              # Main Discord bot logic
│   ├── caldav_client.py    # CalDAV interaction layer
│   ├── date_parser.py      # Date/time parsing utilities
│   ├── ollama_client.py    # Natural language parsing (v1.1+)
│   └── utils.py            # Helper functions
├── k8s/
│   ├── deployment.yaml
│   ├── secrets.yaml.template
│   ├── configmap.yaml
│   └── service.yaml
├── tests/
│   ├── test_date_parser.py
│   ├── test_caldav.py
│   └── test_ollama.py
├── Dockerfile
├── requirements.txt
├── README.md
└── .gitignore
```

### Git Strategy
- Main branch: stable, deployable code
- Feature branches: `feature/natural-language`, `feature/multi-user`, etc.
- Tag releases: `v0.1`, `v1.0`, `v1.1`, etc.
- Push to GitHub (part of existing homelab backup strategy)

### Testing Strategy
- **Unit tests:** Date parsing, CalDAV data transformation
- **Integration tests:** Mock CalDAV server for testing without hitting Nextcloud
- **Manual testing:** Real Discord bot in test server before deploying to main server
- **Regression testing:** Core workflows (add/list/complete) stay working across versions

---

## Configuration Management

### Environment Variables / Secrets
```yaml
# Kubernetes Secret (not committed to git)
apiVersion: v1
kind: Secret
metadata:
  name: tasks-bot-secrets
type: Opaque
stringData:
  DISCORD_TOKEN: "your_discord_bot_token"
  NEXTCLOUD_URL: "https://nextcloud.dawnfire.casa"
  NEXTCLOUD_BOT_USER: "taskbot"
  NEXTCLOUD_BOT_PASSWORD: "app_specific_password"
```

### ConfigMap (non-sensitive config)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tasks-bot-config
data:
  DEFAULT_DUE_TIME: "23:59"
  REMINDER_ADVANCE_MINUTES: "30"
  OLLAMA_MODEL: "phi-3"
  OLLAMA_URL: "http://ollama-service:11434"
```

---

## Success Metrics

### v0.1 Success
- [ ] Bot deployed and reachable
- [ ] Can add task via Discord
- [ ] Task appears in Nextcloud web interface
- [ ] Can complete task via Discord
- [ ] Completion syncs to Nextcloud

### v1.0 Success
- [ ] Can manage full day's tasks from Discord mobile
- [ ] Date parsing handles common formats without confusion
- [ ] Interactive buttons work on iOS and Android
- [ ] Response time <2 seconds for all commands
- [ ] Use bot instead of Nextcloud web for 80%+ of task operations

### v1.1 Success
- [ ] Natural language parsing 80%+ accurate
- [ ] Reminders arrive within 1 minute of due time
- [ ] Ollama integration doesn't slow down bot (<3s total)
- [ ] Prefer DM natural language over slash commands for quick adds

### v2.0 Success
- [ ] All household members actively using bot
- [ ] Shared household task list used for coordination
- [ ] Zero credential leakage incidents
- [ ] Recurring tasks work correctly (no duplicates, no missed generations)

---

## Open Questions & Design Decisions

### 1. Task ID Display
**Question:** How to identify tasks for completion/editing?

**Options:**
A. Sequential numbers (1, 2, 3) - simple but breaks across list calls
B. Short hash (first 6 chars of CalDAV UID) - persistent but less friendly
C. Emoji indicators (🥇, 🥈, 🥉) - fun but limited to ~10 tasks
D. Interactive buttons only (no IDs) - cleanest UX but requires rich embeds

**Leaning toward:** Option D for v1.0 (buttons), with Option B as fallback for advanced users

### 2. Completed Task Visibility
**Question:** Should `/task list` show completed tasks?

**Options:**
A. Hide completed (clean, focused on what's left)
B. Show completed with strikethrough (satisfaction, context)
C. Separate command `/task list completed` (don't clutter main view)

**Leaning toward:** Option A by default, Option C for optional viewing

### 3. Overdue Task Handling
**Question:** How to display overdue tasks?

**Options:**
A. Show on original due date (accurate but requires scrolling past)
B. "Roll forward" to today like Nextcloud does (visible but inaccurate)
C. Dedicated "Overdue" section at top of lists (prominent, organized)

**Leaning toward:** Option C - always show overdue at top regardless of filter

### 4. Reminder Timing Configuration
**Question:** How far in advance to send reminders?

**Options:**
A. Fixed (e.g., always 30 minutes before)
B. Configurable per user (`/task remind-me 1h-before`)
C. Configurable per task (`/task add "Call dentist" due:2pm remind:1h`)
D. Smart based on task type (meetings 15min, errands 2hr)

**Decision deferred to v1.1+**, start with Option A for simplicity

### 5. Ollama Model Selection
**Question:** Which Ollama model for natural language parsing?

**Considerations:**
- Lightweight (fast inference, low resource usage)
- Good at structured output (JSON extraction)
- Available in Ollama (not too obscure)

**Candidates:**
- **phi-3-mini** (3.8B params) - Fast, good at instructions, Microsoft-trained
- **mistral-7b** (7B params) - Higher quality, slower
- **llama3.2** (3B params) - Latest, balanced

**Leaning toward:** phi-3-mini for v1.1, can upgrade to mistral if accuracy insufficient

---

## Dependencies & Prerequisites

### Before Starting Development
- [x] Nextcloud running and accessible
- [x] CalDAV endpoint working (verified via iOS calendar sync)
- [ ] Discord Developer account (free, quick signup)
- [ ] Discord bot created and token obtained
- [ ] Test Discord server for development (separate from main household server)
- [ ] `taskbot` Nextcloud user account with app password
- [ ] Python 3.11+ development environment

### Infrastructure Requirements
- [x] K3s cluster running on Babbage
- [x] Kubectl configured and working from development machine
- [x] Docker registry accessible (for pushing bot images)
- [ ] Ollama service deployed in K3s (for v1.1+)
- [x] Secrets management strategy (K8s secrets)

### Skills/Knowledge Needed
- Python async/await patterns (discord.py is async-first)
- Discord bot development (slash commands, embeds, buttons)
- CalDAV/iCalendar format basics (VTODO structure)
- Kubernetes deployment (already familiar from homelab)
- OAuth/secure credential handling (for v2.0 multi-user)

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk:** CalDAV integration unreliable (sync delays, connection failures)
- **Mitigation:** Implement retry logic, connection pooling, fallback to cached data
- **Severity:** Medium

**Risk:** Ollama inference too slow (>5s response time)
- **Mitigation:** Aggressive caching, fallback to strict parsing, smaller model
- **Severity:** Low (only affects v1.1+)

**Risk:** Multi-user credential storage vulnerable
- **Mitigation:** Encrypt at rest, audit regularly, security review before v2.0
- **Severity:** High

**Risk:** Discord API rate limits (bot gets throttled)
- **Mitigation:** Implement rate limiting on our side, batch operations, cache responses
- **Severity:** Low (unlikely with household-scale usage)

### Scope Risks

**Risk:** Feature creep (trying to build everything at once)
- **Mitigation:** Strict versioning, ship v0.1 before starting v1.0
- **Severity:** High

**Risk:** Over-engineering (building for scale we don't need)
- **Mitigation:** Start with simplest solution, refactor when needed
- **Severity:** Medium

**Risk:** Competing with existing server projects (Discord bot low priority)
- **Mitigation:** This solves immediate pain point (mobile tasks), should be higher priority
- **Severity:** Low

### User Experience Risks

**Risk:** Bot UI confusing (unclear how to use commands)
- **Mitigation:** Good help text, examples in command descriptions, friendly error messages
- **Severity:** Medium

**Risk:** Natural language parsing frustrating (misunderstands input)
- **Mitigation:** Always show what was parsed, easy undo, fall back to strict syntax
- **Severity:** Medium (only v1.1+)

**Risk:** Mobile notification spam (too many reminders)
- **Mitigation:** Configurable reminder frequency, smart batching of overdue tasks
- **Severity:** Low

---

## Documentation Plan

### For Users (Household Members)
- **Getting Started Guide:** How to DM bot, basic slash commands
- **Command Reference:** Full list of commands with examples
- **FAQ:** Common issues, "why isn't my task showing up", etc.
- **Tips & Tricks:** Power user features, keyboard shortcuts, iOS Shortcuts integration

### For Development (Future Cyrus)
- **Architecture Overview:** How bot components fit together
- **CalDAV Integration Details:** VTODO structure, quirks of Nextcloud implementation
- **Deployment Guide:** How to update bot, rollback, check logs
- **Troubleshooting:** Common issues, how to debug
- **Contributing Guide:** For if Martin/Tea/Ellie want to add features

### For Operations
- **Monitoring:** What metrics to watch, normal vs abnormal behavior
- **Incident Response:** Bot down? CalDAV unreachable? Credential leak?
- **Backup/Recovery:** How to restore bot state, user credentials

---

## Timeline Estimates

**Assuming ~4 hours of focused coding per session:**

| Version | Sessions | Calendar Time | Cumulative |
|---------|----------|---------------|------------|
| v0.1    | 2        | 1 week        | 1 week     |
| v1.0    | 3        | 2 weeks       | 3 weeks    |
| Deploy  | 1        | 1 week        | 4 weeks    |
| v1.1    | 4        | 3 weeks       | 7 weeks    |
| v2.0    | 12       | 8 weeks       | 15 weeks   |

**Note:** These are optimistic estimates. Real-world interruptions, debugging, and "oh I should also add..." moments will extend timelines. v0.1 could realistically ship in 2-3 weeks, v1.0 in 4-6 weeks, v1.1 in 8-10 weeks.

**Recommendation:** Don't commit to v2.0 timeline until v1.1 is shipped and being used daily.

---

## Relationship to Other Projects

### Bedroom Dashboard
- **Shared:** Both query Nextcloud CalDAV for tasks
- **Different:** Bot is write-heavy (add/complete), dashboard is read-only (display)
- **Synergy:** Changes via bot appear on dashboard within refresh interval

### Server Management Discord Bot (v0.0.1)
- **Shared:** Discord bot infrastructure, deployment patterns
- **Different:** Different command set, different backend (CalDAV vs Docker/K8s APIs)
- **Synergy:** Could eventually merge into single multi-purpose bot with modules

### Knowledge Manager / Study Bot (Future)
- **Shared:** Discord interface, Ollama for NLP, n8n for workflows
- **Different:** Focus on document processing vs task management
- **Synergy:** Task bot could create tasks from paperless-ngx documents, or from transcribed lecture notes

### Home Assistant
- **Shared:** Task completion could trigger HA automations
- **Different:** HA focuses on physical devices, bot focuses on personal productivity
- **Synergy:** Voice interface to tasks via Alexa → HA → Discord webhook → bot

---

## Next Steps: Moving to Prototyping

Once this roadmap is approved, next thread should focus on:

1. **Discord bot setup** - Create bot in Developer Portal, get token
2. **Local dev environment** - Python venv, install discord.py and caldav
3. **v0.1 implementation** - Basic slash commands, CalDAV connection
4. **Testing against production Nextcloud** - Verify round-trip sync
5. **Iterate until v0.1 success criteria met**

After v0.1 works reliably, revisit this roadmap and plan v1.0 features in detail.

---

## Appendix: Useful Resources

### Discord.py Documentation
- Official guide: https://discordpy.readthedocs.io/
- Slash commands: https://discordpy.readthedocs.io/en/stable/interactions/api.html
- Examples: https://github.com/Rapptz/discord.py/tree/master/examples

### CalDAV Resources
- caldav library: https://github.com/python-caldav/caldav
- CalDAV RFC: https://datatracker.ietf.org/doc/html/rfc4791
- iCalendar VTODO: https://icalendar.org/iCalendar-RFC-5545/3-6-2-to-do-component.html
- Nextcloud CalDAV docs: https://docs.nextcloud.com/server/latest/developer_manual/client_apis/CalDAV/

### Ollama Resources
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Model library: https://ollama.com/library
- Structured output tips: Use JSON mode with specific prompt formatting

### Kubernetes Deployment
- discord.py in K8s: Best practices for long-running bots
- Health checks: Implement `/health` endpoint for K8s probes
- Resource limits: Start with 100m CPU, 256Mi memory, adjust based on usage

---

## Success Definition

This project is successful when:

1. **Daily use:** Cyrus (and ideally Martin) use bot for task management instead of Nextcloud web 80%+ of the time
2. **Mobile-first:** Can manage entire day's tasks from phone without opening browser
3. **Reliable:** Bot uptime >99%, CalDAV sync works consistently
4. **Fast:** Commands respond in <2 seconds, feel instant on mobile
5. **Natural:** Interface feels intuitive, not like fighting with commands
6. **Extensible:** Architecture supports future features without major rewrites

**Stretch goal:** Other household members (Tea, Ellie) adopt bot for their own task management, validating multi-user v2.0 direction.