import logging
from datetime import datetime
from typing import Optional, List, Tuple

from core import utils
from core.constants import STATUS_ACTIVE, STATUS_COMPLETED, STATUS_CANCELLED
from db.schema import get_connection

logger = logging.getLogger(__name__)


# ---------- Season Operations ----------

def get_active_season(channel_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM seasons WHERE channel_id = ? AND status = ?",
            (channel_id, STATUS_ACTIVE)
        ).fetchone()


def get_season(season_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM seasons WHERE id = ?",
            (season_id,)
        ).fetchone()


def create_season(channel_id, guild_id, creator_id, name, prize, duration_days,
                  missed_day_penalty, tetris_bonus_enabled, reminders_enabled,
                  auto_penalty_enabled, start_wordle_id, start_date, end_date,
                  recurring=False, season_number: int = 1) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO seasons
               (channel_id, guild_id, creator_id, name, prize, duration_days,
                missed_day_penalty, tetris_bonus_enabled, reminders_enabled,
                auto_penalty_enabled, start_wordle_id, start_date, end_date, status, recurring,
                season_number)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (channel_id, guild_id, creator_id, name, prize, duration_days,
             missed_day_penalty, int(tetris_bonus_enabled), int(reminders_enabled),
             int(auto_penalty_enabled), start_wordle_id, start_date, end_date, STATUS_ACTIVE,
             int(recurring), season_number)
        )
        return cur.lastrowid


def update_season(season_id: int, name: str = None, prize: str = None):
    """Update the name and/or prize of an existing season."""
    fields = []
    values = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if prize is not None:
        fields.append("prize = ?")
        values.append(prize)
    if not fields:
        return
    values.append(season_id)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE seasons SET {', '.join(fields)} WHERE id = ?",
            values
        )


def update_season_status(season_id: int, status: str, winner_id: Optional[int] = None):
    with get_connection() as conn:
        conn.execute(
            "UPDATE seasons SET status = ?, winner_id = ? WHERE id = ?",
            (status, winner_id, season_id)
        )


def get_all_active_seasons() -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM seasons WHERE status = ?", (STATUS_ACTIVE,)
        ).fetchall()


def get_completed_seasons(channel_id: int) -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM seasons WHERE channel_id = ? AND status IN (?, ?) ORDER BY id DESC",
            (channel_id, STATUS_COMPLETED, STATUS_CANCELLED)
        ).fetchall()


# ---------- Player Operations ----------

def get_player(season_id: int, discord_user_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM players WHERE season_id = ? AND discord_user_id = ?",
            (season_id, discord_user_id)
        ).fetchone()


def register_player(season_id: int, discord_user_id: int, discord_username: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO players (season_id, discord_user_id, discord_username, joined_at) "
            "VALUES (?, ?, ?, ?)",
            (season_id, discord_user_id, discord_username,
             datetime.now(utils.ROMANIA_TZ).isoformat())
        )
        return cur.lastrowid


def unregister_player(season_id: int, discord_user_id: int) -> bool:
    """Remove a player and all their scores from a season. Returns True if found and removed."""
    with get_connection() as conn:
        player = conn.execute(
            "SELECT id FROM players WHERE season_id = ? AND discord_user_id = ?",
            (season_id, discord_user_id)
        ).fetchone()
        if not player:
            return False
        conn.execute("DELETE FROM scores WHERE player_id = ?", (player['id'],))
        conn.execute("DELETE FROM players WHERE id = ?", (player['id'],))
        return True


def get_season_players(season_id: int) -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM players WHERE season_id = ?",
            (season_id,)
        ).fetchall()


def get_player_score_summary(season_id: int, player_id: int) -> dict:
    """Return a single player's aggregated score stats."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT COALESCE(SUM(raw_score), 0)    AS base_score, "
            "       COALESCE(SUM(tetris_bonus), 0) AS tetris_total "
            "FROM scores WHERE season_id = ? AND player_id = ?",
            (season_id, player_id)
        ).fetchone()


def get_all_player_scores_summary(season_id: int) -> list:
    """Return all players in a season with their aggregated score stats — single query."""
    with get_connection() as conn:
        return conn.execute(
            """SELECT p.id, p.discord_user_id, p.discord_username,
                      COALESCE(SUM(s.raw_score), 0)    AS base_score,
                      COALESCE(SUM(s.tetris_bonus), 0) AS tetris_total,
                      COALESCE(SUM(s.green_count), 0)  AS green_total,
                      COALESCE(SUM(s.yellow_count), 0) AS yellow_total
               FROM players p
               LEFT JOIN scores s ON s.player_id = p.id AND s.season_id = p.season_id
               WHERE p.season_id = ?
               GROUP BY p.id, p.discord_user_id, p.discord_username""",
            (season_id,)
        ).fetchall()


# ---------- Score Operations ----------

def get_score(season_id: int, player_id: int, wordle_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM scores WHERE season_id = ? AND player_id = ? AND wordle_id = ?",
            (season_id, player_id, wordle_id)
        ).fetchone()


def get_existing_wordle_ids(season_id: int, player_id: int,
                             start_id: int, end_id: int) -> set:
    """Return the set of wordle_ids already recorded for a player in a range."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT wordle_id FROM scores "
            "WHERE season_id = ? AND player_id = ? AND wordle_id >= ? AND wordle_id <= ?",
            (season_id, player_id, start_id, end_id)
        ).fetchall()
        return {row['wordle_id'] for row in rows}


def batch_insert_penalty_scores(season_id: int, player_id: int,
                                 wordle_ids: List[int], raw_score: int):
    """Insert auto-penalty rows for multiple wordle_ids in a single transaction."""
    now = datetime.now(utils.ROMANIA_TZ).isoformat()
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO scores "
            "(season_id, player_id, wordle_id, raw_score, submitted_at, is_auto_penalty) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            [(season_id, player_id, wid, raw_score, now) for wid in wordle_ids]
        )


def upsert_score(season_id, player_id, wordle_id, raw_score, tetris_bonus=0,
                 green_count=0, yellow_count=0, grid_text=None, is_auto_penalty=False):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO scores
               (season_id, player_id, wordle_id, raw_score, tetris_bonus, green_count,
                yellow_count, grid_text, submitted_at, is_auto_penalty)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(season_id, player_id, wordle_id) DO UPDATE SET
               raw_score = excluded.raw_score,
               tetris_bonus = excluded.tetris_bonus,
               green_count = excluded.green_count,
               yellow_count = excluded.yellow_count,
               grid_text = excluded.grid_text,
               submitted_at = excluded.submitted_at,
               is_auto_penalty = excluded.is_auto_penalty""",
            (season_id, player_id, wordle_id, raw_score, tetris_bonus,
             green_count, yellow_count, grid_text,
             datetime.now(utils.ROMANIA_TZ).isoformat(), int(is_auto_penalty))
        )


def get_scores_for_wordle_id(season_id: int, wordle_id: int) -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM scores WHERE season_id = ? AND wordle_id = ?",
            (season_id, wordle_id)
        ).fetchall()


def get_player_color_totals(season_id: int, player_id: int) -> Tuple[int, int]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(green_count), 0) as greens, "
            "COALESCE(SUM(yellow_count), 0) as yellows "
            "FROM scores WHERE season_id = ? AND player_id = ?",
            (season_id, player_id)
        ).fetchone()
        return (row['greens'], row['yellows']) if row else (0, 0)
