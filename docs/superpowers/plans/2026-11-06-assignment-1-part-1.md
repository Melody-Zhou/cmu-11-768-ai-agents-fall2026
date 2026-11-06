# Assignment 1 Part 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the shared ReAct loop and the Part 1 `CodeAgent` so the offline tests in `assignment-1/tests/test_agent.py` pass.

**Architecture:** `Agent` owns a single message history (`self.messages`) containing assistant actions and linked tool observations. `build_prompt` prepends the subclass-provided system and task prompts. `run` alternates model calls, tool execution, and history updates, with step-limit handling and context compaction. `CodeAgent` supplies coding-specific prompts, registers `execute` / `send_message` (plus `invoke_skill` when skills are loaded), and dispatches tool calls into the sandbox. Skills are discovered from `SKILL.md` files and exposed through progressive disclosure: the prompt gets a metadata catalog, while the full body is returned only by `invoke_skill`.

**Tech Stack:** Python 3.13, `uv`, OpenAI Chat Completions API (tool calling), PyYAML, pytest, Modal/SWE-ReX (only for billable runs).

**Scope:** This plan covers Part 1 and the compaction hooks needed by `tests/test_agent.py`. The Part 3 chess tests (`tests/test_chess_agent.py`) remain failing until Part 3 is implemented. Do not modify `tests/`, `tasks/`, or `chess_app/`.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `assignment-1/src/assignment/agent/base.py` | Shared state, prompt construction, ReAct loop, skill loading, compaction | Implement `__init__` state, `load_skills`, `build_prompt`, `run`, `COMPACTION_SYSTEM_PROMPT`, `compact_context` |
| `assignment-1/src/assignment/agent/code_agent.py` | Coding prompts and tool dispatch | Register tools, build system/task prompts, implement `execute_tool_calls` and helpers |
| `assignment-1/tests/test_agent.py` | Offline integration spec | **Read-only**; do not edit |
| `assignment-1/src/assignment/agent/tools.py` | Tool schemas | **Read-only for Part 1**; schemas are already provided |

The two implementation files change together; keep the diff focused. Do not add new modules for Part 1.

---

## Task 1: Create a feature branch and confirm the red baseline

**Files:** None (git only).

- [ ] **Step 1: Create the implementation branch**

```bash
cd /home/zhouwenguang/project/cmu-11-768-ai-agents-fall2026
git switch -c feat/assignment-1-part-1
```

Expected: `Switched to a new branch 'feat/assignment-1-part-1'`.

- [ ] **Step 2: Run the Part 1 tests to confirm the baseline**

```bash
cd assignment-1
uv run pytest tests/test_agent.py -q
```

Expected: `7 failed` (all failures are `NotImplementedError` or the missing `PLAY_MOVE_TOOL` schema), with the smoke and infrastructure tests unaffected. This is the red phase; the provided tests are the specification and must not be edited.

- [ ] **Step 3: Commit the plan**

```bash
cd /home/zhouwenguang/project/cmu-11-768-ai-agents-fall2026
git add docs/superpowers/plans/2026-11-06-assignment-1-part-1.md
git commit -m "docs: add Assignment 1 Part 1 implementation plan"
```

---

## Task 2: Add agent state and prompt construction

**Files:**
- Modify: `assignment-1/src/assignment/agent/base.py:1-35` (imports/constants) and `:153-154` (state)
- Modify: `assignment-1/src/assignment/agent/base.py:220-230` (`build_prompt`)

- [ ] **Step 1: Add the YAML import**

At the top of `base.py`, add `import yaml` with the other third-party imports:

```python
from dotenv import load_dotenv
from openai import OpenAI
import yaml
```

- [ ] **Step 2: Initialize the message history**

Replace the `TODO(1.1.a)` comment in `Agent.__init__` with:

```python
        # Conversation history after the standing system and task messages.
        # `run` appends each assistant action followed by its linked tool
        # observations. `build_prompt` prepends the system and task messages.
        self.messages: list[dict[str, Any]] = []
```

