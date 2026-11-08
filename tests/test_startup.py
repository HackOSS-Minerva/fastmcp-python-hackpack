"""Check the source-file launch used by local MCP clients."""

import sys
import tempfile
import unittest
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

SERVER = Path(__file__).resolve().parents[1] / "src/weather/main.py"


class StartupTests(unittest.IsolatedAsyncioTestCase):
    async def test_source_server_starts_without_package_path_hooks(self):
        # -I ignores the working directory and PYTHONPATH; only the script and
        # normally installed dependencies are needed to start the server.
        with tempfile.TemporaryDirectory() as directory:
            transport = StdioTransport(
                command=sys.executable,
                args=["-I", str(SERVER)],
                cwd=directory,
                keep_alive=False,
            )
            async with Client(transport) as client:
                tools = await client.list_tools()
                self.assertEqual(
                    {tool.name for tool in tools}, {"get_alerts", "get_forecast"}
                )
                result = await client.call_tool("get_alerts", {"state": "California"})
                self.assertFalse(result.is_error)
                self.assertIn("two-letter US state", result.content[0].text)
