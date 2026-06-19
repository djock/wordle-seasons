import asyncio
import sys
import types
from unittest.mock import AsyncMock

sys.modules.setdefault('schedule', types.SimpleNamespace())
sys.modules.setdefault('dotenv', types.SimpleNamespace(load_dotenv=lambda **kwargs: None))

from bot import scheduler
from core.constants import STATUS_ACTIVE, STATUS_COMPLETED


class FakeSchedule:
    def __init__(self):
        self.jobs = []

    def every(self):
        return FakeJob(self.jobs)


class FakeJob:
    def __init__(self, jobs):
        self.jobs = jobs
        self.run_time = None
        self.job_func = None

    @property
    def day(self):
        return self

    def at(self, run_time):
        self.run_time = run_time
        return self

    def do(self, job_func):
        self.job_func = job_func
        self.jobs.append(self)
        return self


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


def test_start_is_idempotent_but_refreshes_client(monkeypatch):
    fake_schedule = FakeSchedule()
    started_threads = []

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            started_threads.append(self)

    first_client = types.SimpleNamespace(loop=object())
    second_client = types.SimpleNamespace(loop=object())

    monkeypatch.setattr(scheduler, '_client', None)
    monkeypatch.setattr(scheduler, '_started', False)
    monkeypatch.setattr(scheduler, 'schedule', fake_schedule)
    monkeypatch.setattr(scheduler.threading, 'Thread', FakeThread)

    scheduler.start(first_client)
    scheduler.start(second_client)

    assert scheduler._client is second_client
    assert [job.run_time for job in fake_schedule.jobs] == ["20:00", "00:00"]
    assert len(started_threads) == 1
    assert started_threads[0].target is scheduler._run_loop
    assert started_threads[0].daemon is True
