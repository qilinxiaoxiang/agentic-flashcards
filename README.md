# Agentic Flashcards

**A production-informed reference for learning software that AI can enrich and maintain without
becoming the authority over what a person learns.**

The interesting part is not another flashcard UI. It is the operating contract:

- AI handles semantic work: explain a concept in Chinese, English, and Japanese; search for a
  relevant open-license image; and fall back to image generation when search cannot supply one.
- Deterministic software owns durable state: review timing, versions, retries, conflicts, and
  history are explicit and testable rather than improvised by a model.
- The learner keeps authority: people choose collection membership, review cards, and resolve
  conflicting edits.

This public repository is a privacy-safe slice of a private, daily-use learning system. It uses
synthetic cards and provider-neutral interfaces so the engineering patterns are inspectable without
publishing personal learning data, credentials, private media, or vendor-specific production code.

## What it demonstrates

### Multilingual and multimodal AI enrichment

`ContentOrchestrator` separates model capability from product policy:

1. An explanation provider must return non-empty **Chinese, English, and Japanese** content.
2. Visually useful concepts try image search first.
3. Search results must clear both a relevance threshold and an open-license allowlist.
4. Empty or unavailable search falls back to an image-generation provider.
5. The result records whether the image was searched, generated, or intentionally skipped, plus
   the fallback reason.

The repository ships deterministic demo adapters, not live AI credentials. Real model and search
services plug into the typed provider protocols without changing the orchestration policy.

### Adaptive review that remains auditable

The scheduler adapts the next interval from rating, interval, ease, and review count, but the
result is deterministic and covered by tests. Each review can also record observed duration for
later evidence-based tuning. A model may help analyze or propose a better policy; it does not get
permission to silently rewrite review history or due dates.

### Safe maintenance by AI agents

- SQLite/WAL persistence with optimistic card versions.
- Stable operation IDs for retry-safe content writes and reviews.
- Append-only review events and an incremental change cursor.
- A durable native Swift outbox that preserves offline intent and replays in order.
- Explicit conflicts that return the current server card instead of accepting a stale overwrite.
- Repository instructions, architecture routes, change playbooks, and completion gates written for
  the next AI maintainer as well as the next human contributor.

## System shape

```text
AI maintainer -> trilingual/image orchestration -> versioned card mutation
                                                       |
Learner -> SwiftUI review surface -> offline outbox -> SQLite/WAL store -> scheduler
                                                       |
                                        conflicts, change cursor, review ledger
```

Semantic generation and state transitions meet at one narrow, versioned boundary. That separation
lets the AI be creative where creativity is useful while deterministic code protects learning
state where reproducibility matters.

## Repository map

- `src/agentic_flashcards/content.py` — provider-neutral trilingual and image-fallback orchestration.
- `src/agentic_flashcards/scheduler.py` — transparent adaptive review policy.
- `src/agentic_flashcards/store.py` — versioned cards, idempotent operations, review ledger, and
  change cursor.
- `ios/` — Swift package for shared models and a persistent offline outbox, plus a minimal SwiftUI
  review shell.
- `tests/` and `ios/Tests/` — executable behavior contracts.
- `scripts/privacy_check.py` — public-release privacy guard.
- [`docs/AI_MAINTAINER_GUIDE.md`](docs/AI_MAINTAINER_GUIDE.md) — how an AI agent should start,
  modify, verify, and hand off this repository.

## Run the demos

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'

# Versioning, review, idempotent replay, due queue, and change cursor
.venv/bin/agentic-flashcards demo \
  --db /tmp/agentic-flashcards-demo.sqlite

# Trilingual content plus search-first and generation-fallback image paths
.venv/bin/agentic-flashcards content-demo
```

The content demo is fully synthetic and makes no network calls.

## Verify the repository

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/privacy_check.py
swift test --package-path ios
```

## Public reference vs. production system

The private system that motivated this reference goes further: a native lookup-to-card flow,
first-class media with attribution and content-hash caching, searched and generated images in one
picker, review-duration analytics, a scheduling policy shared across Python and Swift, and
checkpointed bulk content repair with preview/commit gates. This repository publishes the
portable contracts and failure controls, not the personal data or private deployment.

## Design boundaries

- AI may propose and maintain content; it does not decide what enters the collection.
- Semantic output is validated before mutation.
- Search precedes generation to prefer attributable, reusable media and avoid unnecessary model
  calls.
- Review history is append-only; retries are idempotent.
- Stale offline writes produce conflicts; they do not silently win.
- The public repository contains synthetic content only.

The operating model follows
[Software Is Switching Operators](https://shawnxiang.com/articles/agentic-life-os/): people direct
and judge, agents execute bounded maintenance, deterministic code protects state, and interfaces
support review.

## License

MIT
