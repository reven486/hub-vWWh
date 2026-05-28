from pathlib import Path

import aiosqlite

from app.core.config import get_settings


def get_db_path() -> Path:
    db_path = Path(get_settings().sqlite.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


async def get_db() -> aiosqlite.Connection:
    return await aiosqlite.connect(str(get_db_path()))


async def init_db() -> None:
    async with aiosqlite.connect(str(get_db_path())) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                turn INTEGER NOT NULL,
                phase TEXT NOT NULL,
                winner TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                alive INTEGER NOT NULL,
                seat INTEGER NOT NULL,
                FOREIGN KEY (match_id) REFERENCES matches(id)
            )
            """
        )
        await db.commit()


async def upsert_match(match_id: str, status: str, turn: int, phase: str, winner: str | None) -> None:
    async with aiosqlite.connect(str(get_db_path())) as db:
        await db.execute(
            """
            INSERT INTO matches (id, status, turn, phase, winner)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,
                turn=excluded.turn,
                phase=excluded.phase,
                winner=excluded.winner,
                updated_at=CURRENT_TIMESTAMP
            """,
            (match_id, status, turn, phase, winner),
        )
        await db.commit()


async def replace_players(match_id: str, players: list[dict]) -> None:
    async with aiosqlite.connect(str(get_db_path())) as db:
        await db.execute("DELETE FROM players WHERE match_id = ?", (match_id,))
        await db.executemany(
            "INSERT INTO players (id, match_id, name, role, alive, seat) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    f"{match_id}:{player['id']}",
                    match_id,
                    player["name"],
                    player["role"],
                    int(player["alive"]),
                    player["seat"],
                )
                for player in players
            ],
        )
        await db.commit()