- [ ] **Step 3: Implement `build_prompt`**

Replace the `build_prompt` body (including the `raise NotImplementedError`) with:

```python
    def build_prompt(self) -> list[dict[str, Any]]:
        """Build the domain-agnostic message sequence for the model."""

        messages: list[dict[str, Any]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if self.task_prompt:
            messages.append({"role": "user", "content": self.task_prompt})
        messages.extend(deepcopy(self.messages))
        return messages
```

Why `deepcopy`: the prompt is logged in `api_prompts` and passed to the provider; callers must not be able to mutate the live history through the returned list.

- [ ] **Step 4: Run a quick import check**

```bash
cd assignment-1
uv run python -c "from assignment.agent.base import Agent; print('ok')"
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add assignment-1/src/assignment/agent/base.py
git commit -m "feat(agent): add message history and domain-agnostic prompt builder"
```

---

## Task 3: Implement the shared ReAct loop

**Files:**
- Modify: `assignment-1/src/assignment/agent/base.py:322-339` (`run`)

- [ ] **Step 1: Replace the `run` TODO with the loop**

Keep the provided `finally:` block exactly as-is. Replace only the `try:` body above it:

```python
        try:
            while not self.finished:
                if self.steps_taken >= self.step_limit:
                    raise StepLimitError(
                        f"Agent reached its step limit of {self.step_limit}."
                    )

                # Compact before asking for the next action, so the request
                # itself uses the reduced working memory.
                self.maybe_compact_context()

                message = self.query_language_model()
                self.messages.append(message)

                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    # Text-only turn: preserve the reasoning and continue.
                    continue

                observations = self.execute_tool_calls(tool_calls)
                self.messages.extend(observations)
```

Do not change the `finally:` block: it writes the trajectory and stops the sandbox on both success and failure.

- [ ] **Step 2: Verify the step-limit behavior**

```bash
cd assignment-1
uv run pytest tests/test_agent.py::test_step_limit_raises -q
```

Expected at this point: still fails, but the failure should now come from `CodeAgent.execute_tool_calls` raising `NotImplementedError` rather than `Agent.run`; Task 4 supplies the missing executor.

- [ ] **Step 3: Commit**

```bash
git add assignment-1/src/assignment/agent/base.py
git commit -m "feat(agent): implement the shared ReAct loop with step limit"
```

---

## Task 4: Build the `CodeAgent` prompts and register its tools

**Files:**
- Modify: `assignment-1/src/assignment/agent/code_agent.py:1-52`

- [ ] **Step 1: Update the imports**

Replace the import block with:

```python
import json
from typing import Any

from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
    format_tool_output,
)
from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL
from assignment.env import Environment
```

- [ ] **Step 2: Register tools and construct prompts**

Replace the two TODO blocks in `CodeAgent.__init__` with:

```python
        # `Agent.__init__` has already loaded skills and registered
        # `invoke_skill` when a catalog exists; add the coding tools after it.
        self.tools.extend([EXECUTE_TOOL, SEND_MESSAGE_TOOL])

        self.system_prompt = self._build_system_prompt()
        self.task_prompt = self._build_task_prompt()
```

- [ ] **Step 3: Add the prompt builders**

Add these methods to `CodeAgent`, before `execute_tool_calls`:

