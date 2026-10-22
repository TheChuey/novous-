---
title: Available Tools
---

### read_agent_memory
- Provider: agentMemory
- Signature: (memory_type: str = 'all') -> str
Read the latest file content copied by read_file and/or the latest directory map copied by map_files.
Call this tool when the user asks for the latest file content or directory map.

### search_knowledge_base
- Provider: agentMemory
- Signature: (query: str, top_k: int = 5) -> str
Search documents in workspace/Knowledge Base using semantic Ollama embeddings; returns passages with source paths and similarity scores.
Call this tool when the user asks a question that requires information from the workspace knowledge base.

### list_knowledge_documents
- Provider: agentMemory
- Signature: () -> str
List documents currently indexed in the semantic Knowledge Base.
Call this tool when the user asks to list the available documents in the Knowledge Base.

### delete_file
- Provider: tools
- Signature: (path: str) -> str
Delete a file or directory from the workspace by relative path.
Call this tool when the user requests to delete a file or directory.

### read_file
- Provider: tools
- Signature: (path: str, request: str = '') -> str
Read a UTF-8 text or Docling-supported document from the configured file-manager root. PDF, DOCX, PPTX, and ODT documents are text-extracted with Docling; OCR is enabled for PDFs to support scanned pages. Text files are limited to 1 MB; documents to 25 MB and 1 MB of extracted text. Successful reads are mirrored to agent memory. Returns JSON with the request, path, content, and scratchpad context.
Call this tool when the user asks to read the content of a file.

### write_file
- Provider: tools
- Signature: (path: str, content: str) -> str
Write UTF-8 content to a workspace file by relative path (bare filenames go in the root). Overwrites existing files and creates missing parent directories. Supports formats such as .txt, .md, .py, .json, .html, .css, and .js. Returns JSON with the resolved path and bytes written.
Call this tool when the user asks to create or write content to a file.

### editor
- Provider: editor
- Signature: (action: str, path: str = '', content: str = '') -> str
Read, write, list a tree, or delete a path through the editor pillar.
Call this tool when the user requests complex file path manipulation, reading/writing specific file contents, or listing the directory tree.

### map_files
- Provider: file_manager
- Signature: (path: str = '') -> str
Return a directory tree and save a copy in the shared agent-memory scratchpad.
Call this tool when the user requests to view the directory structure of a location.
