import re

from core import utils


def score_updated_successful(player_name, wordle_id, score):
    return f"{player_name}, your Wordle #{wordle_id} result has been recorded: {score}"


def tetris_bonus_info(tetris_bonus):
    points_text = "point" if tetris_bonus == 1 else "points"
    emoji = utils.get_random_emoji()
    return f"\nCongratulations! You earned a Tetris Bonus of {tetris_bonus} {points_text} {emoji}"


def missed_days_info(missed_days, penalty_per_day):
    missed_days_text = f"{missed_days} missed days" if missed_days > 1 else "1 missed day"
    total_penalty = missed_days * penalty_per_day
    return f"\nAlso, I found {missed_days_text} and updated the score accordingly: +{total_penalty}"


def season_score(score):
    return f"\nSeason Score: {score}"


def error_recording_result(player_name):
    return f"Sorry {player_name}, there was an error recording your Wordle result. Please try again later."


def _humanize_cell(cell):
    if cell == "⬜":
        return "white square"
    if cell == "⬛":
        return "black square"
    if cell == "🟨":
        return "yellow square"
    if cell == "🟩":
        return "green square"
    if cell == "🟦":
        return "blue square"
    if cell == "🟧":
        return "orange square"
    if not cell:
        return "empty character"
    return repr(cell)


def parsing_issue_detail(error_message):
    if not error_message:
        return "I couldn't understand that message as a Wordle share."

    if "Empty message" in error_message:
        return "I couldn't read any Wordle result from that message."

    if "Missing 'Wordle' keyword" in error_message:
        return "the message does not start with a standard `Wordle ...` header."

    if "Missing Wordle ID" in error_message:
        return "the Wordle number is missing from the header."

    if "Missing grid data" in error_message:
        return "I found the header, but the result grid is missing."

    if "Invalid Wordle ID format" in error_message:
        return "the Wordle number in the header is not a valid number."

    if "Wordle ID must be positive" in error_message or "Wordle ID too large" in error_message:
        return "the Wordle number in the header is outside the expected range."

    if "Invalid score format" in error_message:
        return "the score in the header is not in the usual `2/6` or `X/6` format."

    if "Score must be between 1 and" in error_message:
        return "the score must be between 1 and 6, or `X/6` for a miss."

    width_match = re.search(r"Row (\d+) has (\d+) cells, expected (\d+)", error_message)
    if width_match:
        row_number = int(width_match.group(1)) + 1
        actual = width_match.group(2)
        expected = width_match.group(3)
        return (
            f"row {row_number} has {actual} squares, but I expected {expected}. "
            "This usually means there is an unsupported emoji or an invisible variation character in the grid."
        )

    cell_match = re.search(r"Invalid cell value at \((\d+), (\d+)\): (.+)", error_message)
    if cell_match:
        row_number = int(cell_match.group(1)) + 1
        column_number = int(cell_match.group(2)) + 1
        cell_value = _humanize_cell(cell_match.group(3).strip())
        return (
            f"row {row_number}, column {column_number} contains an unsupported symbol ({cell_value}). "
            "I can read green, yellow, and black squares, plus white/blue/orange variants."
        )

    if "Invalid message format" in error_message:
        return "the message format looks incomplete or malformed."

    return f"I couldn't understand part of the result: {error_message}."


def error_parsing(player_name, error_message=None):
    detail = parsing_issue_detail(error_message)
    return (
        f"Sorry {player_name}, I couldn't record that Wordle result because {detail} "
        "Please copy the full Wordle share and try again."
    )


def leaderboard_title(season_name, day_number_in_season, duration_days):
    if day_number_in_season >= duration_days:
        return f"\n**{season_name} — FINALE** 👑"
    return f"\n**{season_name} leaderboard, day {day_number_in_season} / {duration_days}**"


def winner_congrats(leader):
    return f"\n\n**{leader}**, {utils.get_random_congrats_text()}"


def highest_tetris(winner, points):
    return f"\nHonorable mention for the highest Tetris points gained: **{winner}**, with **{points}** points"
