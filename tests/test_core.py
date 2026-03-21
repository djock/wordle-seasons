# Run with: pytest tests/ -v
import copy
import pytest

from core import localizations
from core.constants import FAILED_WORDLE_SCORE
from core.models import WordleParsingError, ValidationError
from core.parsers import parse_wordle_content, calculate_tetris_bonus, calculate_color_counts, normalize_grid
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
# normalize_grid / alternate color schemes
# ============================================================================

def test_normalize_grid_white_squares():
    """White squares (⬜) should be normalized to black (⬛)."""
    grid = [['⬜', '🟨', '⬜', '🟩', '⬜']]
    result = normalize_grid(grid)
    assert result == [['⬛', '🟨', '⬛', '🟩', '⬛']]


def test_normalize_grid_high_contrast():
    """High contrast mode: blue (🟦) → yellow, orange (🟧) → green."""
    grid = [
        ['⬛', '⬛', '⬛', '🟦', '⬛'],
        ['🟧', '🟧', '🟧', '🟧', '🟧'],
    ]
    result = normalize_grid(grid)
    assert result == [
        ['⬛', '⬛', '⬛', '🟨', '⬛'],
        ['🟩', '🟩', '🟩', '🟩', '🟩'],
    ]


def test_normalize_grid_no_change():
    """Canonical emojis should pass through unchanged."""
    grid = [['🟩', '🟨', '⬛', '🟩', '⬛']]
    result = normalize_grid(grid)
    assert result == grid


def test_parse_wordle_content_white_squares():
    """parse_wordle_content should accept white squares as black."""
    content = "Wordle 1,735 5/6\n⬜⬜🟨⬜⬜\n⬜🟩⬜⬜⬜\n🟨🟩⬜⬜🟨\n⬜🟩🟩🟨⬜\n🟩🟩🟩🟩🟩"
    result = parse_wordle_content(content)
    assert result.wordle_id == 1735
    assert result.score == 5
    assert result.grid[0] == ['⬛', '⬛', '🟨', '⬛', '⬛']


def test_parse_wordle_content_high_contrast():
    """parse_wordle_content should accept high contrast mode (blue/orange)."""
    content = "Wordle 1,735 5/6*\n⬛⬛⬛🟦⬛\n🟦⬛🟦⬛⬛\n🟦⬛⬛🟦⬛\n⬛🟧🟦🟦⬛\n🟧🟧🟧🟧🟧"
    result = parse_wordle_content(content)
    assert result.wordle_id == 1735
    assert result.score == 5
    assert result.grid[4] == ['🟩', '🟩', '🟩', '🟩', '🟩']
    assert result.grid[3][1] == '🟩'  # orange → green
    assert result.grid[0][3] == '🟨'  # blue → yellow


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


def test_parsing_issue_detail_for_wrong_row_width():
    detail = localizations.parsing_issue_detail("Row 0 has 6 cells, expected 5")
    assert "row 1 has 6 squares, but I expected 5" in detail
    assert "invisible variation character" in detail


def test_parsing_issue_detail_for_invalid_cell():
    detail = localizations.parsing_issue_detail("Invalid cell value at (0, 3): ⬜️")
    assert "row 1, column 4 contains an unsupported symbol" in detail
    assert "I can read green, yellow, and black squares" in detail


def test_error_parsing_includes_specific_reason():
    message = localizations.error_parsing("Ionut", "Missing grid data")
    assert "I couldn't record that Wordle result because I found the header, but the result grid is missing." in message
    assert "Please copy the full Wordle share and try again." in message


def test_validate_grid_invalid_cell():
    with pytest.raises(ValidationError):
        validate_grid([['🟩', '🟨', '⬛', '🟩', '❌']])
