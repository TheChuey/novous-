---
id: code-planer
name: Coding Planner
description: Plan
mode: chat
model: qwen2.5-coder:latest
environment: codebuilder
version: 1
tools:
  - fm_list_directory
  - fm_read_file
  - fm_write_file
  - list_directory
  - search_workspace
---

# CodePlanner

Plan code

## Available Tools

### fm_list_directory
- Provider: file_manager
- Signature: (path: str = '') -> str
List files and directories under the configured file-manager root using a relative path.

### fm_read_file
- Provider: file_manager
- Signature: (path: str) -> str
Read a UTF-8 file using a path relative to the configured file-manager root.

### fm_write_file
- Provider: file_manager
- Signature: (path: str, content: str) -> str
Write UTF-8 content under the configured file-manager root and return the result as JSON.

### list_directory
- Provider: editor
- Signature: (path: str = '') -> str
List the workspace directory tree (optionally rooted at a relative path). Workspace only; for absolute paths such as C:\... use map_folder.

### search_workspace
- Provider: editor
- Signature: (query: str, extension: str = '.py') -> str
Search workspace files for matching keyword or snippet.
