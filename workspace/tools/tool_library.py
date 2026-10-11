
"""Interactive Questionnaire Tool (ask_user_questions) for Novous Workspace Agents."""

import html as _html
import http.server as _http_server
import json as _json
import socketserver as _socketserver
import threading as _threading
import urllib.parse as _urlparse
import webbrowser as _webbrowser

from typing import Any

from core_engine.tool_catalog import tool


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_TIMEOUT_SECONDS = 300.0
SERVER_HOST = "127.0.0.1"


# =========================================================
# TOOL
# =========================================================

@tool(name="ask_user_questions", provider="workspace")
def ask_user_questions(
    questions: Any,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """
    Display an interactive questionnaire in the user's browser.

    INPUT:
        questions:
            A list of question dictionaries, a single question
            dictionary, or a JSON string.

        timeout_seconds:
            Maximum number of seconds to wait for submission.

    PROCESS:
        1. Normalize the input.
        2. Validate the questions and timeout.
        3. Start a temporary local HTTP server.
        4. Open the questionnaire in the browser.
        5. Collect answers and wait for submission.

    OUTPUT:
        A JSON string containing the submitted question-and-answer
        pairs, or a structured error/timeout response.
    """

    print("[ask_user_questions] START")
    print(f"[ask_user_questions] Input type: {type(questions).__name__}")

    # ---------------------------------------------------------
    # 1. Normalize input
    # ---------------------------------------------------------

    if isinstance(questions, str):
        cleaned_str = questions.strip()

        try:
            questions = _json.loads(cleaned_str)

        except _json.JSONDecodeError:
            try:
                # Attempt to handle double-escaped JSON.
                questions = _json.loads(
                    cleaned_str.replace('\\"', '"')
                )

            except _json.JSONDecodeError:
                # Treat ordinary text as a single question.
                questions = [
                    {
                        "id": "q1",
                        "question": cleaned_str,
                    }
                ]

    if isinstance(questions, dict):
        questions = [questions]

    if not isinstance(questions, list) or not questions:
        return _json.dumps({
            "status": "ERROR",
            "error_code": "ERR_INVALID_INPUT",
            "message": (
                "questions must be a non-empty list of question "
                "objects, a question object, or a valid query string."
            ),
        })

    # ---------------------------------------------------------
    # 2. Validate and normalize questions
    # ---------------------------------------------------------

    normalized_questions = []
    used_ids = set()

    for index, item in enumerate(questions):
        if not isinstance(item, dict):
            return _json.dumps({
                "status": "ERROR",
                "error_code": "ERR_INVALID_INPUT",
                "message": (
                    f"Question at index {index} must be an object."
                ),
            })

        question_text = str(
            item.get("question", item.get("text", ""))
        ).strip()

        if not question_text:
            return _json.dumps({
                "status": "ERROR",
                "error_code": "ERR_INVALID_INPUT",
                "message": (
                    f"Question at index {index} has no question text."
                ),
            })

        question_id = str(
            item.get("id", f"q{index + 1}")
        ).strip()

        if not question_id or question_id in used_ids:
            return _json.dumps({
                "status": "ERROR",
                "error_code": "ERR_INVALID_INPUT",
                "message": (
                    f"Question ID at index {index} is empty "
                    "or duplicated."
                ),
            })

        used_ids.add(question_id)

        normalized_questions.append({
            "id": question_id,
            "question": question_text,
        })

    # ---------------------------------------------------------
    # 3. Validate timeout
    # ---------------------------------------------------------

    try:
        timeout = float(timeout_seconds)

        if timeout <= 0:
            raise ValueError

    except (TypeError, ValueError):
        return _json.dumps({
            "status": "ERROR",
            "error_code": "ERR_INVALID_INPUT",
            "message": "timeout_seconds must be a positive number.",
        })

    # ---------------------------------------------------------
    # 4. Prepare shared state
    # ---------------------------------------------------------

    collected_answers = {}
    event = _threading.Event()

    # ---------------------------------------------------------
    # 5. Build HTML form
    # ---------------------------------------------------------

    form_fields = []

    for question in normalized_questions:
        question_id = _html.escape(
            question["id"],
            quote=True,
        )

        question_text = _html.escape(
            question["question"]
        )

        form_fields.append(
            f"""
            <div class="question">
                <label for="{question_id}">
                    {question_text}
                </label>

                <textarea
                    id="{question_id}"
                    name="{question_id}"
                    rows="3"
                    placeholder="Enter your answer..."
                ></textarea>
            </div>
            """
        )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>Novous Questionnaire</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 30px 16px;
                font-family: Arial, sans-serif;
                background: #f3f4f6;
                color: #222;
            }}

            .container {{
                max-width: 700px;
                margin: 0 auto;
                padding: 28px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
            }}

            h1 {{
                margin-top: 0;
                font-size: 25px;
            }}

            .description {{
                color: #666;
                line-height: 1.5;
            }}

            .question {{
                margin-top: 24px;
            }}

            label {{
                display: block;
                margin-bottom: 10px;
                font-weight: bold;
                line-height: 1.5;
            }}

            textarea {{
                display: block;
                width: 100%;
                min-height: 90px;
                padding: 12px;
                resize: vertical;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                font: inherit;
            }}

            textarea:focus {{
                outline: 2px solid #93c5fd;
                border-color: #2563eb;
            }}

            button {{
                margin-top: 28px;
                padding: 12px 22px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 15px;
                cursor: pointer;
            }}

            button:hover {{
                background: #1d4ed8;
            }}

            .footer {{
                margin-top: 18px;
                color: #777;
                font-size: 12px;
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <h1>Questionnaire Prompt</h1>

            <p class="description">
                Please answer the following questions and submit
                your responses when finished.
            </p>

            <form method="POST" action="/submit">

                {''.join(form_fields)}

                <button type="submit">
                    Submit Answers
                </button>

            </form>

            <p class="footer">
                Novous Workspace Agent Questionnaire
            </p>

        </div>
    </body>

    </html>
    """

    # ---------------------------------------------------------
    # 6. Create HTTP request handler
    # ---------------------------------------------------------

    class Handler(_http_server.BaseHTTPRequestHandler):
        """Handle questionnaire requests and submissions."""

        def do_GET(self):
            """Display the questionnaire."""

            if self.path != "/":
                self.send_error(404, "Page not found")
                return

            response = html_content.encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def do_POST(self):
            """Collect answers submitted through the form."""

            parsed_path = _urlparse.urlparse(self.path)

            if parsed_path.path != "/submit":
                self.send_error(404, "Page not found")
                return

            # Prevent processing more than one submission.
            if event.is_set():
                self.send_error(409, "Answers already submitted")
                return

            try:
                content_length = int(
                    self.headers.get("Content-Length", "0")
                )

                if content_length < 0 or content_length > 1_000_000:
                    self.send_error(413, "Submission too large")
                    return

                body = self.rfile.read(content_length).decode("utf-8")

                params = _urlparse.parse_qs(
                    body,
                    keep_blank_values=True,
                )

                for question in normalized_questions:
                    question_id = question["id"]

                    answer_values = params.get(question_id, [])

                    collected_answers[question_id] = (
                        answer_values[0]
                        if answer_values
                        else ""
                    )

                # Signal that the user has submitted the form.
                event.set()

                response = b"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>Submission Received</title>
                </head>
                <body style="
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 60px auto;
                    padding: 20px;
                    text-align: center;
                ">
                    <h2>Responses received successfully!</h2>
                    <p>Your answers have been submitted.</p>
                    <p>You can close this browser window.</p>
                </body>
                </html>
                """

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8",
                )
                self.send_header(
                    "Content-Length",
                    str(len(response)),
                )
                self.end_headers()
                self.wfile.write(response)

            except Exception as exc:
                print(
                    "[ask_user_questions] Submission error:",
                    str(exc),
                )

                if not self.wfile.closed:
                    self.send_error(500, "Submission failed")

        def log_message(self, format, *args):
            """Suppress default HTTP server request logs."""
            pass

    # ---------------------------------------------------------
    # 7. Start server, open browser, and wait for answers
    # ---------------------------------------------------------

    server = None

    try:
        print("[ask_user_questions] Starting local HTTP server...")

        # Port 0 asks the operating system to choose an available port.
        # Binding only to localhost prevents external network access.
        class LocalTCPServer(_socketserver.TCPServer):
            allow_reuse_address = True

        server = LocalTCPServer(
            (SERVER_HOST, 0),
            Handler,
        )

        port = server.server_address[1]

        server_thread = _threading.Thread(
            target=server.serve_forever,
            daemon=True,
        )

        server_thread.start()

        url = f"http://{SERVER_HOST}:{port}/"

        print(f"[ask_user_questions] Server ready: {url}")
        print("[ask_user_questions] Opening browser...")

        browser_opened = _webbrowser.open(url)

        if not browser_opened:
            print(
                "[ask_user_questions] Browser did not report "
                "a successful launch. Open this URL manually:"
            )
            print(url)

        print(
            f"[ask_user_questions] Waiting up to {timeout} seconds..."
        )

        completed = event.wait(timeout=timeout)

        if not completed:
            print("[ask_user_questions] Timed out.")

            return _json.dumps({
                "status": "TIMEOUT",
                "error_code": "ERR_TIMEOUT",
                "message": (
                    "No response received within the timeout period."
                ),
            })

        # -----------------------------------------------------
        # 8. Return structured question-and-answer pairs
        # -----------------------------------------------------

        result = {
            "status": "COMPLETED",
            "qa_pairs": [
                {
                    "id": question["id"],
                    "question": question["question"],
                    "answer": collected_answers.get(
                        question["id"],
                        "",
                    ),
                }
                for question in normalized_questions
            ],
        }

        print("[ask_user_questions] Submission completed.")
        print(f"[ask_user_questions] Result type: {type(result).__name__}")

        return _json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as exc:
        print("[ask_user_questions] TOOL EXECUTION ERROR")
        print(f"[ask_user_questions] Error type: {type(exc).__name__}")
        print(f"[ask_user_questions] Error details: {exc}")

        return _json.dumps({
            "status": "ERROR",
            "error_code": "ERR_TOOL_EXECUTION",
            "message": str(exc),
        })

    finally:
        # Always release the local server and its socket.
        if server is not None:
            print("[ask_user_questions] Shutting down server...")

            server.shutdown()
            server.server_close()

        print("[ask_user_questions] END")
