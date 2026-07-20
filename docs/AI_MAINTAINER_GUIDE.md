# AI Maintainer Guide

This is the operating map for an AI agent asked to start, modify, debug, or extend Agentic
Flashcards. The goal is autonomous maintenance inside explicit product and safety boundaries, not
autonomous product authority.

## First pass

1. Read `README.md` and `AGENTS.md` completely.
2. Run `git status --short --branch` and preserve unrelated worktree changes.
3. Inventory the relevant files with `rg --files`; search for the behavior and its tests before
   changing code.
4. Establish a baseline with the narrowest relevant test, then run the full completion gates before
   handoff.

Bootstrap and baseline:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/privacy_check.py
swift test --package-path ios
```

## Architecture routes

- **AI content policy** — `src/agentic_flashcards/content.py`
  - `ExplanationProvider` owns semantic generation.
  - `ImageSearchProvider` and `ImageGenerationProvider` own external capabilities.
  - `ContentOrchestrator` owns validation, license/relevance policy, and fallback order.
- **Scheduling policy** — `src/agentic_flashcards/scheduler.py`
  - Pure function, integer state, ISO dates, no network or model calls.
- **Durable state** — `src/agentic_flashcards/store.py`
  - SQLite/WAL, operation-id replay, optimistic versions, append-only review events, change cursor.
- **Agent/demo entry point** — `src/agentic_flashcards/cli.py`
  - Keep demos deterministic, synthetic, and credential-free.
- **Native offline boundary** — `ios/Sources/AgenticFlashcardsCore/`
  - Shared card/operation models and ordered persistent outbox.
- **Acceptance contracts** — `tests/`, `ios/Tests/`, and `scripts/privacy_check.py`.

## Non-negotiable boundaries

- The model is allowed to generate or repair content. It is not allowed to mutate scheduling state
  outside the store contract or decide collection membership.
- Every retryable write needs a stable operation ID. Every content edit needs the expected card
  version. A stale edit must surface a conflict.
- Review events are evidence. Never rewrite or delete them to make current state look cleaner.
- Search results must satisfy both relevance and reusable-license policy before selection.
- Image generation is a fallback for a visually useful subject, not an unconditional decoration
  step.
- Keep real credentials, personal cards, runtime databases, private media, and workstation paths
  out of commits and test fixtures.

## Change playbooks

### Change review timing

1. Add or adjust cases in `tests/test_scheduler.py` first.
2. Change the pure scheduler without adding AI/provider dependencies.
3. Verify retry behavior and the append-only review event in `tests/test_store.py`.
4. If a field crosses the native boundary, update the Swift model and its round-trip/outbox test in
   the same change.

### Add a model or search provider

1. Implement an existing protocol; do not put vendor branching inside `ContentOrchestrator`.
2. Translate provider-specific failures into a narrow domain error such as
   `ImageSearchUnavailable`.
3. Preserve trilingual validation and search-before-generation ordering.
4. Use fakes in unit tests. Live credentials and paid calls do not belong in the default suite.

### Change persistence or sync

1. Treat operation IDs, card versions, and the change cursor as a single cross-device contract.
2. Make schema changes forward-compatible for an existing SQLite file.
3. Test first execution, identical retry, stale expected version, and incremental sync.
4. Update Swift `Codable` models whenever the wire representation changes.

### Extend the iOS example

Keep the app a review and conflict-resolution surface. Ordinary content maintenance belongs behind
the typed agent/API boundary. Test durable outbox order and failure behavior before adding UI state.

## Failure handling

- Read the complete error before changing code.
- Reproduce with the narrowest test or demo command.
- Fix the owning layer: provider translation, orchestration policy, store invariant, or native
  boundary.
- Add a regression test that would have caught the failure.
- Do not hide a failing provider behind a generic empty result; the fallback reason is part of the
  observable contract.

## Completion gates

A change is ready only when all applicable checks pass:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/privacy_check.py
swift test --package-path ios
```

Also run both CLI demos after changes to orchestration, storage, or packaging. Inspect `git diff`
for private tokens, generated databases, absolute paths, and accidental edits outside the task.

The handoff should state the user-visible outcome, the exact checks run, and any real limitation.
Do not claim a live provider integration from the deterministic demo adapters.
