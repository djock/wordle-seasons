import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROMANIA_TZ = ZoneInfo("Europe/Bucharest")


def get_random_emoji():
    return random.choice(['🎉', '🎊', '🥳'])


def get_random_congrats_text():
    return random.choice([
        "wordsmith extraordinaire! You've conquered this Wordle season with flying colors!",
        "a round of applause for our Wordle wizard! Your lexical prowess knows no bounds",
        "from A to Z, you've mastered them all. Congrats on your spectacular Wordle season victory!",
        "in a world of words, you reign supreme. Kudos on your impressive Wordle season win!",
        "letter by letter, day by day, you've proven yourself the ultimate Wordle player. Bravo!",
        "your dedication to daily puzzles has paid off. Congratulations on your well-deserved Wordle triumph!",
    ])


def get_random_wordle_reminder_text():
    return random.choice([
        "don't forget to tackle today's Wordle challenge. The leaderboard awaits your score!",
        "Wordle time! Have you solved today's puzzle yet? Remember to submit your result if you haven't already.",
        "quick reminder: Your daily dose of Wordle is waiting. Solve it and share your score with us!",
        "the daily puzzle is calling your name. Don't miss out on your chance to climb the leaderboard",
        "did today's Wordle slip your mind? There's still time to play and submit your score. Let's keep the streak going!",
        "where's your head at? put some Wordle time",
        "you better not be playing another game, Wordle isn't going to solve itself now, is it?",
    ])


def calculate_wordle_id_for_date(target_date: datetime) -> int:
    start_date = datetime(2021, 6, 19, 0, 0, 0, tzinfo=ROMANIA_TZ)
    if target_date.tzinfo is None:
        target_date = target_date.replace(tzinfo=ROMANIA_TZ)
    return (target_date - start_date).days


def calculate_wordle_id_of_the_day() -> int:
    return calculate_wordle_id_for_date(datetime.now(ROMANIA_TZ))


def calculate_wordle_id_for_yesterday() -> int:
    return calculate_wordle_id_for_date(datetime.now(ROMANIA_TZ) - timedelta(days=1))


def get_season_end_id(season) -> int:
    """Return the last wordle_id of a season."""
    return season['start_wordle_id'] + season['duration_days'] - 1


def format_mentions(players) -> str:
    """Build a space-separated Discord mention string for a list of players."""
    return " ".join(f"<@{p['discord_user_id']}>" for p in players)


def get_season_display_name(season) -> str:
    """Return the season name with its number, e.g. 'Office Wars (#2)'."""
    return f"{season['name']} (#{season['season_number']})"
