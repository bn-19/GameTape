import sys
import os

# Add backend/ to path so all internal imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from main import app  # noqa: F401 — Vercel picks up `app` as the ASGI handler
