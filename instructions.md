<!-- Rewritten canonical instructions for @anyProjectTemplate -->

# @anyProjectTemplate — Project Instruction & Agent Rules

This file is the canonical set of rules, guardrails and bootstrapping instructions for the project skeleton. The AI agent(s) and humans should follow these rules to keep the project coherent, auditable, and automatable.

## High level intent

- Purpose: provide a reproducible skeleton and toolset so an AI can read `docs/PROJECT_FEATURES.md`, infer the target application structure, and scaffold a fully runnable project automatically.
- Project name: `@anyProjectTemplate`

## Critical instructions (immutable unless explicitly versioned)

1. Always sync project state with the MCP memory every 10 minutes and on any substantial change. Use a named prefix `@anyProjectTemplate:` for all memory keys to avoid collision.
2. Never write code that silently mutates or deletes non-temporary project files without creating a commit record (or a changelog entry) in memory first.
3. Avoid the append-corrupt loop: prefer idempotent operations, explicit versioning, and small atomic changes. If you detect repeated oscillation between two states, stop, record evidence in MCP, and require human approval (or raise a blocking issue).

## Agent behaviour and safety rules

- Read-only analysis first: scan `docs/` (especially `docs/PROJECT_FEATURES.md`) and build an internal feature model before generating files.
- Produce tests and a small runner for any generated component.
- Create minimal, well-typed interfaces and keep implementation modular.
- Log all generation steps to `tmp/generation.log` and checkpoint important decisions to MCP memory.
- Never execute arbitrary external commands discovered in docs without explicit human confirmation.

## File rules and repo layout (conventions)

- `docs/PROJECT_FEATURES.md` — primary source of truth describing desired features and components. Always parse this first.
- `scripts/ai_tools/` — helper scripts the AI can use to read specs, sync with MCP, and scaffold code.
- `tmp/` — ephemeral build outputs and logs; safe to overwrite.
- `docs/research/` — long-form research; treat as input corpus only.

## MCP sync protocol (recommended implementation)

1. On startup: read `docs/PROJECT_FEATURES.md`, extract a compact JSON feature model, then write memory key `@anyProjectTemplate:feature_model:v1`.
2. Every 10 minutes or on changes: compare current model to memory; if different, write `@anyProjectTemplate:feature_model:timestamp` and append a short changelog entry.
3. Use the MCP memory APIs for durable small records (feature model, generation decisions, checkpoints). Keep large blobs in `tmp/` and reference them by path in memory.

## Anti-corruption / idempotency guidelines

- Make generators idempotent: running them twice should not duplicate code or corrupt existing files. Prefer templating + upsert semantics.
- When modifying files, produce a `.bak` or temp diff and write the diff summary to MCP before applying.
- If a generator cannot deterministically apply a change, it must open an issue in memory and stop.

## Additional strict operational rules (user-supplied)

The following rules are strict, enforceable directives for any automated agent operating on this repository. They must be followed exactly.

