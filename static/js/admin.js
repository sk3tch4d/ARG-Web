// ==============================
// ADMIN MODULE
// ==============================
import { collapseAllPanels } from './panels.js';

// ==============================
// ADMIN GATE
// ==============================
export function initAdminLogin() {
  const input = document.getElementById("adpw");
  const errorMsg = document.getElementById("login-error");
  const loginPanel = document.getElementById("login-panel");
  const adminPanels = document.getElementById("admin-panels");

  if (!input || !errorMsg || !loginPanel || !adminPanels) return;

  collapseAllPanels({ excludeSelector: "#login-panel" });

  window.chpw = function () {
    const value = input.value;
    const correct = "getElementById";

    if (value === correct) {
      loginPanel.style.display = "none";
      adminPanels.style.display = "block";
    } else {
      errorMsg.style.display = "block";
    }
  };
}

// ==============================
// CUSTOM JSON UPLOAD FORM
// ==============================
export function initJsonUploadForm() {
  const form = document.getElementById('json-import-form');
  const fileInput = document.getElementById('json-upload');
  if (!form || !fileInput) return;

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
      alert("Please select a JSON file.");
      return;
    }

    const reader = new FileReader();
    reader.onload = function () {
      fetch("/import/shifts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: reader.result
      })
        .then(res => res.json())
        .then(data => {
          alert("Import successful:\n" + JSON.stringify(data));
          fileInput.value = "";
        })
        .catch(err => {
          alert("Error: " + err.message);
        });
    };
    reader.readAsText(file);
  });
}

// ==============================
// AUTO-SUBMIT + LABEL DISPLAY FOR FILE INPUTS
// ==============================
export function initFileUploadDisplay() {
  const jsonInput = document.getElementById("json-upload");
  const csvInput = document.getElementById("csv-upload");

  if (jsonInput) {
    jsonInput.addEventListener("change", function () {
      this.parentElement.textContent = this.files[0]?.name || "Choose JSON File";
      this.form.requestSubmit();
    });
  }

  if (csvInput) {
    csvInput.addEventListener("change", function () {
      this.parentElement.textContent = this.files[0]?.name || "Choose CSV File";
      this.form.submit();
    });
  }
}
