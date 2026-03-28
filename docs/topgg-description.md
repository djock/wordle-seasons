# top.gg Long Description

---

## Turn your Wordle habit into a season-long competition

**Wordle Seasons Bot** brings structured, competitive Wordle seasons to any Discord channel. No spreadsheets, no manual tracking — just paste your daily Wordle result and let the bot handle the rest.

---

## How it works

1. A server admin runs `/season create` to start a season — give it a name, set a duration (1–365 days), and optionally add a prize.
2. Players join with `/register`.
3. Every day, each player pastes their Wordle share text directly in the channel. No command needed — the bot auto-detects and records the score.
4. Once everyone has submitted for the day, the full leaderboard posts automatically.
5. At the end of the season, the bot announces the winner with 🥇🥈🥉 medals and the prize.

---

## Features

**Zero friction score submission**
Players paste their Wordle share text directly in the channel — the bot parses it automatically. Supports all Wordle color schemes: standard, high contrast, and white squares.

**Configurable seasons**
Every season is fully customizable:
- Duration: 1 to 365 days
- Missed-day penalty (default +10 points per missed day)
- Tetris bonus mechanic (optional −1 for clever grid patterns)
- Daily reminders at 20:00 for players who haven't submitted yet
- Auto-penalty applied at midnight so seasons stay on track without admin effort

**Automatic leaderboards**
The leaderboard posts itself the moment every registered player submits for the day. No command needed.

**Multi-channel support**
Each channel runs its own independent season. Multiple channels in the same server can run simultaneously.

**Season history**
Use `/history` to browse past seasons, winners, and prizes in any channel.

**Tetris Bonus mechanic**
An optional twist: when a Wordle grid row is "completed" by colored squares from earlier rows — like a Tetris line clear — the player earns −1 off their season total. Adds strategy to how you approach your guesses.

---

## Scoring

| Event | Points |
|---|---|
| Solved in N attempts | +N |
| Failed (X/6) | +7 |
| Missed day | +penalty (configurable, default +10) |
| Tetris bonus | −1 per bonus earned |

**Lower score wins** — just like Wordle itself.

---

## Example session

```
# Alice pastes her result in the channel:
Wordle 1,245 3/6

⬛🟨⬛⬛⬛
🟩⬛🟨🟨⬛
🟩🟩🟩🟩🟩

# Bot replies:
✅ @Alice — Wordle 1245 solved in 3!
Season score: 18 pts  •  Day 6 / 14

# Once Bob and Charlie submit too, the leaderboard auto-posts:
Office Wordle War — Day 6 / 14
🥇 Alice:   18 pts
🥈 Bob:     21 pts
🥉 Charlie: 27 pts
```

---

## Commands

| Command | What it does |
|---|---|
| `/season create` | Start a new season in this channel |
| `/season cancel` | Cancel the active season |
| `/season info` | Show current season settings |
| `/register` | Join the active season |
| `/leave` | Leave the active season |
| `/leaderboard` | Show current standings |
| `/history` | Show past seasons |
| `/help` | List all commands |

---

## Self-hosted & open source

Wordle Seasons Bot is **self-hosted** — you run it on your own server or machine. This means your data stays yours, there are no usage limits, and you can modify it freely.

Setup takes under 5 minutes with Docker:

```bash
git clone https://github.com/djock/wordle-seasons.git
cd wordle-seasons
cp .env.example .env.prod  # add your bot token
docker-compose up prod -d
```

Full setup guide and source code: **https://github.com/djock/wordle-seasons**

MIT licensed. Contributions welcome.

---

## Required permissions

- Read Messages / View Channels
- Send Messages
- Use Slash Commands
- Mention Everyone (for daily reminders)
