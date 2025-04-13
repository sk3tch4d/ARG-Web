// ==============================
// PANEL MODULE
// ==============================
import { togglePanel, collapseAllPanels } from './panels.js';
window.togglePanel = togglePanel;

// Close Panels: General Override
if (document.getElementById("force-panel")) {
  collapseAllPanels({ excludeSelector: "#force-panel" });
} else {
  collapseAllPanels();
}
// ==============================
// DROPZONE MODULE
// ==============================
import { initDropzone } from './dropzone.js';
initDropzone();

// ==============================
// HEADER TYPEWRITER
// ==============================
import { initTypewriter } from './header.js';
initTypewriter();

// ==============================
// QUOTES MODULE
// ==============================
import { initQuotes, displayRandomQuote } from './quotes.js';
initQuotes();

// ==============================
// SCHEDULE MODULE
// ==============================
import { initScheduleUI } from './schedule.js';
initScheduleUI();

// ==============================
// ADMIN MODULE
// ==============================
import { initAdminLogin, initJsonUploadForm, initFileUploadDisplay } from './admin.js';
initAdminLogin();
initJsonUploadForm();
initFileUploadDisplay();
