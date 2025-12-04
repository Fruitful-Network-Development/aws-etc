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
from flask import Blueprint, request, jsonify
import requests

# Configure logging
logger = logging.getLogger(__name__)

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
    
    if lat_param is None or lon_param is None:
        return jsonify({
            "error": "lat and lon are required query parameters"
        }), 400
    
    try:
        lat = float(lat_param)
        lon = float(lon_param)
    except (TypeError, ValueError):
        return jsonify({
            "error": "lat and lon must be valid numeric values"
        }), 400
    
    # Validate latitude and longitude ranges
    if not (-90 <= lat <= 90):
        return jsonify({
            "error": "lat must be between -90 and 90"
        }), 400
    
    if not (-180 <= lon <= 180):
        return jsonify({
            "error": "lon must be between -180 and 180"
        }), 400
    
    # Validate optional parameters: days and past_days
    try:
        days = int(request.args.get("days", "7"))
        past_days = int(request.args.get("past_days", "0"))
    except (TypeError, ValueError):
        return jsonify({
            "error": "days and past_days must be valid integers"
        }), 400
    
    # Clamp to Open-Meteo limits (docs: up to 16 forecast days; past_days allowed up to 92)
    days = max(1, min(days, 16))
    past_days = max(0, min(past_days, 92))
    
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
        logger.error(f"Weather API returned invalid JSON for lat={lat}, lon={lon}")
        return jsonify({
            "error": "Weather API returned invalid response",
            "message": "The weather service returned malformed data"
        }), 502
    
    # Extract and shape the response data
    daily = data.get("daily", {})
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
    
    logger.info(f"Weather data retrieved successfully for lat={lat}, lon={lon}, days={days}, past_days={past_days}")
    
    return jsonify(out)
