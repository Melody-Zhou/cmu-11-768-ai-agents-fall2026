"""The Part 1 coding agent: fix a software issue and submit a git patch."""

from __future__ import annotations

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

class CodeAgent(Agent):
    """An agent that fixes a software issue and submits a git patch."""

    def __init__(
        self,
        task: str,
        environment: Environment,
        model: str | None = None,
        logs_save_path: str | None = None,
        step_limit: int = 100,
        skills_path: str | None = None,
        auto_stop_environment: bool = True,
        compact_threshold_tokens: int | None = None,
        compaction_keep_recent_steps: int = DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
        compaction_max_tokens: int = DEFAULT_COMPACTION_MAX_TOKENS,
    ):
        super().__init__(
            environment=environment,
            model=model,
            logs_save_path=logs_save_path,
            step_limit=step_limit,
            skills_path=skills_path,
            auto_stop_environment=auto_stop_environment,
            compact_threshold_tokens=compact_threshold_tokens,
            compaction_keep_recent_steps=compaction_keep_recent_steps,
            compaction_max_tokens=compaction_max_tokens,
        )
        self.task = task
        self.submitted_patch = ""

        # `Agent.__init__` has already loaded skills and registered
        # `invoke_skill` when a catalog exists; add the coding tools after it.
        self.tools.extend([EXECUTE_TOOL, SEND_MESSAGE_TOOL])

        self.system_prompt = self._build_system_prompt()
        self.task_prompt = self._build_task_prompt()

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
