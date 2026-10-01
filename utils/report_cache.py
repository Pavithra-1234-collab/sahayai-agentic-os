"""
In-memory store for generated report HTML files.
Keyed by a short random ID so the API can serve them at /api/report/temp/{id}.
"""
CACHE: dict[str, dict] = {}  # id -> {"html": str, "filename": str}
