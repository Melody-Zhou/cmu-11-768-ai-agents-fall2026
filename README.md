<div align="center">

<h1>CMU 11-768 · AI Agents</h1>

<p><strong>Fall 2026 · Carnegie Mellon University</strong></p>

<p>
  <a href="https://www.cmu-agents.com/">Course Website</a> ·
  <a href="https://www.cmu-agents.com/#/assignments">Assignments</a> ·
  <a href="https://www.cmu-agents.com/#/syllabus">Syllabus &amp; Policies</a> ·
  <a href="#assignments">Assignments</a> ·
  <a href="#notes">Notes</a>
</p>

<p>
  <img alt="CMU 11-768" src="https://img.shields.io/badge/CMU-11--768-8A2BE2?style=flat-square">
  <img alt="Fall 2026" src="https://img.shields.io/badge/Fall-2026-1f6feb?style=flat-square">
  <img alt="Claude Code assisted" src="https://img.shields.io/badge/AI-Claude%20Code-d97757?style=flat-square">
</p>

</div>

## Introduction

Implementation of CMU 11-768 (**AI Agents**, Fall 2026), taught by Daniel Fried and Graham Neubig. The course covers the capabilities, applications, training, frameworks, safety, and interaction of LLM-based agents. This repository contains my assignment implementations and links to my lecture notes, developed with assistance from **Claude Code**.

