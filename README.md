# Atlassian-Rovo-Agent-MCP

[中文文档](README.zh-CN.md)

Atlassian-Rovo-Agent-MCP is an open-source MCP server and CLI for validating Atlassian Cloud API tokens in Atlassian Rovo agent workflows.

It helps operators and security teams verify whether a token can still access Jira, Confluence, or Bitbucket after an account is disabled, a token is revoked, or access is expected to be removed.

## What It Provides

| Capability | Description |
| --- | --- |
| MCP server | Exposes token validation as stdio MCP tools for OpenClaw and other MCP clients. |
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

## Installation

```bash
uv sync
```

## OpenClaw MCP Configuration

Add the server to your OpenClaw MCP configuration:

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

## MCP Tools

| Tool | Description |
| --- | --- |
| `validate_atlassian_token` | Validate Jira, Confluence, Bitbucket, or all supported products. |
| `validate_jira_token` | Validate Jira Cloud access only. |
| `validate_confluence_token` | Validate Confluence Cloud access only. |
| `validate_bitbucket_token` | Validate Bitbucket Cloud credentials only. |

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

## Security

- Do not commit API tokens, app passwords, or private account emails.
- Prefer short-lived, restricted credentials for validation workflows.
- Rotate any credential that was stored in local files or shared by mistake.

## License

This project is open source under the [MIT License](LICENSE).
