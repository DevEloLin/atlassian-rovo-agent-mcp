#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atlassian Rovo Agent MCP Server

OpenClaw only connects to this local MCP server. This server exposes local
token-validation tools and transparently proxies Atlassian's official Rovo MCP
tools through mcp-remote.
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, Literal

from mcp import ClientSession, types
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.stdio import stdio_server

from validator import AtlassianValidator


Product = Literal["jira", "confluence", "bitbucket", "all"]

ROVO_MCP_URL = os.getenv("ATLASSIAN_ROVO_MCP_URL", "https://mcp.atlassian.com/v1/mcp")
ROVO_TOOL_PREFIX = os.getenv("ATLASSIAN_ROVO_TOOL_PREFIX", "rovo__")
ROVO_DISCOVERY_TIMEOUT_SECONDS = float(os.getenv("ATLASSIAN_ROVO_DISCOVERY_TIMEOUT_SECONDS", "30"))

server = Server(
    name="Atlassian-Rovo-Agent-MCP",
    version="1.0.0",
    instructions=(
        "A local MCP facade for OpenClaw. It provides Atlassian token validation "
        "tools and forwards Atlassian Rovo MCP tools from the official remote "
        "server via mcp-remote."
    ),
)


LOCAL_TOOL_NAMES = {
    "validate_atlassian_token",
    "validate_jira_token",
    "validate_confluence_token",
    "validate_bitbucket_token",
    "atlassian_rovo_proxy_status",
    "atlassian_rovo_connect",
}


def _object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


LOCAL_TOOLS = [
    types.Tool(
        name="validate_atlassian_token",
        description=(
            "Validate an Atlassian Cloud API token for Jira, Confluence, "
            "Bitbucket, or all supported products."
        ),
        inputSchema=_object_schema(
            {
                "email": {"type": "string", "description": "Atlassian account email."},
                "token": {
                    "type": "string",
                    "description": "Atlassian API token, or Bitbucket app password for Bitbucket.",
                },
                "domain": {
                    "type": "string",
                    "description": "Atlassian site name, e.g. your-company or your-company.atlassian.net.",
                },
                "product": {
                    "type": "string",
                    "enum": ["jira", "confluence", "bitbucket", "all"],
                    "default": "all",
                },
            },
            ["email", "token", "domain"],
        ),
    ),
    types.Tool(
        name="validate_jira_token",
        description="Validate an Atlassian Cloud API token against Jira Cloud.",
        inputSchema=_object_schema(
            {
                "email": {"type": "string"},
                "token": {"type": "string"},
                "domain": {"type": "string"},
            },
            ["email", "token", "domain"],
        ),
    ),
    types.Tool(
        name="validate_confluence_token",
        description="Validate an Atlassian Cloud API token against Confluence Cloud.",
        inputSchema=_object_schema(
            {
                "email": {"type": "string"},
                "token": {"type": "string"},
                "domain": {"type": "string"},
            },
            ["email", "token", "domain"],
        ),
    ),
    types.Tool(
        name="validate_bitbucket_token",
        description="Validate Bitbucket Cloud credentials. Bitbucket usually requires an app password.",
        inputSchema=_object_schema(
            {
                "email": {"type": "string"},
                "token": {"type": "string"},
                "domain": {
                    "type": "string",
                    "default": "unused",
                    "description": "Ignored for Bitbucket validation.",
                },
            },
            ["email", "token"],
        ),
    ),
    types.Tool(
        name="atlassian_rovo_proxy_status",
        description="Report whether the official Atlassian Rovo MCP proxy is connected.",
        inputSchema=_object_schema({}, []),
    ),
    types.Tool(
        name="atlassian_rovo_connect",
        description=(
            "Connect to the official Atlassian Rovo MCP server through mcp-remote. "
            "On first use this may open a browser for Atlassian OAuth authorization."
        ),
        inputSchema=_object_schema(
            {
                "timeout_seconds": {
                    "type": "number",
                    "default": ROVO_DISCOVERY_TIMEOUT_SECONDS,
                    "description": "Maximum time to wait for Rovo MCP connection and tool discovery.",
                }
            },
            [],
        ),
    ),
]