```python
    def _build_system_prompt(self) -> str:
        """Write the standing coding-agent instructions and environment block."""

        system_information = json.dumps(
            {
                "machine": self.env.machine,
                "release": self.env.release,
                "system": self.env.system,
                "version": self.env.version,
            },
            indent=2,
        )
        prompt = f"""You are a coding agent working in a terminal environment.
Use the `execute` tool to inspect the repository, reproduce the issue, edit files,
run tests, and verify your fix. Commands run in /testbed, and every command starts
in a fresh subshell; use the `cwd` and `env` arguments instead of relying on `cd`
or exports from an earlier command. When the task is complete, call
`send_message` with a concise summary.

<system_information>
{system_information}
</system_information>"""
        if self.skills:
            catalog = "\n".join(
                skill["metadata"] for skill in self.skills.values()
            )
            prompt += (
                "\n\nReusable skills are available. Call `invoke_skill` with a "
                "skill's name to load its instructions, and follow them in place "
                "of your default approach.\n\n"
                f"<skills>\n{catalog}\n</skills>"
            )
        return prompt

    def _build_task_prompt(self) -> str:
        """Put the task statement and the working protocol in a user message."""

        prompt = (
            "Solve the following software issue in the repository at /testbed.\n\n"
            f"{self.task}\n\n"
            "Inspect the relevant files, reproduce the failure, make the smallest "
            "correct fix, and run the relevant tests. Use `execute` for every "
            "command. When you are done, call `send_message` with a concise "
            "summary of the change and the tests you ran."
        )
        if self.skills:
            prompt += (
                "\n\nIf a loaded skill covers the next step, invoke it before "
                "proceeding."
            )
        return prompt
```

Do not mention `patch.txt` or submission steps here. The `submit-task` skill body contains those instructions and is only revealed by `invoke_skill`.

- [ ] **Step 4: Run the prompt/skill tests**

```bash
cd assignment-1
uv run pytest tests/test_agent.py::test_skill_catalog_lists_names_without_skill_bodies -q
```

Expected: PASS. The prompt should contain `submit-task` but not `patch.txt`.

- [ ] **Step 5: Commit**

```bash
git add assignment-1/src/assignment/agent/code_agent.py
git commit -m "feat(code-agent): build coding prompts and register tools"
```

---

## Task 5: Implement coding-tool dispatch

**Files:**
- Modify: `assignment-1/src/assignment/agent/code_agent.py:54-63` (`execute_tool_calls`)

- [ ] **Step 1: Replace `execute_tool_calls` with the dispatcher**

```python
    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Execute ``execute`` and ``send_message`` calls in the code sandbox."""

        observations: list[dict[str, str]] = []
        for index, call in enumerate(tool_calls):
            call_id = call.get("id") or f"call_{index}"
            function = call.get("function") or {}
            name = function.get("name")
            arguments = function.get("arguments", "")

            if name == "execute":
                observations.append(self._execute_command(call_id, arguments))
            elif name == "send_message":
                observations.append(self._send_message(call_id, arguments))
            elif name == "invoke_skill":
                observations.append(self._invoke_skill(call_id, arguments))
            else:
                available = ", ".join(
                    tool["function"]["name"] for tool in self.tools
                )
                observations.append(
                    self._tool_error(
                        call_id,
                        f"Unknown tool {name!r}. Available tools: {available}.",
                    )
                )
        return observations
```

- [ ] **Step 2: Add the parsing and execution helpers**

Add these methods after `execute_tool_calls`:

