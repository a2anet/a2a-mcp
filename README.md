# A2A MCP Server

[![PyPI - Version](https://img.shields.io/pypi/v/a2anet-mcp.svg)](https://pypi.org/project/a2anet-mcp) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/a2anet-mcp.svg)](https://pypi.org/project/a2anet-mcp) [![PyPI - Downloads](https://img.shields.io/pypi/dm/a2anet-mcp)](https://pypi.org/project/a2anet-mcp) [![License](https://img.shields.io/github/license/a2anet/a2a-mcp)](https://github.com/a2anet/a2a-mcp/blob/main/LICENSE) [![Tests](https://github.com/a2anet/a2a-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/a2anet/a2a-mcp/actions/workflows/ci.yml) [![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-blue)](https://a2a-protocol.org) [![MCP](https://img.shields.io/badge/MCP-Server-orange)](https://modelcontextprotocol.io) [![Discord](https://img.shields.io/discord/1391916121589944320?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/674NGXpAjU)

An [MCP server](https://modelcontextprotocol.io/specification/latest/server) that implements an [A2A Client](https://a2a-protocol.org/latest/topics/key-concepts/#core-actors-in-a2a-interactions) for the [A2A Protocol](https://a2a-protocol.org/latest/).
The server can be used to connect and send messages to A2A Servers (remote agents).

The server needs to be initialised with one or more [Agent Card](https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/) URLs, each of which can have custom headers for authentication, configuration, etc.

All agents (name and description) can be viewed with the `get_agents` tool, an agent's skills (name and description) can be viewed with the `get_agent` tool, Messages can be sent to the agents with the `send_message` tool, long-running Tasks can be polled with `get_task`, and [Artifacts](https://a2a-protocol.org/latest/topics/key-concepts/#artifacts) can be viewed with `view_text_artifact` and `view_data_artifact` tools.

## ✨ Features

- **6 MCP tools** — `get_agents`, `get_agent`, `send_message`, `get_task`, `view_text_artifact`, and `view_data_artifact` for communicating with A2A agents
- **Simple message sending** — send messages to any A2A agent by ID; Agent Card fetching, headers, and non-blocking streaming are handled automatically
- **Multi-turn conversations** — continue conversations across multiple messages using `context_id`
- **Long-running task support** — if `send_message` times out, use `get_task` to monitor the task until it reaches a terminal state
- **Automatic artifact minimization** — large text and data artifacts are automatically minimized for LLM context windows, with dedicated tools for detailed navigation
- **Task and file storage** — tasks and file artifacts are saved locally to `~/.a2a-mcp/` by default
- **Custom headers and authentication** — configure per-agent custom headers for API keys and other credentials
- **Configurable timeouts and limits** — customisable timeouts, polling intervals, and character limits via environment variables

## 📋 Requirements

To run the server you need to install uv if you haven't already.

MacOS/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 🚀 Quick Start

1. Download [Claude for Desktop](https://claude.com/download)
2. Add the below to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "a2a": {
      "command": "uvx",
      "args": ["a2anet-mcp"],
      "env": {
        "A2A_MCP_AGENT_CARDS": "{\"tweet-search\": {\"url\": \"https://example.com/.well-known/agent-card.json\"}}"
      }
    }
  }
}
```

> **Tip:** If you don't have an Agent Card URL, see: [A2A Net Demo](https://github.com/a2anet/a2anet-demo)

## ⚙️ Configuration

All configuration is via environment variables prefixed with `A2A_MCP_`.

### `A2A_MCP_AGENT_CARDS` (required)

A JSON object mapping agent IDs to their configuration. Each agent must have a `url` key with the full path to the Agent Card. It can optionally have a `custom_headers` key with an object in the form `{"header": "value"}`:

```bash
export A2A_MCP_AGENT_CARDS='{
  "tweet-search": {
    "url": "https://example.com/.well-known/agent-card.json",
    "custom_headers": {"X-API-Key": "your-key"}
  }
}'
```

### Optional settings

| Env Var | Default | Description |
|---------|---------|-------------|
| `A2A_MCP_TASK_STORE` | `true` | Enable task persistence via `JSONTaskStore` |
| `A2A_MCP_FILE_STORE` | `true` | Enable file artifact storage via `LocalFileStore` |
| `A2A_MCP_SEND_MESSAGE_CHARACTER_LIMIT` | `50000` | Character limit for artifact minimization in `send_message` |
| `A2A_MCP_MINIMIZED_OBJECT_STRING_LENGTH` | `5000` | Max string length when minimizing objects |
| `A2A_MCP_VIEW_ARTIFACT_CHARACTER_LIMIT` | `50000` | Character limit for `view_text_artifact` / `view_data_artifact` |
| `A2A_MCP_AGENT_CARD_TIMEOUT` | `15` | Timeout in seconds for fetching agent cards |
| `A2A_MCP_SEND_MESSAGE_TIMEOUT` | `60` | Timeout in seconds for `send_message` |
| `A2A_MCP_GET_TASK_TIMEOUT` | `60` | Timeout in seconds for `get_task` |
| `A2A_MCP_GET_TASK_POLL_INTERVAL` | `5` | Interval in seconds between `get_task` polls |

## 🛠️ Tools

### `get_agents`

Get all agent names and descriptions.

### `get_agent`

Get an agent's name, description, and skill names and descriptions.

| Parameter  | Required | Description |
|------------|----------|-------------|
| `agent_id` | Yes      | Agent ID    |

### `send_message`

Send a message to an agent.

| Parameter    | Required | Description                              |
|--------------|----------|------------------------------------------|
| `agent_id`   | Yes      | Agent ID from `get_agents`               |
| `message`    | Yes      | Your message or request                  |
| `context_id` | No       | Continue an existing conversation        |
| `task_id`    | No       | Task ID for input_required flows         |
| `timeout`    | No       | Override HTTP timeout (seconds)          |

### `get_task`

Get the current state of a task. Monitors until terminal/actionable state or timeout. On timeout, returns the current task state (which may still be non-terminal).

| Parameter       | Required | Description                                  |
|-----------------|----------|----------------------------------------------|
| `agent_id`      | Yes      | Agent ID that owns the task                  |
| `task_id`       | Yes      | Task ID from a previous `send_message`       |
| `timeout`       | No       | Override monitoring timeout (seconds)        |
| `poll_interval` | No       | Override interval between polls (seconds)    |

### `view_text_artifact`

View text content from an artifact with optional line or character range selection.

| Parameter         | Required | Description                              |
|-------------------|----------|------------------------------------------|
| `agent_id`        | Yes      | Agent ID that produced the artifact      |
| `task_id`         | Yes      | Task ID containing the artifact          |
| `artifact_id`     | Yes      | Artifact to view                         |
| `line_start`      | No       | Starting line number (1-based, inclusive) |
| `line_end`        | No       | Ending line number (1-based, inclusive)   |
| `character_start` | No       | Starting character index (0-based)       |
| `character_end`   | No       | Ending character index (0-based)         |

### `view_data_artifact`

View structured data from an artifact with optional filtering.

| Parameter     | Required | Description                                         |
|---------------|----------|-----------------------------------------------------|
| `agent_id`    | Yes      | Agent ID that produced the artifact                 |
| `task_id`     | Yes      | Task ID containing the artifact                     |
| `artifact_id` | Yes      | Artifact to view                                    |
| `json_path`   | No       | Dot-separated path to extract specific fields       |
| `rows`        | No       | Row selection (index, list, range string, or "all") |
| `columns`     | No       | Column selection (name, list, or "all")             |

## 📖 Examples

### List agents

```
get_agents({})
```

```json
{
  "tweet-search": {
    "name": "Tweet Search",
    "description": "Find and analyze tweets by keyword, URL, author, list, or thread. Filter by language, media type, engagement, date range, or location. Get a clean table of tweets with authors, links, media, and counts; then refine the table and generate new columns with AI."
  }
}
```

### Get agent details

```
get_agent({
  "agent_id": "tweet-search"
})
```

```json
{
  "name": "Tweet Search",
  "description": "Find and analyze tweets by keyword, URL, author, list, or thread. Filter by language, media type, engagement, date range, or location. Get a clean table of tweets with authors, links, media, and counts; then refine the table and generate new columns with AI.",
  "skills": [
    {
      "name": "Search Tweets",
      "description": "Search X by keywords, URLs, handles, or conversation IDs. Filter by engagement (retweets/favorites/replies), dates, language, location, media type (images/videos/quotes), user verification status, and author/reply/mention relationships. Sort by Top or Latest. Return 1-10,000 results."
    },
    ...,
    {
      "name": "Generate Table",
      "description": "Generate a new table from any table with AI. Explain what table you want to generate from, what columns you want to keep, and what new columns you want to generate."
    }
  ]
}
```

### Send a message

```
send_message({
  "agent_id": "tweet-search",
  "message": "Find tweets about AI from today (January 12, 2026)"
})
```

```json
{
  "id": "tsk-123",
  "context_id": "ctx-123",
  "kind": "task",
  "status": {
    "state": "completed",
    "message": {
      "context_id": "ctx-123",
      "kind": "message",
      "parts": [
        {
          "kind": "text",
          "text": "I found 10 tweets about \"AI\" posted on January 12, 2026. The search parameters used were:\n\n- Search Terms: AI\n- Start Date: 2026-01-12\n- End Date: 2026-01-13\n- Maximum Items: 10\n\nWould you like to see more tweets, or do you want a summary or analysis of these results?"
        }
      ]
    }
  },
  "artifacts": [
    {
      "artifact_id": "art-123",
      "description": "Tweets about AI posted on January 12, 2026.",
      "name": "AI Tweets from January 12, 2026",
      "parts": [
        {
          "kind": "data",
          "data": {
            "records": {
              "_total_rows": 10,
              "_columns": [
                {
                  "count": 1,
                  "unique_count": 1,
                  "types": [
                    {
                      "name": "int",
                      "count": 1,
                      "percentage": 100.0,
                      "sample_value": 213,
                      "minimum": 213,
                      "maximum": 213,
                      "average": 213
                    }
                  ],
                  "name": "quote.author.mediaCount"
                },
                ...,
                {
                  "count": 10,
                  "unique_count": 1,
                  "types": [
                    {
                      "name": "bool",
                      "count": 10,
                      "percentage": 100.0,
                      "sample_value": false
                    }
                  ],
                  "name": "isPinned"
                }
              ]
            },
            "_tip": "Data was minimized. Call view_data_artifact() to navigate to specific data."
          }
        }
      ]
    }
  ]
}
```

### Handle a long-running task

If the remote agent takes longer than `A2A_MCP_SEND_MESSAGE_TIMEOUT` (default: 60 seconds), `send_message` returns the task in its current state:

```
send_message({
  "agent_id": "tweet-search",
  "message": "Find tweets about AI from today (January 12, 2026)"
})
```

```json
{
  "id": "tsk-123",
  "context_id": "ctx-123",
  "kind": "task",
  "status": {
    "state": "working",
    "message": null
  },
  "artifacts": []
}
```

Use `get_task` to check progress:

```
get_task({
  "agent_id": "tweet-search",
  "task_id": "tsk-123"
})
```

When complete, the response matches the format shown in [Send a message](#send-a-message). If still working, call `get_task` again to continue monitoring.

### Multi-turn conversation

Use `context_id` to continue a conversation:

```
send_message({
  "agent_id": "tweet-search",
  "message": "Can you summarize each of the 10 tweets in the table in 3-5 words each? Just give me a simple list with the author name and summary.",
  "context_id": "ctx-123"
})
```

```json
{
  "id": "tsk-456",
  "context_id": "ctx-123",
  "kind": "task",
  "status": {
    "state": "completed",
    "message": {
      "context_id": "ctx-123",
      "kind": "message",
      "parts": [
        {
          "kind": "text",
          "text": "Here is a simple list of each tweet's author and a 3-5 word summary:\n\n1. alienofeth – Real-time STT intent detection\n2. UnderdogEth_ – AI ownership discussion thread\n3. Count_Down_000 – Learning new vocabulary word\n4. ThaJonseBoy – AI and market predictions\n5. Evelyn852422353 – AI model comparison debate\n6. SyrilTchouta – Language learning with AI\n7. cx. – AI in marketing insights\n8. Halosznn_ – Graphic design course shared\n9. xmaquina – AI smarter models discussion\n10. Flagm8_ – AI and business strategy\n\nLet me know if you want more details or a different format!"
        }
      ]
    }
  },
  "artifacts": [
    {
      "artifact_id": "art-456",
      "description": "A simple list of each tweet's author and a 3-5 word summary of the tweet content.",
      "name": "AI Tweet Summaries 3-5 Words",
      "parts": [
        {
          "kind": "data",
          "data": {
            "records": [
              {
                "author.userName": "ai_q2_",
                "summary": "Possibly understand"
              },
              ...,
              {
                "author.userName": "CallStackTech",
                "summary": "Real-time STT intent detection"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### View data artifact

```
view_data_artifact({
  "agent_id": "tweet-search",
  "task_id": "tsk-123",
  "artifact_id": "art-123",
  "json_path": "records",
  "rows": "all",
  "columns": ["author.userName", "text"]
})
```

```json
{
  "artifact_id": "art-123",
  "description": "Tweets about AI posted on January 12, 2026.",
  "name": "AI Tweets from January 12, 2026",
  "parts": [
    {
      "kind": "data",
      "data": [
        {
          "author.userName": "ai_q2_",
          "text": "@nyank_x わかるかもしれない"
        },
        ...,
        {
          "author.userName": "CallStackTech",
          "text": "Just built a real-time STT pipeline that detects intent faster than you can say \"Hello!\" 🎤✨ Discover how I used Deepgram to achieve su...\n\n🔗 https://t.co/dgbvdlATZ0\n\n#VoiceAI #AI #BuildInPublic"
        }
      ]
    }
  ]
}
```

## 💾 Data Storage

Tasks and file artifacts are persisted locally at `~/.a2a-mcp/`:

- **Tasks**: `~/.a2a-mcp/tasks/`
- **Files**: `~/.a2a-mcp/files/`

Both can be disabled via environment variables (`A2A_MCP_TASK_STORE=false`, `A2A_MCP_FILE_STORE=false`).

## 🔧 Development

### Claude Desktop Setup

For local development:

1. Clone the repository: `git clone https://github.com/a2anet/a2a-mcp.git`
2. Download [Claude for Desktop](https://claude.com/download).
3. Add to the below to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "a2a": {
      "command": "uv",
      "args": ["--directory", "/path/to/a2a-mcp", "run", "a2anet-mcp"],
      "env": {
        "A2A_MCP_AGENT_CARDS": "{\"tweet-search\": {\"url\": \"https://example.com/.well-known/agent-card.json\"}}"
      }
    }
  }
}
```

## 📄 License

`a2anet` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.

## 🤝 Join the A2A Net Community

A2A Net is a site to find and share AI agents and open-source community. Join to share your A2A agents, ask questions, stay up-to-date with the latest A2A news, be the first to hear about open-source releases, tutorials, and more!

- 🌍 Site: [A2A Net](https://a2anet.com)
- 🤖 Discord: [Join the Discord](https://discord.gg/674NGXpAjU)
