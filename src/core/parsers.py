import logging
from typing import List, Tuple

from core.constants import WORDLE_GRID_WIDTH
from core.models import ParsedWordleContent, WordleParsingError
from core.validators import validate_wordle_id, validate_score, validate_grid

logger = logging.getLogger(__name__)


EMOJI_ALIASES = {
	'⬜': '⬛',  # white square → black
	'🟦': '🟨',  # blue square → yellow (high contrast)
	'🟧': '🟩',  # orange square → green (high contrast)
}


def normalize_grid(grid: List[List[str]]) -> List[List[str]]:
	"""Replace alternate color-scheme emojis with canonical ones."""
	return [
		[EMOJI_ALIASES.get(cell, cell) for cell in row]
		for row in grid
	]


def parse_wordle_content(content: str) -> ParsedWordleContent:
	"""
	Parse a raw Discord Wordle message (no player-name prefix).

	Example input:
		"Wordle 1,234 4/6*\\n🟩🟨⬛🟩⬛\\n🟩🟩🟩🟩🟩"
	"""
	try:
		if not content or not content.strip():
			raise WordleParsingError("Empty message")

		parts = content.strip().split('\n')
		header = parts[0].split()

		wordle_idx = next((i for i, t in enumerate(header) if t == 'Wordle'), None)
		if wordle_idx is None:
			raise WordleParsingError("Missing 'Wordle' keyword in message")
		if wordle_idx + 1 >= len(header):
			raise WordleParsingError("Missing Wordle ID after 'Wordle' keyword")

		wordle_id_raw = header[wordle_idx + 1].replace(',', '')
		score_raw = header[-1].split('/')[0]

		rows = [row for row in parts[1:] if row.strip()]
		if not rows:
			raise WordleParsingError("Missing grid data")

		grid = normalize_grid([list(row) for row in rows])

		wordle_id = validate_wordle_id(wordle_id_raw)
		score = validate_score(score_raw)
		validate_grid(grid)

		logger.info(f"Parsed Wordle content: wordle_id={wordle_id}, score={score}")
		return ParsedWordleContent(wordle_id=wordle_id, score=score, grid=grid)

	except (IndexError, AttributeError) as e:
		raise WordleParsingError(f"Invalid message format: {e}") from e


def calculate_tetris_bonus(grid: List[List[str]]) -> int:
	"""Calculate tetris bonus from Wordle grid without modifying input."""
	validate_grid(grid)
	grid_copy = [list(row) for row in grid]

	rows = len(grid_copy)
	cols = len(grid_copy[0])
	bonus = 0

	for row in range(1, rows):
		filled_cells_in_row = 0
		row_updated_with_tetris_rule = False
		green_cells_count = 0
		yellow_cells_count = 0
		tetris_cells = []

		for col in range(cols):
			if grid_copy[row][col] == '🟩':
				green_cells_count += 1
				filled_cells_in_row += 1
			if grid_copy[row][col] == '🟨':
				yellow_cells_count += 1
				filled_cells_in_row += 1
			if grid_copy[row][col] == '⬛':
				for tetris_row in range(row):
					if grid_copy[tetris_row][col] in ['🟨', '🟩']:
						filled_cells_in_row += 1
						row_updated_with_tetris_rule = True
						tetris_cells.append((tetris_row, col))
						break

		is_full_row = filled_cells_in_row == WORDLE_GRID_WIDTH
		is_tetris_row = is_full_row and row_updated_with_tetris_rule
		is_all_colored = (green_cells_count != WORDLE_GRID_WIDTH and
						  green_cells_count + yellow_cells_count == WORDLE_GRID_WIDTH)

		if is_tetris_row or is_all_colored:
			if row_updated_with_tetris_rule:
				for tc in tetris_cells:
					grid_copy[tc[0]][tc[1]] = '⬛'
				for col in range(cols):
					grid_copy[row][col] = '⬛'
			bonus += 1

	return bonus


def calculate_color_counts(grid: List[List[str]]) -> Tuple[int, int]:
	"""Count total green and yellow squares in Wordle grid."""
	validate_grid(grid)
	total_greens = sum(row.count('🟩') for row in grid)
	total_yellows = sum(row.count('🟨') for row in grid)
	return total_greens, total_yellows
