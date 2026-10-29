import json
import inspect
import time
from dataclasses import dataclass, field
from typing import Callable, List, Any
import ollama

MAX_NUM_CTX = 32768

@dataclass
class AgentProfile:
    id: str = ""
    name: str = ""
    description: str = ""
    mode: str = "chat"  # "agent" attaches tools; "chat" takes none
    system_prompt: str = ""
    role: str = ""
    purpose: str = ""
    boundaries: str = ""
    model: str = ""
    tools: List[str] = field(default_factory=list)
    extras: dict = field(default_factory=dict)

class Agent:
    MAX_TOOL_ROUNDS = 6

    def __init__(self, model: str | None, tools: List[Callable], profile: AgentProfile, session=None):
        self.model = model or profile.model or "qwen2.5-coder:latest"
        self.profile = profile
        self.tools = {getattr(f, "name", None) or f.__name__: f for f in (tools or [])}
        self.messages: List[dict] = []
        self.session = session
        self.tool_events: List[dict] = []
        self.tool_stats: dict[str, dict] = {}

    def _extract_text_tool_calls(self, content: str) -> List[dict]:
        text = (content or "").strip()
        calls = []
        decoder = json.JSONDecoder()
        index = 0
        while index < len(text):
            if text[index] not in "[{":
                index += 1
                continue
            try:
                parsed, end = decoder.raw_decode(text, index)
            except json.JSONDecodeError:
                index += 1
                continue

            items = parsed if isinstance(parsed, list) else [parsed]
            found_call = False
            for item in items:
                if not isinstance(item, dict):
                    continue
                tool_name = item.get("name")
                if tool_name not in self.tools:
                    continue
                args = (
                    item.get("parameters")
                    or item.get("arguments")
                    or item.get("args")
                    or {}
                )
                calls.append(
                    {"function": {"name": tool_name, "arguments": args}}
                )
                found_call = True

            index = end if found_call else index + 1
        return calls

    def _format_rag_presenter_reply(self, content: str) -> str:
        if self.profile.id != "rag-presenter":
            return content
        decoder = json.JSONDecoder()
        index = 0
        while index < len(content):
            if content[index] != "{":
                index += 1
                continue
            try:
                parsed, end = decoder.raw_decode(content, index)
            except json.JSONDecodeError:
                index += 1
                continue
            index = end
            if not isinstance(parsed, dict) or parsed.get("name") != "format_answer":
                continue

            arguments = parsed.get("parameters") or parsed.get("arguments") or {}
            if not isinstance(arguments, dict):
                continue
            answer = str(arguments.get("answer") or "").strip()
            if not answer:
                continue

            formatted = answer
            evidence = arguments.get("evidence")
            sources = []
            if isinstance(evidence, list):
                for item in evidence:
                    if isinstance(item, dict) and item.get("path"):
                        path = str(item["path"])
                        if path not in sources:
                            sources.append(path)
            if sources:
                formatted += "\n\n**Sources**\n" + "\n".join(
                    f"- {source}" for source in sources
                )
            return formatted
        return content

    def _is_code_subagent_handoff(self, tool_name: str) -> bool:
        return (
            tool_name == "write_agent_scratchpad"
            and self.profile.id
            in {"code-builder", "tester", "code-troubleshooter"}
        )

    def act(self, tool_call: dict, origin: str) -> Any:
        fn_info = tool_call.get("function", {})
        name = fn_info.get("name")
        args = fn_info.get("arguments", {})

        if name not in self.tools:
            from orchestration.orchestration_telemetry import telemetry_bus

            trace_context = telemetry_bus.current_context()
            if trace_context:
                trace_id, agent_id = trace_context
                telemetry_bus.log_event(
                    trace_id,
                    "TOOL_CALL_END",
                    name or "unknown",
                    agent_id,
                    {
                        "tool_name": name or "unknown",
                        "status": "error",
                        "duration_ms": 0,
                    },
                )
            return f"Error: Tool '{name}' not found."

        stats = self.tool_stats.setdefault(
            name, {"calls": 0, "successes": 0, "errors": 0, "success_rate": 0.0}
        )
        stats["calls"] += 1

        tool_func = self.tools[name]
        from orchestration.orchestration_telemetry import telemetry_bus

        trace_context = telemetry_bus.current_context()
        started = time.perf_counter()
        if trace_context:
            trace_id, agent_id = trace_context
            telemetry_bus.log_event(
                trace_id,
                "TOOL_CALL_START",
                agent_id,
                name,
                {"tool_name": name},
            )
        try:
            if isinstance(args, str):
                args = json.loads(args)
            result = tool_func(**args) if isinstance(args, dict) else tool_func(args)
            if self._is_code_subagent_handoff(name) and trace_context:
                from orchestration.codebuilder_run_state import codebuilder_run_state

                trace_id, agent_id = trace_context
                task_types = {
                    "code-builder": "code_build",
                    "tester": "code_test",
                    "code-troubleshooter": "code_troubleshooting",
                }
                payload = args.get("payload", "") if isinstance(args, dict) else ""
                if isinstance(payload, str) and payload.strip().startswith(("{", "[")):
                    try:
                        payload = json.loads(payload)
                    except json.JSONDecodeError:
                        pass
                codebuilder_run_state.save_handoff(
                    trace_id,
                    agent_id,
                    task_types[agent_id],
                    str(args.get("status", "success"))
                    if isinstance(args, dict)
                    else "success",
                    payload,
                )
            stats["successes"] += 1
            stats["success_rate"] = stats["successes"] / stats["calls"]
            event = {"tool": name, "args": args, "status": "success", "origin": origin}
            result_text = result if isinstance(result, str) else json.dumps(
                result, ensure_ascii=False, default=str
            )
            event["result"] = result_text[:3000]
            if len(result_text) > 3000:
                event["result_truncated"] = True
            if getattr(tool_func, "display_output", False) and isinstance(result, str):
                event["display"] = result
            self.tool_events.append(event)
            if trace_context:
                telemetry_bus.log_event(
                    trace_id,
                    "TOOL_CALL_END",
                    name,
                    agent_id,
                    {
                        "tool_name": name,
                        "status": "success",
                        "duration_ms": int((time.perf_counter() - started) * 1000),
                    },
                )
                if name in {"write_agent_scratchpad", "read_agent_scratchpad"}:
                    handoff = {}
                    if name == "write_agent_scratchpad":
                        handoff = {
                            "status": args.get("status", "success")
                            if isinstance(args, dict)
                            else "success",
                            "subagent_id": args.get("subagent_id", "")
                            if isinstance(args, dict)
                            else "",
                            "direction": "write",
                        }
                        payload = args.get("payload") if isinstance(args, dict) else None
                        try:
                            if isinstance(payload, str):
                                payload = json.loads(payload)
                        except json.JSONDecodeError:
                            payload = None
                        if isinstance(payload, dict):
                            for key in ("results", "issues_found"):
                                if isinstance(payload.get(key), list):
                                    handoff["result_count"] = len(payload[key])
                                    break
                    else:
                        try:
                            memory = json.loads(result) if isinstance(result, str) else {}
                        except json.JSONDecodeError:
                            memory = {}
                        latest = memory.get("latest_subagent_result", {})
                        payload = latest.get("payload", {}) if isinstance(latest, dict) else {}
                        handoff = {
                            "status": latest.get("status", "success")
                            if isinstance(latest, dict)
                            else "success",
                            "subagent_id": latest.get("subagent_id", "")
                            if isinstance(latest, dict)
                            else "",
                            "direction": "read",
                        }
                        if isinstance(payload, dict):
                            for key in ("results", "issues_found"):
                                if isinstance(payload.get(key), list):
                                    handoff["result_count"] = len(payload[key])
                                    break
                    telemetry_bus.log_event(
                        trace_id,
                        "SCRATCHPAD_HANDOFF",
                        agent_id,
                        "scratchpad",
                        handoff,
                    )
            return result
        except Exception as exc:
            stats["errors"] += 1
            stats["success_rate"] = stats["successes"] / stats["calls"]
            err_msg = f"Error executing tool '{name}': {str(exc)}"
            self.tool_events.append({"tool": name, "args": args, "status": "error", "error": str(exc), "origin": origin})
            if trace_context:
                telemetry_bus.log_event(
                    trace_id,
                    "TOOL_CALL_END",
                    name,
                    agent_id,
                    {
                        "tool_name": name,
                        "status": "error",
                        "duration_ms": int((time.perf_counter() - started) * 1000),
                    },
                )
                if name == "write_agent_scratchpad":
                    telemetry_bus.log_event(
                        trace_id,
                        "SCRATCHPAD_HANDOFF",
                        agent_id,
                        "scratchpad",
                        {
                            "status": "error",
                            "subagent_id": args.get("subagent_id", "")
                            if isinstance(args, dict)
                            else "",
                            "direction": "write",
                        },
                    )
            return err_msg

    def observe(self, tool_name: str, result: Any) -> None:
        content = json.dumps(result) if not isinstance(result, str) else result
        self.messages.append({"role": "tool", "name": tool_name, "content": content})

    def think(self, user_input: str) -> str:
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.profile.system_prompt})

        self.messages.append({"role": "user", "content": user_input})

        if self.profile.mode == "chat" or not self.tools:
            res = ollama.chat(model=self.model, messages=self.messages, options={"num_ctx": MAX_NUM_CTX})
            reply = self._format_rag_presenter_reply(res["message"]["content"])
            self.messages.append({"role": "assistant", "content": reply})
            return reply

        for _ in range(self.MAX_TOOL_ROUNDS):
            res = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=[self._ollama_schema(t) for t in self.tools.values()],
                options={"num_ctx": MAX_NUM_CTX}
            )
            msg = res["message"]
            self.messages.append(msg)

            native_calls = msg.get("tool_calls")
            text_calls = self._extract_text_tool_calls(msg.get("content", "")) if not native_calls else []
            tool_calls = native_calls or text_calls

            if not tool_calls:
                return self._format_rag_presenter_reply(msg.get("content", ""))

            origin = "native" if native_calls else "text_json"
            for call in tool_calls:
                tool_name = call["function"]["name"]
                result = self.act(call, origin)
                self.observe(tool_name, result)
                if self._is_code_subagent_handoff(tool_name):
                    if isinstance(result, str) and result.startswith("Error executing tool"):
                        return result
                    return "Code sub-agent scratchpad handoff recorded."

        return "(Executed maximum tool rounds without final text summary.)"

    def think_stream(self, user_input: str):
        """Like think(), but yields token / tool_event dicts as they happen."""
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.profile.system_prompt})
        self.messages.append({"role": "user", "content": user_input})

        use_tools = self.profile.mode != "chat" and bool(self.tools)
        extra = {"tools": [self._ollama_schema(t) for t in self.tools.values()]} if use_tools else {}
        final_text = ""

        for _ in range(self.MAX_TOOL_ROUNDS if use_tools else 1):
            content = ""
            native_calls: List[dict] = []
            for chunk in ollama.chat(model=self.model, messages=self.messages, stream=True,
                                     options={"num_ctx": MAX_NUM_CTX}, **extra):
                msg = chunk["message"]
                piece = msg.get("content") or ""
                if piece:
                    content += piece
                for call in msg.get("tool_calls") or []:
                    native_calls.append(call)

            assistant = {"role": "assistant", "content": content}
            if native_calls:
                assistant["tool_calls"] = native_calls
            self.messages.append(assistant)
            final_text = content

            text_calls = [] if native_calls or not use_tools else self._extract_text_tool_calls(content)
            tool_calls = native_calls or text_calls
            if not tool_calls:
                if content:
                    content = self._format_rag_presenter_reply(content)
                    self.messages[-1]["content"] = content
                    final_text = content
                    yield {"type": "token", "text": content}
                break

            origin = "native" if native_calls else "text_json"
            handoff_attempted = False
            for call in tool_calls:
                name = call["function"]["name"]
                before = len(self.tool_events)
                result = self.act(call, origin)
                self.observe(name, result)
                for event in self.tool_events[before:]:
                    yield {"type": "tool_event", "event": event}
                if self._is_code_subagent_handoff(name):
                    final_text = (
                        result
                        if isinstance(result, str)
                        and result.startswith("Error executing tool")
                        else "Code sub-agent scratchpad handoff recorded."
                    )
                    handoff_attempted = True
                    break
            if handoff_attempted:
                break
        else:
            final_text = "(Executed maximum tool rounds without final text summary.)"

        yield {"type": "done", "reply": final_text}

    def _ollama_schema(self, func: Callable) -> dict:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            properties[param_name] = {"type": "string", "description": f"Parameter {param_name}"}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        return {
            "type": "function",
            "function": {
                "name": getattr(func, "name", None) or func.__name__,
                "description": doc.splitlines()[0] if doc else "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
