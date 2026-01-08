/**
 * Table Sorting Functionality
 * Makes data tables sortable by column with support for:
 * - String sorting
 * - Numeric sorting (including currency and hidden numeric values)
 * - Date sorting
 * - Toggle ascending/descending per column
 */

(function() {
  'use strict';

  /**
   * Extract numeric value from text (handles currency, percentages, ranges)
   * @param {string} text - Text to extract number from
   * @returns {number|null} - Extracted number or null if not found
   */
  function extractNumericValue(text) {
    if (!text || typeof text !== 'string') {
      return null;
    }

    // Remove common currency symbols and text
    let cleaned = text.trim()
      .replace(/^\$/, '')           // Remove leading $
      .replace(/[,\s]/g, '')        // Remove commas and spaces
      .replace(/\+$/, '')           // Remove trailing +
      .replace(/\/mo$/, '')         // Remove /mo suffix
      .replace(/\/yr$/, '')         // Remove /yr suffix
      .replace(/^N\/A$/i, '')       // Handle N/A
      .replace(/^No\s+/i, '')       // Remove "No " prefix
      .replace(/\s*-\s*.*$/, '');    // Handle ranges (take first value)

    // Try to extract first number (handles ranges like "$249 - $699+")
    const numberMatch = cleaned.match(/[\d.]+/);
    if (numberMatch) {
      const num = parseFloat(numberMatch[0]);
      return isNaN(num) ? null : num;
    }

    return null;
  }

  /**
   * Parse date from text
   * @param {string} text - Text to parse date from
   * @returns {Date|null} - Parsed date or null if not found
   */
  function parseDate(text) {
    if (!text || typeof text !== 'string') {
      return null;
    }

    const date = new Date(text.trim());
    return isNaN(date.getTime()) ? null : date;
  }

  /**
   * Get cell value for sorting
   * @param {HTMLElement} cell - Table cell element
   * @returns {string|number|Date|null} - Value to sort by
   */
  function getCellValue(cell) {
    if (!cell) return null;

    // Get text content, handling images (use alt text or parent text)
    let text = '';
    const img = cell.querySelector('img');
    if (img) {
      text = img.alt || img.title || '';
    } else {
      text = cell.textContent || cell.innerText || '';
    }

    text = text.trim();

    // Try to extract numeric value first
    const numericValue = extractNumericValue(text);
    if (numericValue !== null) {
      return numericValue;
    }

    // Try to parse as date
    const dateValue = parseDate(text);
    if (dateValue !== null) {
      return dateValue;
    }

    // Return as string (case-insensitive for comparison)
    return text.toLowerCase();
  }

  /**
   * Compare two values for sorting
   * @param {*} a - First value
   * @param {*} b - Second value
   * @param {boolean} ascending - Sort direction
   * @returns {number} - Comparison result
   */
  function compareValues(a, b, ascending) {
    // Handle null/undefined values
    if (a === null || a === undefined) return ascending ? 1 : -1;
    if (b === null || b === undefined) return ascending ? -1 : 1;

    // Handle dates
    if (a instanceof Date && b instanceof Date) {
      return ascending ? a - b : b - a;
    }

    // Handle numbers
    if (typeof a === 'number' && typeof b === 'number') {
      return ascending ? a - b : b - a;
    }

    // Handle strings
    if (typeof a === 'string' && typeof b === 'string') {
      return ascending ? a.localeCompare(b) : b.localeCompare(a);
    }

    // Mixed types: convert to string
    const aStr = String(a);
    const bStr = String(b);
    return ascending ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
  }

  /**
   * Sort table rows
   * @param {HTMLTableElement} table - Table element
   * @param {number} columnIndex - Column index to sort by
   * @param {boolean} ascending - Sort direction
   */
  function sortTable(table, columnIndex, ascending) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Sort rows
    rows.sort((rowA, rowB) => {
      const cellA = rowA.cells[columnIndex];
      const cellB = rowB.cells[columnIndex];
      const valueA = getCellValue(cellA);
      const valueB = getCellValue(cellB);
      return compareValues(valueA, valueB, ascending);
    });

    // Re-append sorted rows (this preserves event listeners)
    rows.forEach(row => tbody.appendChild(row));
  }

  /**
   * Update header visual indicators
   * @param {HTMLTableElement} table - Table element
   * @param {number} activeColumnIndex - Currently sorted column index
   * @param {boolean} ascending - Sort direction
   */
  function updateHeaderIndicators(table, activeColumnIndex, ascending) {
    const headers = table.querySelectorAll('thead th');
    headers.forEach((header, index) => {
      // Remove existing indicators
      header.classList.remove('sort-asc', 'sort-desc');
      
      // Add indicator to active column
      if (index === activeColumnIndex) {
        header.classList.add(ascending ? 'sort-asc' : 'sort-desc');
      }
    });
  }

  /**
   * Initialize sortable table
   * @param {HTMLTableElement} table - Table element to make sortable
   */
  function initSortableTable(table) {
    const headers = table.querySelectorAll('thead th');
    let currentSortColumn = null;
    let currentSortDirection = true; // true = ascending, false = descending

    headers.forEach((header, index) => {
      // Make header clickable
      header.style.cursor = 'pointer';
      header.setAttribute('role', 'button');
      header.setAttribute('tabindex', '0');
      header.setAttribute('aria-label', `Sort by ${header.textContent.trim()}`);

      // Add click handler
      const handleSort = (e) => {
        e.preventDefault();
        
        // Toggle direction if clicking the same column, otherwise start ascending
        if (currentSortColumn === index) {
          currentSortDirection = !currentSortDirection;
        } else {
          currentSortColumn = index;
          currentSortDirection = true;
        }

        // Sort the table
        sortTable(table, index, currentSortDirection);
        
        // Update visual indicators
        updateHeaderIndicators(table, index, currentSortDirection);
      };

      header.addEventListener('click', handleSort);
      header.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSort(e);
        }
      });
    });
  }

  /**
   * Initialize all sortable tables on page load
   */
  function init() {
    // Only run if JavaScript is available (progressive enhancement)
    const tables = document.querySelectorAll('table.data-table');
    
    if (tables.length === 0) {
      return; // No tables found
    }

    tables.forEach(table => {
      initSortableTable(table);
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM is already ready
    init();
  }
})();

