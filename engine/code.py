"""engine/code.py

The agent runtime: the reusable Agent, the prompt composer, the Ollama
LLM call and the AgentInterface execution seam.

    AgentProfile  - the agent's identity and prompt sections (data)
    Agent        - the generic think / act / observe loop
    PromptManager - definition + tools -> AgentProfile with system prompt
    ask_llm      - structured messages -> the resolved Ollama model
    AgentInterface - build -> replay -> think -> log, plus pipelines

The Agent does not know what KIND of agent it is (research, coding, chat...).
Its behavior comes entirely from its AgentProfile and the tools it was given.

AgentInterface is the single execution seam: every caller (server routers,
headless CLI, test runner) goes through it, so build/think/log behaviour
cannot drift between frontends. It holds configuration only - no
conversation state - so requests stay independent.
"""

from __future__ import annotations

import inspect
import json
import re
from datetime import datetime, timezone
from typing import Any, Callable, List

import ollama
from configuration.interface import resolve_model, supports_tools
from tools.interface import FileSession, append_chat, read_history

from .data import (
    DEFAULT_HISTORY_LIMIT,
    KNOWN_SECTIONS,
    MAX_NUM_CTX,
    AgentProfile,
)
from .helperfunctions import _ollama_tool_schema

__all__ = [
    "Agent",
    "AgentInterface",
    "AgentProfile",
    "PromptManager",
    "ask_llm",
]


# ==========================================================================
# THE GENERIC AGENT OBJECT
# --------------------------------------------------------------------------
# The Agent maintains conversation history and interacts with the LLM
# backend through structured messages. When tools are attached, the LLM
# can request tool calls, which flow through act() -> observe() and a
# follow-up LLM round.
# ==========================================================================

