// html_injection.js
// Loads and injects component HTML files into placeholder divs

async function loadComponentHTML(componentPath) {
  try {
    const response = await fetch(componentPath);
    if (!response.ok) {
      throw new Error(`Failed to load ${componentPath}: ${response.status}`);
    }
    return await response.text();
  } catch (error) {
    console.error(`Error loading component ${componentPath}:`, error);
    return null;
  }
}

async function injectComponent(placeholderId, componentPath) {
  const placeholder = document.getElementById(placeholderId);
  if (!placeholder) {
    console.warn(`Placeholder ${placeholderId} not found`);
    return;
  }

  const html = await loadComponentHTML(componentPath);
  if (html) {
    placeholder.innerHTML = html;
  }
}

async function loadAllComponents() {
  // Load components in order
  await injectComponent('header-placeholder', '/header/header.html');
  await injectComponent('hero-placeholder', '/hero/hero.html');
  await injectComponent('hero-footer-placeholder', '/hero-footer/hero-footer.html');
  await injectComponent('features-placeholder', '/features/features.html');
  await injectComponent('set-in-placeholder', '/set-in/set-in.html');
  await injectComponent('weather-placeholder', '/weather/weather.html');
  await injectComponent('info-blocks-placeholder', '/info-blocks/info-blocks.html');
  await injectComponent('footer-placeholder', '/footer/footer.html');
}

// Initialize component loading when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  await loadAllComponents();
  
  // Dispatch custom event to signal that components are loaded
  document.dispatchEvent(new CustomEvent('componentsLoaded'));
});
