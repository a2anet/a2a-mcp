# A2A MCP Server

[![PyPI - Version](https://img.shields.io/pypi/v/a2anet-mcp.svg)](https://pypi.org/project/a2anet-mcp) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/a2anet-mcp.svg)](https://pypi.org/project/a2anet-mcp) [![PyPI - Downloads](https://img.shields.io/pypi/dm/a2anet-mcp)](https://pypi.org/project/a2anet-mcp) [![License](https://img.shields.io/github/license/a2anet/a2a-mcp)](https://github.com/a2anet/a2a-mcp/blob/main/LICENSE) [![Tests](https://github.com/a2anet/a2a-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/a2anet/a2a-mcp/actions/workflows/ci.yml) [![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-blue)](https://a2a-protocol.org) [![MCP](https://img.shields.io/badge/MCP-Server-orange)](https://modelcontextprotocol.io) [![Discord](https://img.shields.io/discord/1391916121589944320?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/674NGXpAjU)

An [MCP server](https://modelcontextprotocol.io/specification/latest/server) that implements an [A2A Client](https://a2a-protocol.org/latest/topics/key-concepts/#core-actors-in-a2a-interactions) for the [A2A Protocol](https://a2a-protocol.org/latest/).
The server can be used to connect and send messages to A2A Servers (remote agents).

The server needs to be initialised with one or more [Agent Card](https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/) URLs, each of which can have custom headers for authentication, configuration, etc.

All agents (name and description) can be viewed with the `get_agents` tool, an agent's skills (name and description) can be viewed with the `get_agent` tool, Messages can be sent to the agents with the `send_message` tool, long-running Tasks can be polled with `get_task`, and [Artifacts](https://a2a-protocol.org/latest/topics/key-concepts/#artifacts) can be viewed with `view_text_artifact` and `view_data_artifact` tools.

## ✨ Features

- Connect to any A2A Agent
- Use custom headers for authentication and configuration
- View Agent Cards and Skills
- Send Messages to agents
- Poll long-running Tasks
- Continue conversations with agents
- View Artifacts that would overload the context
- Tasks are stored in JSON format in `~/.a2a-mcp/tasks/`
- File bytes and URLs are converted and downloaded to `~/.a2a-mcp/files/`
- Configurable timeouts

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
    {
      "name": "View Table",
      "description": "View specific rows and columns from any table, ask questions about it, and analyse it with AI. If the agent performs searches, explain which rows are good and bad to improve the search."
    },
    {
      "name": "Filter Table",
      "description": "Filter any table with traditional filtering (i.e. patterns like names, URLs, etc). Explain what table you want to filter, and what rows you want to keep or remove."
    },
    {
      "name": "Filter Table with AI",
      "description": "Filter any table with AI filtering (i.e. reasoning, semantic understanding, etc). Explain what table you want to filter, and what rows you want to keep or remove."
    },
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
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "context_id": "cc9b9234-ecb7-4938-901a-a79912b8239f",
  "kind": "task",
  "status": {
    "state": "completed",
    "message": {
      "context_id": "cc9b9234-ecb7-4938-901a-a79912b8239f",
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
      "artifact_id": "97157147-db9f-490c-bc56-5603c99fd23b",
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

### Multi-turn conversation

Use `context_id` to continue a conversation:

```
send_message({
  "agent_id": "tweet-search",
  "message": "Can you summarize each of the 10 tweets in the table in 3-5 words each? Just give me a simple list with the author name and summary.",
  "context_id": "cc9b9234-ecb7-4938-901a-a79912b8239f"
})
```

```json
{
  "id": "f8e7d6c5-b4a3-2109-fedc-ba9876543210",
  "context_id": "cc9b9234-ecb7-4938-901a-a79912b8239f",
  "kind": "task",
  "status": {
    "state": "completed",
    "message": {
      "context_id": "cc9b9234-ecb7-4938-901a-a79912b8239f",
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
      "artifact_id": "ed350a03-c6ef-4154-9163-6c56418ee7a7",
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
              {
                "author.userName": "UnderdogEth_",
                "summary": "AI evolving into reliable teammate"
              },
              {
                "author.userName": "Heisrollo",
                "summary": "AI takeover in industry"
              },
              {
                "author.userName": "_Fabichou_",
                "summary": "Learned new word 'Unendlich'"
              },
              {
                "author.userName": "alienofeth",
                "summary": "AI ownership over smarter models"
              },
              {
                "author.userName": "painted_by_ai",
                "summary": "New Year greetings with superheroes"
              },
              {
                "author.userName": "Pereira_Guto2",
                "summary": "Norman absent due illness"
              },
              {
                "author.userName": "HamzatMusaOpey1",
                "summary": "WEEX AI Trading Hackathon"
              },
              {
                "author.userName": "Count_Down_000",
                "summary": "Self-taught AI philosophy learner"
              },
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
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "artifact_id": "97157147-db9f-490c-bc56-5603c99fd23b",
  "json_path": "records",
  "rows": "all",
  "columns": ["author.userName", "text"]
})
```

```json
{
  "artifact_id": "97157147-db9f-490c-bc56-5603c99fd23b",
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
        {
          "author.userName": "UnderdogEth_",
          "text": "@ThaJonseBoy @HeyElsaAI @HeyElsaAI is turning AI from a tool you use into a teammate you actually rely on."
        },
        {
          "author.userName": "Heisrollo",
          "text": "As you're learning this, you should understand it's one of the industries AI is about to completely takeover."
        },
        {
          "author.userName": "_Fabichou_",
          "text": "@SyrilTchouta Unendlich😌 j'ai appris un nouveau mot"
        },
        {
          "author.userName": "alienofeth",
          "text": "@Evelyn852422353 @xmaquina @xmaquina is about AI ownership, not just smarter models."
        },
        {
          "author.userName": "painted_by_ai",
          "text": "#ClarkKent #BruceWayne #superbat\n新年明けましておめでとうございます(遅い) https://t.co/ShvzHBUvPJ"
        },
        {
          "author.userName": "Pereira_Guto2",
          "text": "@Amzng_Peter Acho tão engraçado que no primeiro filme não temos o Norman pq ele tava morrendo dessa doença e não tínhamos esse contexto, mas aí tínhamos o capanga genérico n1 falando pro Connors terminar o soro do lagarto"
        },
        {
          "author.userName": "HamzatMusaOpey1",
          "text": "@WEEX_Official 📢 WEEX AI Trading Hackathon is Here Again!!! 🔊🔊🔊\n\n@WEEX_Official AI trading /WEEX AI Hackathon is the best AI Trading I've ever used. It's accurate, reliable, and bug free."
        },
        {
          "author.userName": "Count_Down_000",
          "text": "@grok In other words, I am simply a self-taught person who is using the skills I gained from taking Japanese entrance exams, especially the Japanese and English reading comprehension questions, to learn about the philosophy and knowledge system behind the AI ​​GROK and Gemini. https://t.co/IVf2mjGGX6"
        },
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
