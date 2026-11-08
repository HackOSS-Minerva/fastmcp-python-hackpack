"""Exercise the MCP tools without depending on live NWS availability."""

import unittest
from unittest.mock import patch

import httpx
from fastmcp import Client

from weather.main import get_forecast, mcp


class WeatherTests(unittest.IsolatedAsyncioTestCase):
    async def call_tool(self, name, arguments, routes):
        def respond(request):
            self.assertEqual(request.headers["Accept"], "application/geo+json")
            self.assertTrue(
                request.headers["User-Agent"].startswith("weather-hackpack/")
            )
            if request.url.path not in routes:
                self.fail(f"Unexpected NWS request: {request.url}")
            response = routes[request.url.path]
            if isinstance(response, Exception):
                raise response
            status, body = response
            return httpx.Response(status, json=body)

        client_class = httpx.AsyncClient
        with patch(
            "weather.api.httpx.AsyncClient",
            side_effect=lambda **kwargs: client_class(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        ):
            async with Client(mcp) as client:
                result = await client.call_tool(name, arguments)
        return "\n".join(block.text for block in result.content)

    async def test_tools_are_discoverable(self):
        async with Client(mcp) as client:
            tools = await client.list_tools()
        self.assertEqual({tool.name for tool in tools}, {"get_alerts", "get_forecast"})

    async def test_alerts_include_weather_details(self):
        text = await self.call_tool(
            "get_alerts",
            {"state": " ca "},
            {
                "/alerts/active/area/CA": (
                    200,
                    {
                        "features": [
                            {
                                "properties": {
                                    "event": "Flood Warning",
                                    "areaDesc": "Riverside County",
                                    "severity": "Severe",
                                    "description": "Flooding expected.",
                                    "instruction": "Avoid flooded roads.",
                                }
                            }
                        ]
                    },
                )
            },
        )
        self.assertIn("Flood Warning", text)
        self.assertIn("Riverside County", text)
        self.assertIn("Avoid flooded roads.", text)

    async def test_empty_alerts_are_not_an_api_failure(self):
        text = await self.call_tool(
            "get_alerts",
            {"state": "CA"},
            {"/alerts/active/area/CA": (200, {"features": []})},
        )
        self.assertIn("No active alerts", text)

    async def test_invalid_state_does_not_request_weather(self):
        for state in ["", "California", "ZZ", "../CA"]:
            with self.subTest(state=state):
                text = await self.call_tool("get_alerts", {"state": state}, {})
                self.assertIn("two-letter US state", text)

    async def test_api_failures_are_not_reported_as_no_alerts(self):
        for response in [(503, {}), httpx.ConnectError("offline"), (200, {})]:
            with self.subTest(response=response):
                text = await self.call_tool(
                    "get_alerts",
                    {"state": "CA"},
                    {"/alerts/active/area/CA": response},
                )
                self.assertIn("Unable to fetch", text)
                self.assertNotIn("No active alerts", text)

    async def test_null_alert_instructions_have_a_readable_fallback(self):
        text = await self.call_tool(
            "get_alerts",
            {"state": "CA"},
            {
                "/alerts/active/area/CA": (
                    200,
                    {"features": [{"properties": {"instruction": None}}]},
                )
            },
        )
        self.assertIn("No specific instructions provided", text)
        self.assertNotIn("None", text)

    async def test_forecast_follows_grid_url_and_limits_output(self):
        text = await self.call_tool(
            "get_forecast",
            {"latitude": 33.97, "longitude": -117.33},
            {
                "/points/33.97,-117.33": (
                    200,
                    {
                        "properties": {
                            "forecast": "https://api.weather.gov/gridpoints/SGX/1,2/forecast"
                        }
                    },
                ),
                "/gridpoints/SGX/1,2/forecast": (
                    200,
                    {
                        "properties": {
                            "periods": [
                                {
                                    "name": f"Period {i}",
                                    "temperature": 75,
                                    "temperatureUnit": "F",
                                    "windSpeed": "5 mph",
                                    "windDirection": "W",
                                    "detailedForecast": "Sunny.",
                                }
                                for i in range(6)
                            ]
                        }
                    },
                ),
            },
        )
        self.assertIn("Period 0", text)
        self.assertIn("Period 4", text)
        self.assertNotIn("Period 5", text)
        self.assertIn("75°F", text)
        self.assertIn("5 mph W", text)
        self.assertIn("Sunny.", text)

    async def test_precise_coordinates_are_rounded_for_nws(self):
        text = await self.call_tool(
            "get_forecast",
            {"latitude": 33.973051, "longitude": -117.331321},
            {
                "/points/33.9731,-117.3313": (
                    200,
                    {
                        "properties": {
                            "forecast": "https://api.weather.gov/gridpoints/SGX/1,2/forecast"
                        }
                    },
                ),
                "/gridpoints/SGX/1,2/forecast": (
                    200,
                    {
                        "properties": {
                            "periods": [
                                {
                                    "name": "Tonight",
                                    "temperature": 62,
                                    "temperatureUnit": "F",
                                    "windSpeed": "5 mph",
                                    "windDirection": "E",
                                    "detailedForecast": "Clear.",
                                }
                            ]
                        }
                    },
                ),
            },
        )
        self.assertIn("Tonight", text)
        self.assertIn("62°F", text)
        self.assertIn("Clear.", text)

    async def test_invalid_coordinates_do_not_request_weather(self):
        for latitude, longitude in [(91, 0), (0, -181)]:
            with self.subTest(latitude=latitude, longitude=longitude):
                text = await self.call_tool(
                    "get_forecast", {"latitude": latitude, "longitude": longitude}, {}
                )
                self.assertIn("valid coordinates", text)

    async def test_non_finite_coordinates_are_rejected_before_http(self):
        # JSON transport rejects these values itself; exercise the Python boundary.
        for latitude, longitude in [(float("nan"), 0), (0, float("inf"))]:
            text = await get_forecast(latitude, longitude)
            self.assertIn("valid coordinates", text)

    async def test_unavailable_grid_returns_a_readable_error(self):
        for response in [(404, {}), (200, {"properties": {}})]:
            with self.subTest(response=response):
                text = await self.call_tool(
                    "get_forecast",
                    {"latitude": 0, "longitude": 0},
                    {"/points/0.0,0.0": response},
                )
                self.assertIn("Unable to fetch", text)

    async def test_empty_or_unavailable_forecast_returns_a_readable_error(self):
        for response in [(503, {}), (200, {"properties": {"periods": []}})]:
            with self.subTest(response=response):
                text = await self.call_tool(
                    "get_forecast",
                    {"latitude": 33.97, "longitude": -117.33},
                    {
                        "/points/33.97,-117.33": (
                            200,
                            {
                                "properties": {
                                    "forecast": "https://api.weather.gov/gridpoints/SGX/1,2/forecast"
                                }
                            },
                        ),
                        "/gridpoints/SGX/1,2/forecast": response,
                    },
                )
                self.assertIn("Unable to fetch", text)
