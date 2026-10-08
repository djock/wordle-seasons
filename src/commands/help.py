import discord
from discord import app_commands


HELP_TEXT = """\
**Wordle Seasons Bot** — run competitive Wordle seasons in your server.

**Season management**
`/season create` — start a new season in this channel (name, duration, prize, options)
`/season cancel` — cancel the active season (creator only)
`/season info` — show current season settings and status

**Players**
`/register` — join the active season in this channel
`/leave` — leave the active season and remove your scores

**Scores & standings**
`/leaderboard` — show the current standings
`/history` — show past seasons in this channel

**Submitting results**
Just paste your Wordle share text in the channel — no command needed. \
The bot auto-detects and records your score.

Lower score is better. Missed days cost penalty points (default +10). \
An optional Tetris bonus rewards clever grid patterns with −1.

🔗 Source & self-hosting: <https://github.com/djock/wordle-seasons>
"""


@app_commands.command(name="help", description="Show all Wordle Seasons commands and how to play")
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(HELP_TEXT, ephemeral=True)
