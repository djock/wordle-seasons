import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'wordle_seasons.db')


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                prize TEXT,
                duration_days INTEGER NOT NULL DEFAULT 14,
                missed_day_penalty INTEGER NOT NULL DEFAULT 10,
                tetris_bonus_enabled INTEGER NOT NULL DEFAULT 1,
                reminders_enabled INTEGER NOT NULL DEFAULT 1,
                auto_penalty_enabled INTEGER NOT NULL DEFAULT 1,
                start_wordle_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                winner_id INTEGER,
                recurring INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL REFERENCES seasons(id),
                discord_user_id INTEGER NOT NULL,
                discord_username TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                UNIQUE(season_id, discord_user_id)
            );

            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL REFERENCES seasons(id),
                player_id INTEGER NOT NULL REFERENCES players(id),
                wordle_id INTEGER NOT NULL,
                raw_score INTEGER NOT NULL,
                tetris_bonus INTEGER NOT NULL DEFAULT 0,
                green_count INTEGER NOT NULL DEFAULT 0,
                yellow_count INTEGER NOT NULL DEFAULT 0,
                grid_text TEXT,
                submitted_at TEXT NOT NULL,
                is_auto_penalty INTEGER NOT NULL DEFAULT 0,
                UNIQUE(season_id, player_id, wordle_id)
            );
        """)
        # Migrations for existing databases
        try:
            conn.execute("ALTER TABLE seasons ADD COLUMN recurring INTEGER NOT NULL DEFAULT 0")
            logger.info("Migration: added 'recurring' column to seasons")
        except Exception:
            pass  # column already exists
    logger.info("Database initialized")
