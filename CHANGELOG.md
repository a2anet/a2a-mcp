# Changelog

## [2.0.0](https://github.com/a2anet/a2a-mcp/compare/a2anet-mcp-v1.0.3...a2anet-mcp-v2.0.0) (2026-03-26)


### ⚠ BREAKING CHANGES

* Environment variable, tool names, tool parameters, and response formats have all changed.

### Features

* add get_task, get_agent_card_from_url, add_agent tools and timeout config ([2912122](https://github.com/a2anet/a2a-mcp/commit/291212247ca85039ab540279779ffb8f24a22132))
* extract tool definitions into A2ATools from a2a-utils ([#7](https://github.com/a2anet/a2a-mcp/issues/7)) ([0fb1697](https://github.com/a2anet/a2a-mcp/commit/0fb1697bfbfd089d280bd6a6f107b95bd3726991))
* migrate server to use A2ASession and AgentManager from a2a-utils ([81e2b61](https://github.com/a2anet/a2a-mcp/commit/81e2b6103090df88f73bb2655d95f563b0d413ca))


### Bug Fixes

* surface agent initialization errors in get_agents response ([c536b1b](https://github.com/a2anet/a2a-mcp/commit/c536b1b75a63aa89a1b48abfff7940869c0318cf))

## [1.0.3](https://github.com/a2anet/a2a-mcp/compare/a2anet-mcp-v1.0.2...a2anet-mcp-v1.0.3) (2026-01-15)


### Bug Fixes

* collect columns from all rows to handle sparse data correctly ([d6da991](https://github.com/a2anet/a2a-mcp/commit/d6da991bea74613cfb2b37bf7f3d3d92c4aeed40))


### Documentation

* update tip in `README.md` to link to A2A Net Demo ([8267e3f](https://github.com/a2anet/a2a-mcp/commit/8267e3ffc9dc789c0becbc13280837d4ae85a9e5))

## [1.0.2](https://github.com/a2anet/a2a-mcp/compare/a2anet-mcp-v1.0.1...a2anet-mcp-v1.0.2) (2026-01-14)


### Bug Fixes

* increase `httpx.AsyncClient` timeout to 300s for long-running Tasks ([7051290](https://github.com/a2anet/a2a-mcp/commit/7051290e6de8567de6c44bcd7c883240afc23e23))

## [1.0.1](https://github.com/a2anet/a2a-mcp/compare/a2anet-mcp-v1.0.0...a2anet-mcp-v1.0.1) (2026-01-12)


### Bug Fixes

* return Task specific Artifacts only from `handle_send_message_to_agent` ([1d18336](https://github.com/a2anet/a2a-mcp/commit/1d183361049e018d772cdb80561857b991dfa011))


### Documentation

* add widgets to `README.md` ([24847f1](https://github.com/a2anet/a2a-mcp/commit/24847f17ae1a0caa50af59978117fa42d78acb97))
* update `README.md` with real-world examples ([9e2fb3d](https://github.com/a2anet/a2a-mcp/commit/9e2fb3d54e480b404113ed63ee89e4d2e45ba80a))
