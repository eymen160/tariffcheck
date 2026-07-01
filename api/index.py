"""Vercel serverless entry point.

The Flask app lives in backend/ — put it on the import path and expose the
WSGI `app` object, which Vercel's Python runtime serves directly. The full
request path (e.g. /api/analyze) reaches Flask, and backend/app.py already
registers every route under both / and /api/ prefixes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import app  # noqa: E402,F401
