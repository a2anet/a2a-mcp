# A2A MCP Server

An [MCP server](https://modelcontextprotocol.io/specification/latest/server) that implements an [A2A Client](https://a2a-protocol.org/latest/topics/key-concepts/#core-actors-in-a2a-interactions) for the [A2A Protocol](https://a2a-protocol.org/latest/).
The server can be used to connect and send messages to A2A Servers (remote agents).

The server needs to be initialised with one or more [Agent Card](https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/) URLs, each of which can have custom headers for authentication, configuration, etc.

Agents and their skills can be viewed with the `list_available_agents` tool, messages can be sent to the agents with the `send_message_to_agent` tool, and [Artifacts](https://a2a-protocol.org/latest/topics/key-concepts/#artifacts) that would overload the context can be viewed with `view_text_artifact` and `view_data_artifact` tools.

## ✨ Features

- Connect to any A2A Agent
- Use custom headers for authentication and configuration
- View Agent Cards and Skills
- Send messages to agents
- Continue conversations with agents
- View Artifacts that would overload the context
- Agent conversations are stored in JSON format

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
        "A2A_AGENT_CARDS": "[{\"url\": \"https://example.com/.well-known/agent-card.json\"}]"
      }
    }
  }
}
```

> **Tip:** If you don't have an Agent Card URL
>
> 1. Create an account on [A2A Net](https://a2anet.com/)
> 2. Pick an agent (e.g. "Tweet Search")
> 3. Take its URL and add `/agent-card.json` to the end of it (e.g. `https://a2anet.com/agent/7TaFj4YlbpngypjX74zl/agent-card.json`)
> 4. Go to [Dashboard](https://a2anet.com/dashboard)
> 5. Click "+ Create Key" > Name your key (e.g. "Test") > Click "Create"
> 6. Set `A2A_AGENT_CARDS` to the Agent Card URL and API key (e.g. `"[{\"url\": \"https://a2anet.com/agent/7TaFj4YlbpngypjX74zl/agent-card.json\"}, \"custom_headers\": {\"X-API-Key\": \"a2anet_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\"}]"`)

## ⚙️ Configuration

`A2A_AGENT_CARDS` should be a JSON stringified list of objects. Each object must have a `url` key with the full path to the Agent Card. It can optionally have a `custom_headers` key with an object in the form `{"header": "value"}`:

```bash
export A2A_AGENT_CARDS='[
  {
    "url": "https://example.com/.well-known/agent-card.json",
    "custom_headers": {"X-API-Key": "your-key"} # Optional
  }
]'
```

## 🛠️ Tools

### `list_available_agents`

Discover available agents and their capabilities.

### `send_message_to_agent`

Send a message to an agent.

| Parameter    | Required | Description                             |
| ------------ | -------- | --------------------------------------- |
| `agent_name` | Yes      | Agent name from `list_available_agents` |
| `message`    | Yes      | Your message or request                 |
| `context_id` | No       | Continue an existing conversation       |

### `view_text_artifact`

View text content from an artifact with optional line range selection.

| Parameter     | Required | Description                               |
| ------------- | -------- | ----------------------------------------- |
| `context_id`  | Yes      | Conversation context ID                   |
| `artifact_id` | Yes      | Artifact to view                          |
| `line_start`  | No       | Starting line number (1-based, inclusive) |
| `line_end`    | No       | Ending line number (1-based, inclusive)   |

### `view_data_artifact`

View structured data from an artifact with optional filtering.

| Parameter     | Required | Description                                         |
| ------------- | -------- | --------------------------------------------------- |
| `context_id`  | Yes      | Conversation context ID                             |
| `artifact_id` | Yes      | Artifact to view                                    |
| `json_path`   | No       | Dot-separated path to extract specific fields       |
| `rows`        | No       | Row selection (index, list, range string, or "all") |
| `columns`     | No       | Column selection (name, list, or "all")             |

## 📖 Examples

### List agents

```
list_available_agents()
```

```json
{
  "agents": [
    {
      "name": "Twitter Agent",
      "description": "Find and analyze tweets",
      "skills": ["Find Tweets", "Analyze Sentiment"]
    }
  ],
  "count": 1
}
```

### Send a message

```
send_message_to_agent(
  agent_name="Twitter Agent",
  message="Find tweets about AI from today"
)
```

```json
{
  "context_id": "ctx-xyz789",
  "status": {
    "state": "completed",
    "message": {
      "parts": [
        { "type": "text", "text": "Found 25 tweets about AI." }
      ]
    }
  },
  "artifacts": [
    {
      "artifact_id": "art-456",
      "name": "Tweet Results",
      "parts": [
        {
          "type": "data",
          "data": {
            "_total_rows": 25,
            "_columns": [...],
            "_tip": "Table data was minimized. Use view_data_artifact to view specific data."
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
send_message_to_agent(
  agent_name="Twitter Agent",
  message="Filter to only verified accounts",
  context_id="ctx-xyz789"
)
```

```json
{
  "context_id": "ctx-xyz789",
  "status": {
    "state": "completed",
    "message": {
      "parts": [
        { "type": "text", "text": "Filtered to 8 tweets from verified accounts." }
      ]
    }
  },
  "artifacts": [...]
}
```

### View data artifact

```
view_data_artifact(
  context_id="ctx-xyz789",
  artifact_id="art-456",
  rows="0-5",
  columns=["author", "text"]
)
```

```json
{
  "artifact_id": "art-456",
  "name": "Tweet Results",
  "total_rows": 25,
  "total_columns": 5,
  "selected_rows": 5,
  "selected_columns": 2,
  "available_columns": ["id", "author", "text", "likes", "retweets"],
  "data": [
    { "author": "@techwriter", "text": "AI is transforming..." },
    { "author": "@ainews", "text": "Breaking: New model..." }
  ]
}
```

## 💾 Data Storage

Agent conversations are stored in JSON format to a standard path and can be inspected.

- **Linux**: `~/.local/share/a2anet-mcp/conversations/`
- **macOS**: `~/Library/Application Support/a2anet-mcp/conversations/`
- **Windows**: `AppData/Local/A2ANet/a2anet-mcp/conversations/`

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
        "A2A_AGENT_CARDS": "[{\"url\": \"https://example.com/.well-known/agent-card.json\"}]"
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