class Agent:
    """A generic AI agent that can think (ask the LLM), act (call a tool) and
    observe (record the tool's result back into the conversation)."""

    def __init__(self, model: str | None, tools: List[Callable], profile: AgentProfile, session: FileSession | None = None):
        """Store the model, tools, profile, and optional FileSession."""
        self.model = model
        self.profile = profile
        self.tools = {
            getattr(f, "name", None) or getattr(f, "__name__"): f
            for f in tools
        }
        self.messages: List[dict] = []
        self.session = session or FileSession()
        self.tool_events: List[dict] = []  # structured tool-execution log for this turn

    def _extract_text_tool_calls(self, content: str) -> List[dict]:
        """Find tool calls that a model wrote as plain-text JSON instead of using
        Ollama's native tool_calls field (a common quirk of small local models).

        Accepts bare JSON, ```json fenced blocks, a JSON object or ARRAY of
        objects embedded in prose, and objects wrapped under keys like
        "tool_calls" / "calls" / "functions". ONLY names present in self.tools
        are returned, and only when the call's required arguments are present
        (so prose that merely mention a tool is never executed).

        Tool-call objects may use "arguments", "args" OR "parameters" as the
        arguments key (small models differ).
        """
        text = (content or "").strip()
        if text.startswith("```"):  # unwrap markdown code fences
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()

        candidates: List[dict] = []
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            parsed = None

        if parsed is not None:
            # Top-level array of calls, object wrapped around a list of calls,
            # or a single call object.
            if isinstance(parsed, list):
                candidates.extend(parsed)
            elif isinstance(parsed, dict):
                found = False
                for wrap_key in ("tool_calls", "calls", "functions", "call"):
                    wrapped = parsed.get(wrap_key)
                    if isinstance(wrapped, list):
                        candidates.extend(wrapped)
                        found = True
                        break
                    if isinstance(wrapped, dict):
                        candidates.append(wrapped)
                        found = True
                        break
                if not found:
                    candidates.append(parsed)
        else:
            # one nesting level allowed so nested "arguments" objects are captured
            for match in re.finditer(r"\{(?:[^{}]|\{[^{}]*\})*\}", content or ""):
                try:
                    candidates.append(json.loads(match.group(0)))
                except json.JSONDecodeError:
                    continue

        calls: List[dict] = []
        for item in candidates:
            if not isinstance(item, dict) or item.get("name") not in self.tools:
                continue
            # Accept "arguments", "args", or "parameters" as the args key.
            args = item.get("arguments", item.get("args", item.get("parameters", {}))) or {}
            args = self._normalize_args(item["name"], args)
            if not self._has_required_args(item["name"], args):
                continue
            calls.append({"function": {"name": item["name"], "arguments": args}})
        return calls

    def _has_required_args(self, name: str, args: dict) -> bool:
        """True when every required (no-default) parameter of the tool is present
        in args. Prevents executing narration that merely mentions a tool."""
        fn = self.tools.get(name)
        if fn is None:
            return False
        args_schema = getattr(fn, "args_schema", None)
        if args_schema is not None:
            required = {
                name for name, field in args_schema.model_fields.items()
                if field.is_required()
            }
            return required.issubset(args.keys())
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return True
        required = {p.name for p in sig.parameters.values() if p.default is inspect.Parameter.empty}
        return required.issubset(args.keys())

    def _normalize_args(self, name: str, args) -> dict:
        """Coerce the many different argument shapes small local models send for
        tool calls into a clean dict of keyword args the tool actually accepts.

        Handles:
            - args as a JSON string: '{"path": "..."}'
            - single-key wrappers:   {"args": {...}}, {"arguments": {...}}
            - positional list:       ["E:\\..."], [name, content, path]
            - string booleans:       {"overwrite": "false"} -> False
            - anything non-dict:     gracefully -> {}
        """
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, TypeError):
                return {}

        if isinstance(args, dict) and len(args) == 1:
            if "args" in args:
                args = args["args"]
            elif "arguments" in args:
                args = args["arguments"]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, TypeError):
                    return {}

        if isinstance(args, list):
            fn = self.tools.get(name)
            if fn is not None:
                try:
                    schema = getattr(fn, "args_schema", None)
                    params = list(schema.model_fields) if schema is not None else [
                        p.name for p in inspect.signature(fn).parameters.values()
                        if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                    ]
                    bound = {}
                    for param, value in zip(params, args):
                        if param not in bound:
                            bound[param] = value
                    bool_params = {
                        field_name for field_name, field in schema.model_fields.items()
                        if field.annotation is bool
                    } if schema is not None else set()
                    return self._coerce_bools(bound, bool_params)
                except (TypeError, ValueError):
                    pass
            return {}

        if not isinstance(args, dict):
            return {}

        # Drop any keys that aren't actual parameters of the tool, so stray
        # keys the model invents (e.g. "path" on a no-arg tool) never crash
        # the call. Tools exposing **kwargs keep everything.
        bool_params = set()
        fn = self.tools.get(name)
        if fn is not None:
            schema = getattr(fn, "args_schema", None)
            if schema is not None:
                valid = set(fn.args)
                args = {k: v for k, v in args.items() if k in valid}
                bool_params = {
                    field_name for field_name, field in schema.model_fields.items()
                    if field.annotation is bool
                }
                return self._coerce_bools(args, bool_params)
            try:
                sig = inspect.signature(fn)
                if not any(
                    p.kind == inspect.Parameter.VAR_KEYWORD
                    for p in sig.parameters.values()
                ):
                    valid = {p.name for p in sig.parameters.values() if p.kind in (
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        inspect.Parameter.KEYWORD_ONLY,
                    )}
                    args = {k: v for k, v in args.items() if k in valid}
                bool_params = {
                    p.name for p in sig.parameters.values() if p.annotation is bool
                }
            except (TypeError, ValueError):
                pass

        return self._coerce_bools(args, bool_params)

    @staticmethod
    def _coerce_bools(args: dict, bool_params: set) -> dict:
        """Turn string 'true'/'false'/'1'/'0' into real bools, but ONLY for
        parameters that are actually typed as bool (so a string param like
        name="yes" is never mangled)."""
        coerced = dict(args)
        for key, value in list(coerced.items()):
            if (
                key in bool_params
                and isinstance(value, str)
                and value.strip().lower() in ("true", "false", "yes", "no", "1", "0")
            ):
                coerced[key] = value.strip().lower() in ("true", "yes", "1")
        return coerced

    MAX_TOOL_ROUNDS = 6
    REPEAT_LIMIT = 3
    _REPEAT_WARNING = (
        "System guard: you have already sent this exact tool call with the "
        "same arguments earlier in this conversation, and it already ran. "
        "Calling it again will not change its result. STOP issuing tool calls "
        "now and answer in plain text, using the tool results you already have."
    )
    _REPEAT_FEEDBACK = (
        "(The agent kept repeating the same tool call and stopped answering "
        "in text. Please rephrase your request or ask again.)"
    )

    @staticmethod
    def _round_signature(tool_calls) -> tuple:
        """Order-independent, hashable fingerprint of one tool round so two
        rounds with the same calls and same arguments compare as identical."""
        normalized = []
        for tool_call in tool_calls:
            fn = tool_call.get("function", {})
            name = str(fn.get("name", ""))
            args = fn.get("arguments", {})
            if isinstance(args, dict):
                items = tuple(sorted((str(k), repr(v)) for k, v in args.items()))
            else:
                items = (repr(args),)
            normalized.append((name, items))
        return tuple(sorted(normalized))

    def think(self, user_input: str) -> str:
        """Add user input to history, send the conversation to the LLM, and return its reply."""
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.profile.system_prompt})

        self._inject_session_context()

        self.messages.append({"role": "user", "content": user_input})

        tool_callables = list(self.tools.values()) if self.tools else None

        message = ask_llm(messages=self.messages, model=self.model, tools=tool_callables)
        self.messages.append(message)

        # Native tool_calls, or calls the model wrote as plain-text JSON.
        # Both paths flow through act()/observe() and a follow-up LLM round.
        # Keep looping while the model keeps issuing tool calls, so a chain of
        # tool calls always ends in a real text reply (never a silent "").
        tool_calls = message.get("tool_calls") or self._extract_text_tool_calls(message.get("content", ""))
        last_signature = None
        repeat_count = 0
        for _ in range(self.MAX_TOOL_ROUNDS):
            if not tool_calls:
                break

            signature = self._round_signature(tool_calls)
            if signature == last_signature:
                repeat_count += 1
            else:
                repeat_count = 1
                last_signature = signature

            if repeat_count >= self.REPEAT_LIMIT:
                print(f"[Agent.think] identical tool round {signature} repeated x{repeat_count}; suppressing.")
                self.messages.append({"role": "user", "content": self._REPEAT_WARNING})
                message = ask_llm(messages=self.messages, model=self.model, tools=tool_callables)
                self.messages.append(message)
                content = (message.get("content", "") or "").strip()
                tool_calls = message.get("tool_calls") or self._extract_text_tool_calls(content)
                if content and not tool_calls:
                    print("[Agent.think] loop suppressed; model answered in text.")
                    return content
                print("[Agent.think] model ignored the loop warning; returning feedback reply.")
                return self._REPEAT_FEEDBACK

            origin = "native tool_calls" if message.get("tool_calls") else "TEXT reply"
            print(f"[Agent.think] Executing {len(tool_calls)} tool call(s) from {origin}.")
            for tool_call in tool_calls:
                result = self.act(tool_call, origin)
                self.observe(tool_call["function"]["name"], result)

            self._inject_session_context()

            message = ask_llm(messages=self.messages, model=self.model, tools=tool_callables)
            self.messages.append(message)
            tool_calls = message.get("tool_calls") or self._extract_text_tool_calls(message.get("content", ""))

        content = message.get("content", "") or ""
        if not content.strip():
            print(f"[Agent.think] No text reply after {self.MAX_TOOL_ROUNDS} tool round(s); returning fallback.")
            return "(I ran my tools but did not produce a final answer. Please ask again.)"
        return content

    _SESSION_CONTEXT_ROLE = "system"
    _SESSION_CONTEXT_PREFIX = "CURRENT FILE SESSION STATE"

    def _inject_session_context(self) -> None:
        """Add current FileSession state as context for the model, replacing any
        previously injected block so history doesn't grow duplicate state."""
        if not self.session:
            return
        state = self.session.get_state()
        if not any(state.values()):
            return
        context_entries = []
        for key, value in state.items():
            if value:
                context_entries.append(f"  {key}: {value}")
        context = f"{self._SESSION_CONTEXT_PREFIX} (from previous tool calls):\n" + "\n".join(context_entries)

        # Replace any earlier context block instead of appending another one.
        for i, message in enumerate(self.messages):
            if (
                message.get("role") == self._SESSION_CONTEXT_ROLE
                and str(message.get("content", "")).startswith(self._SESSION_CONTEXT_PREFIX)
            ):
                self.messages[i]["content"] = context
                return
        self.messages.append({"role": self._SESSION_CONTEXT_ROLE, "content": context})

    @staticmethod
    def _op_succeeded(result) -> tuple[bool, str]:
        """Classify a tool's result as (ok, error_msg).

        Tools report failed OPERATIONS as dicts with success=False or an
        "error" key even when the call itself executed (e.g. read_file on a
        path that does not exist). Execution-level 'success' and operation
        success are different things; the op_ok field records the difference
        so the live feed can flag hallucinated paths instead of showing
        [OK] everywhere.

        The result may arrive as a real dict or as a string representation
        (str(dict) uses single quotes, which is NOT valid JSON - so this
        inspects the object directly and only JSON-parses real JSON strings).
        """
        payload = result
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                return True, ""
        if isinstance(payload, dict):
            if payload.get("success") is False:
                return False, str(payload.get("error") or "operation failed")
            if payload.get("error"):
                return False, str(payload["error"])
        return True, ""

    def act(self, tool_call: dict, origin: str = "") -> str:
        """Run one tool that the LLM asked for, using the name and args it chose."""
        name = tool_call.get("function", {}).get("name")
        args = self._normalize_args(name, tool_call.get("function", {}).get("arguments", {}))
        timestamp = datetime.now().strftime("%H:%M:%S")
        if name in self.tools:
            try:
                tool = self.tools[name]
                raw_result = tool.invoke(args) if hasattr(tool, "invoke") else tool(**args)
                result = str(raw_result)
                print(f"[Agent.act] Executed {name} -> {result[:100]}...")
                op_ok, op_error = self._op_succeeded(raw_result)
                run_event = {
                    "time": timestamp,
                    "tool": name,
                    "args": args,
                    "result_preview": result[:200],
                    "status": "success",
                    "op_ok": op_ok,
                }
                if op_error:
                    run_event["op_error"] = op_error
                self.tool_events.append(run_event)
                self._log_tool_event({
                    **run_event,
                    "origin": origin,
                })
                return result
            except Exception as e:
                print(f"[Agent.act] Error executing {name}: {e}")
                self.tool_events.append({
                    "time": timestamp,
                    "tool": name,
                    "args": args,
                    "error": str(e),
                    "status": "error",
                })
                self._log_tool_event({
                    "time": timestamp,
                    "tool": name,
                    "args": args,
                    "error": str(e),
                    "status": "error",
                    "origin": origin,
                })
                return f"Error executing tool: {e}"
        print(f"[Agent.act] Missing tool requested: {name}")
        self.tool_events.append({
            "time": timestamp,
            "tool": name,
            "args": args,
            "status": "missing",
        })
        self._log_tool_event({
            "time": timestamp,
            "tool": name,
            "args": args,
            "status": "missing",
            "origin": origin,
        })
        return f"Error: {name} missing"

    def _log_tool_event(self, event: dict) -> None:
        """Report one structured tool event to the process-wide tool log
        (data/toollog/tool_usage.jsonl). Deliberately fail-safe so a
        logging problem can never break the tool call that just succeeded."""
        event.setdefault("agentId", self.profile.id or "")
        event.setdefault("agentName", self.profile.name or "")
        event.setdefault("model", self.model or "")
        event["time"] = datetime.now().isoformat(timespec="seconds")
        try:
            from tools.interface import append_tool_event

            append_tool_event(event)
        except Exception:
            pass

    def observe(self, name: str, result: str) -> None:
        """Record a tool's result back into the conversation history."""
        self.messages.append({"role": "tool", "content": result, "name": name})


