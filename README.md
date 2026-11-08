# FastMCP Python Hackpack

A [FastMCP](https://gofastmcp.com/v3/getting-started/quickstart) starter for building your own MCP server.

## Prerequisites

- Python 3.14 or higher (installed automatically by uv if needed)
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Run locally

```bash
uv sync --locked --no-editable
uv run --locked --no-editable python src/weather/main.py
```

The server uses stdio and waits for an MCP client to connect. Running it alone waits for client messages; it does not open a webpage. Press Ctrl+C to stop it.

## Connect an MCP client

For Claude Desktop, open **Settings → Developer → Edit Config** and add this entry to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "/ABSOLUTE/PATH/TO/uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/YOUR/PROJECT",
        "run",
        "--locked",
        "--no-editable",
        "python",
        "src/weather/main.py"
      ]
    }
  }
}
```

Replace both paths and restart Claude Desktop. Find uv with `which uv` (macOS/Linux) or `where uv` (Windows).

For Codex CLI:

```bash
codex mcp add weather -- /ABSOLUTE/PATH/TO/uv --directory /ABSOLUTE/PATH/TO/YOUR/PROJECT run --locked --no-editable python src/weather/main.py
```
Restart Codex after changing its server configuration.

## Development

Add your tools in `src/weather/main.py` using `@mcp.tool`. Keep API calls in `src/weather/api.py` and constants in `src/weather/constants.py`. Restart your MCP client after changes.

Use logging or stderr for debugging; stdout is reserved for MCP messages.

```bash
# Add a dependency
uv add <package>

# Add a development dependency
uv add --dev <package>

# Check lint errors
uv run --locked --no-editable ruff check .

# Check formatting
uv run --locked --no-editable ruff format --check .

# Format files
uv run --locked --no-editable ruff format .

# Reinstall the package after source changes, then run tests
uv sync --locked --no-editable --reinstall-package fastmcp-python-hackpack
uv run --locked --no-editable python -m unittest discover -s tests -v

# Build
uv build
```
