import logging
from typing import List, Union

from core.constants import FAILED_WORDLE_SCORE, MAX_WORDLE_ATTEMPTS, WORDLE_GRID_WIDTH
from core.models import ValidationError

logger = logging.getLogger(__name__)


def validate_wordle_id(wordle_id: str) -> int:
	try:
		wordle_id_int = int(wordle_id)
		if wordle_id_int < 0:
			raise ValidationError(f"Wordle ID must be positive: {wordle_id}")
		if wordle_id_int > 99999:
			raise ValidationError(f"Wordle ID too large: {wordle_id}")
		return wordle_id_int
	except ValueError:
		raise ValidationError(f"Invalid Wordle ID format: {wordle_id}")


def validate_score(score: Union[str, int]) -> int:
	if score == "X":
		return FAILED_WORDLE_SCORE
	try:
		score_int = int(score)
		if not (1 <= score_int <= MAX_WORDLE_ATTEMPTS):
			raise ValidationError(f"Score must be between 1 and {MAX_WORDLE_ATTEMPTS}: {score}")
		return score_int
	except ValueError:
		raise ValidationError(f"Invalid score format: {score}")


def validate_grid(grid: List[List[str]]) -> None:
	if not grid:
		raise ValidationError("Grid cannot be empty")

	for i, row in enumerate(grid):
		if not isinstance(row, list):
			raise ValidationError(f"Row {i} is not a list")
		if len(row) != WORDLE_GRID_WIDTH:
			raise ValidationError(
				f"Row {i} has {len(row)} cells, expected {WORDLE_GRID_WIDTH}"
			)
		for j, cell in enumerate(row):
			if cell not in ['🟩', '🟨', '⬛']:
				raise ValidationError(
					f"Invalid cell value at ({i}, {j}): {cell}"
				)
