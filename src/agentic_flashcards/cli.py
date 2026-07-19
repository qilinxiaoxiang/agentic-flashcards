from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .store import FlashcardStore


def demo(db_path: str, cards_path: str) -> dict:
    store = FlashcardStore(db_path)
    cards = json.loads(Path(cards_path).read_text(encoding="utf-8"))
    for card in cards:
        store.upsert(operation_id=f"seed:{card['card_id']}", expected_version=0, **card)
    first = cards[0]["card_id"]
    result = store.review(
        operation_id="demo-review-1", card_id=first, reviewed_on=date.today().isoformat(), rating=2
    )
    replay = store.review(
        operation_id="demo-review-1", card_id=first, reviewed_on=date.today().isoformat(), rating=2
    )
    return {
        "seeded": len(cards),
        "review": result,
        "idempotent_replay": replay == result,
        "due": [card["id"] for card in store.due(date.today().isoformat())],
        "changes": store.changes(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentic-flashcards")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("demo")
    command.add_argument("--db", required=True)
    command.add_argument(
        "--cards",
        default=str(Path(__file__).resolve().parents[2] / "examples" / "cards.json"),
    )
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(demo(args.db, args.cards), indent=2))
