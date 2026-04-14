import asyncio
import logging
import schedule
import threading
import time
from datetime import datetime, timedelta

from core import utils
from core.constants import STATUS_ACTIVE, STATUS_COMPLETED
from bot import service as bot_service
import db.repository as db_repo

logger = logging.getLogger(__name__)

_client = None


def start(client):
    global _client
    _client = client

    schedule.every().day.at("20:00").do(
        lambda: asyncio.run_coroutine_threadsafe(run_reminders(), _client.loop)
    )
    schedule.every().day.at("00:00").do(
        lambda: asyncio.run_coroutine_threadsafe(run_midnight_jobs(), _client.loop)
    )
    threading.Thread(target=_run_loop, daemon=True).start()
    logger.info("Scheduler started")


def _run_loop():
    while True:
        schedule.run_pending()
        time.sleep(1)


async def run_reminders():
    """Send daily reminders for all active seasons that have reminders enabled."""
    today_wordle_id = utils.calculate_wordle_id_of_the_day()
    for season in db_repo.get_all_active_seasons():
        if not season['reminders_enabled']:
            continue

        season_end_id = utils.get_season_end_id(season)
        if not (season['start_wordle_id'] <= today_wordle_id <= season_end_id):
            continue

        missing = bot_service.get_missing_players(season, today_wordle_id)
        if not missing:
            continue

        channel = _client.get_channel(season['channel_id'])
        if not channel:
            continue

        await channel.send(
            f"{utils.format_mentions(missing)} {utils.get_random_wordle_reminder_text()}"
        )


async def run_midnight_jobs():
    """Apply auto-penalties and finalize ended seasons."""
    yesterday_wordle_id = utils.calculate_wordle_id_for_yesterday()
    for season in db_repo.get_all_active_seasons():
        await _process_season(season, yesterday_wordle_id)


async def _process_season(season, yesterday_wordle_id: int):
    channel = _client.get_channel(season['channel_id'])
    season_end_id = utils.get_season_end_id(season)

    # Auto-penalty for yesterday's missing players
    if (season['auto_penalty_enabled'] and
            season['start_wordle_id'] <= yesterday_wordle_id <= season_end_id):
        missing = bot_service.get_missing_players(season, yesterday_wordle_id)
        for player in missing:
            db_repo.upsert_score(
                season['id'], player['id'], yesterday_wordle_id,
                raw_score=season['missed_day_penalty'],
                is_auto_penalty=True
            )

        if missing and channel:
            await channel.send(
                f"⏰ Auto-update: Added **{season['missed_day_penalty']}** penalty points "
                f"for missing yesterday's Wordle to {utils.format_mentions(missing)}"
            )
            lb = bot_service.get_leaderboard(season, yesterday_wordle_id)
            await channel.send(lb)

    # Finalize season if all days have passed
    if yesterday_wordle_id >= season_end_id:
        await finalize_season(season, channel)


async def finalize_season(season, channel):
    """Post finale, announce winner, archive season, and renew if recurring."""
    current_season = db_repo.get_season(season['id'])
    if not current_season or current_season['status'] != STATUS_ACTIVE:
        return

    season = current_season
    season_end_id = utils.get_season_end_id(season)

    # Collect players before finalizing so we can re-register them in the next season
    previous_players = db_repo.get_season_players(season['id'])

    player_scores = bot_service.get_sorted_player_scores(season)
    winner_id = player_scores[0].discord_user_id if player_scores else None

    msg = bot_service.build_leaderboard_message(season, player_scores, season_end_id, is_final=True)

    db_repo.update_season_status(season['id'], STATUS_COMPLETED, winner_id)
    logger.info(f"Season '{season['name']}' finalized, winner Discord ID: {winner_id}")

    if channel:
        await channel.send(msg)

    if season['recurring']:
        await _renew_season(season, season_end_id, previous_players, channel)


async def _renew_season(season, previous_end_id: int, previous_players: list, channel):
    """Create the next iteration of a recurring season, carrying over all players."""
    now = datetime.now(utils.ROMANIA_TZ)
    new_start_wordle_id = previous_end_id + 1
    start_date = now.isoformat()
    end_date = (now + timedelta(days=season['duration_days'])).isoformat()
    new_season_number = season['season_number'] + 1

    new_season_id = db_repo.create_season(
        channel_id=season['channel_id'],
        guild_id=season['guild_id'],
        creator_id=season['creator_id'],
        name=season['name'],
        prize=season['prize'],
        duration_days=season['duration_days'],
        missed_day_penalty=season['missed_day_penalty'],
        tetris_bonus_enabled=season['tetris_bonus_enabled'],
        reminders_enabled=season['reminders_enabled'],
        auto_penalty_enabled=season['auto_penalty_enabled'],
        start_wordle_id=new_start_wordle_id,
        start_date=start_date,
        end_date=end_date,
        recurring=True,
        season_number=new_season_number,
    )

    for player in previous_players:
        db_repo.register_player(new_season_id, player['discord_user_id'], player['discord_username'])

    end_display = (now + timedelta(days=season['duration_days'])).strftime("%Y-%m-%d")
    new_season = db_repo.get_season(new_season_id)
    display_name = utils.get_season_display_name(new_season)
    logger.info(f"Recurring season '{display_name}' renewed, new season ID: {new_season_id}")

    if channel:
        await channel.send(
            f"🔄 **{display_name}** has been automatically renewed!\n"
            f"📅 New season runs for **{season['duration_days']} days** (ends {end_display})\n"
            f"📊 Starting from Wordle **#{new_start_wordle_id}**\n"
            f"All previous players have been re-registered. Good luck! 🍀\n"
            f"💰 To set a new prize, use `/season update prize:...`"
        )
