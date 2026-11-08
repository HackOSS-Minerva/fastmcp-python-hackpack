"""A small weather MCP server to extend for your hackathon project."""

from fastmcp import FastMCP

from weather.api import make_nws_request
from weather.constants import NWS_API_BASE, STATE_CODES

mcp = FastMCP("Weather")


@mcp.tool
async def get_alerts(state: str) -> str:
    """Get active weather alerts for a two-letter US state code, e.g. CA or NY."""
    state = state.strip().upper()
    if state not in STATE_CODES:
        return "Provide a valid two-letter US state or territory code, such as CA."

    data = await make_nws_request(f"{NWS_API_BASE}/alerts/active/area/{state}")
    features = data.get("features") if data else None
    if not isinstance(features, list):
        return "Unable to fetch weather alerts. Please try again later."
    if not features:
        return f"No active alerts for {state}."

    alerts = []
    for feature in features:
        props = feature.get("properties") or {}
        alerts.append(
            f"Event: {props.get('event') or 'Unknown'}\n"
            f"Area: {props.get('areaDesc') or 'Unknown'}\n"
            f"Severity: {props.get('severity') or 'Unknown'}\n"
            f"Description: {props.get('description') or 'No description available'}\n"
            f"Instructions: {props.get('instruction') or 'No specific instructions provided'}"
        )
    return "\n---\n".join(alerts)


@mcp.tool
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get the next five forecast periods for US latitude/longitude coordinates."""
    # Chained comparisons also reject NaN and infinity.
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return "Provide valid coordinates: latitude -90 to 90, longitude -180 to 180."

    # NWS maps a location to a forecast grid before returning forecast periods.
    latitude, longitude = round(latitude, 4), round(longitude, 4)
    points = await make_nws_request(f"{NWS_API_BASE}/points/{latitude},{longitude}")
    forecast_url = (points.get("properties") or {}).get("forecast") if points else None
    if not isinstance(forecast_url, str) or not forecast_url.startswith(
        f"{NWS_API_BASE}/"
    ):
        return "Unable to fetch forecast data for this location. NWS covers US locations only."

    data = await make_nws_request(forecast_url)
    periods = (data.get("properties") or {}).get("periods") if data else None
    if not isinstance(periods, list) or not periods:
        return "Unable to fetch a detailed forecast. Please try again later."

    forecasts = []
    for period in periods[:5]:
        forecasts.append(
            f"{period['name']}:\n"
            f"Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
            f"Wind: {period['windSpeed']} {period['windDirection']}\n"
            f"Forecast: {period['detailedForecast']}"
        )
    return "\n---\n".join(forecasts)


def main() -> None:
    """Start the local MCP server; stdout is reserved for protocol messages."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