```python
    def _parse_arguments(
        self, call_id: str, arguments: Any
    ) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
        """Parse one tool call's JSON arguments, or return a tool-error message."""

        try:
            parsed = json.loads(arguments)
        except (json.JSONDecodeError, TypeError) as exc:
            return None, self._tool_error(
                call_id, f"Malformed JSON arguments: {exc}"
            )
        if not isinstance(parsed, dict):
            return None, self._tool_error(
                call_id, "Tool arguments must be a JSON object."
            )
        return parsed, None

    def _tool_error(self, call_id: str, message: str) -> dict[str, str]:
        """Turn a recoverable tool failure into a linked observation."""

        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": f"<tool_error>{message}</tool_error>",
        }

    def _execute_command(self, call_id: str, arguments: Any) -> dict[str, str]:
        parsed, error = self._parse_arguments(call_id, arguments)
        if error is not None:
            return error
        assert parsed is not None  # guaranteed by _parse_arguments

        command = parsed.get("command")
        command_is_string = isinstance(command, str)
        command_is_argv = (
            isinstance(command, list)
            and bool(command)
            and all(isinstance(part, str) for part in command)
        )
        if not (command_is_string or command_is_argv):
            return self._tool_error(
                call_id,
                "The `execute` tool needs a `command` string or a non-empty "
                "list of strings.",
            )

        allowed = {"command", "shell", "cwd", "timeout", "env"}
        unknown = set(parsed) - allowed
        if unknown:
            return self._tool_error(
                call_id,
                f"Unknown `execute` arguments: {', '.join(sorted(unknown))}.",
            )

        kwargs = {
            key: parsed[key]
            for key in ("shell", "cwd", "timeout", "env")
            if key in parsed and parsed[key] is not None
        }
        try:
            output = self.env.execute(command, **kwargs)
        except Exception as exc:
            return self._tool_error(
                call_id,
                f"Command failed to start: {type(exc).__name__}: {exc}",
            )
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": format_tool_output(output),
        }

    def _send_message(self, call_id: str, arguments: Any) -> dict[str, str]:
        parsed, error = self._parse_arguments(call_id, arguments)
        if error is not None:
            return error
        assert parsed is not None

        summary = parsed.get("summary")
        if not isinstance(summary, str):
            return self._tool_error(
                call_id, "The `send_message` tool needs a string `summary`."
            )
        self.finished = True
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": "Message received. The task is complete.",
        }

    def _invoke_skill(self, call_id: str, arguments: Any) -> dict[str, str]:
        parsed, error = self._parse_arguments(call_id, arguments)
        if error is not None:
            return error
        assert parsed is not None

        name = parsed.get("name")
        if not isinstance(name, str) or not name.strip():
            return self._tool_error(
                call_id, "The `invoke_skill` tool needs a string `name`."
            )
        skill = self.skills.get(name.strip())
        if skill is None:
            available = ", ".join(sorted(self.skills)) or "(none)"
            return self._tool_error(
                call_id,
                f"Unknown skill {name!r}. Available skills: {available}.",
            )
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": skill["content"],
        }
```

- [ ] **Step 3: Run the prompt, step-limit, and error-recovery tests**

```bash
cd assignment-1
uv run pytest \
  tests/test_agent.py::test_prompt_carries_task_action_and_result \
  tests/test_agent.py::test_long_observation_is_truncated \
  tests/test_agent.py::test_step_limit_raises \
  tests/test_agent.py::test_malformed_arguments_are_not_executed \
  tests/test_agent.py::test_unknown_tool_is_not_executed \
  -q
```

Expected: `5 passed`.

- [ ] **Step 4: Commit**

```bash
git add assignment-1/src/assignment/agent/code_agent.py
git commit -m "feat(code-agent): dispatch coding tools with recoverable errors"
```

---

## Task 6: Implement skill discovery and progressive disclosure

**Files:**
- Modify: `assignment-1/src/assignment/agent/base.py:156-167` (`load_skills`)

- [ ] **Step 1: Replace the `load_skills` TODO with the parser**

```python
    def load_skills(self, skills_path: Path) -> dict[str, dict[str, str]]:
        """Load the skill folders exposed to this agent."""

        if not skills_path.is_dir():
            raise ValueError(f"Skills path is not a directory: {skills_path}")

        skills: dict[str, dict[str, str]] = {}
        for child in sorted(skills_path.iterdir()):
            if not child.is_dir():
                continue

            skill_file = child / "SKILL.md"
            if not skill_file.is_file():
                raise ValueError(
                    f"Skill directory {child} is missing a SKILL.md file."
                )
            try:
                text = skill_file.read_text(encoding="utf-8")
            except OSError as exc:
                raise ValueError(
                    f"Could not read skill file {skill_file}: {exc}"
                ) from exc

            if not text.startswith("---"):
                raise ValueError(
                    f"Skill file {skill_file} must start with YAML frontmatter."
                )
            parts = text.split("---", 2)
            if len(parts) < 3:
                raise ValueError(
                    f"Skill file {skill_file} has malformed YAML frontmatter."
                )
            try:
                metadata = yaml.safe_load(parts[1])
            except yaml.YAMLError as exc:
                raise ValueError(
                    f"Skill file {skill_file} has invalid YAML frontmatter: {exc}"
                ) from exc
            if not isinstance(metadata, dict):
                raise ValueError(
                    f"Skill file {skill_file} frontmatter must be a mapping."
                )

            name = metadata.get("name")
            description = metadata.get("description")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    f"Skill file {skill_file} needs a non-empty string `name`."
                )
            if not isinstance(description, str) or not description.strip():
                raise ValueError(
                    f"Skill file {skill_file} needs a non-empty string `description`."
                )

            name = name.strip()
            if name in skills:
                raise ValueError(
                    f"Duplicate skill name {name!r} in {skills_path}."
                )
            skills[name] = {
                "metadata": f"name: {name}\ndescription: {description.strip()}",
                "content": text,
            }
        return skills
```

