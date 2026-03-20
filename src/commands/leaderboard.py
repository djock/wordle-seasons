import discord
from discord import app_commands

from core import utils
from core.constants import STATUS_COMPLETED
from bot import service as bot_service
import db.repository as db_repo


@app_commands.command(name="leaderboard", description="Show the current season standings")
async def leaderboard(interaction: discord.Interaction):
    season = db_repo.get_active_season(interaction.channel_id)
    if not season:
        await interaction.response.send_message(
            "No active season in this channel.", ephemeral=True
        )
        return

    today_wordle_id = utils.calculate_wordle_id_of_the_day()
    is_final = today_wordle_id >= utils.get_season_end_id(season)

    msg = bot_service.get_leaderboard(season, today_wordle_id, is_final=is_final)
    await interaction.response.send_message(msg)


@app_commands.command(name="history", description="Show past seasons in this channel")
async def history(interaction: discord.Interaction):
    past_seasons = db_repo.get_completed_seasons(interaction.channel_id)

    if not past_seasons:
        await interaction.response.send_message(
            "No completed seasons in this channel yet.", ephemeral=True
        )
        return

    lines = ["**Past Seasons**"]
    for season in past_seasons[:10]:
        status_icon = "✅" if season['status'] == STATUS_COMPLETED else "❌"
        winner_text = f" — 🏆 <@{season['winner_id']}>" if season['winner_id'] else ""
        prize_text = f" • 🎁 {season['prize']}" if season['prize'] else ""
        lines.append(
            f"{status_icon} **{season['name']}** "
            f"({season['duration_days']}d){winner_text}{prize_text}"
        )

    await interaction.response.send_message("\n".join(lines))