> **Note:** This is an unofficial personal learning record. It is not affiliated with or endorsed by Carnegie Mellon University or the course staff. Assignment solutions are my own work and may differ from the official solutions. Course policy requires assignments to be completed individually and AI assistance to be disclosed — see [Course Policy and AI Use](#course-policy-and-ai-use).

## Assignments

| # | Topic | Due | Weight | Status | Local | Official |
|:---:|-------|-----|:------:|:------:|-------|----------|
| 1 | **Harness** — ReAct coding agent, context compaction, and chess agent | Mon, Sep 14, 2026 | 10% | 🚧 Scaffolded — TODOs pending | [assignment-1/](./assignment-1/) | [cmu-agents/assignment-1](https://github.com/cmu-agents/assignment-1) |
| 2 | **Eval** — evaluation framework for agent correctness and functionality | Thu, Oct 1, 2026 | 15% | ⏳ Planned | — | [cmu-agents/assignment-2](https://github.com/cmu-agents/assignment-2) |
| 3 | **Training** — training procedures to adapt and improve the agent | Thu, Oct 29, 2026 | 15% | ⏳ Planned | — | [cmu-agents/assignment-3](https://github.com/cmu-agents/assignment-3) |

The remaining course grade comes from lecture highlights (10%) and the half-semester research project (50%: Project Hours 5%, Poster 15%, Report 30%). Assignments 1–3 are individual; the project is done in teams of 2–4.

## Notes

Unofficial lecture notes (in Chinese) are published on my WeChat official account. Each post maps to one lecture:

| # | Lecture | Published | Article |
|:---:|---------|:---------:|:-------:|
| 1 | Course Overview: What Is an Agent? | 2026-10-28 | [Read](https://mp.weixin.qq.com/s?__biz=MzY5MDQ1NjczOA==&mid=2247483877&idx=1&sn=a0b5d51e5eef3911df102e57f8a68a38&chksm=f3c95028c4bed93e7c937112ac32503e5b1c1b818e12c711b55387de70fdcf36ec7aef41fd6e) |
| 2 | Agent Capabilities 1: Tool Use | 2026-10-29 | [Read](https://mp.weixin.qq.com/s?__biz=MzY5MDQ1NjczOA==&mid=2247483930&idx=1&sn=3558436bf2c7af43ab767bc1ea838f94&chksm=f3c953d7c4bedac12d3d200b2fdf0ad9e7cca14fc8ce3f04cbdd0bfaa4f420dfb926bc1e3a71) |
| 3 | Agent Capabilities 2: Context Management for Long-Context Agents | 2026-11-03 | [Read](https://mp.weixin.qq.com/s?__biz=MzY5MDQ1NjczOA==&mid=2247483982&idx=1&sn=cdcc4d89cd090ddcfaa69e6ff32a84b5&chksm=f3c95383c4beda95d81d0a171760dd3c2e4d151cf5edc255a1fc51a70332bbf0da29f753b5bb) |
| 4 | Agent Capabilities 3: Skills and Memory | 2026-11-04 | [Read](https://mp.weixin.qq.com/s?__biz=MzY5MDQ1NjczOA==&mid=2247484025&idx=1&sn=ba8ed32dd88788d8d4e01edae801fb06&chksm=f3c953b4c4bedaa28677d6cff8d984bea31408b0a326aaea493100e3dab6ee94cfa5fe2fe3e4) |

New posts are added as the course progresses. The full album is also available [here](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzY5MDQ1NjczOA==&action=getalbum&album_id=4757631553994948609).

## Setup

### Assignment 1

Assignment 1 is a self-contained Python project. The complete problem statement, grading breakdown, and submission requirements are in [`assignment-1/ASSIGNMENT.md`](./assignment-1/ASSIGNMENT.md). Modal access and API credits are distributed by the course staff.

Prerequisites:

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A [Modal](https://modal.com/) account
- The course-provided OpenAI-compatible endpoint and API key

```bash
cd assignment-1
make setup                 # uv sync + verify the pinned chess_app checkout
uv run modal setup         # one-time Modal login
cp .env.example .env       # fill in the course base URL and key
make doctor                # validate configuration without launching a sandbox
make test                  # fast, offline public tests
```

The public tests fail until the student TODOs are implemented. `make test-modal` and every agent run are **billable** and launch real Modal sandboxes.

Key runs (see `ASSIGNMENT.md` for the full sequence):

```bash
make run-code-agent                                  # Part 1: generate artifacts/fix.patch
make check-part1                                     # replay the patch in a fresh testbed

COMPACT_THRESHOLD=6000 \
make run-swebench-agent INSTANCE=django__django-15368  # Part 2
make check-swebench INSTANCE=django__django-15368

make run-chess-agent                                 # Part 3
make run-obs-deepseek-no-legal
make run-obs-deepseek-legal
make run-obs-gpt-oss-no-legal
make run-obs-gpt-oss-legal
```

`chess_app` is a git submodule pinned to the assignment's base commit. Clone with `git clone --recurse-submodules`, or initialize it with `git submodule update --init` at the repository root. Do not edit the checkout in `assignment-1/chess_app/`; patches are replayed in a fresh testbed instead.

## Repository Structure

```text
.
├── assignment-1/                  # Assignment 1: harness, compaction, chess agent
│   ├── ASSIGNMENT.md              # Official handout (upstream; do not edit)
│   ├── README.md                  # Official assignment README (upstream; do not edit)
│   ├── Makefile                   # Official task runners
│   ├── pyproject.toml             # uv project and entry points
│   ├── uv.lock                    # Locked dependencies
│   ├── src/assignment/            # Harness implementation (student TODOs)
│   │   ├── agent/                 # Agent loop, coding agent, chess agent, tools
│   │   ├── eval/                  # Evaluation helpers
│   │   ├── env.py                 # Modal/SWE-ReX environment
│   │   └── ...
│   ├── tasks/                     # Provided tasks, skills, and SWE-bench instances
│   ├── tests/                     # Public tests (upstream; do not edit)
│   ├── chess_app/                 # Submodule: cmu-agents/chess-app @ 4aaabca
│   ├── artifacts/                 # Generated patches, trajectories, and reports
│   ├── AI_USAGE.md                # AI-assistance disclosure
│   └── UPSTREAM.md                # Vendoring and provenance notes
├── .gitmodules                    # chess_app submodule
├── .gitignore
├── CLAUDE.md                      # Guidance for Claude Code in this repository
├── LICENSE
└── README.md
```

### Assignment 1 status

The upstream scaffold is vendored at commit [`67498d8`](https://github.com/cmu-agents/assignment-1/commit/67498d87e36f7b45a2a4ce82d65d1139fb6a51c0), and `chess_app` is pinned to [`4aaabca`](https://github.com/cmu-agents/chess-app/commit/4aaabca1194ef5f175ccae4fecf902bc71cc303b). All student TODOs are still open; see [`CLAUDE.md`](./CLAUDE.md#assignment-1-implementation-map) for the implementation map.

| Part | Scope | Key files |
|:---:|-------|-----------|
| 1.1 | Prompt construction and coding-agent system/task prompts | `src/assignment/agent/base.py`, `src/assignment/agent/code_agent.py` |
| 1.2 | ReAct loop, step limit, and completion | `src/assignment/agent/base.py` |
| 1.3 | `execute` / `send_message` tool dispatch | `src/assignment/agent/code_agent.py` |
| 1.4 | Skill discovery and progressive disclosure | `src/assignment/agent/base.py`, `src/assignment/agent/code_agent.py` |
| 2.1–2.2 | Model-generated context compaction | `src/assignment/agent/base.py` |
| 3.1 | `play_move` schema and execution | `src/assignment/agent/tools.py`, `src/assignment/agent/chess_tools.py`, `src/assignment/agent/chess_agent.py` |
| 3.3 | `simulate_move` | `src/assignment/agent/tools.py`, `src/assignment/agent/chess_tools.py`, `src/assignment/agent/chess_agent.py` |
| 3.4 | `run_python` in the sandbox | `src/assignment/agent/tools.py`, `src/assignment/agent/chess_tools.py`, `src/assignment/agent/chess_agent.py` |
| 3.5 | Chess skill invocation | `src/assignment/agent/chess_tools.py`, `src/assignment/agent/chess_agent.py` |

## Course Policy and AI Use

- **Individual work.** Assignments 1–3 must be completed individually. You may discuss concepts and general approaches, but the submitted code, analysis, and writing must be your own.
- **AI tools.** AI assistance is permitted unless an assignment says otherwise. It must be disclosed in [`assignment-1/AI_USAGE.md`](./assignment-1/AI_USAGE.md), and you remain responsible for the accuracy, validity, and understanding of all submitted work.
- **Academic integrity.** Follow the [CMU academic-integrity policy](https://www.cmu.edu/student-affairs/ocr/) and the course's collaboration rules.

## References

- [CMU 11-768: AI Agents (Fall 2026)](https://www.cmu-agents.com/)
- [Course syllabus and policies](https://www.cmu-agents.com/#/syllabus)
- [Course assignments](https://www.cmu-agents.com/#/assignments)
- [Assignment 1: Build an Agent Harness](https://github.com/cmu-agents/assignment-1)
- [chess-app](https://github.com/cmu-agents/chess-app)
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Agent Skills protocol](https://agentskills.io/home)

## Acknowledgements

- Course instructors Daniel Fried and Graham Neubig, and the 11-768 teaching staff.
- Assignment 1 authors Weiwei Sun and Saujas Vaduguru, with feedback from the course staff.
- Thanks to the maintainers of uv, Modal, SWE-ReX, and the chess-app project.
- README layout inspired by [Melody-Zhou/mit-6.5940-tinyml-fall2026](https://github.com/Melody-Zhou/mit-6.5940-tinyml-fall2026).

## License

My own solutions and notes are released under the [MIT License](./LICENSE). Course-provided materials — including `ASSIGNMENT.md`, the assignment scaffolding, tests, tasks, and `chess_app` — remain the property of their original authors and are included for personal, educational reference only.
