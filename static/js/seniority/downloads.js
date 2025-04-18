// ==============================
// DOWNLOADS.JS
// Downloads for Search Results
// ==============================

import * as XLSX from "https://cdn.sheetjs.com/xlsx-latest/package/xlsx.mjs";


// ==============================
// INIT BUTTON DOWNLOAD
// ==============================
export function setupDownloadButton() {
  const btn = document.getElementById("download-search-button");
  if (btn) {
    btn.addEventListener("click", downloadSearch);
  }
}


// ==============================
// DOWNLOADS XLSX
// ==============================
export function downloadSearch() {
  const results = window.currentSearchResults || [];
  if (!results.length) {
    alert("No search results to download.");
    return;
  }

  // Define headers and row order
  const headers = ["Years", "First Name", "Last Name", "Status", "Position"];
  const dataRows = results.map(row => [
    Math.round(row["Years"] || 0),
    row["First Name"] || "",
    row["Last Name"] || "",
    row["Status"] || "",
    row["Position"] || ""
  ]);

  // Prepare the worksheet
  const worksheet = XLSX.utils.aoa_to_sheet([
    headers,
    [], // Blank row after header
    ...dataRows,
  ]);

  // Auto column widths with fallback
  worksheet['!cols'] = headers.map((_, i) => {
    const colData = dataRows.map(r => String(r[i] || ""));
    const maxLen = Math.max(headers[i].length, ...colData.map(x => x.length));
    return { wch: maxLen + 3 }; // +3 buffer for padding
  });

  // Set header row height
  worksheet['!rows'] = [{ hpt: 20 }];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Search Results");
  XLSX.writeFile(workbook, "Search_Results.xlsx");
}