class RovoProxy:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._exit_stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._remote_to_public: dict[str, str] = {}
        self._public_to_remote: dict[str, str] = {}
        self._last_error: str | None = None

    @property
    def connected(self) -> bool:
        return self._session is not None

    async def connect(self) -> None:
        if self._session is not None:
            return

        async with self._lock:
            if self._session is not None:
                return

            params = StdioServerParameters(
                command=os.getenv("ATLASSIAN_ROVO_MCP_REMOTE_COMMAND", "npx"),
                args=[
                    "-y",
                    os.getenv("ATLASSIAN_ROVO_MCP_REMOTE_PACKAGE", "mcp-remote@latest"),
                    ROVO_MCP_URL,
                ],
            )
            stack = AsyncExitStack()

            try:
                read, write = await stack.enter_async_context(stdio_client(params))
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
            except BaseException as exc:
                await stack.aclose()
                self._last_error = str(exc)
                self._exit_stack = None
                self._session = None
                raise RuntimeError(f"Unable to connect to Atlassian Rovo MCP via mcp-remote: {exc}") from exc

            self._exit_stack = stack
            self._session = session
            self._last_error = None

    async def list_tools(self) -> list[types.Tool]:
        await self.connect()
        assert self._session is not None

        result = await self._session.list_tools()
        self._remote_to_public.clear()
        self._public_to_remote.clear()

        proxied_tools: list[types.Tool] = []
        for tool in result.tools:
            public_name = tool.name
            if public_name in LOCAL_TOOL_NAMES:
                public_name = f"{ROVO_TOOL_PREFIX}{tool.name}"

            self._remote_to_public[tool.name] = public_name
            self._public_to_remote[public_name] = tool.name

            proxied_tools.append(
                types.Tool(
                    name=public_name,
                    title=tool.title,
                    description=tool.description,
                    inputSchema=tool.inputSchema,
                    outputSchema=tool.outputSchema,
                    icons=tool.icons,
                    annotations=tool.annotations,
                    _meta=tool.meta,
                )
            )

        return proxied_tools

    async def call_tool(self, public_name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        await self.connect()
        assert self._session is not None

        remote_name = self._public_to_remote.get(public_name, public_name)
        result = await self._session.call_tool(remote_name, arguments=arguments)
        return result

    def status(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "remote_url": ROVO_MCP_URL,
            "discovery_timeout_seconds": ROVO_DISCOVERY_TIMEOUT_SECONDS,
            "tool_prefix_for_collisions": ROVO_TOOL_PREFIX,
            "last_error": self._last_error,
        }

    async def connect_status(self, timeout_seconds: float) -> dict[str, Any]:
        tools = await asyncio.wait_for(self.list_tools(), timeout=timeout_seconds)
        return {
            **self.status(),
            "remote_tool_count": len(tools),
            "remote_tools": [tool.name for tool in tools],
        }


rovo_proxy = RovoProxy()


def _normalize_domain(domain: str) -> str:
    """Accept either 'your-company' or 'your-company.atlassian.net'."""
    normalized = domain.strip().removeprefix("https://").removeprefix("http://")
    normalized = normalized.removesuffix("/")
    normalized = normalized.removesuffix(".atlassian.net")
    return normalized


def _validate(email: str, token: str, domain: str, product: Product) -> dict[str, Any]:
    if not email.strip():
        raise ValueError("email is required")
    if not token.strip():
        raise ValueError("token is required")
    if not domain.strip():
        raise ValueError("domain is required")

    validator = AtlassianValidator(
        email=email.strip(),
        token=token.strip(),
        domain=_normalize_domain(domain),
    )

    if product == "all":
        results = validator.validate_all()
    elif product == "jira":
        results = [validator.validate_jira()]
    elif product == "confluence":
        results = [validator.validate_confluence()]
    elif product == "bitbucket":
        results = [validator.validate_bitbucket()]
    else:
        raise ValueError("product must be one of: jira, confluence, bitbucket, all")

    return {
        "valid": all(result["valid"] for result in results),
        "summary": {
            "total": len(results),
            "passed": sum(1 for result in results if result["valid"]),
            "failed": sum(1 for result in results if not result["valid"]),
        },
        "results": results,
    }


def _text_result(data: dict[str, Any]) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))],
        structuredContent=data,
    )


def _local_tool_result(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
    if name == "validate_atlassian_token":
        product = arguments.get("product", "all")
        return _text_result(
            _validate(
                email=arguments["email"],
                token=arguments["token"],
                domain=arguments["domain"],
                product=product,
            )
        )

    if name == "validate_jira_token":
        return _text_result(
            _validate(
                email=arguments["email"],
                token=arguments["token"],
                domain=arguments["domain"],
                product="jira",
            )
        )

    if name == "validate_confluence_token":
        return _text_result(
            _validate(
                email=arguments["email"],
                token=arguments["token"],
                domain=arguments["domain"],
                product="confluence",
            )
        )

    if name == "validate_bitbucket_token":
        return _text_result(
            _validate(
                email=arguments["email"],
                token=arguments["token"],
                domain=arguments.get("domain", "unused"),
                product="bitbucket",
            )
        )

    if name == "atlassian_rovo_proxy_status":
        return _text_result(rovo_proxy.status())

    if name == "atlassian_rovo_connect":
        raise ValueError("atlassian_rovo_connect is async and must be handled by call_tool")

    raise ValueError(f"Unknown local tool: {name}")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    tools = list(LOCAL_TOOLS)
    try:
        tools.extend(await asyncio.wait_for(rovo_proxy.list_tools(), timeout=ROVO_DISCOVERY_TIMEOUT_SECONDS))
    except Exception:
        # Keep local validation available even before the user completes Rovo OAuth
        # or installs Node.js/npx. The status tool exposes the last proxy error.
        pass
    return tools


@server.call_tool(validate_input=True)
async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
    if name == "atlassian_rovo_connect":
        timeout_seconds = float(arguments.get("timeout_seconds", ROVO_DISCOVERY_TIMEOUT_SECONDS))
        try:
            return _text_result(await rovo_proxy.connect_status(timeout_seconds=timeout_seconds))
        except Exception as exc:
            return _text_result({**rovo_proxy.status(), "connected": False, "error": str(exc)})

    if name in LOCAL_TOOL_NAMES:
        return _local_tool_result(name, arguments)

    return await rovo_proxy.call_tool(name, arguments)


async def run_server() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(NotificationOptions()),
        )


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
