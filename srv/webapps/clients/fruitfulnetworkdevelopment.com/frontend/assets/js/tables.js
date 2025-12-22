(function () {
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
    const headers = table.querySelectorAll("thead .sortable");
    let currentCol = -1;
    let currentDir = "asc";

    headers.forEach((header, index) => {
      header.addEventListener("click", () => {
        headers.forEach((h) =>
          h.classList.remove("sort-asc", "sort-desc", "sort-active")
        );

        if (currentCol === index) {
          currentDir = currentDir === "asc" ? "desc" : "asc";
        } else {
          currentCol = index;
          currentDir = "asc";
        }

        header.classList.add("sort-active");
        header.classList.add(currentDir === "asc" ? "sort-asc" : "sort-desc");

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

  function initAll() {
    document
      .querySelectorAll(".tbl-payments__table[data-sortable='true'], .tbl-pos__table[data-sortable='true']")
      .forEach(makeSortable);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
