// pagination.js – håndterer sidetall og navigasjon
import { renderPage, setPage } from './render.js';

export function renderPagination(elementId, currentPage, totalItems, perPage) {
  const maxPage = Math.ceil(totalItems / perPage) || 1;
  const el = document.getElementById(elementId);
  if (!el) return;

  el.innerHTML = "";

  const prevBtn = document.createElement("button");
  prevBtn.textContent = "◀ Forrige";
  prevBtn.disabled = currentPage === 1;
  prevBtn.addEventListener("click", () => {
    if (currentPage > 1) {
      setPage(currentPage - 1);
      renderPage(currentPage - 1);
    }
  });
  el.appendChild(prevBtn);

  const info = document.createElement("span");
  info.textContent = ` Side ${currentPage} av ${maxPage} `;
  el.appendChild(info);

  const nextBtn = document.createElement("button");
  nextBtn.textContent = "Neste ▶";
  nextBtn.disabled = currentPage >= maxPage;
  nextBtn.addEventListener("click", () => {
    if (currentPage < maxPage) {
      setPage(currentPage + 1);
      renderPage(currentPage + 1);
    }
  });
  el.appendChild(nextBtn);
}

// Optional default export for compatibility
export default renderPagination;