# ==========================================================================
# PROMPT COMPOSITION
# ==========================================================================

class PromptManager:
    """Builds an AgentProfile from an agent definition and composes the system prompt."""

    @staticmethod
    def build(definition: dict, tools: List[Callable] | None = None) -> AgentProfile:
        """Build an AgentProfile.

        Args:
            definition: {"meta": {...agent.json...}, "sections": {...parsed agent.md...}}
            tools:      resolved tool functions; their docstrings become the
                        AVAILABLE TOOLS section of the prompt.

        Steps:
            1. Map metadata and markdown sections onto the profile fields
            2. Collect unknown sections as extras
            3. Compose the system prompt
        """
        meta = definition.get("meta", {})
        sections = {k.lower().strip(): v for k, v in definition.get("sections", {}).items()}

        known = {name: sections.get(name, "") for name in KNOWN_SECTIONS}
        extras = {
            name: content for name, content in sections.items()
            if name not in KNOWN_SECTIONS and name not in ("skills", "identity")
        }

        profile = AgentProfile(
            id=meta.get("id", ""),
            name=meta.get("name", ""),
            description=meta.get("description", ""),
            mode=meta.get("mode", "chat"),
            **known,
            extras=extras,
        )
        profile.system_prompt = PromptManager.compose_system_prompt(profile, tools)
        return profile

    @staticmethod
    def compose_system_prompt(profile: AgentProfile, tools: List[Callable] | None = None) -> str:
        """Build the final system prompt from profile sections."""
        parts = []

        if profile.role:
            parts.append(f"ROLE\n{profile.role}")

        if profile.purpose:
            parts.append(f"PURPOSE\n{profile.purpose}")

        if profile.personality:
            parts.append(f"PERSONALITY\n{profile.personality}")

        if profile.boundaries:
            parts.append(f"BOUNDARIES\n{profile.boundaries}")

        if profile.communication:
            parts.append(f"COMMUNICATION STYLE\n{profile.communication}")

        if profile.principles:
            parts.append(f"PRINCIPLES\n{profile.principles}")

        if profile.decision_style:
            parts.append(f"DECISION STYLE\n{profile.decision_style}")

        tool_lines = PromptManager._tool_lines(tools)
        if tool_lines:
            parts.append("AVAILABLE TOOLS\n" + "\n".join(tool_lines))

        # Generic extra sections (user, greeting, project_notes, ...) become
        # UPPERCASE-titled blocks, sorted for deterministic prompts.
        for title, content in sorted(profile.extras.items()):
            if content:
                parts.append(f"{title.upper()}\n{content}")

        return "\n\n".join(parts)

    @staticmethod
    def _tool_lines(tools: List[Callable] | None) -> List[str]:
        """Format tool callables as '- id: first docstring line' lines."""
        lines = []
        for fn in tools or []:
            doc = (getattr(fn, "description", None) or fn.__doc__ or "").strip()
            summary = doc.splitlines()[0] if doc else ""
            name = getattr(fn, "name", None) or getattr(fn, "__name__")
            lines.append(f"- {name}: {summary}")
        return lines


