import asyncio
import sys
import types
from unittest.mock import AsyncMock

sys.modules.setdefault('schedule', types.SimpleNamespace())
sys.modules.setdefault('dotenv', types.SimpleNamespace(load_dotenv=lambda **kwargs: None))

from bot import scheduler
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
