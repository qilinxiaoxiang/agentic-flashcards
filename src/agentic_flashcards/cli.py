from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .content import (
    ContentOrchestrator,
    ImageAsset,
    TrilingualExplanation,
)
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


class _DemoExplainer:
    def explain(self, term: str) -> TrilingualExplanation:
        return TrilingualExplanation(
            chinese=f"{term} 的中文示例解释。",
            english=f"A synthetic English explanation of {term}.",
            japanese=f"{term}の日本語による説明例です。",
        )


class _DemoSearch:
    def __init__(self, results: list[ImageAsset]):
        self.results = results

    def search(self, query: str, *, limit: int) -> list[ImageAsset]:
        return self.results[:limit]


class _DemoGenerator:
    def generate(self, prompt: str) -> ImageAsset:
        return ImageAsset(
            uri="generated://synthetic-orbit",
            alt="A synthetic educational illustration of an orbit",
            attribution="deterministic demo adapter",
            license="model-generated",
        )


def content_demo() -> dict:
    searched = ImageAsset(
        uri="https://example.invalid/public-domain-orbit.svg",
        alt="A synthetic diagram of an orbit",
        attribution="synthetic public-domain demo",
        license="Public Domain",
        relevance_score=0.95,
    )
    common = {"explainer": _DemoExplainer(), "image_generator": _DemoGenerator()}
    search_result = ContentOrchestrator(
        **common, image_search=_DemoSearch([searched])
    ).enrich("orbit", visually_useful=True)
    generated_result = ContentOrchestrator(
        **common, image_search=_DemoSearch([])
    ).enrich("orbit", visually_useful=True)
    return {
        "search_first": asdict(search_result),
        "generation_fallback": asdict(generated_result),
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
    commands.add_parser("content-demo")
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(demo(args.db, args.cards), indent=2))
    elif args.command == "content-demo":
        print(json.dumps(content_demo(), indent=2, ensure_ascii=False))
