# Atlassian-Rovo-Agent-MCP

[English README](README.md)

Atlassian-Rovo-Agent-MCP 是一个面向 Atlassian Rovo agent 工作流的开源本地 MCP facade。

OpenClaw 只需要连接这个 MCP Server。本项目会暴露本地 token 校验工具，并在内部通过 `mcp-remote` 转发 Atlassian 官方 Rovo MCP Server 的 tools。

## 能力概览

| 能力 | 说明 |
| --- | --- |
| MCP facade | 通过一个本地 MCP Server 同时暴露本地校验工具，并代理 Atlassian 官方 Rovo MCP tools。 |
| CLI | 提供本地命令行校验工具。 |
| 多产品校验 | 支持 Jira Cloud、Confluence Cloud 和 Bitbucket Cloud。 |
| 结构化输出 | 返回通过/失败汇总，以及 API 可返回的用户信息。 |

## 支持的产品

| 产品 | 校验端点 |
| --- | --- |
| Jira Cloud | `/rest/api/3/myself` |
| Confluence Cloud | `/wiki/rest/api/user/current` |
| Bitbucket Cloud | `/2.0/user` |

注意：Bitbucket Cloud 通常需要使用 App Password，而不是 Atlassian API Token。

## 环境要求

- Python 3.10+
- `uv`
- Node.js 18+
- `npx`

## 安装

```bash
uv sync
```

## OpenClaw MCP 配置

OpenClaw 只需要配置这个 MCP Server：

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

本项目会在内部连接 Atlassian 官方 Rovo MCP endpoint：

```text
https://mcp.atlassian.com/v1/mcp
```

首次使用时，`mcp-remote` 会打开浏览器进行 Atlassian OAuth 授权。授权完成后，OpenClaw 可以从这个单一 MCP Server 发现本地工具和被代理的官方 Rovo tools。

## MCP Tools

| Tool | 说明 |
| --- | --- |
| `validate_atlassian_token` | 校验 Jira、Confluence、Bitbucket 或全部产品。 |
| `validate_jira_token` | 仅校验 Jira Cloud。 |
| `validate_confluence_token` | 仅校验 Confluence Cloud。 |
| `validate_bitbucket_token` | 仅校验 Bitbucket Cloud 凭证。 |
| `atlassian_rovo_proxy_status` | 查看官方 Rovo MCP 代理连接状态。 |
| `atlassian_rovo_connect` | 主动触发官方 Rovo MCP 连接、OAuth 和 tool discovery。 |

官方 Atlassian Rovo MCP tools 会以原始名称转发。如果远端 tool 名称与本地 tool 冲突，会使用 `rovo__` 前缀暴露。

### `validate_atlassian_token` 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `email` | 是 | Atlassian 账户邮箱。 |
| `token` | 是 | Atlassian API Token。Bitbucket 请使用 App Password。 |
| `domain` | 是 | Atlassian 站点名，例如 `your-company` 或 `your-company.atlassian.net`。 |
| `product` | 否 | `jira`、`confluence`、`bitbucket` 或 `all`，默认 `all`。 |

## 命令行使用

校验全部支持的产品：

```bash
uv run atlassian-rovo-agent-validator \
  --email user@example.com \
  --token YOUR_API_TOKEN \
  --domain your-company
```

只校验单个产品：

```bash
uv run atlassian-rovo-agent-validator \
  --email user@example.com \
  --token YOUR_API_TOKEN \
  --domain your-company \
  --product jira
```

支持的 `--product`：

- `jira`
- `confluence`
- `bitbucket`
- `all`

## 项目结构

```text
mcp_server.py      # stdio MCP server
validator.py       # 核心校验逻辑和 CLI
pyproject.toml     # 包元数据和命令入口
requirements.txt   # pip 兼容依赖列表
uv.lock            # uv 锁定依赖图
```

## 配置项

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ATLASSIAN_ROVO_MCP_URL` | `https://mcp.atlassian.com/v1/mcp` | 官方 Rovo MCP endpoint。 |
| `ATLASSIAN_ROVO_MCP_REMOTE_COMMAND` | `npx` | 用于启动 `mcp-remote` 的命令。 |
| `ATLASSIAN_ROVO_MCP_REMOTE_PACKAGE` | `mcp-remote@latest` | `mcp-remote` 包版本。 |
| `ATLASSIAN_ROVO_DISCOVERY_TIMEOUT_SECONDS` | `30` | tool discovery 最长等待时间，超时后只返回本地 tools。 |
| `ATLASSIAN_ROVO_TOOL_PREFIX` | `rovo__` | 仅当官方 tool 名与本地 tool 冲突时使用的前缀。 |

## 安全注意事项

- 不要把 API Token、App Password 或敏感邮箱提交到代码库。
- 尽量使用短期、低权限或专用的校验凭证。
- 如果凭证曾经写入本地文件或被分享，应立即轮换。
- 被代理的 Rovo MCP 操作会使用完成 OAuth 授权的 Atlassian 用户权限。

## 开源协议

本项目基于 [MIT License](LICENSE) 开源。
