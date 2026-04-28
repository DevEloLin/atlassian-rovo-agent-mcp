#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atlassian Rovo Agent MCP Server

通过 MCP stdio 暴露现有 token 校验逻辑，供 OpenClaw 等 MCP Client 调用。
"""

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from validator import AtlassianValidator


Product = Literal["jira", "confluence", "bitbucket", "all"]


mcp = FastMCP(
    name="Atlassian-Rovo-Agent-MCP",
    instructions=(
        "Validate Atlassian Cloud API tokens against Jira, Confluence, "
        "and Bitbucket endpoints. Inputs include email, token, domain, and product."
    ),
)


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


@mcp.tool(
    name="validate_atlassian_token",
    description=(
        "Validate an Atlassian Cloud API token for Jira, Confluence, "
        "Bitbucket, or all supported products."
    ),
    structured_output=True,
)
def validate_atlassian_token(
    email: str,
    token: str,
    domain: str,
    product: Product = "all",
) -> dict[str, Any]:
    """
    Validate an Atlassian token.

    Args:
        email: Atlassian account email.
        token: Atlassian API token, or Bitbucket app password for Bitbucket.
        domain: Atlassian site name, for example 'your-company' or
            'your-company.atlassian.net'.
        product: jira, confluence, bitbucket, or all.
    """
    return _validate(email=email, token=token, domain=domain, product=product)


@mcp.tool(
    name="validate_jira_token",
    description="Validate an Atlassian Cloud API token against Jira Cloud.",
    structured_output=True,
)
def validate_jira_token(email: str, token: str, domain: str) -> dict[str, Any]:
    return _validate(email=email, token=token, domain=domain, product="jira")


@mcp.tool(
    name="validate_confluence_token",
    description="Validate an Atlassian Cloud API token against Confluence Cloud.",
    structured_output=True,
)
def validate_confluence_token(email: str, token: str, domain: str) -> dict[str, Any]:
    return _validate(email=email, token=token, domain=domain, product="confluence")


@mcp.tool(
    name="validate_bitbucket_token",
    description="Validate credentials against Bitbucket Cloud. Bitbucket usually requires an app password.",
    structured_output=True,
)
def validate_bitbucket_token(email: str, token: str, domain: str = "unused") -> dict[str, Any]:
    return _validate(email=email, token=token, domain=domain, product="bitbucket")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
