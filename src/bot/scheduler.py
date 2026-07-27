import asyncio
import logging
from datetime import datetime, time as datetime_time, timedelta

from core import utils
from core.constants import STATUS_ACTIVE, STATUS_COMPLETED
from bot import service as bot_service
import db.repository as db_repo

logger = logging.getLogger(__name__)

_client = None
_scheduler_task = None


def start(client):
    global _client, _scheduler_task
    _client = client

    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_run_loop())
    logger.info("Scheduler started")


async def _run_loop():
    """Run daily jobs on the Discord event loop in Romania time.

    Keeping the scheduler on the same loop as Discord avoids submitting
    coroutines from a second thread, which can silently fail after reconnects.
    The date guards also make a job run once when the bot starts after its
    scheduled time.
    """
    reminder_date = None
    midnight_date = None
    while True:
        now = datetime.now(utils.ROMANIA_TZ)
        today = now.date()

        if now.time() >= datetime_time(20, 0) and reminder_date != today:
            reminder_date = today
            try:
                await run_reminders()
            except Exception:
                logger.exception("Daily reminder job failed")

        if now.time() < datetime_time(20, 0) and midnight_date != today:
            midnight_date = today
            try:
                await run_midnight_jobs()
            except Exception:
                logger.exception("Midnight job failed")

        await asyncio.sleep(30)


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

        try:
            await channel.send(
                f"{utils.format_mentions(missing)} {utils.get_random_wordle_reminder_text()}"
            )
        except Exception:
            logger.exception("Failed to send reminder for season %s", season['id'])


async def run_midnight_jobs():
    """Apply auto-penalties and finalize ended seasons."""
    yesterday_wordle_id = utils.calculate_wordle_id_for_yesterday()
    for season in db_repo.get_all_active_seasons():
        try:
            await _process_season(season, yesterday_wordle_id)
        except Exception:
            logger.exception("Failed to process season %s", season['id'])


async def _process_season(season, yesterday_wordle_id: int):
    channel = _client.get_channel(season['channel_id'])
    season_end_id = utils.get_season_end_id(season)

    # Auto-penalty for yesterday's missing players
    missing_by_id = {}
    if season['auto_penalty_enabled']:
        last_penalty_id = min(yesterday_wordle_id, season_end_id)
        if last_penalty_id >= season['start_wordle_id']:
            for wordle_id in range(season['start_wordle_id'], last_penalty_id + 1):
                missing = bot_service.get_missing_players(season, wordle_id)
                for player in missing:
                    missing_by_id[player['id']] = player
                    db_repo.upsert_score(
                        season['id'], player['id'], wordle_id,
                        raw_score=season['missed_day_penalty'],
                        is_auto_penalty=True
                    )

        if missing_by_id and channel:
            try:
                await channel.send(
                    f"⏰ Auto-update: Added **{season['missed_day_penalty']}** penalty points "
                    f"for missed Wordle days to {utils.format_mentions(list(missing_by_id.values()))}"
                )
                lb = bot_service.get_leaderboard(season, yesterday_wordle_id)
                for chunk in utils.split_message(lb):
                    await channel.send(chunk)
            except Exception:
                logger.exception("Failed to send penalty update for season %s", season['id'])

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
        try:
            for chunk in utils.split_message(msg):
                await channel.send(chunk)
        except Exception:
            logger.exception("Failed to send finale for season %s", season['id'])

    if season['recurring']:
        await _renew_season(season, season_end_id, previous_players, channel)


async def _renew_season(season, previous_end_id: int, previous_players: list, channel):
    """Create the next iteration of a recurring season, carrying over all players."""
    now = datetime.now(utils.ROMANIA_TZ)
    new_start_wordle_id = previous_end_id + 1
    start_date = now.isoformat()
    end_date = (now + timedelta(days=season['duration_days'] - 1)).isoformat()
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
        db_repo.register_player(
            new_season_id, player['discord_user_id'], player['discord_username'],
            joined_wordle_id=new_start_wordle_id,
        )

    end_display = (now + timedelta(days=season['duration_days'] - 1)).strftime("%Y-%m-%d")
    new_season = db_repo.get_season(new_season_id)
    display_name = utils.get_season_display_name(new_season)
    logger.info(f"Recurring season '{display_name}' renewed, new season ID: {new_season_id}")

    if channel:
        try:
            renewal = (
                f"🔄 **{display_name}** has been automatically renewed!\n"
                f"📅 New season runs for **{season['duration_days']} days** (ends {end_display})\n"
                f"📊 Starting from Wordle **#{new_start_wordle_id}**\n"
                f"All previous players have been re-registered. Good luck! 🍀\n"
            )
            renewal += "💰 To set a new prize, use `/season update prize:...`"
            for chunk in utils.split_message(renewal):
                await channel.send(chunk)
        except Exception:
            logger.exception("Failed to send renewal notice for season %s", season['id'])
