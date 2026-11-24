import asyncio
import sys
import types
from unittest.mock import AsyncMock, Mock

sys.modules.setdefault('dotenv', types.SimpleNamespace(load_dotenv=lambda **kwargs: None))

from bot import scheduler
from bot import service as bot_service
from core.models import ParsedWordleContent
from core.constants import STATUS_ACTIVE, STATUS_COMPLETED


def test_finalize_season_skips_non_active(monkeypatch):
    season = {
        'id': 7,
        'status': STATUS_ACTIVE,
        'name': 'Spring',
        'start_wordle_id': 1000,
        'duration_days': 3,
        'channel_id': 1,
        'recurring': 0,
    }

    monkeypatch.setattr(
        scheduler.db_repo,
        'get_season',
        lambda season_id: {**season, 'status': STATUS_COMPLETED}
    )
    update_status = AsyncMock()
    channel = AsyncMock()

    monkeypatch.setattr(scheduler.db_repo, 'update_season_status', update_status)

    asyncio.run(scheduler.finalize_season(season, channel))

    update_status.assert_not_called()
    channel.send.assert_not_called()


def test_process_season_catches_up_missed_days_and_finalizes(monkeypatch):
    season = {
        'id': 7,
        'status': STATUS_ACTIVE,
        'name': 'Spring',
        'season_number': 1,
        'start_wordle_id': 1000,
        'duration_days': 3,
        'channel_id': 1,
        'auto_penalty_enabled': 1,
        'auto_update_enabled': 1,
        'missed_day_penalty': 10,
        'recurring': 0,
    }
    players = [{'id': 11, 'discord_user_id': 101, 'discord_username': 'Ada'}]
    channel = AsyncMock()
    finalize = AsyncMock()
    upsert = Mock()

    monkeypatch.setattr(scheduler.bot_service, 'get_missing_players', lambda *_: players)
    monkeypatch.setattr(scheduler.db_repo, 'upsert_score', upsert)
    monkeypatch.setattr(scheduler, 'finalize_season', finalize)

    class Client:
        def get_channel(self, _):
            return channel

    scheduler._client = Client()
    asyncio.run(scheduler._process_season(season, 1002))

    assert [call.args[2] for call in upsert.call_args_list] == [1000, 1001, 1002]
    finalize.assert_awaited_once_with(season, channel)


def test_late_joiner_is_not_missing_before_registration(monkeypatch):
    season = {'id': 1, 'start_wordle_id': 100}
    players = [
        {'id': 1, 'joined_wordle_id': 100},
        {'id': 2, 'joined_wordle_id': 102},
    ]
    monkeypatch.setattr(scheduler.bot_service.db_repo, 'get_season_players', lambda _: players)
    monkeypatch.setattr(
        scheduler.bot_service.db_repo,
        'get_scores_for_wordle_id',
        lambda *_: [{'player_id': 1}],
    )

    assert scheduler.bot_service.get_missing_players(season, 100) == []


def test_future_wordle_submission_is_rejected(monkeypatch):
    season = {
        'id': 1,
        'start_wordle_id': 100,
        'duration_days': 2,
        'auto_penalty_enabled': 1,
    }
    player = {'id': 2, 'discord_username': 'Ada'}
    parsed = ParsedWordleContent(101, 3, [['⬛'] * 5])
    monkeypatch.setattr(bot_service, 'parse_wordle_content', lambda _: parsed)
    monkeypatch.setattr(bot_service.utils, 'calculate_wordle_id_of_the_day', lambda: 100)

    result = bot_service.update_score(player, 'future', season)

    assert result.wordle_id is None
    assert 'has not been published yet' in result.message


def test_midnight_penalties_apply_silently_when_auto_update_off(monkeypatch):
    season = {
        'id': 7,
        'status': STATUS_ACTIVE,
        'name': 'Spring',
        'season_number': 1,
        'start_wordle_id': 1000,
        'duration_days': 10,
        'channel_id': 1,
        'auto_penalty_enabled': 1,
        'auto_update_enabled': 0,
        'missed_day_penalty': 10,
        'recurring': 0,
    }
    players = [{'id': 11, 'discord_user_id': 101, 'discord_username': 'Ada'}]
    channel = AsyncMock()
    upsert = Mock()

    monkeypatch.setattr(scheduler.bot_service, 'get_missing_players', lambda *_: players)
    monkeypatch.setattr(scheduler.db_repo, 'upsert_score', upsert)

    class Client:
        def get_channel(self, _):
            return channel

    scheduler._client = Client()
    asyncio.run(scheduler._process_season(season, 1001))

    assert [call.args[2] for call in upsert.call_args_list] == [1000, 1001]
    channel.send.assert_not_called()


def test_finale_still_archives_but_is_silent_when_season_end_off(monkeypatch):
    season = {
        'id': 7,
        'status': STATUS_ACTIVE,
        'name': 'Spring',
        'season_number': 1,
        'start_wordle_id': 1000,
        'duration_days': 3,
        'channel_id': 1,
        'recurring': 0,
        'season_end_enabled': 0,
    }
    monkeypatch.setattr(scheduler.db_repo, 'get_season', lambda _: season)
    monkeypatch.setattr(scheduler.db_repo, 'get_season_players', lambda _: [])
    monkeypatch.setattr(scheduler.bot_service, 'get_sorted_player_scores', lambda _: [])
    monkeypatch.setattr(scheduler.bot_service, 'build_leaderboard_message', lambda *a, **k: 'final')
    update_status = Mock()
    monkeypatch.setattr(scheduler.db_repo, 'update_season_status', update_status)
    channel = AsyncMock()

    asyncio.run(scheduler.finalize_season(season, channel))

    update_status.assert_called_once()
    channel.send.assert_not_called()


def test_notifications_message_lists_each_flag():
    from commands.season import _notifications_message

    season = {
        'name': 'Spring', 'season_number': 1, 'recurring': 0,
        'reminders_enabled': 0, 'auto_update_enabled': 0, 'season_end_enabled': 1,
    }
    msg = _notifications_message(season)

    assert '`reminder`: **false**' in msg
    assert '`auto_update`: **false**' in msg
    assert '`season_end`: **true**' in msg