Why `sorted`: deterministic catalog order and deterministic duplicate detection.

- [ ] **Step 2: Run the skill tests**

```bash
cd assignment-1
uv run pytest tests/test_agent.py::test_skill_catalog_lists_names_without_skill_bodies -q
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add assignment-1/src/assignment/agent/base.py
git commit -m "feat(agent): load skills with progressive disclosure"
```

---

## Task 7: Implement context compaction

**Files:**
- Modify: `assignment-1/src/assignment/agent/base.py:30-33` (`COMPACTION_SYSTEM_PROMPT`)
- Modify: `assignment-1/src/assignment/agent/base.py:255-286` (`compact_context`)

- [ ] **Step 1: Write the compaction system prompt**

Replace the empty `COMPACTION_SYSTEM_PROMPT` and its TODO comment with:

```python
COMPACTION_SYSTEM_PROMPT = """You compact the working memory of a software-engineering agent.
Write a concise, factual summary of the earlier steps supplied by the user.
Preserve:
- the objective and any explicit constraints;
- files inspected or changed, with their paths;
- commands run and their concrete results;
- edits made and tests run;
- failed approaches and why they failed;
- current blockers and the next concrete action.
Do not invent details. Do not copy raw logs, long file contents, or conversational filler.
Return only the summary."""
```

- [ ] **Step 2: Implement `compact_context`**

Keep the two `### Do not modify this section ###` blocks and the final return exactly as provided. Replace the `raise NotImplementedError` and fill in the compaction prompt/state update:

```python
    def compact_context(self):
        """Replace parts of prompt with model-generated working memory."""

        assistant_positions = [
            index
            for index, message in enumerate(self.messages)
            if message.get("role") == "assistant"
        ]
        if len(assistant_positions) < self.compaction_keep_recent_steps:
            raise ValueError(
                "Not enough assistant steps to compact while keeping "
                f"{self.compaction_keep_recent_steps} recent step(s)."
            )
        keep_start = assistant_positions[-self.compaction_keep_recent_steps]
        old_prefix = self.messages[:keep_start]
        recent = self.messages[keep_start:]

        compaction_prompt = [
            {"role": "system", "content": COMPACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Original task:\n"
                    f"{self.task_prompt}\n\n"
                    "Earlier conversation to summarize:\n"
                    f"{json.dumps(old_prefix, ensure_ascii=False, indent=2)}"
                ),
            },
        ]

        ### Do not modify this section ###
        compaction_response = self.client.chat.completions.create(
            model=self.model,
            messages=compaction_prompt,
            reasoning_effort="medium",
            max_completion_tokens=self.compaction_max_tokens,
        )
        ##################################

        # Use `compaction_response` to update what `build_prompt` emits, but
        # DO NOT modify the object itself. Let the method return it unchanged.
        summary = self.process_response(compaction_response).get("content") or ""
        self.messages = [
            {
                "role": "user",
                "content": (
                    "<compacted_context>\n"
                    f"{summary}\n"
                    "</compacted_context>"
                ),
            },
            *recent,
        ]

        ### Do not modify this section ###
        return compaction_prompt, compaction_response.model_dump(mode="json")
        ##################################
```

