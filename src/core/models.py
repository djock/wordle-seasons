from dataclasses import dataclass
from typing import List, Optional


class WordleParsingError(Exception):
	pass


class ValidationError(Exception):
	pass


class DatabaseError(Exception):
	pass


@dataclass
class ParsedWordleContent:
	"""Parsed raw Discord Wordle message (no player-name prefix)."""
	wordle_id: int
	score: int
	grid: List[List[str]]


@dataclass
class PlayerScore:
	player_name: str
	discord_user_id: int
	base_score: int
	tetris_points: int

	@property
	def effective_score(self) -> int:
		return self.base_score - self.tetris_points


@dataclass
class UpdateResult:
	message: str
	wordle_id: Optional[int]
