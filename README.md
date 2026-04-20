# LPI Smart AI Agent (Level 3 & 4 Ready)

An advanced, autonomous intelligent agent that processes user queries, handles dynamic intent routing, and orchestrates LPI tools to generate grounded, structured responses.

## Key Features
- **Dynamic Tool Selection:** Automatically parses user intent (e.g., 'how', 'example', 'overview') to select the right MCP tools.
- **Multi-Tool Orchestration:** Sequentially runs multiple tools and aggregates context.
- **Structured JSON Output:** Returns clean `{query, tools_used, outputs}` objects for downstream API usage.
- **Auto-Discovery Path Hunter:** Intelligently scans directories to ensure robust connection to the MCP server.
- **A2A Discovery Node:** Includes `agent.json` to act as a secure mesh node.

## How Intent Routing Works
- `how` / `implement` -> Triggers `get_methodology_step`
- `example` / `case` -> Triggers `get_case_studies`
- `what` / `overview` -> Triggers `smile_overview`
- `get_insights` is enforced dynamically.

## Insights
Combining rule-based dynamic tool routing with LLM parsing provides the most robust and secure architecture for enterprise deployments.