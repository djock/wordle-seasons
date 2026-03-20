<div align="center">
  <img src="assets/banner.png" alt="Wordle Seasons Bot" width="200" />

  # Wordle Seasons Bot

  A self-hosted Discord bot for running competitive Wordle seasons — multi-server, slash commands, SQLite, no external dependencies.

  ![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)
  ![discord.py](https://img.shields.io/badge/discord.py-2.0+-5865F2?logo=discord&logoColor=white)
  ![License](https://img.shields.io/badge/license-MIT-green)
</div>

---

## What is this?

Wordle Seasons Bot lets any Discord server run competitive Wordle seasons in any channel. Players paste their daily Wordle result, and the bot automatically tracks scores, handles missed days, and announces a winner at the end of each season.

**Key features:**

- **Multi-server & multi-channel** — each channel runs its own independent season
- **Slash commands** — `/season create`, `/register`, `/leaderboard`, `/history`
- **Configurable seasons** — duration, missed-day penalty, tetris bonus, reminders, auto-penalty
- **Automatic leaderboard** — posts standings once all players have submitted for the day
- **Tetris bonus mechanic** — rewards clever Wordle grid patterns with score deductions
- **Daily automation** — reminders at 20:00, auto-penalty + season finalization at midnight (Romania time / Europe/Bucharest)
- **SQLite storage** — no external database needed; a single file holds everything
- **Docker-ready** — includes `Dockerfile` and `docker-compose.yml`

---

## Table of Contents

- [How It Works](#how-it-works)
- [Scoring](#scoring)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [1. Create a Discord Application](#1-create-a-discord-application)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Run the Bot](#3-run-the-bot)
- [Slash Commands](#slash-commands)
- [Daily Automation](#daily-automation)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## How It Works

1. A server admin runs `/season create` to start a season in a channel, choosing its name, duration, and optional prize.
2. Players join with `/register`.
3. Every day, each player pastes their Wordle result directly in the channel — no command needed. The bot parses the message automatically.
4. Once all registered players have submitted for the day, the bot posts the updated leaderboard.
5. At midnight, the bot penalises any players who forgot to submit and finalizes the season when its last day passes.
6. The winner is announced with medals, a congratulatory message, and the season prize.

---

## Scoring

| Event | Points |
|---|---|
| Solved in N attempts | +N |
| Failed (X/6) | +7 |
| Missed day | +penalty (configurable, default 10) |
| Tetris bonus | −1 per bonus earned |

**Lower score is better** — fewer attempts = better, same as Wordle itself.

### Tetris Bonus

An optional mechanic that rewards grid patterns similar to a Tetris line clear. When a Wordle row becomes "complete" using colored squares from earlier rows, the player earns −1 off their season total. Can be disabled per season.

### Final Score Formula

```
Final Score = SUM(daily attempt counts + missed-day penalties) - SUM(tetris bonuses)
```

Tiebreaker: higher cumulative tetris points wins.

---

## Project Structure

```
wordle-seasons/
├── src/
│   ├── app.py              # Bot entry point, Discord event handlers
│   ├── config.py           # Environment variable loading
│   │
│   ├── core/               # Pure domain logic — no Discord dependency
│   │   ├── constants.py    # Game constants and season status values
│   │   ├── models.py       # Dataclasses and custom exceptions
│   │   ├── parsers.py      # Wordle message parsing, tetris bonus, color counts
│   │   ├── validators.py   # Input validation (ID, score, grid)
│   │   ├── utils.py        # Timezone helpers, Wordle ID calculation, random text
│   │   └── localizations.py # All user-facing message strings
│   │
│   ├── db/                 # Database layer (SQLite)
│   │   ├── schema.py       # Table definitions and connection helper
│   │   └── repository.py   # All CRUD operations
│   │
│   ├── bot/                # Bot service layer
│   │   ├── service.py      # Score processing, leaderboard building
│   │   └── scheduler.py    # Scheduled jobs (reminders, midnight tasks)
│   │
│   └── commands/           # Discord slash command handlers
│       ├── season.py       # /season create | cancel | info
│       ├── player.py       # /register
│       └── leaderboard.py  # /leaderboard | /history
│
├── tests/
│   └── test_core.py        # Unit tests for core/ (parsers, validators)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── pytest.ini
```

---

## Getting Started

### 1. Create a Discord Application

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) and click **New Application**.
2. Go to **Bot** → click **Add Bot**.
3. Under **Privileged Gateway Intents**, enable:
   - **Server Members Intent**
   - **Message Content Intent**
4. Go to **OAuth2 → URL Generator**, select scopes `bot` + `applications.commands`, and permissions:
   - Send Messages
   - Read Messages / View Channels
   - Mention Everyone
   - Use Slash Commands
5. Open the generated URL in a browser to invite the bot to your server.
6. Copy your **Bot Token** (Bot page → Reset Token) and your **Application ID** (General Information page).

### 2. Configure Environment Variables

Create `.env.prod` (and optionally `.env.dev`) in the project root:

```env
BOT_TOKEN=your_discord_bot_token
WORDLE_BOT_ID=your_application_id
```

Optional:

```env
# Path to the SQLite database file (default: wordle_seasons.db in working dir)
DB_PATH=/data/wordle_seasons.db
```

### 3. Run the Bot

**Option A — Docker Compose (recommended)**

```bash
# Production
docker-compose up prod -d

# Development (mounts source for live reload)
docker-compose up dev

# Run tests
docker-compose run tests
```

**Option B — Local Python**

```bash
pip install -r requirements.txt

# Development mode
STAGE=dev python src/app.py

# Production mode
python src/app.py
```

The SQLite database is created automatically on first run.

---

## Slash Commands

### `/season create`

Starts a new season in the current channel. Only one active season is allowed per channel at a time.

| Parameter | Required | Default | Description |
|---|---|---|---|
| `name` | ✅ | — | Season name, e.g. `Summer 2025` |
| `days` | ✅ | — | Duration in days (1–365) |
| `prize` | ❌ | none | Prize description, e.g. `Winner buys dinner` |
| `missed_penalty` | ❌ | `10` | Points added for each missed day |
| `tetris` | ❌ | `true` | Enable tetris bonus mechanic |
| `reminders` | ❌ | `true` | Send daily reminders to players who haven't submitted |
| `auto_penalty` | ❌ | `true` | Auto-apply missed day penalty at midnight |

```
/season create name:Office Wordle War days:14 prize:Loser buys coffee
```

### `/season cancel`

Cancels the active season. Only the person who created it can cancel it.

### `/season info`

Shows the active season's configuration, current day, and player count.

### `/register`

Joins the active season in the current channel. Players can join at any point during the season.

### `/leaderboard`

Shows the current standings for the active season.

```
Office Wordle War leaderboard, day 4 / 14
[1] Alice: 18
[2] Bob: 21
[3] Charlie: 24
```

### `/history`

Shows the last 10 completed or cancelled seasons in the channel.

```
Past Seasons
✅ Office Wordle War (14d) — 🏆 @Alice • 🎁 Loser buys coffee
✅ Winter Challenge (7d) — 🏆 @Bob
❌ Abandoned Season (30d)
```

---

## Submitting Results

Players paste their Wordle share text directly in the channel — no command needed:

```
Wordle 1,245 3/6*

⬛🟨⬛⬛⬛
🟩⬛🟨🟨⬛
🟩🟩🟩🟩🟩
```

The bot responds with a confirmation, the player's running season score, and any tetris bonus or missed-day penalty info. Once **all registered players** have submitted for that Wordle, the leaderboard is posted automatically.

---

## Daily Automation

The bot runs two scheduled jobs every day in the **Europe/Bucharest** timezone:

| Time | Job | Condition |
|---|---|---|
| 20:00 | **Reminder** — mentions players who haven't submitted today | `reminders: true` |
| 00:00 | **Auto-penalty** — applies missed day points for yesterday's no-shows | `auto_penalty: true` |
| 00:00 | **Season check** — finalizes any season whose last day has passed | always |

At season end, the bot posts the full final leaderboard with 🥇🥈🥉 medals, the winner announcement, prize, and a highest-tetris honorable mention.

---

## Development

**Run tests:**

```bash
pytest tests/ -v
```

**Project dependencies:**

```
discord.py>=2.0.0
python-dotenv
schedule
pytest
```

**Adding a new slash command:**

1. Create a handler function (or `app_commands.Group`) in `src/commands/`
2. Register it in `src/app.py`'s `setup_hook()`

**Database schema** is in `db/schema.py` and is auto-applied on startup via `init_db()`. The SQLite file defaults to `wordle_seasons.db` in the working directory; override with the `DB_PATH` environment variable.

**Backing up the database:**

```bash
# Local
cp wordle_seasons.db wordle_seasons_backup_$(date +%Y%m%d).db

# From a Docker volume
docker run --rm \
  -v wordlebot_seasons_data:/data \
  -v $(pwd):/backup \
  alpine cp /data/wordle_seasons.db /backup/wordle_seasons_backup.db
```

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for anything beyond a small bug fix, so we can discuss the approach first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes and add tests where applicable
4. Run `pytest tests/ -v` and confirm all tests pass
5. Open a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.