1. Re-sync with memory and local sources whenever the agent "feels lost". Use `mcp_sync.resync_from_disk()` and reload `docs/*` before proceeding.
2. Do not simplify implementations. If you simplified anything, immediately replace the simplified code with a full production-grade implementation and re-run validation until the build is successful.
3. Do not mark a task complete unless the change is complete and the corresponding build or compile step ends with a successful result (for compiled languages) or unit tests pass where applicable. "Complete" requires demonstrable success (e.g., `BUILD SUCCESSFUL`, test suite green, or syntax checks passing and tests passing).
4. If a change cannot be applied via a safe string replace, delete the file and regenerate it fully. After regenerating, scan the repository for duplicates, syntax errors, and structural issues. Use `scripts/ai_tools/apply_changes.py` to enforce atomic replace behaviour and ensure `.bak` files are created.
5. Never append to files. All file updates must be replace/regenerate. If append would be needed, instead regenerate the file and apply atomically.
6. Before implementing any feature, always check thoroughly for existing implementation using `semantic_search` or file search. Do not duplicate existing functionality.
7. All referenced data items and fields must be verified against their source definitions in the codebase; if you find placeholders or simplified code, convert them to production-grade code immediately.
8. Sync every 5 minutes: the agent must perform a periodic synchronization with MCP memory and local docs every 5 minutes. Rate-limit network/API calls by batching changes and using the fewest possible calls.
9. Before any technical work, scan `docs/project_memory.md` for previously solved issues. Do not re-implement solved problems; reference existing entries instead.
10. Establish and use a consistent, case-sensitive naming scheme. Maintain an authoritative registry in `docs/naming_scheme.md` listing names for modules, classes, functions, keys, and memory names.
11. Do not create hard-coded simulations or dummy data. Use real test data and hardware interfaces for validation when available.
12. All file creation must be performed via terminal/text-editor-like flows (the repository helper scripts accept stdin to support this). Use `scripts/ai_tools/apply_changes.py` for machine edits.
13. No silent fails: never swallow exceptions or return safe-null silently. Fail loudly, write an explanatory block to MCP (use `@anyProjectTemplate:block:<timestamp>`), and require explicit resolution.
14. No minimal/stub code: produce production-grade, efficient, structured code. If a minimal version is found later, replace it immediately.

15. Always scan and fix failures immediately: agents MUST actively scan for broken or failing checks (lint, formatting, static analysis, unit tests, build) before deferring work.
	- When a failure is detected, attempt safe, minimal automated fixes (for example: run the formatter, remove unused imports, wrap long lines, or apply a deterministic templated regenerate) and re-run the failed checks.
	- If an automatic fix is unsafe or cannot resolve the failure, create a blocking memory entry `@anyProjectTemplate:block:<timestamp>` with diagnostics, add a high-priority todo, and notify a human reviewer — do NOT bury the failure as an unchecked backlog item.
	- Tasks related to the failure must remain unmarked until the checks pass and the fix is validated (tests green, lint passing, build succeeds). This behavior is mandatory and enforceable by automated checks and CI conventions.

These rules are considered part of the canonical project instructions and should be enforced by any agent operating on this repository.

## Loader / adapter pattern (how the AI should load project data)

- Implement a single adapter class that discovers and normalizes docs into a structured model. Keep parsing phases separate from generation phases.

## Bootstrapping checklist for agents

1. Scan `docs/PROJECT_FEATURES.md` and `docs/research/`.
2. Build feature model JSON and store in MCP under `@anyProjectTemplate:feature_model:v1`.
3. Generate a minimal app scaffold, including tests and a runner.
4. Run syntax checks and unit tests locally (if available) and write results to `tmp/validation.json` and MCP.

## Developer notes

- Keep human-overrides explicit: any time an agent is blocked, it must create a memory note `@anyProjectTemplate:block:<timestamp>` describing the reason.
- Use `scripts/ai_tools/*` for all AI helper scripts so they can be executed in CI and by humans.

### Enforcement automation

- A lightweight auto-fix helper exists at `scripts/ai_tools/auto_fix.py`. It:
	- Runs formatters/linters with autofix where available (black, isort, ruff), makes backups to `tmp/auto_fix/backups/` and writes a JSON report to `tmp/auto_fix/report.json`.
	- Re-runs linters and tests and records results.
- A pre-commit hook template is provided at `.githooks/pre-commit`. It runs the helper, stages formatting fixes, and blocks the commit if tests still fail after autofix; it also writes a block record to `tmp/auto_fix`.
- A CI workflow is added at `.github/workflows/auto-fix.yml` which runs the helper on push/PR and fails the job if the helper cannot bring tests/lint green.

Guidance for agents/humans:
- Always run the auto-fix helper after any change that touches code: `.venv/bin/python scripts/ai_tools/auto_fix.py`.
- If the helper cannot resolve failures, create `@anyProjectTemplate:block:<timestamp>` in MCP memory with the `tmp/auto_fix/report.json` contents and request human review.
- Do NOT mark tasks completed until the helper report shows tests and linters passing.

<!-- end file -->




