// ==============================
// RESULTS.JS
// Render Search Result Entries
// ==============================

import { getSeniorityEmoji } from './emoji.js';

// ==============================
// RENDER MATCHED RESULTS
// ==============================
export function renderResults(matches) {
  const resultsDiv = document.getElementById("seniority-results");
  if (!matches || matches.length === 0) {
    resultsDiv.innerHTML = "<p>No matching entries found.</p>";
    return;
  }

  let html = "<ul style='list-style: none; padding-left: 0;'>";

  matches.forEach(row => {
    const first = row["First Name"] || "";
    const last = row["Last Name"] || "";
    const position = row["Position"] || "";
    const status = row["Status"] || "";
    const years = parseFloat(row["Years"] || 0);
    const emoji = getSeniorityEmoji(status, position);

    html += "<li style='margin-bottom: 1.5em;'>";
    html += `<strong>${first} ${last}</strong><br>`;
    html += `${emoji} ${status}<br>`;
    html += `<em>${position}</em><br>`;
    html += `${years.toFixed(2)} Years`;
    html += "</li>";
  });

  html += "</ul>";
  resultsDiv.innerHTML = html;
  resultsDiv.scrollTop = 0;
}
