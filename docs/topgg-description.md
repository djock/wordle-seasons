### Turn your Wordle habit into a season-long competition

**Wordle Seasons Bot** brings structured, competitive Wordle seasons to any Discord channel. No spreadsheets, no manual tracking — just paste your daily Wordle result and let the bot handle the rest.


### How it works

1. A server admin runs `/season create` to start a season — give it a name, set a duration, and optionally add a prize.
2. Players join with `/register`.
3. Every day, paste your Wordle result directly in the channel. No command needed — the bot detects and records it automatically.
4. Once everyone has submitted for the day, the leaderboard posts automatically.
5. At the end of the season, the bot announces the winner with 🥇🥈🥉 medals and the prize.


### Features

**Zero friction** — paste your Wordle share text, the bot does the rest. Supports all color schemes: standard, high contrast, and white squares.

**Configurable seasons** — set duration, missed-day penalty, optional Tetris bonus, daily reminders, and auto-penalty at midnight.

**Automatic leaderboards** — posts the moment every player submits for the day.

**Multi-channel** — each channel runs its own independent season.

**Season history** — browse past seasons, winners, and prizes with `/history`.

**Tetris Bonus** — an optional twist: grid patterns that mimic a Tetris line clear earn −1 off your season total.


### Scoring

**Lower score wins**, just like Wordle itself.

- Solved in N attempts → **+N pts**
- Failed (X/6) → **+7 pts**
- Missed day → **+penalty** (default +10, configurable)
- Tetris bonus → **−1 pt** per bonus earned


### Commands

`/season create` · `/season cancel` · `/season info` · `/register` · `/leave` · `/leaderboard` · `/history` · `/help`
