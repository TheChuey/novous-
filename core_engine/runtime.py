import json
import inspect
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

    def act(self, tool_call: dict, origin: str) -> Any:
        fn_info = tool_call.get("function", {})
        name = fn_info.get("name")
        args = fn_info.get("arguments", {})

        if name not in self.tools:
            return f"Error: Tool '{name}' not found."

        stats = self.tool_stats.setdefault(
            name, {"calls": 0, "successes": 0, "errors": 0, "success_rate": 0.0}
        )
        stats["calls"] += 1

        tool_func = self.tools[name]
        try:
            if isinstance(args, str):
                args = json.loads(args)
            result = tool_func(**args) if isinstance(args, dict) else tool_func(args)
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
            return result
        except Exception as exc:
            stats["errors"] += 1
            stats["success_rate"] = stats["successes"] / stats["calls"]
            err_msg = f"Error executing tool '{name}': {str(exc)}"
            self.tool_events.append({"tool": name, "args": args, "status": "error", "error": str(exc), "origin": origin})
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
            for call in tool_calls:
                name = call["function"]["name"]
                before = len(self.tool_events)
                result = self.act(call, origin)
                self.observe(name, result)
                for event in self.tool_events[before:]:
                    yield {"type": "tool_event", "event": event}
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
