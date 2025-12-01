# /srv/webapps/webapps/platform/modules/weather.py

from flask import Blueprint, request, jsonify
import requests

weather_bp = Blueprint("weather", __name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Open‑Meteo allows requesting multiple daily variables at once.  Keep them in
# a single list so the query string and the response shaping stay in sync.
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

@weather_bp.route("/api/weather/daily")
def get_daily_weather():
    """
    Query Open-Meteo for daily forecast + (optional) recent past days.

    Query params:
      lat        (required, float)
      lon        (required, float)
      days       (optional, int, forecast days, 1–16, default 7)
      past_days  (optional, int, days back, 0–92, default 0)

    Returns a thin JSON wrapper with just the fields you care about.
    """

    # --- validate inputs ---
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({
            "error": "lat and lon are required numeric query parameters"
        }), 400

    try:
        days = int(request.args.get("days", "7"))
        past_days = int(request.args.get("past_days", "0"))
    except ValueError:
        return jsonify({"error": "days and past_days must be integers"}), 400

    # clamp to Open-Meteo limits (docs: up to 16 forecast days; past_days allowed)
    days = max(1, min(days, 16))
    past_days = max(0, min(past_days, 92))

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "auto",
        "forecast_days": days,
        "past_days": past_days,
    }

    try:
        resp = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        # surface a clean error to the frontend
        return jsonify({
            "error": "Upstream weather API request failed",
            "details": str(exc)
        }), 502

    data = resp.json()

    # Optionally thin out the payload so students see just the essentials
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

    return jsonify(out)
