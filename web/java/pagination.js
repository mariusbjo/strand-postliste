// Pagination-funksjoner

function renderPagination(elementId, page, totalItems) {
  const maxPage = Math.ceil(totalItems / perPage) || 1;
  const el = document.getElementById(elementId);
  if (!el) return;

  el.innerHTML =
    `<button onclick='prevPage()' ${page === 1 ? "disabled" : ""}>Forrige</button>
     <span>Side ${page} av ${maxPage}</span>
     <button onclick='nextPage()' ${page >= maxPage ? "disabled" : ""}>Neste</button>`;
}

function prevPage() {
  if (currentPage > 1) {
    currentPage--;
    renderPage(currentPage);
  }
}

function nextPage() {
  const maxPage = Math.ceil(getFilteredData().length / perPage) || 1;
  if (currentPage < maxPage) {
    currentPage++;
    renderPage(currentPage);
  }
}

