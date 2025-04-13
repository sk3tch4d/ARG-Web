// ==============================
//  SHARED SCRIPTS
// ==============================

// === HEADER TYPEWRITER ===
const typedTextEl = document.getElementById("typed-text");
if (typedTextEl) {
  const text = typedTextEl.innerText?.trim() || "ARG Analyzer";
  const speed = 100;
  let i = 0;
  function typeWriter() {
    if (i < text.length) {
      typedTextEl.innerHTML += text.charAt(i);
      i++;
      setTimeout(typeWriter, speed);
    }
  }
  window.addEventListener("DOMContentLoaded", typeWriter);
}

// === DROPZONE FUNCTIONALITY ===
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");

let quotes = [];

fetch('/static/quotes.json')
  .then(response => response.json())
  .then(data => {
    quotes = data;
    const quote = quotes[Math.floor(Math.random() * quotes.length)];
    document.getElementById("quote").textContent = quote;
  })
  .catch(error => {
    console.error("Failed to load quotes:", error);
  });

document.querySelector("form")?.addEventListener("submit", function () {
  document.getElementById("upload-form")?.style?.display = "none";
  document.getElementById("loading")?.style?.display = "block";
  document.getElementById("quote").textContent = quotes[Math.floor(Math.random() * quotes.length)];
});

fileInput?.addEventListener("change", () => {
  fileList.innerHTML = "";
  [...fileInput.files].forEach(file => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.className = "file-action uploaded";
    link.href = "#";
    link.textContent = file.name;
    li.appendChild(link);
    fileList.appendChild(li);
  });
});

dropZone?.addEventListener("dragover", e => {
  e.preventDefault();
  dropZone.classList.add("active");
});

dropZone?.addEventListener("dragleave", e => {
  e.preventDefault();
  dropZone.classList.remove("active");
});

dropZone?.addEventListener("drop", e => {
  e.preventDefault();
  fileInput.files = e.dataTransfer.files;
  fileInput.dispatchEvent(new Event("change"));
  dropZone.classList.remove("active");
});

// === PANEL TOGGLE MERGED VERSION ===
function togglePanel(header) {
  const panel = header.closest('.panel');
  const body = header.nextElementSibling;

  document.querySelectorAll('.panel').forEach(p => {
    if (p !== panel) {
      p.classList.remove('open');
      const otherBody = p.querySelector('.panel-body');
      if (otherBody) otherBody.classList.remove('open');
    }
  });

  const isOpen = panel.classList.toggle('open');
  header.classList.toggle('open', isOpen);
  if (body) body.classList.toggle('open', isOpen);

  // Mobile focus reset
  if (!isOpen) {
    setTimeout(() => {
      const resetTarget = document.getElementById('mobile-focus-reset');
      if (resetTarget) {
        resetTarget.focus();
      }
    }, 10);
  }

  // Re-trigger bounce
  header.classList.remove('bounce');
  void header.offsetWidth;
  header.classList.add('bounce');
}

// === Shared: Close all panel bodies initially ===
document.querySelectorAll('.panel-body').forEach(e => {
  e.classList.remove('open');
});

// === FETCHING SCHEDULE ===
async function fetchWorkingOnDate() {
  const dateInput = document.getElementById('working-date');
  const resultsDiv = document.getElementById('working-date-results');
  const loadingDiv = document.getElementById('working-date-loading');
  const dateStr = dateInput.value;

  if (!dateStr) return;

  resultsDiv.innerHTML = "";
  loadingDiv.style.display = "block";

  try {
    const response = await fetch(`/api/working_on_date?date=${dateStr}`);
    const data = await response.json();
    const shiftIcons = { Day: '☀️', Evening: '🌇', Night: '🌙' };
    let html = '';

    if (data.error) {
      html = `<p class="error">${data.error}</p>`;
    } else {
      ['Day', 'Evening', 'Night'].forEach(type => {
        if (data[type] && data[type].length > 0) {
          html += `<h4>${shiftIcons[type]} <span class="badge badge-${type.toLowerCase()}">${type}</span></h4><ul>`;
          data[type].forEach(([name, shift]) => {
            html += `<li>${name} (${shift})</li>`;
          });
          html += `</ul>`;
        }
      });
      if (!html) html = "<p>No employees scheduled for this date.</p>";
    }

    resultsDiv.innerHTML = html;
  } catch (err) {
    resultsDiv.innerHTML = `<p class="error">Error fetching data</p>`;
  } finally {
    loadingDiv.style.display = "none";
  }
}

// === FORMAT CUSTOM DATE LABEL ===
function updateCustomDateText(date, element) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);
  date.setHours(0, 0, 0, 0);

  if (date.getTime() === today.getTime()) {
    element.textContent = "Today";
    return;
  } else if (date.getTime() === tomorrow.getTime()) {
    element.textContent = "Tomorrow";
    return;
  }

  const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  const getOrdinal = (n) => {
    if (n > 3 && n < 21) return "th";
    switch (n % 10) {
      case 1: return "st";
      case 2: return "nd";
      case 3: return "rd";
      default: return "th";
    }
  };

  const weekday = dayNames[date.getDay()];
  const month = monthNames[date.getMonth()];
  const day = date.getDate();
  element.textContent = `${weekday} ${month} ${day}${getOrdinal(day)}`;
}

// === INIT LABELS AND FETCH ON LOAD ===
window.addEventListener("DOMContentLoaded", () => {
  const dateInput = document.getElementById("working-date");
  const customText = document.getElementById("custom-date-text");

  if (dateInput && customText) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const isoDate = today.toISOString().split('T')[0];
    dateInput.value = isoDate;

    const [y, m, d] = isoDate.split('-').map(Number);
    const localToday = new Date(y, m - 1, d);
    updateCustomDateText(localToday, customText);
    fetchWorkingOnDate();

    dateInput.addEventListener("change", () => {
      const [y, m, d] = dateInput.value.split('-').map(Number);
      const selected = new Date(y, m - 1, d);
      updateCustomDateText(selected, customText);
      fetchWorkingOnDate();
    });

    dateInput.addEventListener("input", () => {
      const [y, m, d] = dateInput.value.split('-').map(Number);
      const selected = new Date(y, m - 1, d);
      updateCustomDateText(selected, customText);
    });
  }
});
