import discord
from discord import app_commands
from datetime import datetime, timedelta

from core import utils
from core.utils import get_season_display_name
import db.repository as db_repo


class SeasonGroup(app_commands.Group, name="season", description="Manage Wordle seasons"):

    @app_commands.command(name="create", description="Start a new Wordle season in this channel")
    @app_commands.describe(
        name="Season name, e.g. 'Summer 2025'",
        days="Duration in number of days",
        number="Season number (default: 1). Auto-increments on each renewal.",
        prize="Prize for the winner (optional)",
        missed_penalty="Points added for missed days (default: 10)",
        tetris="Enable tetris bonus mechanic (default: true)",
        reminders="Send daily reminders to players who haven't submitted (default: true)",
        auto_penalty="Auto-apply missed day penalty at midnight (default: true)",
        recurring="Automatically start a new season with the same settings when this one ends (default: false)",
    )
    async def create(
        self,
        interaction: discord.Interaction,
        name: str,
        days: int,
        number: int = 1,
        prize: str = None,
        missed_penalty: int = 10,
        tetris: bool = True,
        reminders: bool = True,
        auto_penalty: bool = True,
        recurring: bool = False,
    ):
        channel_id = interaction.channel_id
        guild_id = interaction.guild_id

        existing = db_repo.get_active_season(channel_id)
        if existing:
            await interaction.response.send_message(
                f"There's already an active season in this channel: **{existing['name']}**.\n"
                "Use `/season cancel` to cancel it first.",
                ephemeral=True
            )
            return

        if days < 1 or days > 365:
            await interaction.response.send_message(
                "Season duration must be between 1 and 365 days.", ephemeral=True
            )
            return

        today_wordle_id = utils.calculate_wordle_id_of_the_day()
        now = datetime.now(utils.ROMANIA_TZ)
        start_date = now.isoformat()
        end_date = (now + timedelta(days=days)).isoformat()

        season_id = db_repo.create_season(
            channel_id=channel_id,
            guild_id=guild_id,
            creator_id=interaction.user.id,
            name=name,
            prize=prize,
            duration_days=days,
            missed_day_penalty=missed_penalty,
            tetris_bonus_enabled=tetris,
            reminders_enabled=reminders,
            auto_penalty_enabled=auto_penalty,
            start_wordle_id=today_wordle_id,
            start_date=start_date,
            end_date=end_date,
            recurring=recurring,
            season_number=number,
        )

        season = db_repo.get_season(season_id)
        display_name = get_season_display_name(season)
        prize_line = f"\n🎁 Prize: **{prize}**" if prize else ""
        tetris_line = "" if tetris else "\n⚠️ Tetris bonus disabled"
        recurring_line = "\n🔄 Recurring: new season starts automatically when this one ends" if recurring else ""
        end_display = (now + timedelta(days=days)).strftime("%Y-%m-%d")

        await interaction.response.send_message(
            f"🎮 Season **{display_name}** has started!\n"
            f"📅 Duration: **{days} days** (ends {end_display})\n"
            f"📊 Starting from Wordle **#{today_wordle_id}**"
            f"{prize_line}{tetris_line}{recurring_line}\n\n"
            f"Players can join with `/register` 🙋"
        )

    @app_commands.command(name="cancel", description="Cancel the active season in this channel")
    async def cancel(self, interaction: discord.Interaction):
        season = db_repo.get_active_season(interaction.channel_id)
        if not season:
            await interaction.response.send_message(
                "No active season in this channel.", ephemeral=True
            )
            return

        if season['creator_id'] != interaction.user.id:
            await interaction.response.send_message(
                "Only the person who created the season can cancel it.", ephemeral=True
            )
            return

        db_repo.update_season_status(season['id'], 'cancelled')
        await interaction.response.send_message(
            f"❌ Season **{get_season_display_name(season)}** has been cancelled."
        )

    @app_commands.command(name="info", description="Show the active season details")
    async def info(self, interaction: discord.Interaction):
        season = db_repo.get_active_season(interaction.channel_id)
        if not season:
            await interaction.response.send_message(
                "No active season in this channel.", ephemeral=True
            )
            return

        players = db_repo.get_season_players(season['id'])
        today_wordle_id = utils.calculate_wordle_id_of_the_day()
        day_in_season = max(1, today_wordle_id - season['start_wordle_id'] + 1)

        prize_line = f"\n🎁 Prize: **{season['prize']}**" if season['prize'] else ""
        tetris_line = f"\n🎲 Tetris bonus: {'enabled' if season['tetris_bonus_enabled'] else 'disabled'}"
        penalty_line = f"\n⚠️ Missed day penalty: {season['missed_day_penalty']} pts"
        recurring_line = "\n🔄 Recurring: yes" if season['recurring'] else ""

        await interaction.response.send_message(
            f"**{get_season_display_name(season)}**\n"
            f"📅 Day {day_in_season} / {season['duration_days']} "
            f"(Wordle #{season['start_wordle_id']}–"
            f"#{utils.get_season_end_id(season)})\n"
            f"👥 Players: {len(players)}"
            f"{prize_line}{tetris_line}{penalty_line}{recurring_line}"
        )

    @app_commands.command(name="update", description="Update the active season's name or prize")
    @app_commands.describe(
        name="New base name for the season",
        prize="New prize for the winner",
    )
    async def update(
        self,
        interaction: discord.Interaction,
        name: str = None,
        prize: str = None,
    ):
        season = db_repo.get_active_season(interaction.channel_id)
        if not season:
            await interaction.response.send_message(
                "No active season in this channel.", ephemeral=True
            )
            return

        if season['creator_id'] != interaction.user.id:
            await interaction.response.send_message(
                "Only the person who created the season can update it.", ephemeral=True
            )
            return

        if name is None and prize is None:
            await interaction.response.send_message(
                "Provide at least one of `name` or `prize` to update.", ephemeral=True
            )
            return

        db_repo.update_season(season['id'], name=name, prize=prize)
        updated = db_repo.get_season(season['id'])

        changes = []
        if name is not None:
            changes.append(f"📛 Name: **{get_season_display_name(updated)}**")
        if prize is not None:
            changes.append(f"🎁 Prize: **{prize}**" if prize else "🎁 Prize: removed")

        await interaction.response.send_message(
            "✅ Season updated!\n" + "\n".join(changes)
        )
