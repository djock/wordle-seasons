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


def error_parsing(player_name):
    return f"Sorry {player_name}, there was an error parsing your Wordle result. Please check your submission format and try again."


def leaderboard_title(season_name, day_number_in_season, duration_days):
    if day_number_in_season >= duration_days:
        return f"\n**{season_name} — FINALE** 👑"
    return f"\n**{season_name} leaderboard, day {day_number_in_season} / {duration_days}**"


def winner_congrats(leader):
    return f"\n\n**{leader}**, {utils.get_random_congrats_text()}"


def highest_tetris(winner, points):
    return f"\nHonorable mention for the highest Tetris points gained: **{winner}**, with **{points}** points"
