---
title: Skill ask_user_questions
---

## Skill: ask_user_questions

When additional user information is required to identify a problem, create a valid JSON file containing the necessary questions and save it inside the workspace. Call `ask_user_questions(json_file_path, timeout_seconds=300.0)` using a workspace-root-relative path without the `workspace/` prefix. The tool pauses the agent until the user submits their answers and returns them as a JSON string. Parse and evaluate the returned answers, update the investigation's evidence and hypotheses, and continue asking targeted questions as needed. Treat answers as user-reported information, not independently verified facts, and never invent missing answers or tool results.
