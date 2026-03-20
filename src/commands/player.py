import discord
from discord import app_commands

import db.repository as db_repo


@app_commands.command(name="register", description="Join the active season in this channel")
async def register(interaction: discord.Interaction):
    season = db_repo.get_active_season(interaction.channel_id)
    if not season:
        await interaction.response.send_message(
            "No active season in this channel. Ask someone to start one with `/season create`.",
            ephemeral=True
        )
        return

    existing = db_repo.get_player(season['id'], interaction.user.id)
    if existing:
        await interaction.response.send_message(
            f"You're already registered for **{season['name']}**!", ephemeral=True
        )
        return

    db_repo.register_player(
        season['id'],
        interaction.user.id,
        interaction.user.display_name
    )

    await interaction.response.send_message(
        f"✅ {interaction.user.mention} has joined **{season['name']}**!\n"
        "Submit your daily Wordle results in this channel to score points."
    )


@app_commands.command(name="leave", description="Leave the active season in this channel")
async def leave(interaction: discord.Interaction):
    season = db_repo.get_active_season(interaction.channel_id)
    if not season:
        await interaction.response.send_message(
            "No active season in this channel.", ephemeral=True
        )
        return

    removed = db_repo.unregister_player(season['id'], interaction.user.id)
    if not removed:
        await interaction.response.send_message(
            f"You're not registered for **{season['name']}**.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"👋 {interaction.user.mention} has left **{season['name']}**. "
        "Your scores have been removed."
    )
