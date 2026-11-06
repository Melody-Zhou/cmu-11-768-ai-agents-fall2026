# Upstream provenance

This directory vendors the official Assignment 1 starter repository. The upstream files are kept verbatim so the assignment's checks and task runners work as intended.

| Component | Source | Commit |
|---|---|---|
| `assignment-1/` | [cmu-agents/assignment-1](https://github.com/cmu-agents/assignment-1) | `67498d87e36f7b45a2a4ce82d65d1139fb6a51c0` (2026-09-11) |
| `assignment-1/chess_app/` | [cmu-agents/chess-app](https://github.com/cmu-agents/chess-app) | `4aaabca1194ef5f175ccae4fecf902bc71cc303b` (2026-09-01) |

## Changes made while vendoring

- The upstream `assignment-1/chess_app` submodule and its `assignment-1/.gitmodules` were replaced by a single root-level submodule at `assignment-1/chess_app`. This keeps the monorepo's git metadata at the root while preserving the assignment's `verify_source` check, which requires a clean `chess_app` checkout at the pinned base commit.
- No course source, test, task, or `chess_app` file was modified.

## Keeping upstream files pristine

`ASSIGNMENT.md`, `README.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `tests/`, `tasks/`, and `chess_app/` are upstream files. Student work belongs in `src/assignment/agent/` (and `src/assignment/prompts.py` only when the assignment calls for it). Record any necessary deviation here.
