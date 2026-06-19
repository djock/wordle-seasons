import os
import time
import logging

import discord
from discord.ext import commands

import config
from core import utils
from bot import scheduler
from bot import service as bot_service
from db.schema import init_db
import db.repository as db_repo
from commands.season import SeasonGroup
from commands.player import register, leave
from commands.leaderboard import leaderboard, history
from commands.help import help_command

os.environ.setdefault("TZ", "Europe/Bucharest")
if hasattr(time, "tzset"):
    time.tzset()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def setup_hook():
    bot.tree.add_command(SeasonGroup())
    bot.tree.add_command(register)
    bot.tree.add_command(leave)
    bot.tree.add_command(leaderboard)
    bot.tree.add_command(history)
    bot.tree.add_command(help_command)
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

bot.setup_hook = setup_hook


@bot.event
async def on_ready():
    for guild in bot.guilds:
        logger.info(f"Connected to server: {guild.name} (ID: {guild.id})")
    scheduler.start(bot)


@bot.event
async def on_message(message):
    if message.author.id == config.WORDLE_BOT_ID:
        return

    if 'Wordle' not in message.content:
        return
    if '/' not in message.content and 'X/' not in message.content:
        return

    season = db_repo.get_active_season(message.channel.id)
    if not season:
        return

    player = db_repo.get_player(season['id'], message.author.id)
    if not player:
        await message.channel.send(
            f"Hey {message.author.mention}! Use `/register` to join **{season['name']}** before submitting scores."
        )
        return

    result = bot_service.update_score(player, message.content, season)
    await message.channel.send(result.message)

    if result.wordle_id is not None:
        wordle_id = result.wordle_id
        if bot_service.all_players_submitted(season, wordle_id):
            season_end_id = utils.get_season_end_id(season)
            is_final = wordle_id >= season_end_id
            if is_final:
                await scheduler.finalize_season(season, message.channel)
            else:
                lb_msg = bot_service.get_leaderboard(season, wordle_id, is_final=False)
                await message.channel.send(lb_msg)


if __name__ == '__main__':
    init_db()
    bot.run(config.BOT_TOKEN)
