# fastmcp-python-hackpack

A small [FastMCP](https://gofastmcp.com/v3/getting-started/quickstart) server to extend for your hackathon project. Based on the weather example in the [MCP server tutorial](https://modelcontextprotocol.io/docs/develop/build-server).

## Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/). `uv sync --locked --no-editable` installs Python 3.14 automatically if needed.

Weather data comes from the [National Weather Service API](https://www.weather.gov/documentation/services-web-api). No API key is required. Forecasts cover US locations; alerts accept US state and territory codes.

## Use this template

On the GitHub template repository, select **Use this template → Create a new repository**. Clone your new repository and open its folder in a terminal.

If you received this starter as a local folder, open that folder directly.

## Run locally

```bash
uv sync --locked --no-editable
uv run --locked --no-editable python src/weather/main.py
```

The server uses **stdio**: an MCP client starts it and communicates through stdin/stdout. Running it alone waits for client messages; it does not open a webpage. Press Ctrl+C to stop it.

The server runs directly from its source file so it does not need an editable-install `.pth` path hook. The `--no-editable` flag keeps uv from creating those hooks during setup or subsequent runs. This avoids import failures on macOS when `.pth` files carry the `hidden` filesystem flag; no filesystem-flag repair is needed.

## Connect an MCP client

For Claude Desktop, open **Settings → Developer → Edit Config** and merge this entry into `claude_desktop_config.json`:

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

Replace both paths. Find your uv executable with `which uv` on macOS/Linux or `where uv` on Windows. On Windows, escape backslashes in JSON or use forward slashes. Run the install step above before connecting, then fully restart Claude Desktop. Other local MCP clients can use the same command and arguments.

For Codex CLI, register the same source-file launch:

```bash
codex mcp add weather -- /ABSOLUTE/PATH/TO/uv --directory /ABSOLUTE/PATH/TO/YOUR/PROJECT run --locked --no-editable python src/weather/main.py
```

Restart Codex after changing its server configuration. Existing Claude and Codex configurations that end in `"weather"` must be updated to use `"python", "src/weather/main.py"` after the run flags instead. The server name remains `weather`.

Try asking:

- “What are the active weather alerts in California?”
- “Get the weather forecast for Riverside, California, at latitude 33.97, longitude -117.33.”

These tools are provided:

| Tool | Input | Result |
| --- | --- | --- |
| `get_alerts` | Two-letter state code, e.g. `CA` | Active alerts or a message when none are active |
| `get_forecast` | Latitude and longitude | The next five NWS forecast periods |

A forecast period is usually a day or night, not necessarily a full day. Network failures and unsupported locations return a readable message.

## Project structure

```text
src/weather/main.py                 # Server, tools, and NWS request helper
tests/test_weather.py               # Offline tool tests
pyproject.toml                      # Dependencies and weather CLI entry point
uv.lock                             # Reproducible dependency versions
.python-version                     # Python 3.14
.github/workflows/pull-request.yaml  # Format, lint, test, and build checks
```

## Extend the starter

Edit `src/weather/main.py`. Add a function with type hints and a descriptive docstring, then decorate it with `@mcp.tool`. Restart your MCP client after changing the server. Use `make_nws_request` for additional NWS endpoints, or replace the weather tools with your project's API calls.

Keep stdout reserved for MCP messages: use Python logging or stderr for debugging, not `print()`.

## Lint

```bash
uv run --locked --no-editable ruff check .
```

## Format

```bash
uv run --locked --no-editable ruff format --check .
```

To apply formatting, run `uv run --locked --no-editable ruff format .`.

## Test

Tests import the installed package. After editing Python code, reinstall it before testing so the tests exercise the latest version:

```bash
uv sync --locked --no-editable --reinstall-package fastmcp-python-hackpack
```

```bash
uv run --locked --no-editable python -m unittest discover -s tests -v
```

Weather tests call the MCP tools with mocked HTTP responses. A startup test also launches the source file through stdio from an unrelated directory. No NWS access or AI account is needed. CI repeats startup on Linux and macOS, marking `.pth` files hidden on macOS.

## Build

```bash
uv build
```

## Publishing

After uploading this folder to GitHub, enable **Settings → General → Template repository** to provide the “Use this template” flow. Like the referenced HackOSS-Minerva starters, this folder does not declare a license; choose one before publishing if required by the organization.
