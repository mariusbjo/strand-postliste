import { renderPage } from './render.js';

// === Global state for filtere ===
let currentFilter = "";
let currentSearch = "";
let currentStatus = "";
let currentSort = "dato-desc";
let dateFrom = "";
let dateTo = "";
let currentPage = 1;

// === Filterfunksjoner ===
function applySearch() {
  const input = document.getElementById("searchInput");
  currentSearch = input ? input.value.trim() : "";
  currentPage = 1;
  renderPage(currentPage);
}

function applyDateFilter() {
  const fromEl = document.getElementById("dateFrom");
  const toEl = document.getElementById("dateTo");
  dateFrom = fromEl ? fromEl.value : "";
  dateTo = toEl ? toEl.value : "";
  currentPage = 1;
  renderPage(currentPage);
}

function applyFilter() {
  const el = document.getElementById("filterType");
  currentFilter = el ? el.value : "";
  currentPage = 1;
  renderPage(currentPage);
}

function applyStatusFilter() {
  const el = document.getElementById("statusFilter");
  currentStatus = el ? el.value : "";
  currentPage = 1;
  renderPage(currentPage);
}

function applySort() {
  const el = document.getElementById("sortSelect");
  currentSort = el ? el.value : "dato-desc";
  currentPage = 1;
  renderPage(currentPage);
}

function changePerPage() {
  const el = document.getElementById("perPage");
  if (el && el.value) {
    const newVal = parseInt(el.value, 10);
    if (!isNaN(newVal)) {
      perPage = newVal; // perPage er definert i template.html
    }
  }
  currentPage = 1;
  renderPage(currentPage);
}

// === Koble filterfelter til event listeners ===
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) searchInput.addEventListener("input", applySearch);

  const dateFromEl = document.getElementById("dateFrom");
  const dateToEl = document.getElementById("dateTo");
  if (dateFromEl) dateFromEl.addEventListener("change", applyDateFilter);
  if (dateToEl) dateToEl.addEventListener("change", applyDateFilter);

  const filterTypeEl = document.getElementById("filterType");
  if (filterTypeEl) filterTypeEl.addEventListener("change", applyFilter);

  const statusFilterEl = document.getElementById("statusFilter");
  if (statusFilterEl) statusFilterEl.addEventListener("change", applyStatusFilter);

  const sortSelectEl = document.getElementById("sortSelect");
  if (sortSelectEl) sortSelectEl.addEventListener("change", applySort);

  const perPageEl = document.getElementById("perPage");
  if (perPageEl) perPageEl.addEventListener("change", changePerPage);
});
