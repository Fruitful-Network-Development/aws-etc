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

  // WEATHER WIDGET MOCK
  // The weather widget is broken down into individual elements within the
  // markup.  These assignments populate the widget with placeholder values.
  const locationEl = document.getElementById('weather-location');
  const dateEl = document.getElementById('weather-date');
  const tempEl = document.getElementById('weather-temp');
  const feelsEl = document.getElementById('weather-feels');
  const humidityEl = document.getElementById('weather-humidity');
  const visibilityEl = document.getElementById('weather-visibility');
  const sunriseEl = document.getElementById('weather-sunrise');
  const sunsetEl = document.getElementById('weather-sunset');
  const windEl = document.getElementById('weather-wind');
  const pressureEl = document.getElementById('weather-pressure');
  const uvEl = document.getElementById('weather-uv');

  if (locationEl) locationEl.textContent = 'Hagen, Germany';
  if (dateEl) dateEl.textContent = 'Sunday, 23 April';
  if (tempEl) tempEl.textContent = '17°';
  if (feelsEl) feelsEl.textContent = '15°';
  if (humidityEl) humidityEl.textContent = '81%';
  if (visibilityEl) visibilityEl.textContent = '11 km';
  if (sunriseEl) sunriseEl.textContent = '06:18 a.m.';
  if (sunsetEl) sunsetEl.textContent = '08:39 p.m.';
  if (windEl) windEl.textContent = '18 km/h SW';
  if (pressureEl) pressureEl.textContent = '1001 hPa';
  if (uvEl) uvEl.textContent = '0 low';
  
});
