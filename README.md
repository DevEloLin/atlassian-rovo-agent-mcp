# Atlassian-Rovo-Agent-MCP

[中文文档](README.zh-CN.md)

Atlassian-Rovo-Agent-MCP is an open-source local MCP facade for Atlassian Rovo agent workflows.

OpenClaw connects only to this server. This server exposes local token-validation tools and forwards tools from Atlassian's official Rovo MCP Server through `mcp-remote`.

## What It Provides

| Capability | Description |
| --- | --- |
| MCP facade | Exposes local validation tools and proxies official Atlassian Rovo MCP tools through one local MCP server. |
| CLI | Provides a direct command-line validator for local checks. |
| Multi-product validation | Supports Jira Cloud, Confluence Cloud, and Bitbucket Cloud. |
| Structured output | Returns pass/fail summaries and user information when APIs return it. |

## Supported Products

| Product | Validation endpoint |
| --- | --- |
| Jira Cloud | `/rest/api/3/myself` |
| Confluence Cloud | `/wiki/rest/api/user/current` |
| Bitbucket Cloud | `/2.0/user` |

Note: Bitbucket Cloud usually requires an app password instead of an Atlassian API token.

## Requirements

- Python 3.10+
- `uv`
- Node.js 18+
- `npx`

## Installation

```bash
uv sync
```

## OpenClaw MCP Configuration

Add only this server to your OpenClaw MCP configuration:

```json
{
  "mcpServers": {
    "Atlassian-Rovo-Agent-MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/Atlassian-Rovo-Agent-MCP",
        "run",
        "atlassian-rovo-agent-mcp"
      ]
    }
  }
}
```

The server connects to Atlassian's official Rovo MCP endpoint internally:

```text
https://mcp.atlassian.com/v1/mcp
```

On first use, `mcp-remote` opens a browser for Atlassian OAuth authorization. After authorization, OpenClaw can discover both the local tools and the proxied Rovo tools from this single MCP server.

## MCP Tools

| Tool | Description |
| --- | --- |
| `validate_atlassian_token` | Validate Jira, Confluence, Bitbucket, or all supported products. |
| `validate_jira_token` | Validate Jira Cloud access only. |
| `validate_confluence_token` | Validate Confluence Cloud access only. |
| `validate_bitbucket_token` | Validate Bitbucket Cloud credentials only. |
| `atlassian_rovo_proxy_status` | Show official Rovo MCP proxy connection status. |
| `atlassian_rovo_connect` | Trigger official Rovo MCP connection and OAuth/tool discovery. |

Official Atlassian Rovo MCP tools are forwarded with their original names. If a remote tool name collides with a local tool, it is exposed with the `rovo__` prefix.

### `validate_atlassian_token` Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `email` | Yes | Atlassian account email. |
| `token` | Yes | Atlassian API token. For Bitbucket, use an app password. |
| `domain` | Yes | Atlassian site name, such as `your-company` or `your-company.atlassian.net`. |
| `product` | No | `jira`, `confluence`, `bitbucket`, or `all`. Defaults to `all`. |

## CLI Usage

Validate all supported products:

```bash
uv run atlassian-rovo-agent-validator \
  --email user@example.com \
  --token YOUR_API_TOKEN \
  --domain your-company
```

Validate a single product:

```bash
uv run atlassian-rovo-agent-validator \
  --email user@example.com \
  --token YOUR_API_TOKEN \
  --domain your-company \
  --product jira
```

Supported `--product` values:

- `jira`
- `confluence`
- `bitbucket`
- `all`

## Project Layout

```text
mcp_server.py      # stdio MCP server
validator.py       # core validation logic and CLI
pyproject.toml     # package metadata and command entry points
requirements.txt   # pip-compatible dependency list
uv.lock            # locked dependency graph for uv
```

## Configuration

| Environment variable | Default | Description |
| --- | --- | --- |
| `ATLASSIAN_ROVO_MCP_URL` | `https://mcp.atlassian.com/v1/mcp` | Official Rovo MCP endpoint. |
| `ATLASSIAN_ROVO_MCP_REMOTE_COMMAND` | `npx` | Command used to launch `mcp-remote`. |
| `ATLASSIAN_ROVO_MCP_REMOTE_PACKAGE` | `mcp-remote@latest` | `mcp-remote` package spec. |
| `ATLASSIAN_ROVO_DISCOVERY_TIMEOUT_SECONDS` | `30` | Maximum time to wait during tool discovery before returning local tools only. |
| `ATLASSIAN_ROVO_TOOL_PREFIX` | `rovo__` | Prefix used only when an official tool name collides with a local tool name. |

## Security

- Do not commit API tokens, app passwords, or private account emails.
- Prefer short-lived, restricted credentials for validation workflows.
- Rotate any credential that was stored in local files or shared by mistake.
- Proxied Rovo MCP actions use the permissions of the Atlassian user who completes OAuth.

## License

This project is open source under the [MIT License](LICENSE).
