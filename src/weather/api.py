"""National Weather Service HTTP requests and response fields used by the tools."""

from typing import TypedDict, cast

import httpx

from weather.constants import USER_AGENT


class AlertProperties(TypedDict, total=False):
    event: str | None
    areaDesc: str | None
    severity: str | None
    description: str | None
    instruction: str | None


class AlertFeature(TypedDict):
    properties: AlertProperties | None


class ForecastPeriod(TypedDict):
    name: str
    temperature: int | float | None
    temperatureUnit: str
    windSpeed: str
    windDirection: str
    detailedForecast: str


class NWSProperties(TypedDict, total=False):
    forecast: str | None
    periods: list[ForecastPeriod]


class NWSResponse(TypedDict, total=False):
    features: list[AlertFeature]
    properties: NWSProperties | None


async def make_nws_request(url: str) -> NWSResponse | None:
    """Fetch NWS JSON, returning None when the service is unavailable."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data: object = response.json()
        except httpx.HTTPError, ValueError:
            return None
    return cast(NWSResponse, data) if isinstance(data, dict) else None
