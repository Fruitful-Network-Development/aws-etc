document.addEventListener("DOMContentLoaded", () => {
  const dateEl = document.getElementById("current-date");
  if (!dateEl) return;

  const now = new Date();

  const formatted = now.toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric"
  });

  dateEl.textContent = formatted;
});

