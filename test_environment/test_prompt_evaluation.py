from test_environment.test_runner import run_prompt_component_tests


def test_prompt_evaluation_reports_each_component():
    report = run_prompt_component_tests(
        "Workspace Research Assistant",
        "Help users research workspace documents and provide evidence-backed answers.",
        [
            {
                "title": "Research process",
                "category": "workflow",
                "content": "Inspect relevant documents, compare evidence, and report verified findings.",
            },
            {
                "title": "Workspace retrieval",
                "category": "skills",
                "content": "Use semantic retrieval when a question depends on information across workspace documents.",
            },
        ],
        [
            {
                "name": "search_workspace",
                "signature": "(query: str)",
                "description": "Search workspace documents and return relevant passages when the answer needs source evidence.",
            },
        ],
    )

    names = [component["name"] for component in report["components"]]
    assert names == [
        "Prompt title",
        "Prompt description",
        "Prompt sections",
        "Section title: Research process",
        "Section: Research process",
        "Skill title: Workspace retrieval",
        "Skill: Workspace retrieval",
        "Tool name: search_workspace",
        "Tool: search_workspace",
    ]
    assert report["passed"] is True


def test_prompt_evaluation_marks_missing_title_and_vague_tool_language():
    report = run_prompt_component_tests(
        "",
        "Do this task.",
        [
            {"title": "Instructions", "category": "general", "content": "Short."},
        ],
        [
            {"name": "lookup", "signature": "()", "description": "A helper."},
        ],
    )

    assert report["passed"] is False
    failed_names = [
        component["name"] for component in report["components"] if not component["passed"]
    ]
    assert "Prompt title" in failed_names
    assert "Prompt description" in failed_names
    assert "Section: Instructions" in failed_names
    assert "Tool: lookup" in failed_names
