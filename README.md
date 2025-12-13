# A2A MCP Server

A Model Context Protocol (MCP) server that connects Claude and other LLMs to the [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/latest/). This server enables LLMs to interact with multiple A2A-compatible agents through a unified, structured interface.

The A2A protocol standardizes agent communication by introducing concepts like **Agent Cards**, **Tasks**, **Artifacts**, **Context**, and more. This MCP server bridges the gap between MCP-compatible LLMs (like Claude Desktop) and any A2A-compatible agent, allowing you to build powerful multi-agent workflows.

## ✨ Features

- **Multi-Agent Support** - Connect to multiple A2A agents simultaneously from a single MCP server
- **Conversation Management** - Track multi-turn conversations with automatic context and task state tracking
- **Persistent Conversations** - Conversations automatically saved to disk and survive server restarts
- **Structured Responses** - Get JSON-formatted responses with task metadata, agent messages, and artifacts
- **Smart Response Minimization** - Automatically minimize large datasets (shows first/last items) to avoid overwhelming LLMs
- **Powerful Artifact Filtering** - Filter artifacts using regex, JSON path, or field extraction without additional LLM calls
- **Name Conflict Resolution** - Automatically handles duplicate agent names with intelligent suffixing
- **Parallel Agent Loading** - Fetches and initializes agent cards in parallel for fast startup
- **Custom Headers Support** - Add authentication headers per-agent or globally
- **Type-Safe** - Written in Python with full type hints and strict mypy checking

