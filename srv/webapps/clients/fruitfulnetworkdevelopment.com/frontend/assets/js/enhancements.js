/* =========================
   ENHANCEMENTS
   Progressive enhancement system
   All features degrade gracefully - components work without JS
   ========================= */

(function() {
  'use strict';

  /* =========================
     Table Sorting Enhancement
     ========================= */
  function getCellText(cell) {
    return cell ? cell.textContent.trim() : "";
  }

  function detectValueType(value) {
    if (!value) return "text";
    const datePatterns = [
      /^\d{4}-\d{2}-\d{2}$/,
      /^\d{2}\/\d{2}\/\d{4}$/,
      /^\d{2}-\d{2}-\d{4}$/
    ];
    if (datePatterns.some((re) => re.test(value))) return "date";
    if (/\d/.test(value)) return "number";
    return "text";
  }

  function extractNumericValue(value) {
    if (!value) return 0;
    const rangeMatch = value.match(/([\d,]+\.?\d*)\s*[–-]\s*[\d,]+\.?\d*/);
    if (rangeMatch) return parseFloat(rangeMatch[1].replace(/,/g, ""));
    const numMatch = value.match(/[\d,]+\.?\d*/);
    if (numMatch) return parseFloat(numMatch[0].replace(/,/g, ""));
    const lower = value.toLowerCase();
    if (lower === "n/a" || lower === "none") return -1;
    if (lower.includes("unlimited")) return 999999999;
    return 0;
  }

  function compareValues(a, b, type) {
    if (a === b) return 0;
    if (type === "number") {
      return extractNumericValue(a) - extractNumericValue(b);
    }
    if (type === "date") {
      return new Date(a) - new Date(b);
    }
    return a.localeCompare(b, undefined, { sensitivity: "base" });
  }

  function makeSortable(table) {
    if (!table) return;
    const headers = table.querySelectorAll("thead .table__header--sortable");
    let currentCol = -1;
    let currentDir = "asc";

    headers.forEach((header, index) => {
      header.addEventListener("click", () => {
        headers.forEach((h) => {
          h.classList.remove("is-sorted-asc", "is-sorted-desc", "is-active");
        });

        if (currentCol === index) {
          currentDir = currentDir === "asc" ? "desc" : "asc";
        } else {
          currentCol = index;
          currentDir = "asc";
        }

        header.classList.add("is-active");
        header.classList.add(currentDir === "asc" ? "is-sorted-asc" : "is-sorted-desc");

        const tbody = table.querySelector("tbody");
        const rows = Array.from(tbody.querySelectorAll("tr"));
        if (!rows.length) return;

        let type = "text";
        for (const row of rows) {
          const t = getCellText(row.cells[index]);
          if (t) {
            type = detectValueType(t);
            break;
          }
        }

        rows
          .sort((ra, rb) => {
            const a = getCellText(ra.cells[index]);
            const b = getCellText(rb.cells[index]);
            const cmp = compareValues(a, b, type);
            return currentDir === "asc" ? cmp : -cmp;
          })
          .forEach((r) => tbody.appendChild(r));
      });
    });
  }

  function initTableSorting() {
    document
      .querySelectorAll(".table--sortable .table__table")
      .forEach(makeSortable);
  }

  /* =========================
     Responsive Header Height
     ========================= */
  function computeHeaderHeightPx() {
    const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const isMobile = vw < 820;
    const h = isMobile ? (vw / 12) : (vw / 34);
    // Clamp to keep it usable (prevents absurd sizes on very small/large screens)
    return Math.max(44, Math.min(92, Math.round(h)));
  }

  function applySizingVars() {
    const h = computeHeaderHeightPx();
    document.documentElement.style.setProperty("--header-h", h + "px");
  }

  /* =========================
     Header Scroll State
     ========================= */
  function syncHeaderScrollState() {
    const header = document.querySelector('.header');
    if (!header) return;
    const y = window.scrollY || document.documentElement.scrollTop || 0;
    if (y > 10) {
      header.classList.add("is-scrolled");
    } else {
      header.classList.remove("is-scrolled");
    }
  }

  /* =========================
     Navigation Active State
     ========================= */
  function setActiveNavButton() {
    const currentPage = window.location.pathname.split('/').pop().replace('.html', '') || 'index';
    const pageName = currentPage === 'index' || currentPage === '' ? 'home' : currentPage;
    const navButtons = document.querySelectorAll('.header__nav-button[data-page]');
    navButtons.forEach(btn => {
      const btnPage = btn.getAttribute('data-page');
      if (btnPage === pageName) {
        btn.classList.add('is-active');
      } else {
        btn.classList.remove('is-active');
      }
    });
  }

  /* =========================
     Navigation Handlers (Global functions for onclick)
     ========================= */
  window.navigate_to_page = function(page) {
    if (page === 'home') {
      window.location.href = "/index.html";
    } else {
      window.location.href = "/" + page + ".html";
    }
  };

  window.return_home = function() {
    window.location.href = "/";
  };

  window.open_search = function() {
    // Placeholder: implement search modal/functionality
    console.log("open_search()");
  };

  window.open_sidebar_menu = function() {
    // Placeholder: implement sidebar menu
    console.log("open_sidebar_menu()");
  };

  window.link_to_instagram = function() {
    console.log("link_to_instagram()");
  };

  window.link_to_x = function() {
    console.log("link_to_x()");
  };

  window.link_to_facebook = function() {
    console.log("link_to_facebook()");
  };

  /* =========================
     Parallax Effect (Optional - disabled by default)
     ========================= */
  function initParallax() {
    const hero = document.querySelector('.o-section--hero');
    if (!hero) return;
    
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;
    
    // Uncomment to enable JS-based parallax if CSS fixed doesn't work:
    // window.addEventListener('scroll', () => {
    //   const scrolled = window.pageYOffset;
    //   const rate = scrolled * 0.5;
    //   hero.style.backgroundPosition = `center ${rate}px`;
    // }, { passive: true });
  }

 /* =========================
     Initialize All Enhancements
     ========================= */
  function init() {
    syncHeaderScrollState();
    setActiveNavButton();
    initTableSorting();
    // initParallax(); // Uncomment to enable JS-based parallax fallback

    window.addEventListener("resize", applySizingVars);
    window.addEventListener("scroll", syncHeaderScrollState, { passive: true });
  }

  // Apply sizing immediately to prevent flash of incorrect sizing
  applySizingVars();

  // Initialize when DOM is ready
  applySizingVars();

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
