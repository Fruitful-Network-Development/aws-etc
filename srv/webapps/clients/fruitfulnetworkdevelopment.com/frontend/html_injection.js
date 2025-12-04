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

async function loadAllComponents() {script.js
  // Load components in order: header, body, then sub-components, then overlay
  await injectComponent('header-placeholder', '/header/header.html');
  await injectComponent('body-placeholder', '/body/body.html');
  
  // After body is loaded, inject sub-components into their placeholdersdata_injection.js
  await injectComponent('oeuvre-placeholder', '/oeuvre/oeuvre.html');
  await injectComponent('anthology-placeholder', '/anthology/anthology.html');
  await injectComponent('compendium-placeholder', '/compendium/compendium.html');
  
  // Load overlay last
  await injectComponent('overlay-placeholder', '/overlay/overlay.html');
}

// Initialize component loading when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  await loadAllComponents();
  
  // Dispatch custom event to signal that components are loaded
  document.dispatchEvent(new CustomEvent('componentsLoaded'));
});
