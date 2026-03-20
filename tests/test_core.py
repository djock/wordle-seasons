# Run with: pytest tests/ -v
import copy
import pytest

from core.constants import FAILED_WORDLE_SCORE
from core.models import WordleParsingError, ValidationError
from core.parsers import parse_wordle_content, calculate_tetris_bonus, calculate_color_counts
from core.validators import validate_wordle_id, validate_score, validate_grid


# ============================================================================
# parse_wordle_content
# ============================================================================

def test_parse_wordle_content():
    content = "Wordle 1,234 4/6*\n\n🟩🟨⬛🟩⬛\n🟩🟩🟩🟩🟩\n🟩🟩🟩🟩🟩\n🟩🟩🟩🟩🟩"
    result = parse_wordle_content(content)
    assert result.wordle_id == 1234
    assert result.score == 4
    assert len(result.grid) == 4


def test_parse_wordle_content_x_score():
    content = "Wordle 1,234 X/6\n🟩🟨⬛🟩⬛\n🟩⬛🟩🟩⬛\n🟩⬛🟩🟩⬛\n🟩⬛🟩🟩⬛\n🟩⬛🟩🟩⬛\n🟩⬛🟩🟩⬛"
    result = parse_wordle_content(content)
    assert result.score == FAILED_WORDLE_SCORE


def test_parse_wordle_content_empty():
    with pytest.raises(WordleParsingError):
        parse_wordle_content("")


def test_parse_wordle_content_missing_grid():
    with pytest.raises(WordleParsingError):
        parse_wordle_content("Wordle 1234 4/6")


def test_parse_wordle_content_missing_keyword():
    with pytest.raises(WordleParsingError):
        parse_wordle_content("Game 1234 4/6\n🟩🟩🟩🟩🟩")


# ============================================================================
# calculate_tetris_bonus
# ============================================================================

def test_calculate_tetris_bonus():
    grid = [
        ['🟩', '🟨', '🟨', '⬛', '⬛'],
        ['🟩', '⬛', '🟩', '🟩', '🟩'],
        ['🟩', '🟩', '🟩', '🟩', '🟩']
    ]
    assert calculate_tetris_bonus(grid) == 1


def test_calculate_tetris_bonus_multiple_rows():
    grid = [
        ['🟩', '🟨', '⬛', '🟩', '⬛'],
        ['🟩', '⬛', '🟩', '🟩', '🟩'],
        ['🟩', '⬛', '🟩', '🟩', '🟩'],
        ['🟩', '🟩', '🟩', '🟩', '🟩']
    ]
    assert calculate_tetris_bonus(grid) == 1


def test_calculate_tetris_no_bonus():
    grid = [
        ['⬛', '🟩', '⬛', '⬛', '⬛'],
        ['⬛', '🟩', '⬛', '⬛', '⬛'],
        ['⬛', '🟩', '🟨', '🟨', '⬛'],
        ['🟩', '🟩', '🟩', '🟩', '🟩']
    ]
    assert calculate_tetris_bonus(grid) == 0


def test_calculate_tetris_no_side_effects():
    grid = [
        ['🟩', '🟨', '⬛', '🟩', '⬛'],
        ['🟩', '⬛', '🟩', '🟩', '🟩']
    ]
    original = copy.deepcopy(grid)
    calculate_tetris_bonus(grid)
    assert grid == original


# ============================================================================
# calculate_color_counts
# ============================================================================

def test_calculate_color_counts():
    grid = [
        ['🟩', '🟨', '⬛', '🟩', '⬛'],
        ['🟩', '🟩', '🟩', '🟩', '🟩']
    ]
    greens, yellows = calculate_color_counts(grid)
    assert greens == 7
    assert yellows == 1


def test_calculate_color_counts_empty_grid():
    grid = [['⬛', '⬛', '⬛', '⬛', '⬛']]
    greens, yellows = calculate_color_counts(grid)
    assert greens == 0
    assert yellows == 0


# ============================================================================
# validate_wordle_id
# ============================================================================

def test_validate_wordle_id_valid():
    assert validate_wordle_id("1234") == 1234


def test_validate_wordle_id_negative():
    with pytest.raises(ValidationError):
        validate_wordle_id("-5")


def test_validate_wordle_id_too_large():
    with pytest.raises(ValidationError):
        validate_wordle_id("999999")


def test_validate_wordle_id_invalid_format():
    with pytest.raises(ValidationError):
        validate_wordle_id("abc")


# ============================================================================
# validate_score
# ============================================================================

def test_validate_score_valid():
    assert validate_score("4") == 4
    assert validate_score(3) == 3


def test_validate_score_x():
    assert validate_score("X") == FAILED_WORDLE_SCORE


def test_validate_score_out_of_range():
    with pytest.raises(ValidationError):
        validate_score(7)
    with pytest.raises(ValidationError):
        validate_score(0)


# ============================================================================
# validate_grid
# ============================================================================

def test_validate_grid_valid():
    validate_grid([
        ['🟩', '🟨', '⬛', '🟩', '⬛'],
        ['🟩', '🟩', '🟩', '🟩', '🟩']
    ])


def test_validate_grid_empty():
    with pytest.raises(ValidationError):
        validate_grid([])


def test_validate_grid_wrong_width():
    with pytest.raises(ValidationError):
        validate_grid([['🟩', '🟨', '⬛']])


def test_validate_grid_invalid_cell():
    with pytest.raises(ValidationError):
        validate_grid([['🟩', '🟨', '⬛', '🟩', '❌']])
