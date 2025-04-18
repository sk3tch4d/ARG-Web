// ==============================
// SEARCH.JS
// Core Search + Filter Utilities
// ==============================


// ==============================
// NORMALIZATION HELPERS
// ==============================
export function normalize(str) {
  return String(str || "")
    .toLowerCase()
    .replace(/[-_]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function isMobile() {
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}


// ==============================
// PANEL TOGGLING
// ==============================
export function openPanelById(panelId) {
  const panel = document.getElementById(panelId);
  const header = panel?.querySelector(".panel-header");
  if (panel && header && !panel.classList.contains("open")) {
    header.click();
  }
}


// ==============================
// SEARCH FROM GLOBAL STATS
// ==============================
export function searchFromStat(query) {
  const input = document.getElementById("seniority-search");
  const data = window.seniorityData || [];
  let matches = [];

  if (query.startsWith("Years>=")) {
    const threshold = parseFloat(query.split(">=")[1]);
    matches = data.filter(row => parseFloat(row["Years"] || 0) >= threshold);
    input.value = `${threshold}+`;
  } else {
    matches = data.filter(row =>
      Object.values(row).some(val =>
        normalize(val).includes(normalize(query))
      )
    );
    input.value = query;
  }

  renderResults(matches);
  populateStats(matches);
  openPanelById("search-panel");
}


// ==============================
// MAIN SEARCH FUNCTION
// ==============================
export function doSenioritySearch() {
  const input = document.getElementById("seniority-search");
  const queryRaw = input.value.trim();
  const query = normalize(queryRaw);
  const data = window.seniorityData || [];

  if (!query) {
    renderResults([]);
    populateStats([]);
    window.currentSearchResults = [];
    return;
  }

  let matches;
  if (!isNaN(queryRaw)) {
    const minYears = parseFloat(queryRaw);
    matches = data.filter(row => parseFloat(row["Years"] || 0) >= minYears);
  } else {
    matches = data.filter(row =>
      Object.values(row).some(val =>
        normalize(val).includes(query)
      )
    );
  }

  renderResults(matches);
  populateStats(matches);
  window.currentSearchResults = matches;
}
