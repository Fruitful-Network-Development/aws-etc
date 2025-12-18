# /srv/webapps/platform/modules/weather.py

"""
Weather Blueprint exposing a simple Open-Meteo daily forecast API.

Endpoint contract
-----------------
GET /api/weather/daily

Query parameters:
- ``lat`` (required, float): latitude in decimal degrees (-90..90)
- ``lon`` (required, float): longitude in decimal degrees (-180..180)
- ``days`` (optional, int): forecast days, clamped to 1–16 (default 7)
- ``past_days`` (optional, int): include up to 92 previous days (default 0)

JSON response (abridged):
```
{
    "latitude": float,
    "longitude": float,
    "timezone": "America/New_York",
    "unit_system": {"precipitation_sum": "mm", ...},
    "daily": {
        "time": ["2024-01-01", ...],
        "temperature_max": [float, ...],
        "temperature_min": [float, ...],
        "temperature_mean": [float, ...],
        "apparent_temperature_max": [float, ...],
        "apparent_temperature_min": [float, ...],
        "sunrise": ["2024-01-01T07:45", ...],
        "sunset": ["2024-01-01T17:12", ...],
        "precipitation_sum": [float, ...],
        "windspeed_max": [float, ...],
        "winddirection_dominant": [int, ...],
        "uv_index_max": [float, ...]
    },
    "source": "open-meteo"
}
```
Arrays in ``daily`` share the same index ordering. The first element covers the
earliest day returned (today when ``past_days`` is 0).

Registration example in app.py::

    from modules.weather import weather_bp
    app.register_blueprint(weather_bp)
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Tuple

from flask import Blueprint, request, jsonify
import requests

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Flask Blueprint for weather endpoints
weather_bp = Blueprint("weather", __name__)

# Open-Meteo API configuration
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo allows requesting multiple daily variables at once.
# Keep them in a single list so the query string and the response shaping stay in sync.
DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "sunrise",
    "sunset",
    "precipitation_sum",
    "windspeed_10m_max",
    "winddirection_10m_dominant",
    "uv_index_max",
]


def _parse_float(name: str, raw: str | None, *, min_value: float, max_value: float) -> Tuple[Dict[str, Any] | None, float | None]:
    """Parse and validate a float query parameter with range enforcement.

    Returns (error_response, parsed_value). Only one of the tuple entries will
    be non-None.
    """

    if raw is None:
        return ({"error": f"{name} is required", "parameter": name}, 400), None

    try:
        value = float(raw)
    except (TypeError, ValueError):
        return (
            {"error": f"{name} must be a valid number", "parameter": name},
            400,
        ), None

    if not math.isfinite(value):
        return (
            {"error": f"{name} must be a finite number", "parameter": name},
            400,
        ), None

    if not (min_value <= value <= max_value):
        return (
            {
                "error": f"{name} must be between {min_value} and {max_value}",
                "parameter": name,
            },
            400,
        ), None

    return None, value


def _parse_int(
    name: str, raw: str | None, *, default: int, min_value: int, max_value: int
) -> Tuple[Dict[str, Any] | None, int | None]:
    """Parse and clamp an integer query parameter within bounds.

    Returns (error_response, parsed_value). Only one of the tuple entries will
    be non-None.
    """

    if raw is None:
        raw = str(default)

    try:
        value = int(raw)
    except (TypeError, ValueError):
        return (
            {
                "error": f"{name} must be a whole number",
                "parameter": name,
            },
            400,
        ), None

    value = max(min_value, min(value, max_value))
    return None, value


@weather_bp.route("/api/weather/daily", methods=["GET"])
def get_daily_weather():
    """
    Query Open-Meteo for daily forecast data (optionally including recent past days).

    Error responses:
        400: missing/invalid query parameters
        502: upstream weather API failure
    """
    # Validate required parameters: lat and lon
    lat_param = request.args.get("lat")
    lon_param = request.args.get("lon")

    lat_error, lat = _parse_float("lat", lat_param, min_value=-90, max_value=90)
    if lat_error:
        logger.warning("Invalid latitude: %s", lat_param)
        return jsonify(lat_error[0]), lat_error[1]

    lon_error, lon = _parse_float("lon", lon_param, min_value=-180, max_value=180)
    if lon_error:
        logger.warning("Invalid longitude: %s", lon_param)
        return jsonify(lon_error[0]), lon_error[1]

    # Validate optional parameters: days and past_days
    days_error, days = _parse_int(
        "days",
        request.args.get("days"),
        default=7,
        min_value=1,
        max_value=16,
    )
    if days_error:
        logger.warning("Invalid days parameter: %s", request.args.get("days"))
        return jsonify(days_error[0]), days_error[1]

    past_days_error, past_days = _parse_int(
        "past_days",
        request.args.get("past_days"),
        default=0,
        min_value=0,
        max_value=92,
    )
    if past_days_error:
        logger.warning("Invalid past_days parameter: %s", request.args.get("past_days"))
        return jsonify(past_days_error[0]), past_days_error[1]

    logger.info(
        "Weather request received",
        extra={
            "lat": lat,
            "lon": lon,
            "days": days,
            "past_days": past_days,
        },
    )
    
    # Build request parameters for Open-Meteo API
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "auto",
        "forecast_days": days,
        "past_days": past_days,
    }
    
    try:
        resp = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.Timeout:
        logger.error(f"Weather API request timed out for lat={lat}, lon={lon}")
        return jsonify({
            "error": "Weather API request timed out",
            "message": "The weather service did not respond in time"
        }), 502
    except requests.HTTPError as exc:
        logger.error(f"Weather API HTTP error: {exc.response.status_code} for lat={lat}, lon={lon}")
        return jsonify({
            "error": "Weather API request failed",
            "message": f"Upstream service returned status {exc.response.status_code}"
        }), 502
    except requests.RequestException as exc:
        logger.error(f"Weather API request exception: {exc} for lat={lat}, lon={lon}")
        return jsonify({
            "error": "Weather API request failed",
            "message": "Unable to connect to weather service"
        }), 502
    
    try:
        data = resp.json()
    except ValueError:
        logger.error(
            "Weather API returned invalid JSON for lat=%s, lon=%s", lat, lon
        )
        return (
            jsonify({
                "error": "Weather API returned invalid response",
                "message": "The weather service returned malformed data",
            }),
            502,
        )

    try:
        daily = data.get("daily") or {}
        out = {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "unit_system": data.get("daily_units", {}),
            "daily": {
                "time": daily.get("time", []),
                "temperature_max": daily.get("temperature_2m_max", []),
                "temperature_min": daily.get("temperature_2m_min", []),
                "temperature_mean": daily.get("temperature_2m_mean", []),
                "apparent_temperature_max": daily.get("apparent_temperature_max", []),
                "apparent_temperature_min": daily.get("apparent_temperature_min", []),
                "sunrise": daily.get("sunrise", []),
                "sunset": daily.get("sunset", []),
                "precipitation_sum": daily.get("precipitation_sum", []),
                "windspeed_max": daily.get("windspeed_10m_max", []),
                "winddirection_dominant": daily.get("winddirection_10m_dominant", []),
                "uv_index_max": daily.get("uv_index_max", []),
            },
            "source": "open-meteo",
        }
    except Exception as exc:  # Broad catch to avoid leaking 500s to clients
        logger.exception(
            "Failed to shape weather response for lat=%s, lon=%s", lat, lon
        )
        return (
            jsonify({
                "error": "Failed to process weather data",
                "message": str(exc),
            }),
            502,
        )

    if not out["daily"].get("time"):
        logger.error(
            "Weather API response missing daily data for lat=%s, lon=%s", lat, lon
        )
        return (
            jsonify({
                "error": "Weather API returned incomplete data",
                "message": "Daily forecast data unavailable for the given coordinates",
            }),
            502,
        )

    logger.info(
        "Weather data retrieved successfully",
        extra={
            "lat": lat,
            "lon": lon,
            "days": days,
            "past_days": past_days,
        },
    )

    return jsonify(out)
