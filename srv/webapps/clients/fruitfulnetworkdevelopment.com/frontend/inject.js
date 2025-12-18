/* =========================
   HTML Injection Loader
   - Loads component HTML from: assets/injections/<file>.html
   - Injects into: .slot[data-component="<componentKey>"]
   
   INJECTION CONTRACT:
   Each component HTML file must respect the layout contract:
   - Root element fills its parent (100% width/height)
   - Uses CSS Grid for internal layout (not Flexbox for outer structure)
   - References shared CSS variables from index.html (:root)
     * Colors: --c1 through --c9
     * Spacing: --gap-xs, --gap-sm, --gap-md, --gap-lg, --gap-xl
     * Layout: --maxw, --section-grid-gap, etc.
   - Does NOT set outer padding, background colors, or heights
     (these are handled by containers in index.html)
   - Only defines internal grid structure and typography
   
   COMPONENT NAMING:
   - Use descriptive names: "SectionName_variant" format
   - Map to HTML files in COMPONENT_MAP below
   ========================= */

(() => {
  const INJECTION_BASE = "assets/injections/";

  const COMPONENT_MAP = {
    // HERO
    "section_1": "hero.html",
    "hero_footer": "hero_footer.html",

    // MAIN SECTIONS
    "Server_section": "section_1.html",
    "Operate_section": "section_2.html",
    "Offer_section": "section_3.html",

    // DIVIDERS
    "Invest_divider": "divider_1.html",
    "Vision_divider": "divider_2.html",

    // FOOTER
    "footer": "footer.html",
  };

  const cache = new Map();

  function qsAll(sel, root = document) {
    return Array.from(root.querySelectorAll(sel));
  }

  async function fetchText(url) {
    if (cache.has(url)) return cache.get(url);

    const bust = `v=${Date.now()}`;
    const res = await fetch(`${url}?${bust}`, { cache: "no-store" });

    if (!res.ok) throw new Error(`Failed to load ${url} (${res.status} ${res.statusText})`);

    const txt = await res.text();
    cache.set(url, txt);
    return txt;
  }

  function injectHTML(container, html) {
    // Injects HTML into container. No layout logic here - all layout
    // is handled by CSS (containers define grids, components use them).
    
    // First inject the HTML
    container.innerHTML = html;
    
    // Then check for hero title variable and update if present
    const heroTitle = container.getAttribute("data-hero-title");
    if (heroTitle) {
      // Find the h1 element that was just injected
      const titleElement = container.querySelector('#hero-title-placeholder');
      if (titleElement) {
        // Split title by spaces and wrap each word in a <span>
        const words = heroTitle.trim().split(/\s+/);
        // Clear existing content and add new spans
        titleElement.innerHTML = words.map(word => `<span>${word}</span>`).join('\n    ');
        // Remove the placeholder ID since we've updated it
        titleElement.removeAttribute('id');
      }
    }
  }

  async function injectAll() {
    const slots = qsAll(".slot[data-component]");

    for (const slot of slots) {
      const key = slot.getAttribute("data-component")?.trim();
      if (!key) continue;

      const file = COMPONENT_MAP[key];
      if (!file) {
        console.warn(`[inject] No mapping for data-component="${key}"`);
        continue;
      }

      try {
        const html = await fetchText(`${INJECTION_BASE}${file}`);
        injectHTML(slot, html);
      } catch (err) {
        console.error(`[inject] ${err.message}`);
        slot.innerHTML =
          `<div style="padding:12px;color:#b00020;font:14px/1.4 system-ui;">
             Failed to load <b>${file}</b> for <code>${key}</code>.
           </div>`;
      }
    }
  }

  document.addEventListener("DOMContentLoaded", injectAll);
  window.__injectRefresh = injectAll;
})();

