# Repository instructions

## Start here

1. Read `README.md` for the product contract and public/private boundary.
2. Read `docs/AI_MAINTAINER_GUIDE.md` for architecture routes, change playbooks, and completion
   gates.
3. Inspect the current worktree before editing; preserve unrelated user changes.

## Invariants

- This public repository uses synthetic content only.
- Agents may maintain content and propose changes; the learner controls collection membership and
  conflict resolution.
- Keep scheduling deterministic, review history append-only, and retries idempotent.
- Preserve optimistic versions and explicit stale-write conflicts across Python and Swift models.
- Do not add personal cards, credentials, private media, absolute workstation paths, or code/data
  copied from a private repository.
- Keep AI/search vendors behind the protocols in `content.py`; provider credentials never belong in
  the repository.

## Done means

Run Python tests, lint, the privacy scan, and Swift tests. Update the README and AI maintainer guide
when a change moves a public contract, architecture route, command, or invariant.
