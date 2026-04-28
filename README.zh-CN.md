# Atlassian-Rovo-Agent-MCP

[English README](README.md)

Atlassian-Rovo-Agent-MCP 是一个开源的 MCP Server 和命令行工具，用于在 Atlassian Rovo agent 工作流中校验 Atlassian Cloud API Token。

它适合 IT 运维、安全审计和账号下线检查等场景，尤其用于验证账号被禁用、token 被撤销或权限应被移除后，是否仍然可以访问 Jira、Confluence 或 Bitbucket。

## 能力概览

| 能力 | 说明 |
| --- | --- |
| MCP Server | 通过 stdio MCP tools 暴露 token 校验能力，可接入 OpenClaw 和其他 MCP Client。 |
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

## 安装

```bash
uv sync
```

## OpenClaw MCP 配置

把下面配置加入 OpenClaw 的 MCP 配置：

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

| Tool | 说明 |
| --- | --- |
| `validate_atlassian_token` | 校验 Jira、Confluence、Bitbucket 或全部产品。 |
| `validate_jira_token` | 仅校验 Jira Cloud。 |
| `validate_confluence_token` | 仅校验 Confluence Cloud。 |
| `validate_bitbucket_token` | 仅校验 Bitbucket Cloud 凭证。 |

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

## 安全注意事项

- 不要把 API Token、App Password 或敏感邮箱提交到代码库。
- 尽量使用短期、低权限或专用的校验凭证。
- 如果凭证曾经写入本地文件或被分享，应立即轮换。

## 开源协议

本项目基于 [MIT License](LICENSE) 开源。
