"""SQLite CRUD operations for indexed document chunks and embedding vectors."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator


DATABASE_PATH = Path(__file__).resolve().parent / "data" / "knowledge.sqlite3"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                path TEXT PRIMARY KEY,
                modified_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                indexed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
                path TEXT NOT NULL REFERENCES documents(path) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                PRIMARY KEY (path, chunk_index)
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
            """
        )


def replace_document(
    path: str,
    modified_ns: int,
    size_bytes: int,
    indexed_at: str,
    chunks: Iterable[tuple[str, list[float]]],
) -> None:
    """Atomically replace one indexed document and all of its chunks."""
    with connect() as connection:
        connection.execute("DELETE FROM documents WHERE path = ?", (path,))
        connection.execute(
            "INSERT INTO documents(path, modified_ns, size_bytes, indexed_at) VALUES (?, ?, ?, ?)",
            (path, modified_ns, size_bytes, indexed_at),
        )
        connection.executemany(
            "INSERT INTO chunks(path, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
            [
                (path, index, content, json.dumps(vector, separators=(",", ":")))
                for index, (content, vector) in enumerate(chunks)
            ],
        )


def document_metadata(path: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT path, modified_ns, size_bytes, indexed_at FROM documents WHERE path = ?",
            (path,),
        ).fetchone()
    return dict(row) if row else None


def list_documents() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT d.path, d.modified_ns, d.size_bytes, d.indexed_at, COUNT(c.chunk_index) AS chunks
            FROM documents d LEFT JOIN chunks c ON c.path = d.path
            GROUP BY d.path
            ORDER BY d.path COLLATE NOCASE
            """
        ).fetchall()
    return [dict(row) for row in rows]


def delete_document(path: str) -> bool:
    with connect() as connection:
        cursor = connection.execute("DELETE FROM documents WHERE path = ?", (path,))
    return cursor.rowcount > 0


def delete_documents_under(prefix: str, keep_paths: set[str]) -> list[str]:
    """Remove stale documents below a normalized source directory."""
    normalized_prefix = prefix.rstrip("/\\").replace("\\", "/") + "/"
    normalized_keep = {path.replace("\\", "/") for path in keep_paths}
    with connect() as connection:
        rows = connection.execute("SELECT path FROM documents").fetchall()
        stale = [
            row["path"] for row in rows
            if row["path"].replace("\\", "/").startswith(normalized_prefix)
            and row["path"].replace("\\", "/") not in normalized_keep
        ]
        connection.executemany("DELETE FROM documents WHERE path = ?", [(path,) for path in stale])
    return stale


def list_chunks() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT path, chunk_index, content, embedding FROM chunks"
        ).fetchall()
    result = []
    for row in rows:
        result.append({
            "path": row["path"],
            "chunk_index": row["chunk_index"],
            "content": row["content"],
            "embedding": json.loads(row["embedding"]),
        })
    return result


def get_document_chunks(path: str) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT path, chunk_index, content, embedding
            FROM chunks WHERE path = ? ORDER BY chunk_index
            """,
            (path,),
        ).fetchall()
    return [
        {
            "path": row["path"],
            "chunk_index": row["chunk_index"],
            "content": row["content"],
            "embedding": json.loads(row["embedding"]),
        }
        for row in rows
    ]
