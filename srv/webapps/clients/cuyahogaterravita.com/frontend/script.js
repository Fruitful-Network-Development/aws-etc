// script.js

document.addEventListener('DOMContentLoaded', function() {
  const menuToggle = document.querySelector('.menu-toggle');
  const searchBtn = document.querySelector('.search-btn');
  const cartBtn = document.querySelector('.cart-btn');
  const learnMoreBtn = document.getElementById('learn-more-btn');
  const csaSignupBtn = document.getElementById('csa-signup-btn');
  const csaSignupBtn2 = document.getElementById('csa-signup-btn-2');
  const newsletterForm = document.getElementById('newsletter-form');

  menuToggle && menuToggle.addEventListener('click', () => {
    // TODO: toggle mobile nav menu
    // e.g. open/close side or dropdown menu
    console.log("Menu toggle clicked");
  });

  searchBtn && searchBtn.addEventListener('click', () => {
    // TODO: open search input
    console.log("Search button clicked");
  });

  cartBtn && cartBtn.addEventListener('click', () => {
    // TODO: open shopping cart overlay / page
    console.log("Cart button clicked");
  });

  learnMoreBtn && learnMoreBtn.addEventListener('click', () => {
    // TODO: scroll or navigate to more info section
    console.log("Learn More clicked");
  });

  csaSignupBtn && csaSignupBtn.addEventListener('click', () => {
    // TODO: open CSA sign-up form / modal
    console.log("CSA Sign-Up clicked (hero)");
  });

  csaSignupBtn2 && csaSignupBtn2.addEventListener('click', () => {
    // TODO: open CSA sign-up form / modal
    console.log("CSA Sign-Up clicked (program intro)");
  });

  newsletterForm && newsletterForm.addEventListener('submit', (e) => {
    e.preventDefault();
    // TODO: handle newsletter form submission (e.g. send AJAX)
    console.log("Newsletter form submitted");
  });

  // WEATHER WIDGET (live data from /api/weather/daily)
  const locationEl = document.getElementById('weather-location');
  const dateEl = document.getElementById('weather-date');
  const tempEl = document.getElementById('weather-temp');
  const feelsEl = document.getElementById('weather-feels');
  const humidityEl = document.getElementById('weather-humidity');
  const precipitationEl = document.getElementById('weather-precipitation');
  const sunriseEl = document.getElementById('weather-sunrise');
  const sunsetEl = document.getElementById('weather-sunset');
  const windEl = document.getElementById('weather-wind');
  const pressureEl = document.getElementById('weather-pressure');
  const uvEl = document.getElementById('weather-uv');

  const WEATHER_COORDS = { lat: 41.241, lon: -81.548 }; // Cuyahoga Valley, OH

  const formatDate = (isoDate) => {
    if (!isoDate) return '—';
    const date = new Date(`${isoDate}T00:00:00`);
    return date.toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (isoDateTime) => {
    if (!isoDateTime) return '—';
    const date = new Date(isoDateTime);
    return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  };

  const formatWind = (speed, direction) => {
    if (speed == null) return '—';
    const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const idx = Math.round(((direction ?? 0) % 360) / 45) % 8;
    return `${Math.round(speed)} km/h ${dirs[idx]}`;
  };

  const setText = (el, value) => {
    if (el) el.textContent = value;
  };

  const updateWeatherDisplay = (payload) => {
    if (!payload || !payload.daily) return;

    const daily = payload.daily;
    const precipitationUnit = payload.unit_system?.precipitation_sum || 'mm';
    const firstDay = {
      date: daily.time?.[0],
      tempMax: daily.temperature_max?.[0],
      tempMean: daily.temperature_mean?.[0],
      apparentMax: daily.apparent_temperature_max?.[0],
      sunrise: daily.sunrise?.[0],
      sunset: daily.sunset?.[0],
      windspeed: daily.windspeed_max?.[0],
      windDirection: daily.winddirection_dominant?.[0],
      uvIndex: daily.uv_index_max?.[0],
      precipitation: daily.precipitation_sum?.[0],
    };

    setText(locationEl, payload.timezone?.replace(/_/g, ' ') || 'Local forecast');
    setText(dateEl, formatDate(firstDay.date));
    setText(tempEl, firstDay.tempMax != null ? `${Math.round(firstDay.tempMax)}°` : '—');
    setText(feelsEl, firstDay.apparentMax != null ? `${Math.round(firstDay.apparentMax)}°` : '—');
    setText(humidityEl, '—');
    setText(
      precipitationEl,
      firstDay.precipitation != null
        ? `${Math.round(firstDay.precipitation * 10) / 10} ${precipitationUnit}`
        : '—'
    );
    setText(sunriseEl, formatTime(firstDay.sunrise));
    setText(sunsetEl, formatTime(firstDay.sunset));
    setText(windEl, formatWind(firstDay.windspeed, firstDay.windDirection));
    setText(pressureEl, '—');
    setText(uvEl, firstDay.uvIndex != null ? `${firstDay.uvIndex} UV` : '—');
  };

  const fetchWeather = () => {
    const url = `/api/weather/daily?lat=${WEATHER_COORDS.lat}&lon=${WEATHER_COORDS.lon}&days=1`;

    fetch(url)
      .then((resp) => {
        if (!resp.ok) throw new Error(`Weather API error: ${resp.status}`);
        return resp.json();
      })
      .then((data) => updateWeatherDisplay(data))
      .catch((err) => {
        console.error(err);
        setText(locationEl, 'Weather unavailable');
      });
  };

  fetchWeather();

});