# ==========================================================================
# THE LLM CALL
# ==========================================================================

def _get_context_window(model: str) -> int | None:
    """Return the model's max context length from Ollama, capped; None if unknown."""
    try:
        info = ollama.show(model=model).model_dump()
        model_info = info.get("modelinfo") or info.get("model_info") or {}
        length = model_info.get("llama.context_length")
        if not length:
            return None
        return min(int(length), MAX_NUM_CTX)
    except Exception as exc:
        print(f"[ask_llm] context lookup failed for {model}: {exc}")
        return None


def ask_llm(messages: List[dict], model: str | None = None, tools: List[Callable] | None = None) -> dict:
    """Send structured messages to the resolved model via Ollama and return the full message dict."""
    resolved = resolve_model(model, require_tools=bool(tools))

    # A model Ollama reports as NOT supporting tools must not be asked to
    # (Ollama rejects the request with 400) - drop the tool schemas and let
    # the agent answer without tool use rather than crash the chat.
    if tools and supports_tools(resolved) is False:
        print(f"[ask_llm] model '{resolved}' does not support tools - continuing without tool use")
        tools = None

    num_ctx = _get_context_window(resolved)

    options = {"num_ctx": num_ctx} if num_ctx else {}
    print(f"[ask_llm] calling ollama.chat with model={resolved} num_ctx={num_ctx} tools={len(tools) if tools else 0}")

    for attempt in (1, 2):
        kwargs = {
            "model": resolved,
            "messages": messages,
            "options": options,
        }
        if tools:
            kwargs["tools"] = [
                _ollama_tool_schema(tool) if hasattr(tool, "args_schema") else tool
                for tool in tools
            ]

        response = ollama.chat(**kwargs)
        message = response["message"]

        content = message.get("content", "") or ""
        tool_calls = message.get("tool_calls") or []

        print(f"[ask_llm] reply received ({len(content)} chars, {len(tool_calls)} tool calls)")

        if content.strip() or tool_calls:
            return message

        print(f"[ask_llm] empty reply on attempt {attempt} - retrying")

    return {"role": "assistant", "content": "(The model returned an empty reply. Please try again.)"}