The `old_prefix` is summarized; the latest complete assistant action and all of its linked tool observations (`recent`) stay verbatim. `build_prompt` prepends the original system/task messages, so they remain untouched.

- [ ] **Step 3: Run the compaction test**

```bash
cd assignment-1
uv run pytest tests/test_agent.py::test_context_compaction_summarizes_old_steps_and_keeps_recent_tool_pair -q
```

Expected: PASS. The compaction call has no `tools` keyword; the next action prompt contains the summary and the recent `call_recent` / `ls -la` / output, and no longer contains the old long file command or its output.

- [ ] **Step 4: Commit**

```bash
git add assignment-1/src/assignment/agent/base.py
git commit -m "feat(agent): compact old context into model-generated working memory"
```

---

## Task 8: Run the complete Part 1 suite and verify the diff

**Files:** None (verification only).

- [ ] **Step 1: Run the full Part 1 test file**

```bash
cd assignment-1
uv run pytest tests/test_agent.py tests/test_smoke.py tests/test_infrastructure.py -q
```

Expected: `10 passed` (7 `test_agent.py` + 1 smoke + 2 infrastructure).

- [ ] **Step 2: Confirm the expected Part 3 failures are unchanged**

```bash
uv run pytest -q
```

Expected: the four `tests/test_chess_agent.py` failures remain because Part 3 is not implemented; no `test_agent.py` failures remain. Report the exact count in the final summary.

- [ ] **Step 3: Check the diff for accidental changes**

```bash
cd /home/zhouwenguang/project/cmu-11-768-ai-agents-fall2026
git status --short
git diff --stat main...HEAD
git diff --check
```

Expected: only `src/assignment/agent/base.py`, `src/assignment/agent/code_agent.py`, and the plan file are changed. No `tests/`, `tasks/`, or `chess_app/` changes. No whitespace errors in our files.

- [ ] **Step 4: Commit any final fixes**

If Step 1 or Step 2 required a fix, commit it with a focused message, then rerun Step 1.

---

## Notes for the Implementer

- The provided `format_tool_output` already truncates long values to under 10,000 characters while retaining both ends. Use it for `execute` observations; do not write a second truncation path.
- `Agent.query_language_model` already records `api_prompts` / `api_responses` and increments `steps_taken`. Do not duplicate that bookkeeping.
- `maybe_compact_context` is already implemented and must not be modified. It computes the threshold, calls `compact_context`, and records the event.
- The `finally:` block in `Agent.run` is provided infrastructure. Do not modify it.
- Tool-call IDs can repeat across turns; always link an observation with the `id` from the same assistant message.
- A text-only assistant turn is valid: append it and continue. Do not synthesize an observation.
- `send_message` sets `finished = True`; the loop exits after the current batch of tool calls.
- Do not mention `patch.txt` in the system or task prompt. The `submit-task` skill body is only revealed through `invoke_skill`.
- The `system_information` block must be present verbatim in the `CodeAgent` system prompt, with the four values read from the environment.

## Self-Review

- **Spec coverage:** 1.1.a (state + `build_prompt`, Tasks 2–3), 1.1.b (CodeAgent prompts, Task 4), 1.2 (`run`, Task 3), 1.3 (tool dispatch, Task 5), 1.4 (skills, Task 6). Observation truncation uses the provided `format_tool_output`. The `test_agent.py` compaction test requires 2.1/2.2 hooks; Task 7 implements them. The SWE-bench token-usage experiment and reports remain Part 2 work.
- **Placeholder scan:** No TBD/TODO placeholders; each code step has complete code.
- **Type consistency:** `self.messages`, `self.skills`, `self.system_prompt`, `self.task_prompt`, `self.finished`, `self.steps_taken`, `self.step_limit`, and `self.compaction_*` match the existing `Agent` attributes. Helper names (`_execute_command`, `_send_message`, `_invoke_skill`, `_parse_arguments`, `_tool_error`) are used consistently.
