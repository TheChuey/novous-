"""Permanent storage for custom tools promoted from the Prompt Testing Workbench.

Promoted tools are appended below the PROMOTION_MARKER by tools/interface.py,
which performs AST validation, registry updates, and rollback on failure.
"""
from core_engine.tool_catalog import tool

# PROMOTION_MARKER: tools appended below will be registered as custom tools

