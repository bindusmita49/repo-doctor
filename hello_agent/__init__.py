# hello_agent/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Makes hello_agent/ a Python package so ADK's CLI can import it with:
#   import hello_agent
#
# ADK discovers agents by looking for a `root_agent` attribute on the package.
# Importing `agent` here ensures that attribute is available at package level.
# ─────────────────────────────────────────────────────────────────────────────
from . import agent  # noqa: F401  (imported for ADK discovery side-effect)