## 📋 Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- An MCP-compatible client (like [Claude Desktop](https://claude.ai/download))
- At least one A2A-compatible agent (see [A2A Net](https://a2anet.com/) for examples)

## 📦 Installation

This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable dependency management.

```bash
# Clone the repository
git clone https://github.com/A2ANet/a2a-mcp.git
cd a2a-mcp

# Install dependencies
uv sync
```

## ⚡ Quick Start

### 1. Configure Your Agents

Set the `A2A_AGENT_CARDS` environment variable with your agent configuration:

```bash
export A2A_AGENT_CARDS='[
  {
    "url": "https://a2anet.com/agent/YOUR_AGENT_ID/agent-card.json",
    "custom_headers": {
      "X-API-Key": "your-api-key-here"
    }
  }
]'
```

For multiple agents:

```bash
export A2A_AGENT_CARDS='[
  {
    "url": "https://a2anet.com/agent/twitter/agent-card.json",
    "custom_headers": {"X-API-Key": "twitter-key"}
  },
  {
    "url": "https://a2anet.com/agent/analytics/agent-card.json",
    "custom_headers": {"Authorization": "Bearer analytics-token"}
  }
]'
```

### 2. Test the Server

```bash
# Run the server
uv run python main.py
```

You should see:

```
Successfully initialized 2 agent(s):
  - Twitter Agent: Find and analyze tweets by keyword, author, or URL
    Skills: Find Tweets, Filter Table, Generate Table
  - Analytics Agent: Analyze data and generate insights
    Skills: Data Analysis, Visualization, Reporting
A2A MCP Server is ready
```

### 3. Add to Claude Desktop

Edit your Claude Desktop configuration file:

**macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "a2a": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/a2a-mcp",
        "run",
        "python",
        "main.py"
      ],
      "env": {
        "A2A_AGENT_CARDS": "[{\"url\": \"https://a2anet.com/agent/YOUR_ID/agent-card.json\", \"custom_headers\": {\"X-API-KEY\": \"your-key\"}}]"
      }
    }
  }
}
```

Restart Claude Desktop and the A2A tools will be available!

## 🚀 Usage

### Available Tools

The MCP server provides three main tools:

#### 1. `send_message_to_agent`

Send a message to an A2A agent and receive a structured response.

**Parameters:**
- `agent_name` (string, required): Name of the agent (from `list_available_agents`)
- `message` (string, required): Your message or request
- `context_id` (string, optional): Context ID to continue a conversation

**Example: Start a new conversation**

```
send_message_to_agent(
  agent_name="Twitter Agent",
  message="Find tweets about AI from the last week"
)
```

**Response:**

```json
{
  "task_id": "task-abc123",
  "context_id": "ctx-xyz789",
  "task_state": "completed",
  "agent_message": "I found 50 tweets about AI from the last week.",
  "artifacts": [
    {
      "artifact_id": "art-456",
      "name": "AI Tweets",
      "description": "Search results for tweets about AI",
      "parts": [
        {
          "type": "data",
          "data": {
            "_type": "minimized_list",
            "length": 50,
            "first": {
              "text": "AI is transforming healthcare...",
              "author": "@techexpert",
              "likes": 142
            },
            "last": {
              "text": "Latest AI research breakthrough...",
              "author": "@airesearcher",
              "likes": 89
            }
          }
        }
      ]
    }
  ],
  "tips": [
    "Use view_artifact to see full artifact content or apply filters (regex, json_path, field)",
    "Task completed successfully. You can start a new conversation or view artifacts for details."
  ]
}
```

**Example: Continue a conversation**

```
send_message_to_agent(
  agent_name="Twitter Agent",
  message="Show only tweets from verified accounts",
  context_id="ctx-xyz789"
)
```

#### 2. `view_artifact`

View and filter artifacts with powerful filtering options.

**Parameters:**
- `agent_name` (string, required): Agent that created the artifact
- `context_id` (string, required): Context ID from the conversation
- `artifact_id` (string, required): Artifact ID to view
- `filter_type` (string, optional): Filter type - `"none"`, `"regex"`, `"json_path"`, or `"field"`
- `filter_value` (string, optional): Filter pattern or path

**Example: View full artifact**

```
view_artifact(
  agent_name="Twitter Agent",
  context_id="ctx-xyz789",
  artifact_id="art-456"
)
```

**Example: Extract usernames with regex**

```
view_artifact(
  agent_name="Twitter Agent",
  context_id="ctx-xyz789",
  artifact_id="art-456",
  filter_type="regex",
  filter_value="@\\w+"
)
```

**Response:**

```json
{
  "artifact_id": "art-456",
  "filter_type": "regex",
  "pattern": "@\\w+",
  "matches": ["@techexpert", "@airesearcher", "@mlpractitioner"],
  "match_count": 3,
  "tips": [
    "Regex patterns are applied to the entire artifact. Use capturing groups to extract specific parts."
  ]
}
```

**Example: Extract specific field with JSON path**

```
view_artifact(
  agent_name="Twitter Agent",
  context_id="ctx-xyz789",
  artifact_id="art-456",
  filter_type="json_path",
  filter_value="tweets[0].author.name"
)
```

**Response:**

```json
{
  "artifact_id": "art-456",
  "filter_type": "json_path",
  "path": "tweets[0].author.name",
  "results": ["Tech Expert"],
  "result_count": 1,
  "tips": [
    "Try accessing nested fields with paths like 'data[0].field' or 'items[*].name'"
  ]
}
```

#### 3. `list_available_agents`

List all available A2A agents with their capabilities.

**Example:**

```
list_available_agents()
```

**Response:**

```json
{
  "agents": [
    {
      "name": "Twitter Agent",
      "description": "Find and analyze tweets by keyword, author, or URL",
      "skills": ["Find Tweets", "Filter Table", "Generate Table"],
      "url": "https://a2anet.com/agent/twitter/agent-card.json"
    },
    {
      "name": "Analytics Agent",
      "description": "Analyze data and generate insights from various sources",
      "skills": ["Data Analysis", "Visualization", "Reporting"],
      "url": "https://a2anet.com/agent/analytics/agent-card.json"
    }
  ],
  "count": 2,
  "tips": [
    "Use the agent name exactly as shown when calling send_message_to_agent",
    "Check the skills list to understand what each agent can do"
  ]
}
```

## 🧩 Core Concepts

### The A2A Protocol

The [A2A Protocol](https://a2a-protocol.org/latest/) is like HTTP for AI agents. Just as HTTP standardized web communication, A2A standardizes agent-to-agent communication with concepts like:

- **Agent Card**: Metadata about an agent (name, description, skills, endpoints)
- **Context**: A conversation thread with persistent message history
- **Task**: A unit of work with states (submitted, working, completed, failed, etc.)
- **Message**: A communication between user and agent with multiple parts
- **Artifact**: Structured outputs (documents, data, images) generated by agents
- **Parts**: Components of messages/artifacts (TextPart, DataPart, FilePart)

### Architecture

```
┌─────────────────┐
│  Claude Desktop │
│   (MCP Client)  │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────────────────────┐
│     A2A MCP Server              │
│  ┌──────────────────────────┐  │
│  │   AgentManager           │  │  Fetches agent cards
│  │   - Parallel loading     │  │  Creates A2A clients
│  │   - Name conflict res.   │  │  Manages headers
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │   ConversationManager    │  │  Tracks conversations
│  │   - Context tracking     │  │  Stores artifacts
│  │   - Task state           │  │  Message history
│  └────────────┬─────────────┘  │
│               │                 │
│  ┌────────────▼─────────────┐  │
│  │   Persistence Layer      │  │  JSON file storage
│  │   - Auto save/load       │  │  ~/.a2a-mcp-conversations/
│  │   - Survives restarts    │  │  Per-conversation files
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │   Response Minimizer     │  │  Minimizes large data
│  │   - List truncation      │  │  Shows first/last
│  │   - Nested handling      │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │   ArtifactFilter         │  │  Regex filtering
│  │   - JSON path queries    │  │  Field extraction
│  │   - Field extraction     │  │  Pattern matching
│  └──────────────────────────┘  │
└────────┬────────────────────────┘
         │ A2A Protocol (HTTP/JSON)
         │
         │     ┌─────────────────┐
         ├─────▶  Twitter Agent  │
         │     └─────────────────┘
         │     ┌─────────────────┐
         ├─────▶ Analytics Agent │
         │     └─────────────────┘
         │     ┌─────────────────┐
         └─────▶   Your Agent    │
               └─────────────────┘
