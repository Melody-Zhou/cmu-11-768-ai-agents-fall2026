# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal solutions to **CMU 11-768: AI Agents (Fall 2026)**. The repository currently contains the vendored Assignment 1 scaffold and will grow to hold the three assignments plus links to lecture notes. The `README.md` is the public index; the notes themselves live on WeChat.

- Course: https://www.cmu-agents.com/
- Instructors: Daniel Fried and Graham Neubig
- Assignments: **1 Harness** (10%, due Mon Sep 14, 2026), **2 Eval** (15%, due Thu Oct 1, 2026), **3 Training** (15%, due Thu Oct 29, 2026). All are individual.
- Current state: Assignment 1 scaffold only. All student TODOs are open, so `make test` intentionally fails.
- Upstream provenance: `assignment-1` @ [`67498d8`](https://github.com/cmu-agents/assignment-1/commit/67498d87e36f7b45a2a4ce82d65d1139fb6a51c0), `chess_app` submodule @ [`4aaabca`](https://github.com/cmu-agents/chess-app/commit/4aaabca1194ef5f175ccae4fecf902bc71cc303b). See `assignment-1/UPSTREAM.md`.

## Repository Structure

```text
.
├── assignment-1/                  # Assignment 1: harness, compaction, chess agent
│   ├── ASSIGNMENT.md              # Official handout (upstream; do not edit)
│   ├── README.md                  # Official assignment README (upstream; do not edit)
│   ├── Makefile                   # Official task runners
│   ├── pyproject.toml             # uv project; entry points
│   ├── uv.lock                    # Locked dependencies
│   ├── src/assignment/
│   │   ├── agent/
│   │   │   ├── base.py            # Shared domain-independent ReAct loop
│   │   │   ├── code_agent.py      # Part 1 coding agent
│   │   │   ├── chess_agent.py     # Part 3 chess agent
│   │   │   ├── chess_tools.py     # Chess tool implementations
│   │   │   └── tools.py           # OpenAI tool schemas
│   │   ├── eval/                  # Evaluation helpers
│   │   ├── env.py                 # Modal/SWE-ReX sandbox environment
│   │   ├── prompts.py             # Chess prompts (edit only if the task requires it)
│   │   ├── task.py                # Task loader
│   │   └── utils/image.py         # Testbed image builder + source verification
│   ├── tasks/                     # Provided tasks, skills, SWE-bench instances (do not edit)
│   ├── tests/                     # Public tests (upstream; do not edit)
│   ├── chess_app/                 # Submodule: cmu-agents/chess-app @ 4aaabca
│   ├── artifacts/                 # Generated patches, trajectories, reports (deliverables)
│   ├── AI_USAGE.md                # AI-assistance disclosure
│   └── UPSTREAM.md                # Vendoring/provenance notes
├── .gitmodules                    # chess_app submodule
├── .gitignore
├── CLAUDE.md
├── LICENSE
└── README.md
```

## Working Rules

- **Read `assignment-1/ASSIGNMENT.md` before changing code.** It is the source of truth for required behavior, grading, and submission.
- **Only student code changes belong in `assignment-1/src/assignment/agent/`.** `src/assignment/prompts.py` may be changed only when the assignment explicitly calls for it (the submission includes it only if changed). Do not modify `tests/`, `tasks/`, `chess_app/`, `ASSIGNMENT.md`, or the assignment's `README.md`.
- **Do not duplicate the shared ReAct loop in a subclass.** Implement the loop, prompt construction, and compaction once in `Agent`; subclasses supply only domain prompts, tools, and tool executors.
- **Use only the intended tools for each agent.** `CodeAgent` gets `execute`, `send_message`, and `invoke_skill` when skills exist. `ChessAgent` gets `play_move`, plus `simulate_move` / `run_python` only with `--programmatic-tools`, plus `invoke_skill` only when skills exist.
- **No secrets in the repository.** Never commit `.env`, API keys, Modal tokens, or credentials. Do not print them in logs, trajectories, or reports. Use `.env.example` as the tracked template.
- **Disclose AI assistance.** Keep `assignment-1/AI_USAGE.md` current whenever AI tools contribute code or analysis. You must be able to explain every submitted line; the course assesses understanding through a quiz.
- **Course policy.** Assignments are individual. Do not post solutions publicly or push solution code to a public remote without explicit user confirmation that the course permits it.
- **Keep upstream scaffolding intact.** Treat vendored files as read-only. If a layout change is genuinely necessary (for example, the root-level `chess_app` submodule), record it in `assignment-1/UPSTREAM.md`.
- **Artifacts are deliverables.** Keep generated patches, trajectories, and reports in `assignment-1/artifacts/`. Do not hand-edit model-generated artifacts; rerun the agent instead.
- **Notes list individual articles.** In `README.md`, list every published note with its own WeChat article URL, title, and publication date. Use the album URL only as a secondary "full album" reference; never replace the per-article table with a single album link.
- **English in `README.md` and `CLAUDE.md`.** Course code and docs are English; notes links may point to Chinese posts.
- **Minimal diffs.** Match the surrounding style and comment density. Do not add speculative abstractions, extra dependencies, or unrelated refactors.

## Environment and Commands

Assignment 1 uses Python 3.11+, [uv](https://docs.astral.sh/uv/), [Modal](https://modal.com/), and an OpenAI-compatible endpoint. Run everything from `assignment-1/`.

```bash
cd assignment-1

make setup                  # uv sync, init submodule, verify chess_app at 4aaabca
uv run modal setup          # one-time Modal login (interactive)
cp .env.example .env        # then fill in OPENAI_BASE_URL / OPENAI_API_KEY
make doctor                 # validate config without launching a sandbox (online)
uv run assignment-doctor --offline   # same checks without contacting the endpoint
make test                   # fast, offline, non-billable public tests
```

Billable commands (require Modal credentials and API credits):

```bash
make test-modal
make test-chess-modal

make run-code-agent         # Part 1 -> artifacts/fix.patch + part1-trajectory.json
make check-part1            # replay the patch in a fresh testbed

COMPACT_THRESHOLD=6000 \
SWEBENCH_PATCH=artifacts/django__django-15368.patch \
SWEBENCH_TRAJECTORY=artifacts/django__django-15368-trajectory.json \
make run-swebench-agent INSTANCE=django__django-15368
make check-swebench INSTANCE=django__django-15368

COMPACT_THRESHOLD=0 \
SWEBENCH_PATCH=artifacts/django__django-15368-baseline.patch \
SWEBENCH_TRAJECTORY=artifacts/django__django-15368-baseline-trajectory.json \
make run-swebench-agent INSTANCE=django__django-15368

make run-chess-agent
make run-obs-deepseek-no-legal
make run-obs-deepseek-legal
make run-obs-gpt-oss-no-legal
make run-obs-gpt-oss-legal

uv run assignment-play-chess --programmatic-tools \
  --skills-path tasks/chess-skills \
  --trajectory artifacts/part3-python-skill-trajectory.json
```

Key environment variables: `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` (default `deepseek/deepseek-v4-flash-0731`), `OPENAI_MAX_RETRIES` (default 5). `COMPACT_THRESHOLD=0` disables compaction.

The `chess_app` submodule must exist and be clean at `4aaabca`; `make setup` and `make doctor` fail otherwise. Never "fix" the app inside the submodule. `make check-part1` applies a generated patch to a fresh testbed.

## Assignment 1 Implementation Map

The handout numbers the TODOs; this map points to where each one lives.

| TODO | Requirement | Where |
|---|---|---|
| 1.1.a | Agent state, message history, and domain-agnostic `build_prompt` | `agent/base.py` |
| 1.1.b | `CodeAgent` system and task prompts; `<system_information>` block verbatim from `env` | `agent/code_agent.py` |
| 1.2 | ReAct loop, completion via `finished`, `StepLimitError` | `agent/base.py` |
| 1.3 | `execute` / `send_message` dispatch, one linked observation per call, recoverable errors | `agent/code_agent.py` |
| 1.4 | Skill discovery, YAML frontmatter, metadata/content mapping, progressive disclosure | `agent/base.py`, `agent/code_agent.py` |
| 2.1 | `COMPACTION_SYSTEM_PROMPT` and `compact_context` | `agent/base.py` |
| 2.2 | Call `maybe_compact_context()` before each new action request | `agent/base.py` |
| 3.1.a | `play_move` strict OpenAI function schema | `agent/tools.py` |
| 3.1.b | `_play_move` against `POST /api/move`, recoverable `<chess_error>` | `agent/chess_tools.py` |
| 3.1 | Register `play_move`, dispatch calls, update `last_state`/`finished`, one move per batch | `agent/chess_agent.py` |
| 3.3.a | `simulate_move` schema (`fen`, optional `move`) | `agent/tools.py` |
| 3.3.b | `_simulate_move` against `POST /api/simulate` | `agent/chess_tools.py` |
| 3.4 | `run_python` schema, base64 sandbox execution, state refresh | `agent/tools.py`, `agent/chess_tools.py`, `agent/chess_agent.py` |
| 3.5 | `_invoke_skill` for the chess agent; register `INVOKE_SKILL_TOOL` only when skills exist | `agent/chess_tools.py`, `agent/chess_agent.py` |

Behavioral constraints that are easy to miss:

- **Prompt validity.** Exactly one `system` message first, then a `user` task message, then alternating assistant actions and linked `tool` observations. Preserve assistant reasoning and tool-call arguments. `build_prompt` should not mutate agent state.
- **Tool IDs.** A provider may reuse `call_0` across turns; match each observation to the call in the same assistant action. Do not assume IDs are globally unique.
- **Text-only recovery.** If the model returns no tool call, preserve the assistant message and continue rather than crashing or inventing an observation.
- **Observation truncation.** `format_tool_output` already truncates values over 10,000 characters while keeping both ends; use it for coding-tool observations.
- **Skills.** Each child directory of `skills_path` must contain a `SKILL.md`. Parse the YAML frontmatter, key the mapping by `name`, expose a concise `metadata` catalog in the system prompt, and return the full `content` from `invoke_skill`. Reject duplicate names and missing/malformed frontmatter with a clear `ValueError`. If no skills are loaded, no part of the prompt may mention `patch.txt` or submission steps.
- **Compaction.** Summarize only an old prefix. Keep the original system/task messages verbatim and at least the latest complete assistant action with all linked tool observations. The summary must change what `build_prompt` emits and reduce prompt length. Do not touch `api_prompts` / `api_responses`; they are evaluation bookkeeping. The provided `compact_context` scaffold returns `(compaction_prompt, compaction_response)` unchanged, and `maybe_compact_context` records the event.
- **Chess errors.** Malformed JSON, non-object arguments, missing/non-string fields, illegal positions/moves, and transport failures must become `<chess_error>...</chess_error>` observations, not exceptions.
- **Parallel chess calls.** The live position changes after a move, so execute at most one `play_move` per batch and reject the rest recoverably.
- **`run_python` isolation.** Model-written code must never execute in the local agent process. Send base64-encoded code through `env.execute` to `python /opt/assignment/sandbox_python.py <port> <base64>`. A non-zero sandbox command is a `<chess_error>`; a Python exception from the snippet is a successful runner invocation with an `error` field. After each snippet, re-read the live board, update `last_state` / `finished`, and append the formatted state.
- **Reports.** `artifacts/token-usage-analysis.md` compares compacted vs. full-context token usage and tradeoffs. `artifacts/observation-experiment.md` records `play_move` calls, illegal rejections, invalid-move rate, and `game_over` for the four A/B runs.

## Verification

Before claiming work is complete:

```bash
cd assignment-1

# Fast, offline, non-billable
make test

# Configuration only (no sandbox)
uv run assignment-doctor --offline

# Patch replay (billable setup; requires artifacts/fix.patch)
make check-part1

# Repository hygiene
git status --short
git diff --check
git ls-files | grep -E '(^|/)\.env$' || true       # must print nothing
git grep -nE '(sk-[A-Za-z0-9]{16,}|OPENAI_API_KEY=.+)' -- ':!*.example' || true
```

Rules for reporting results:

- Never claim tests pass without the actual output. If a command cannot run because `uv`, Modal, `.env`, or credits are missing, say so explicitly.
- `make test` failing on the starter TODOs is expected. Distinguish "not implemented yet" from "implemented but broken".
- Do not commit or push until the user asks. When asked to commit, include only source, docs, and intended artifacts.

## Git and Ignore Rules

- Do not commit or push unless the user asks.
- Never commit `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, Modal credentials, or local caches. The assignment's own `.gitignore` already covers most of these; the root `.gitignore` covers repository-wide files.
- Do not commit the contents of `chess_app/`; commit only the submodule pointer. Use `git submodule update --init` after cloning.
- `assignment-1/artifacts/` is intentionally tracked because the assignment submission includes patches, trajectories, and reports. Avoid committing temporary logs or oversized caches; coordinate with the user before adding large artifacts.
- Do not add broad ignore rules for `src/`, `tests/`, `tasks/`, `artifacts/`, or `*.md`; they are course sources or deliverables.
- When updating `README.md`, keep the anchors `#assignments`, `#notes`, and `#course-policy-and-ai-use`, and keep relative links valid.
