# A2A MCP Server

[![PyPI - Version](https://img.shields.io/pypi/v/a2anet-mcp.svg)](https://pypi.org/project/a2anet-mcp) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/a2anet-mcp.svg)](https://pypi.org/project/a2anet-mcp) [![PyPI - Downloads](https://img.shields.io/pypi/dm/a2anet-mcp)](https://pypi.org/project/a2anet-mcp) [![License](https://img.shields.io/github/license/a2anet/a2a-mcp)](https://github.com/a2anet/a2a-mcp/blob/main/LICENSE) [![Tests](https://github.com/a2anet/a2a-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/a2anet/a2a-mcp/actions/workflows/ci.yml) [![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-blue)](https://a2a-protocol.org) [![MCP](https://img.shields.io/badge/MCP-Server-orange)](https://modelcontextprotocol.io) [![Discord](https://img.shields.io/discord/1391916121589944320?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/674NGXpAjU)

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

> **Tip:** If you don't have an Agent Card URL, see: [A2A Net Demo](https://github.com/a2anet/a2anet-demo)

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
list_available_agents({})
```

```json
{
  "agents": [
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
      ],
      "url": "https://a2anet.com/agent/7TaFj4YlbpngypjX74zl/agent-card.json"
    }
  ],
  "count": 1,
  "tips": [
    "Use the agent name exactly as shown when calling send_message_to_agent",
    "Check the skills list to understand what each agent can do"
  ]
}
```

### Send a message

```
send_message_to_agent({
  `message`: `Find tweets about AI from today (January 12, 2026)`,
  `agent_name`: `Tweet Search`
})
```

```json
{
  "context_id": "cc9b9234-ecb7-4938-901a-a79912b8239f",
  "status": {
    "state": "completed",
    "message": {
      "parts": [
        {
          "type": "text",
          "text": "I found 10 tweets about \"AI\" posted on January 12, 2026. The search parameters used were:\n\n- Search Terms: AI\n- Start Date: 2026-01-12\n- End Date: 2026-01-13\n- Maximum Items: 10\n\nWould you like to see more tweets, or do you want a summary or analysis of these results?"
        }
      ]
    }
  },
  "artifacts": [
    {
      "artifact_id": "97157147-db9f-490c-bc56-5603c99fd23b",
      "name": "AI Tweets from January 12, 2026",
      "description": "Tweets about AI posted on January 12, 2026.",
      "parts": [
        {
          "type": "data",
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
            "_tip": "Object was minimized (original: 60,971 chars). String values truncated to 100 chars. Lists summarized. Use json_path to access specific fields, with rows/columns for list data."
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
send_message_to_agent({
  `message`: `Can you summarize each of the 10 tweets in the table in 3-5 words each? Just give me a simple list with the author name and summary.`,
  `agent_name`: `Tweet Search`,
  `context_id`: `cc9b9234-ecb7-4938-901a-a79912b8239f`
})
```

```json
{
  "context_id": "cc9b9234-ecb7-4938-901a-a79912b8239f",
  "status": {
    "state": "completed",
    "message": {
      "parts": [
        {
          "type": "text",
          "text": "Here is a simple list of each tweet's author and a 3-5 word summary:\n\n1. alienofeth \u2013 Real-time STT intent detection\n2. UnderdogEth_ \u2013 AI ownership discussion thread\n3. Count_Down_000 \u2013 Learning new vocabulary word\n4. ThaJonseBoy \u2013 AI and market predictions\n5. Evelyn852422353 \u2013 AI model comparison debate\n6. SyrilTchouta \u2013 Language learning with AI\n7. cx. \u2013 AI in marketing insights\n8. Halosznn_ \u2013 Graphic design course shared\n9. xmaquina \u2013 AI smarter models discussion\n10. Flagm8_ \u2013 AI and business strategy\n\nLet me know if you want more details or a different format!"
        }
      ]
    }
  },
  "artifacts": [
    {
      "artifact_id": "ed350a03-c6ef-4154-9163-6c56418ee7a7",
      "name": "AI Tweet Summaries 3-5 Words",
      "description": "A simple list of each tweet's author and a 3-5 word summary of the tweet content.",
      "parts": [
        {
          "type": "data",
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
  `rows`: `all`,
  `columns`: [
    `author.userName`,
    `text`
  ],
  `json_path`: `records`,
  `context_id`: `cc9b9234-ecb7-4938-901a-a79912b8239f`,
  `artifact_id`: `97157147-db9f-490c-bc56-5603c99fd23b`
})
```

```json
{
  "artifact_id": "97157147-db9f-490c-bc56-5603c99fd23b",
  "name": "AI Tweets from January 12, 2026",
  "json_path": "records",
  "total_rows": 10,
  "total_columns": 55,
  "selected_rows": 10,
  "selected_columns": 2,
  "available_columns": [
    "type",
    "id",
    "url",
    "twitterUrl",
    "text",
    "fullText",
    "source",
    "retweetCount",
    "replyCount",
    "likeCount",
    "quoteCount",
    "createdAt",
    "lang",
    "bookmarkCount",
    "isReply",
    "inReplyToId",
    "conversationId",
    "inReplyToUserId",
    "inReplyToUsername",
    "isPinned",
    "author.type",
    "author.userName",
    "author.url",
    "author.twitterUrl",
    "author.id",
    "author.name",
    "author.isBlueVerified",
    "author.profilePicture",
    "author.coverPicture",
    "author.description",
    "author.followers",
    "author.following",
    "author.status",
    "author.canDm",
    "author.canMediaTag",
    "author.createdAt",
    "author.entities.description.urls",
    "author.fastFollowersCount",
    "author.favouritesCount",
    "author.hasCustomTimelines",
    "author.isTranslator",
    "author.mediaCount",
    "author.statusesCount",
    "author.withheldInCountries",
    "author.possiblySensitive",
    "author.pinnedTweetIds",
    "entities.hashtags",
    "entities.symbols",
    "entities.timestamps",
    "entities.urls",
    "entities.user_mentions",
    "isRetweet",
    "isQuote",
    "media",
    "isConversationControlled"
  ],
  "data": [
    {
      "author.userName": "ai_q2_",
      "text": "@nyank_x \u308f\u304b\u308b\u304b\u3082\u3057\u308c\u306a\u3044"
    },
    {
      "author.userName": "UnderdogEth_",
      "text": "@ThaJonseBoy @HeyElsaAI @HeyElsaAI is turning AI from a tool you use into a teammate you actually rely on."
    },
    {
      "author.userName": "Heisrollo",
      "text": "As you\u2019re learning this, you should understand it\u2019s one of the industries AI is about to completely takeover."
    },
    {
      "author.userName": "_Fabichou_",
      "text": "@SyrilTchouta Unendlich\ud83d\ude0c j'ai appris un nouveau mot"
    },
    {
      "author.userName": "alienofeth",
      "text": "@Evelyn852422353 @xmaquina @xmaquina is about AI ownership, not just smarter models."
    },
    {
      "author.userName": "painted_by_ai",
      "text": "#ClarkKent #BruceWayne #superbat\n\u65b0\u5e74\u660e\u3051\u307e\u3057\u3066\u304a\u3081\u3067\u3068\u3046\u3054\u3056\u3044\u307e\u3059(\u9045\u3044) https://t.co/ShvzHBUvPJ"
    },
    {
      "author.userName": "Pereira_Guto2",
      "text": "@Amzng_Peter Acho t\u00e3o engra\u00e7ado que no primeiro filme n\u00e3o temos o Norman pq ele tava morrendo dessa doen\u00e7a e n\u00e3o t\u00ednhamos esse contexto, mas a\u00ed t\u00ednhamos o capanga gen\u00e9rico n1 falando pro Connors terminar o soro do lagarto"
    },
    {
      "author.userName": "HamzatMusaOpey1",
      "text": "@WEEX_Official \ud83d\udce2 WEEX AI Trading Hackathon is Here Again!!! \ud83d\udd0a\ud83d\udd0a\ud83d\udd0a\n\n@WEEX_Official AI trading /WEEX AI Hackathon is the best AI Trading I've ever used. It's accurate, reliable, and bug free."
    },
    {
      "author.userName": "Count_Down_000",
      "text": "@grok In other words, I am simply a self-taught person who is using the skills I gained from taking Japanese entrance exams, especially the Japanese and English reading comprehension questions, to learn about the philosophy and knowledge system behind the AI \u200b\u200bGROK and Gemini. https://t.co/IVf2mjGGX6"
    },
    {
      "author.userName": "CallStackTech",
      "text": "Just built a real-time STT pipeline that detects intent faster than you can say \"Hello!\" \ud83c\udfa4\u2728 Discover how I used Deepgram to achieve su...\n\n\ud83d\udd17 https://t.co/dgbvdlATZ0\n\n#VoiceAI #AI #BuildInPublic"
    }
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
