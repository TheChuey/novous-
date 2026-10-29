"""Safe code-change previews for orchestration traces."""

from difflib import SequenceMatcher

from file_manager import backend

_MAX_PREVIEW_CONTENT_BYTES = 1_000_000
_MAX_HIGHLIGHTED_LINES = 120


def changed_line_numbers(before: str, after: str, basis: str) -> list[int]:
    """Return bounded 1-based changed lines in either the old or proposed content."""
    if basis not in {"before", "after"}:
        raise ValueError("Diff basis must be 'before' or 'after'.")
    old_lines = before.splitlines()
    new_lines = after.splitlines()
    if max(len(old_lines), len(new_lines)) > 5_000:
        raise ValueError("Code preview files cannot exceed 5,000 lines.")
    changed = set()
    for operation, old_start, old_end, new_start, new_end in SequenceMatcher(
        a=old_lines, b=new_lines, autojunk=False
    ).get_opcodes():
        if operation == "equal":
            continue
        lines, start, end = (
            (old_lines, old_start, old_end)
            if basis == "before"
            else (new_lines, new_start, new_end)
        )
        if start == end:
            anchor = start if basis == "before" else start + 1
            changed.add(max(1, min(anchor, len(lines))))
        else:
            changed.update(range(start + 1, end + 1))
        if len(changed) >= _MAX_HIGHLIGHTED_LINES:
            break
    return sorted(changed)[:_MAX_HIGHLIGHTED_LINES]


def _read_current_file(path: str) -> tuple[str, str, bool]:
    if not isinstance(path, str) or not path.strip() or len(path) > 512:
        raise ValueError("Provide a workspace-relative file path of at most 512 characters.")
    resolved = backend.resolve_workspace_path(path.strip())
    relative_path = resolved.relative_to(backend.workspace_root()).as_posix()
    if resolved.exists() and not resolved.is_file():
        raise IsADirectoryError(f"Code preview target is not a file: {relative_path}")
    exists = resolved.is_file()
    if exists and resolved.stat().st_size > _MAX_PREVIEW_CONTENT_BYTES:
        raise ValueError("The existing file exceeds the 1 MB code preview limit.")
    current = resolved.read_text(encoding="utf-8") if exists else ""
    return relative_path, current, exists


def _publish_change_event(
    event_type: str, relative_path: str, lines: list[int], file_exists: bool
) -> None:
    from orchestration.orchestration_telemetry import telemetry_bus

    context = telemetry_bus.current_context()
    if context is None:
        return
    trace_id, agent_id = context
    telemetry_bus.log_event(
        trace_id,
        event_type,
        agent_id,
        "editor",
        {
            "path": relative_path,
            "changed_lines": lines,
            "file_exists": file_exists,
        },
    )


def preview_code_change(path: str, proposed_content: str) -> dict:
    """Compare proposed code with the current workspace file and notify the editor."""
    if not isinstance(proposed_content, str):
        raise ValueError("Proposed file content must be text.")
    if len(proposed_content.encode("utf-8")) > _MAX_PREVIEW_CONTENT_BYTES:
        raise ValueError("Code preview content exceeds the 1 MB code preview limit.")
    relative_path, current, exists = _read_current_file(path)
    lines = changed_line_numbers(current, proposed_content, "before")
    _publish_change_event("CODE_CHANGE_PREVIEW", relative_path, lines, exists)
    return {
        "status": "success" if lines else "nothing_found",
        "path": relative_path,
        "changed_lines": lines,
        "file_exists": exists,
    }


def record_applied_code_change(
    relative_path: str, previous_content: str, written_content: str
) -> None:
    """Publish changed line numbers after a workspace file write succeeds."""
    lines = changed_line_numbers(previous_content, written_content, "after")
    from orchestration.codebuilder_run_state import codebuilder_run_state
    from orchestration.orchestration_telemetry import telemetry_bus

    context = telemetry_bus.current_context()
    if context is not None:
        codebuilder_run_state.save_workspace_source(
            context[0], relative_path, written_content
        )
    _publish_change_event("CODE_CHANGE_APPLIED", relative_path, lines, True)
