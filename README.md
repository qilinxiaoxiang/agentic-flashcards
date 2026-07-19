# Agentic Flashcards

A privacy-safe reference implementation of a review system that agents can maintain without
taking control of learning decisions.

The server keeps cards, review history, scheduling state, versions, and a change feed in SQLite.
A native Swift client can review offline, queue mutations, and resolve version conflicts after it
reconnects. Agents can propose or repair card content through the same versioned API surface; the
learner chooses what belongs in the collection and resolves conflicting edits.

This repository applies the operating model from
[Software Is Switching Operators](https://shawnxiang.com/articles/agentic-life-os/): people decide,
agents execute bounded maintenance, deterministic code protects state, and the interface supports
review.

## What is included

- SQLite/WAL service layer with versioned card writes and an append-only review ledger.
- Deterministic adaptive scheduling based on rating, interval, ease, and review count.
- Offline mutation outbox with stable operation IDs and explicit conflict responses.
- Change cursor for incremental synchronization.
- Native SwiftUI example client and a Swift package containing cache/outbox models.
- Synthetic cards, deterministic demo, unit tests, privacy scan, and secret scan.

No personal cards, production credentials, private media, or source from the private learning
system are included.

## Run the demo

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/agentic-flashcards demo --db /tmp/agentic-flashcards-demo.sqlite
.venv/bin/pytest
.venv/bin/python scripts/privacy_check.py
```

The demo imports `examples/cards.json`, records synthetic reviews, prints the due queue, and
replays one operation to prove idempotency.

## Conflict model

Every card has an integer `version`. A mutation carries `expected_version` and a stable
`operation_id`. If the local copy is stale, the server returns the current card and records no
change. If an offline client retries an already accepted operation, it receives the original
result. The client can then present local and server copies for human resolution.

## iOS example

`ios/` contains a native Swift package for card/sync models plus a SwiftUI application shell.
`OfflineOutbox` persists pending operations as JSON, retries them in order, and stops at a conflict
so the UI can ask the learner which version to keep.

```bash
cd ios
swift test
```

## License

MIT