```

### Project Structure

```
a2a-mcp/
├── main.py                      # Entry point, initialization
├── src/
│   ├── __init__.py             # Package initialization
│   ├── types.py                # Data models (AgentInfo, ConversationState)
│   ├── config.py               # Configuration loading (env/file)
│   ├── agent_manager.py        # Agent card fetching & client management
│   ├── conversation_manager.py # Conversation state tracking
│   ├── persistence.py          # JSON-based conversation persistence
│   ├── response_minimizer.py   # Large response minimization
│   ├── artifact_filter.py      # Artifact filtering (regex/json_path/field)
│   └── server.py               # MCP server & tool handlers
├── pyproject.toml              # Project config, dependencies
└── README.md                   # This file
```

### Key Components

#### AgentManager

Manages the lifecycle of A2A agent connections:

- Fetches agent cards in parallel for fast startup
- Creates and configures A2A clients with custom headers
- Resolves name conflicts (e.g., "Twitter Agent" → "Twitter Agent (2)")
- Provides agent discovery and lookup

#### ConversationManager

Tracks conversation state across multiple turns:

- Manages context IDs for conversation continuity
- Stores task IDs and task states
- Maintains message history
- Caches both full and minimized artifacts
- **Persists conversations to disk** - Survives server restarts

**Persistence Location**: Conversations are automatically saved to `~/.a2a-mcp-conversations/` as JSON files. Each conversation is stored separately and loaded on server startup, so you can continue conversations even after restarting the MCP server or Claude Desktop.

#### Response Minimizer

Prevents context overflow by intelligently minimizing large responses:

- Lists with 3+ items show only first and last
- Nested structures are minimized recursively
- Preserves structure with `_type: "minimized_list"`
- Keeps originals available via `view_artifact`

#### ArtifactFilter

Provides fast, efficient filtering without LLM involvement:

- **Regex**: Pattern matching across text and JSON
- **JSON Path**: Extract nested fields (e.g., `users[0].profile.name`)
- **Field**: Get top-level fields only
- **None**: Return full artifact

## 🔧 Configuration

### Environment Variables

```bash
# Required: JSON array of agent card configurations
export A2A_AGENT_CARDS='[
  {
    "url": "https://a2anet.com/agent/YOUR_AGENT_ID/agent-card.json",
    "custom_headers": {
      "X-API-Key": "your-key",
      "Authorization": "Bearer token"
    }
  }
]'

# Optional: Global headers applied to all agents
export A2A_GLOBAL_HEADERS='{"User-Agent": "A2A-MCP-Server/1.0"}'
```

### Configuration File (Alternative)

Create a `config.json` file:

```json
{
  "agent_cards": [
    {
      "url": "https://a2anet.com/agent/1/agent-card.json",
      "custom_headers": {
        "X-API-Key": "secret123"
      }
    }
  ],
  "global_headers": {
    "User-Agent": "A2A-MCP-Server/1.0"
  }
}
```

Then modify `main.py`:

```python
config = A2AMCPConfig.from_file("config.json")
```

## 🛠️ Development

### Type Checking

```bash
uv run mypy src main.py
```

### Linting and Formatting

```bash
# Check code quality
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Running Tests

```bash
# Coming soon
uv run pytest
```

## 🐛 Troubleshooting

### Server Not Starting

**Problem**: Server fails to start or shows configuration error

**Solutions**:
1. Verify `A2A_AGENT_CARDS` is valid JSON
2. Check that agent card URLs are accessible
3. Ensure custom headers are properly formatted
4. Review logs in stderr for detailed error messages

```bash
# Test your configuration
uv run python main.py 2>&1 | grep -i error
```

