# Knowledge sources

Novous supports multiple named knowledge sources from **Knowledge Sources** in
Chat & Test Controls. Each source connects one folder to a matching name and a
separate SQLite index. Select a source to search or manage its indexed files.
No implicit default source is created. Older default-source configuration is
migrated to a named branch, retaining its legacy index until that branch is
explicitly deleted.

Agent tools can list knowledge sources and search or list documents by source
ID. This also works for archived sources: archiving preserves the index, and
agents can continue to access that branch without restoring it.

Sources may point to folders that are currently unavailable; their name and
path remain saved, and indexing reports that the folder cannot be scanned.
Archiving removes a source from active selection without deleting its path or
index. Archived sources can be restored later.

Branches can be renamed without changing their folder or index. Deleting a
branch removes its saved source entry and indexed vectors; it never deletes
files from the linked folder. A branch cannot be deleted while its scan is
queued, running, pausing, or paused.

Indexing runs as a background job. The dialog shows progress and document
errors, and supports pausing between files, resuming, and scheduling a resume.
Scheduled resumes use the local time selected in the browser and require the
Novous server and computer to remain running and awake. Completed files remain
indexed; on resume, unchanged files are skipped. Stale-document cleanup occurs
only after a scan reaches completion.

When indexing a file fails, the scan pauses for a choice: retry that file, skip
only that file and ask again on a later error, or skip all remaining errors.
Completion reports checked, indexed, unchanged, skipped, and failed counts so
skipped files are not mistaken for successfully indexed files.

PDF indexing uses Docling's PDF parsing extra. If its native parser cannot load,
Novous falls back to PyMuPDF for PDFs with selectable text. Scanned PDFs that
need OCR still require a working OCR-capable parser. These dependencies are
included in `requirements.txt`. Install them in the same Python environment
used to run Novous with:

`pip install -r requirements.txt`

The automatic scanner cycles through active sources for updates every
60 seconds. To adjust the small delay between files, set
`NOVOUS_RAG_SCAN_DELAY_SECONDS` before starting the server; it defaults to
`0.15` seconds and can be set to `0` to disable the delay.
