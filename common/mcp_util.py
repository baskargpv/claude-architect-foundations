"""Synchronous helpers around an in-process MCP server (mcp>=2.3)."""

from __future__ import annotations

import asyncio
import json

from mcp import Client


def tool_defs(server) -> list[dict]:
    """The server's tools as Messages API tool definitions."""
    async def _list():
        async with Client(server) as c:
            return (await c.list_tools()).tools
    return [{"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
            for t in asyncio.run(_list())]


def call(server, name: str, args: dict):
    """Call a tool; returns the raw CallToolResult (is_error, content, structured_content)."""
    async def _call():
        async with Client(server) as c:
            return await c.call_tool(name, args)
    return asyncio.run(_call())


def call_json(server, name: str, args: dict) -> dict:
    """Call a tool whose text content is JSON and return it parsed."""
    return json.loads(call(server, name, args).content[0].text)


def resources(server) -> list:
    async def _list():
        async with Client(server) as c:
            return (await c.list_resources()).resources
    return asyncio.run(_list())


def read_resource(server, uri: str) -> str:
    async def _read():
        async with Client(server) as c:
            return (await c.read_resource(uri)).contents[0].text
    return asyncio.run(_read())
