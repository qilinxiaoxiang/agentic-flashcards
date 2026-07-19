from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from .scheduler import next_schedule


class CardConflict(RuntimeError):
    def __init__(self, current: dict):
        super().__init__("card version conflict")
        self.current = current


class FlashcardStore:
    def __init__(self, path: str | Path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cards(
              id TEXT PRIMARY KEY, front TEXT NOT NULL, back TEXT NOT NULL,
              tags_json TEXT NOT NULL, due_on TEXT NOT NULL, interval_days INTEGER NOT NULL,
              ease INTEGER NOT NULL, repetitions INTEGER NOT NULL, version INTEGER NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS review_events(
              operation_id TEXT PRIMARY KEY, card_id TEXT NOT NULL REFERENCES cards(id),
              reviewed_on TEXT NOT NULL, rating INTEGER NOT NULL, result_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS content_operations(
              operation_id TEXT PRIMARY KEY, result_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS changes(
              cursor INTEGER PRIMARY KEY AUTOINCREMENT, card_id TEXT NOT NULL,
              version INTEGER NOT NULL, changed_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _card(row: sqlite3.Row) -> dict:
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json"))
        return item

    def get(self, card_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
        return self._card(row) if row else None

    def upsert(
        self,
        *,
        operation_id: str,
        card_id: str,
        front: str,
        back: str,
        tags: list[str] | None = None,
        expected_version: int | None = None,
    ) -> dict:
        prior = self.conn.execute(
            "SELECT result_json FROM content_operations WHERE operation_id=?", (operation_id,)
        ).fetchone()
        if prior:
            return json.loads(prior["result_json"])
        front, back = front.strip(), back.strip()
        if not operation_id or not card_id or not front or not back:
            raise ValueError("operation_id, card_id, front, and back are required")
        current = self.get(card_id)
        if current is None and expected_version not in {None, 0}:
            raise CardConflict({})
        if current is not None and expected_version != current["version"]:
            raise CardConflict(current)
        version = 1 if current is None else current["version"] + 1
        due_on = current["due_on"] if current else date.today().isoformat()
        interval = current["interval_days"] if current else 0
        ease = current["ease"] if current else 200
        repetitions = current["repetitions"] if current else 0
        now = self._now()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute(
                """INSERT INTO cards
                   (id,front,back,tags_json,due_on,interval_days,ease,repetitions,version,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET front=excluded.front,back=excluded.back,
                   tags_json=excluded.tags_json,version=excluded.version,updated_at=excluded.updated_at""",
                (
                    card_id,
                    front,
                    back,
                    json.dumps(sorted(set(tags or []))),
                    due_on,
                    interval,
                    ease,
                    repetitions,
                    version,
                    now,
                ),
            )
            result = self.get(card_id)
            encoded = json.dumps(result, sort_keys=True)
            self.conn.execute(
                "INSERT INTO content_operations VALUES (?,?,?)", (operation_id, encoded, now)
            )
            self.conn.execute(
                "INSERT INTO changes(card_id,version,changed_at) VALUES (?,?,?)",
                (card_id, version, now),
            )
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise

    def review(self, *, operation_id: str, card_id: str, reviewed_on: str, rating: int) -> dict:
        prior = self.conn.execute(
            "SELECT result_json FROM review_events WHERE operation_id=?", (operation_id,)
        ).fetchone()
        if prior:
            return json.loads(prior["result_json"])
        current = self.get(card_id)
        if current is None:
            raise ValueError("unknown card")
        schedule = next_schedule(
            reviewed_on=reviewed_on,
            rating=rating,
            interval_days=current["interval_days"],
            ease=current["ease"],
            repetitions=current["repetitions"],
        )
        now = self._now()
        result = {
            "card_id": card_id,
            "due_on": schedule.due_on,
            "interval_days": schedule.interval_days,
            "ease": schedule.ease,
            "repetitions": schedule.repetitions,
        }
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute(
                """UPDATE cards SET due_on=?,interval_days=?,ease=?,repetitions=?,
                   version=version+1,updated_at=? WHERE id=?""",
                (
                    schedule.due_on,
                    schedule.interval_days,
                    schedule.ease,
                    schedule.repetitions,
                    now,
                    card_id,
                ),
            )
            updated = self.get(card_id)
            result["version"] = updated["version"]
            self.conn.execute(
                "INSERT INTO review_events VALUES (?,?,?,?,?,?)",
                (
                    operation_id,
                    card_id,
                    reviewed_on,
                    rating,
                    json.dumps(result, sort_keys=True),
                    now,
                ),
            )
            self.conn.execute(
                "INSERT INTO changes(card_id,version,changed_at) VALUES (?,?,?)",
                (card_id, updated["version"], now),
            )
            self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise

    def due(self, on_date: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM cards WHERE due_on<=? ORDER BY due_on,id", (on_date,)
        )
        return [self._card(row) for row in rows]

    def changes(self, after_cursor: int = 0) -> dict:
        rows = list(
            self.conn.execute(
                "SELECT * FROM changes WHERE cursor>? ORDER BY cursor", (after_cursor,)
            )
        )
        cards = [self.get(row["card_id"]) for row in rows]
        return {"cursor": rows[-1]["cursor"] if rows else after_cursor, "cards": cards}