### Agent Not Found

**Problem**: "Agent 'X' not found" when calling `send_message_to_agent`

**Solutions**:
1. Use `list_available_agents` to see loaded agents
2. Check agent card URL in `A2A_AGENT_CARDS`
3. Verify authentication headers if required
4. Check stderr logs for agent fetch errors

```bash
# Check which agents loaded successfully
uv run python main.py 2>&1 | grep "Successfully initialized"
```

### Name Conflicts

**Problem**: Multiple agents have the same name

**Solution**: The server automatically renames duplicates:
- First agent: "Twitter Agent"
- Second agent: "Twitter Agent (2)"
- Third agent: "Twitter Agent (3)"

Use the renamed version when calling tools.

### Response Too Large

**Problem**: Agent returns huge datasets that overwhelm the LLM

**Solution**: The server automatically minimizes large responses. For lists with 3+ items, only first and last are shown. Use `view_artifact` with filters to extract specific data:

```
# Instead of viewing the full artifact
view_artifact(..., filter_type="json_path", filter_value="items[0].summary")
```

## 📚 Examples

### Example 1: Multi-Turn Conversation

```python
# Step 1: Send initial message
response = send_message_to_agent(
    agent_name="Twitter Agent",
    message="Find tweets about Python from today"
)
# Extract context_id from response
context_id = response["context_id"]

# Step 2: Continue conversation
response = send_message_to_agent(
    agent_name="Twitter Agent",
    message="Filter to show only tweets with more than 100 likes",
    context_id=context_id
)

# Step 3: View specific artifact
view_artifact(
    agent_name="Twitter Agent",
    context_id=context_id,
    artifact_id=response["artifacts"][0]["artifact_id"],
    filter_type="json_path",
    filter_value="tweets[*].text"
)
```

### Example 2: Using Multiple Agents

```python
# List available agents
agents = list_available_agents()

# Use different agents for different tasks
twitter_response = send_message_to_agent(
    agent_name="Twitter Agent",
    message="Find recent tweets about 'climate change'"
)

analytics_response = send_message_to_agent(
    agent_name="Analytics Agent",
    message="Analyze sentiment trends in climate discussions"
)
```

### Example 3: Advanced Filtering

```python
# Get artifact
response = send_message_to_agent(
    agent_name="Data Agent",
    message="Get user database"
)

artifact_id = response["artifacts"][0]["artifact_id"]
context_id = response["context_id"]

# Extract all email addresses with regex
emails = view_artifact(
    agent_name="Data Agent",
    context_id=context_id,
    artifact_id=artifact_id,
    filter_type="regex",
    filter_value=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# Extract nested user data with JSON path
user_names = view_artifact(
    agent_name="Data Agent",
    context_id=context_id,
    artifact_id=artifact_id,
    filter_type="json_path",
    filter_value="users[*].profile.displayName"
)
```

## 🗺️ Roadmap

- [x] Multi-agent support
- [x] Conversation management
- [x] Response minimization
- [x] Artifact filtering (regex, JSON path, field)
- [x] Structured JSON responses
- [x] Tips and guidance in responses
- [x] Conversation persistence (JSON-based)
- [ ] File part support (images, documents)
- [ ] Streaming responses
- [ ] Agent push notifications
- [ ] Built-in caching layer
- [ ] Retry logic with exponential backoff
- [ ] Agent health monitoring
- [ ] Database persistence (SQLite/PostgreSQL)
- [ ] WebSocket support
- [ ] CI/CD pipeline
- [ ] Comprehensive test suite
- [ ] Docker support
- [ ] Contributing guidelines

## 📄 License

Apache 2.0 - See LICENSE file for details

## 🤝 Join the A2A Net Community

A2A Net is a community for discovering and sharing AI agents built on open standards.

- 🌍 **Website**: [https://a2anet.com/](https://a2anet.com/)
- 🤖 **Discord**: [https://discord.gg/674NGXpAjU](https://discord.gg/674NGXpAjU)
- 📖 **A2A Protocol Spec**: [https://a2a-protocol.org/latest/](https://a2a-protocol.org/latest/)
- 🐙 **GitHub**: [https://github.com/A2ANet](https://github.com/A2ANet)

Share your A2A agents, ask questions, stay up-to-date with the latest A2A news, and be the first to hear about releases, tutorials, and more!

## 🙏 Acknowledgments

- Built with the [A2A SDK](https://github.com/a2aproject/a2a-js)
- Powered by the [MCP Protocol](https://modelcontextprotocol.io/)
- Inspired by the vision of standardized agent communication
