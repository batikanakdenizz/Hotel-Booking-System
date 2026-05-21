"""Tool registry — function definitions + dispatcher.

All tools call back to our own platform via the gateway (see config.gateway_url).
This deliberately mirrors what an out-of-process MCP server would look like —
each tool is a pure async function with structured args/return — but stays
in-process for simpler deployment on Render's free tier.
"""
from app.tools.registry import OPENAI_TOOL_SCHEMAS, dispatch_tool

__all__ = ["OPENAI_TOOL_SCHEMAS", "dispatch_tool"]