# ==========================================================================
# HISTORY
# ==========================================================================

def _as_history(
    agent_id: str | None,
    limit: int | None = DEFAULT_HISTORY_LIMIT,
) -> list[dict] | None:
    """Read one agent's recent turns from the chat log as model messages.

    Scoped by agent id so agents never see each other's conversations.
    Returns None (meaning "no history") when logging is unavailable or
    limit is falsy, so a broken log never blocks a conversation.
    """
    if not limit or limit <= 0:
        return None
    try:
        entries = read_history(limit=limit, agent=agent_id)
    except Exception as exc:  # pragma: no cover - logging must not break runs
        print(f"[INTERFACE] history unavailable: {exc}")
        return None

    history: list[dict] = []
    for entry in entries:
        sender = str(entry.get("sender", ""))
        content = str(entry.get("message", "") or "")
        if not content:
            continue
        history.append({
            "role": "assistant" if sender in ("agent", "ai") else "user",
            "content": content,
        })
    return history or None


# ==========================================================================
# THE EXECUTION SEAM
# ==========================================================================

class AgentInterface:
    """Thin, stable API over the build/think loop and pipeline chain."""

    def __init__(
        self,
        bridge: Any = None,
        model: str | None = None,
        log_sink: Callable[[dict], None] | None = None,
    ) -> None:
        """Create a runner.

        Args:
            bridge:   optional Project Manager provider (ProjectManagerBridge
                      or DirectProjectIO). When present, the file tools route
                      through the Project Manager filesystem.
            model:    optional default model override for every run.
            log_sink: optional callback receiving every chat log entry as it
                      is written, so a host can mirror the log elsewhere.
        """
        self.bridge = bridge
        self.model = model
        self.log_sink = log_sink

    # ============================================================
    # INTERNAL
    # ============================================================

    def _log(self, sender: str, message: str, agent_id: str) -> dict:
        """Write one chat log entry and hand it to the sink."""
        entry = append_chat(sender, message, agent=agent_id)
        if self.log_sink is not None:
            try:
                self.log_sink(entry)
            except Exception as exc:  # pragma: no cover - sink must not break runs
                print(f"[INTERFACE] log sink failed: {exc}")
        return entry

    def _think(
        self,
        agent: Any,
        message: str,
        agent_id: str,
        history: list[dict] | None,
        persist: bool = True,
    ) -> tuple[str, list[dict]]:
        """Replay history, run one turn, and optionally log both sides.

        One place for the build-think-log order, so chat, single-agent
        and pipeline runs behave identically. The current turn is not in
        ``history``.
        """
        if history:
            from agents.interface import replay_history

            replay_history(agent, history)
        reply = agent.think(message)
        if not persist:
            now = datetime.now(timezone.utc).isoformat()
            return reply, [
                {"ts": now, "sender": "user", "message": message, "agent": agent_id},
                {"ts": now, "sender": "agent", "message": reply, "agent": agent_id},
            ]
        entries = [
            self._log("user", message, agent_id),
            self._log("agent", reply, agent_id),
        ]
        return reply, entries

    # ============================================================
    # CHAT (one agent, resolved by id)
    # ============================================================

    def run_chat(
        self,
        message: str,
        agent_id: str | None = None,
        model: str | None = None,
        history: list[dict] | None = None,
        use_logged_history: bool = True,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run one agent and return its reply.

        agent_id is resolved through the agent roots, so an agent created
        in the Project Manager works exactly like a bundled library agent.
        With no agent_id the first discovered agent is used.

        Args:
            history: explicit prior turns ({role, content}). When None and
                ``use_logged_history`` is set, this agent's own log history
                is replayed (the current turn is logged after the model has
                answered).
            persist: write the turn to the headless chat log. Browser chat
                sessions pass False and own persistence in saved text files.
        Returns {"reply", "agent_id", "name", "model", "tool_events",
        "entries"}.
        """
        from agents.interface import build_agent

        resolved_id = agent_id or self._default_agent_id()
        agent = build_agent(resolved_id, model=model or self.model, bridge=self.bridge)

        if history is None and use_logged_history:
            history = _as_history(resolved_id, DEFAULT_HISTORY_LIMIT)

        reply, entries = self._think(
            agent, message, resolved_id, history, persist=persist
        )

        return {
            "reply": reply,
            "agent_id": resolved_id,
            "name": agent.profile.name,
            "model": agent.model,
            "tool_events": agent.tool_events,
            "entries": entries,
        }

    # ============================================================
    # SINGLE AGENT (explicit definition, or by id)
    # ============================================================

    def run_single_agent(
        self,
        user_input: str,
        json_path: str | None = None,
        md_path: str | None = None,
        agent_id: str | None = None,
        model: str | None = None,
        history: list[dict] | None = None,
        use_logged_history: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run one agent built from explicit agent.json + agent.md paths.

        This is the headless construction path: the definition can live
        anywhere, not only inside a registered root. When json_path/md_path
        are omitted the agent is resolved by ``agent_id`` instead.

        ``persist`` controls whether the turn is written to the chat log.

        Returns {"reply", "agent_id", "model", "tool_events", "name",
        "description", "entries"}.
        """
        from agents.interface import build_agent, build_agent_from_definition

        if json_path and md_path:
            agent = build_agent_from_definition(
                json_path,
                md_path,
                model=model or self.model,
                bridge=self.bridge,
            )
            # A definition loaded from an explicit path may be outside any
            # registered root; use its own id so history stays per-agent.
            resolved_id = str(agent.profile.id)
        elif agent_id:
            resolved_id = agent_id
            agent = build_agent(
                agent_id,
                model=model or self.model,
                bridge=self.bridge,
            )
        else:
            raise ValueError(
                "Provide json_path + md_path, or an agent_id, to run."
            )

        if history is None and use_logged_history:
            history = _as_history(resolved_id, DEFAULT_HISTORY_LIMIT)

        reply, entries = self._think(
            agent, user_input, resolved_id, history, persist=persist
        )

        return {
            "reply": reply,
            "agent_id": resolved_id,
            "name": agent.profile.name,
            "description": agent.profile.description,
            "model": agent.model,
            "tool_events": agent.tool_events,
            "entries": entries,
        }

    # ============================================================
    # PIPELINE
    # ============================================================

    def run_pipeline(
        self,
        user_input: str,
        agent_configs: list | None = None,
        model: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run the ordered agent chain (feed-forward).

        Args:
            agent_configs:
                None  -> load steps from the default pipeline config.
                list  -> each element is either an agent id (str) or a dict with
                         "json_path" + "md_path" (ad-hoc step agents).
            persist: whether to write the exchange to the chat log.

        Returns:
            {"reply", "outputs": [...step outputs...], "tool_events",
             "model", "entries"}.
        """
        from pipelines.interface import run_pipeline as _run_pipeline

        result = _run_pipeline(
            user_input,
            model=model or self.model,
            steps=agent_configs,
            bridge=self.bridge,
        )
        if persist:
            # A cascade is not one agent, so log it untagged rather than
            # attribute it to whichever step happened to run first.
            result["entries"] = [
                self._log("user", user_input, None),
                self._log("agent", result["reply"], None),
            ]
        else:
            now = datetime.now(timezone.utc).isoformat()
            result["entries"] = [
                {"ts": now, "sender": "user", "message": user_input},
                {"ts": now, "sender": "agent", "message": result["reply"]},
            ]
        result["model"] = model or self.model
        return result

    # ============================================================
    # UTILITIES
    # ============================================================

    def _default_agent_id(self) -> str:
        agents = self.list_agents()
        if not agents:
            raise RuntimeError(
                "No agents are registered. Register an agent root "
                "(see agents.interface.register_agent_root) and check that "
                "<id>/agent.json exists in it."
            )
        return agents[0]["id"]

    def list_agents(self) -> list[dict]:
        """Every agent across every registered root (see the registry)."""
        from agents.interface import list_agents

        return list_agents()

    def get_agent(self, agent_id: str) -> dict | None:
        """Metadata for one agent id, or None when it is not registered."""
        from agents.interface import get_agent_meta

        return get_agent_meta(agent_id)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        bridge = getattr(self.bridge, "expose", lambda: None)()
        return (
            f"<AgentInterface model={self.model!r} "
            f"bridge={json.dumps(bridge or {}, default=str) or 'local disk'}>"
        )
