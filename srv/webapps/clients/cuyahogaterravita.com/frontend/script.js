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
  const hourlyContainer = document.querySelector('.weather-hourly');

  const DEFAULT_COORDS = { lat: 41.241, lon: -81.548, name: 'Cuyahoga Valley' };
  let currentCoords = { ...DEFAULT_COORDS };

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

  const formatHourlyLabel = (isoDateTime, index) => {
    if (!isoDateTime) return index === 0 ? 'Now' : '—';
    const date = new Date(isoDateTime);
    return index === 0
      ? 'Now'
      : date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  };

  const getHourlyIcon = (hourly, index) => {
    if (!hourly) return null;
    const directIcon = hourly.icon?.[index] || hourly.weather_icon?.[index];
    if (directIcon) return directIcon;

    const code = hourly.weathercode?.[index];
    if (code != null) {
      return `https://open-meteo.com/images/weather-icons/${code}.png`;
    }

    return null;
  };

  const renderHourly = (payload) => {
    const hourly = payload?.hourly;
    if (!hourly || !hourly.time || !hourlyContainer) return;

    const temperatures =
      hourly.temperature_2m || hourly.temperature || hourly.temperature_2m_mean || hourly.temperature_2m_max;
    const entries = hourly.time
      .map((time, index) => ({
        time,
        temperature: temperatures?.[index],
        icon: getHourlyIcon(hourly, index),
      }))
      .filter((entry) => entry.time);

    while (hourlyContainer.children.length > entries.length) {
      hourlyContainer.removeChild(hourlyContainer.lastElementChild);
    }

    while (hourlyContainer.children.length < entries.length) {
      const tile = document.createElement('div');
      tile.className = 'hour';

      const timeLabel = document.createElement('span');
      const iconWrapper = document.createElement('span');
      iconWrapper.className = 'icon';
      const tempLabel = document.createElement('span');
      tempLabel.className = 'hourly-temp';

      tile.appendChild(timeLabel);
      tile.appendChild(iconWrapper);
      tile.appendChild(tempLabel);
      hourlyContainer.appendChild(tile);
    }

    Array.from(hourlyContainer.children).forEach((tile, index) => {
      const entry = entries[index];
      if (!entry) return;

      const [timeLabel, iconWrapper, tempLabel] = tile.children;

      setText(timeLabel, formatHourlyLabel(entry.time, index));

      iconWrapper.innerHTML = '';
      const iconSrc = entry.icon;
      if (iconSrc) {
        const img = document.createElement('img');
        img.src = iconSrc;
        img.alt = 'Weather icon';
        iconWrapper.appendChild(img);
      }

      setText(tempLabel, entry.temperature != null ? `${Math.round(entry.temperature)}°` : '—');
    });
  };

  const updateWeatherDisplay = (payload, overrideLabel) => {
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

    setText(
      locationEl,
      overrideLabel || payload.timezone?.replace(/_/g, ' ') || 'Local forecast'
    );
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
    
    renderHourly(payload);
  };

  const fetchWeather = (coords = currentCoords, label = coords.name) => {
    const url = `/api/weather/daily?lat=${coords.lat}&lon=${coords.lon}&days=1`;

    setText(locationEl, label || 'Loading forecast…');

    fetch(url)
      .then((resp) => {
        if (!resp.ok) throw new Error(`Weather API error: ${resp.status}`);
        return resp.json();
      })
      .then((data) => updateWeatherDisplay(data, label))
      .catch((err) => {
        console.error(err);
        setText(locationEl, 'Weather unavailable');
      });
  };

  const queryForm = document.querySelector('.weather-query');
  const queryInput = document.querySelector('.query-input');
  let queryFeedback;

  const getOrCreateFeedback = () => {
    if (queryFeedback) return queryFeedback;
    queryFeedback = document.createElement('div');
    queryFeedback.className = 'query-feedback';
    queryFeedback.setAttribute('role', 'status');
    queryFeedback.setAttribute('aria-live', 'polite');
    queryFeedback.style.marginTop = '0.25rem';
    queryFeedback.style.fontSize = '0.9rem';
    queryFeedback.style.color = '#f0f0f0';
    queryForm?.appendChild(queryFeedback);
    return queryFeedback;
  };

  const showFeedback = (message, isError = false) => {
    const feedbackEl = getOrCreateFeedback();
    feedbackEl.textContent = message;
    feedbackEl.style.color = isError ? '#ffb4a2' : '#f0f0f0';
  };

  const FALLBACK_LOCATIONS = {
    peninsula: { lat: 41.241, lon: -81.548, name: 'Peninsula, OH' },
    akron: { lat: 41.0814, lon: -81.519, name: 'Akron, OH' },
    cleveland: { lat: 41.4993, lon: -81.6944, name: 'Cleveland, OH' },
    cuyahoga: { lat: 41.2806, lon: -81.5678, name: 'Cuyahoga Valley National Park' },
  };

  const resolveQueryToCoords = (query) => {
    const trimmed = query.trim();
    if (!trimmed) {
      return Promise.reject(new Error('Please enter a location.'));
    }

    const normalized = trimmed.toLowerCase();
    if (FALLBACK_LOCATIONS[normalized]) {
      return Promise.resolve(FALLBACK_LOCATIONS[normalized]);
    }

    const geocodeUrl = `/api/geocode?query=${encodeURIComponent(trimmed)}`;

    return fetch(geocodeUrl)
      .then((resp) => {
        if (!resp.ok) throw new Error('Unable to reach geocoding service.');
        return resp.json();
      })
      .then((data) => {
        const result = data?.results?.[0];
        if (!result?.latitude || !result?.longitude) {
          throw new Error('Location not found. Try a nearby city.');
        }
        return {
          lat: result.latitude,
          lon: result.longitude,
          name: result.name || trimmed,
        };
      });
  };

  queryForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const queryValue = queryInput?.value || '';

    showFeedback('Looking up location…');

    resolveQueryToCoords(queryValue)
      .then((coords) => {
        currentCoords = { ...coords };
        showFeedback(`Showing weather for ${coords.name || queryValue}.`);
        fetchWeather(currentCoords, coords.name || queryValue);
      })
      .catch((err) => {
        console.error(err);
        showFeedback(err.message || 'Unable to find that location.', true);
        queryInput?.focus();
      });
  });

  fetchWeather();

});
