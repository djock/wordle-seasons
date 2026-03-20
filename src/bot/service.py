import json
import logging
from typing import Optional, List
from datetime import datetime

import config
from core import localizations, utils
from core.models import PlayerScore, UpdateResult, WordleParsingError, ValidationError
from core.parsers import parse_wordle_content, calculate_tetris_bonus, calculate_color_counts
import db.repository as db_repo

logger = logging.getLogger(__name__)


def update_score(player, message_content: str, season) -> UpdateResult:
    """Process a Wordle submission from a registered player."""
    player_name = player['discord_username']
    season_id = season['id']
    player_id = player['id']

    try:
        parsed = parse_wordle_content(message_content)
        wordle_id = parsed.wordle_id
        score = parsed.score
        grid = parsed.grid

        season_start = season['start_wordle_id']
        season_end = utils.get_season_end_id(season)
        if not (season_start <= wordle_id <= season_end):
            return UpdateResult(
                message=f"Wordle #{wordle_id} is not part of the current season "
                        f"(#{season_start}–#{season_end}).",
                wordle_id=None
            )

        existing = db_repo.get_score(season_id, player_id, wordle_id)
        if existing and not existing['is_auto_penalty']:
            return UpdateResult(
                message=f"You already submitted Wordle #{wordle_id}!",
                wordle_id=None
            )

        tetris_bonus = 0
        if season['tetris_bonus_enabled']:
            tetris_bonus = calculate_tetris_bonus(grid)
        green_count, yellow_count = calculate_color_counts(grid)

        # Backfill any missed days before this submission — batch to avoid N+1
        missed_ids = []
        if wordle_id > season_start:
            existing_ids = db_repo.get_existing_wordle_ids(
                season_id, player_id, season_start, wordle_id - 1
            )
            missed_ids = [i for i in range(season_start, wordle_id) if i not in existing_ids]
            if missed_ids:
                db_repo.batch_insert_penalty_scores(
                    season_id, player_id, missed_ids, season['missed_day_penalty']
                )

        grid_text = json.dumps([list(row) for row in grid])
        db_repo.upsert_score(
            season_id, player_id, wordle_id,
            raw_score=score,
            tetris_bonus=tetris_bonus,
            green_count=green_count,
            yellow_count=yellow_count,
            grid_text=grid_text,
            is_auto_penalty=False
        )

        stats = db_repo.get_player_score_summary(season_id, player_id)
        effective = stats['base_score'] - stats['tetris_total']

        message = localizations.score_updated_successful(player_name, wordle_id, score)
        if tetris_bonus > 0:
            message += localizations.tetris_bonus_info(tetris_bonus)
        if missed_ids:
            message += localizations.missed_days_info(len(missed_ids), season['missed_day_penalty'])
        message += localizations.season_score(effective)

        return UpdateResult(message=message, wordle_id=wordle_id)

    except (WordleParsingError, ValidationError) as e:
        logger.error(f"Parsing/validation error for {player_name}: {e}")
        return UpdateResult(message=localizations.error_parsing(player_name), wordle_id=None)
    except Exception as e:
        logger.exception(f"Unexpected error in update_score for {player_name}: {e}")
        return UpdateResult(message=localizations.error_recording_result(player_name), wordle_id=None)


def get_sorted_player_scores(season) -> List[PlayerScore]:
    """Return all players sorted by effective score (lowest first). Single DB query."""
    rows = db_repo.get_all_player_scores_summary(season['id'])
    player_scores = [
        PlayerScore(
            player_name=row['discord_username'],
            discord_user_id=row['discord_user_id'],
            base_score=row['base_score'],
            tetris_points=row['tetris_total'],
        )
        for row in rows
    ]
    player_scores.sort(key=lambda x: (x.effective_score, -x.tetris_points))
    return player_scores


def build_leaderboard_message(season, player_scores: List[PlayerScore],
                               wordle_id: Optional[int] = None,
                               is_final: bool = False) -> str:
    """Build a leaderboard message from a pre-sorted player scores list."""
    if not player_scores:
        return f"No players registered for **{season['name']}** yet."

    if wordle_id is not None:
        day_in_season = wordle_id - season['start_wordle_id'] + 1
        title = localizations.leaderboard_title(
            season['name'], day_in_season, season['duration_days']
        )
    else:
        title = f"\n**{season['name']} Leaderboard**"

    medals = ["🥇", "🥈", "🥉"]
    message = title
    for i, ps in enumerate(player_scores, 1):
        indicator = medals[i - 1] if (is_final and i <= 3) else f"[{i}]"
        message += f"\n{indicator} {ps.player_name}: {ps.effective_score}"
        if is_final:
            message += f" (tetris: {ps.tetris_points})"

    if is_final:
        leader = player_scores[0].player_name
        message += localizations.winner_congrats(leader)
        if season['prize']:
            message += f"\n🎁 Prize: **{season['prize']}**"
        top_tetris = max(player_scores, key=lambda x: x.tetris_points)
        message += localizations.highest_tetris(top_tetris.player_name, str(top_tetris.tetris_points))

    return message


def get_leaderboard(season, wordle_id: Optional[int] = None, is_final: bool = False) -> str:
    """Generate a leaderboard message for a season."""
    return build_leaderboard_message(season, get_sorted_player_scores(season), wordle_id, is_final)


def all_players_submitted(season, wordle_id: int) -> bool:
    """Return True if every registered player has submitted for this wordle_id."""
    players = db_repo.get_season_players(season['id'])
    if not players:
        return False
    submitted_ids = {s['player_id'] for s in db_repo.get_scores_for_wordle_id(season['id'], wordle_id)}
    return all(p['id'] in submitted_ids for p in players)


def get_missing_players(season, wordle_id: int) -> list:
    """Return players who haven't submitted for wordle_id."""
    players = db_repo.get_season_players(season['id'])
    submitted_ids = {s['player_id'] for s in db_repo.get_scores_for_wordle_id(season['id'], wordle_id)}
    return [p for p in players if p['id'] not in submitted_ids]
