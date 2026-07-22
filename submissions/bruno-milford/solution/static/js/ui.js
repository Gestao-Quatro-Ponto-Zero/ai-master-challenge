window.Raven = window.Raven || {};

window.Raven.ui = {
  debounce(callback, delay = 180) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => callback(...args), delay);
    };
  },
  toast(message, type = "info") {
    const container = document.getElementById("toast");
    if (!container) return;
    const item = document.createElement("div");
    item.className = `toast toast-${type}`;
    item.innerHTML = `<span>${message}</span><button type="button" aria-label="Fechar aviso">x</button>`;
    item.querySelector("button").addEventListener("click", () => item.remove());
    container.appendChild(item);
    setTimeout(() => item.remove(), 4800);
  },
  emptyState(title = "Nenhum dado encontrado", body = "Nao existem registros para os filtros selecionados.") {
    return `<div class="empty-state"><strong>${title}</strong><span>${body}</span></div>`;
  },
  errorState(message = "Ocorreu um problema ao consultar as informacoes.") {
    return `<div class="error-state"><strong>Nao foi possivel carregar os dados</strong><span>${message}</span></div>`;
  },
  paginate({ rows, page, pageSize, targetId, onPage }) {
    const pages = Math.max(1, Math.ceil(rows.length / pageSize));
    const safePage = Math.min(page, pages);
    const start = (safePage - 1) * pageSize;
    const target = document.getElementById(targetId);
    if (target) {
      const buttons = [];
      const maxButtons = Math.min(pages, 9);
      for (let i = 1; i <= maxButtons; i += 1) {
        buttons.push(`<button class="${i === safePage ? "active" : ""}" data-page="${i}" type="button">${i}</button>`);
      }
      target.innerHTML = buttons.join("");
      target.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", () => onPage(Number(button.dataset.page)));
      });
    }
    return { pageRows: rows.slice(start, start + pageSize), page: safePage, pages };
  },
  initShell() {
    const menu = document.getElementById("menuToggle");
    const backdrop = document.getElementById("sidebarBackdrop");
    const refresh = document.getElementById("globalRefresh");
    if (menu) {
      menu.addEventListener("click", () => {
        document.body.classList.add("sidebar-open");
        if (backdrop) backdrop.hidden = false;
      });
    }
    if (backdrop) {
      backdrop.addEventListener("click", () => {
        document.body.classList.remove("sidebar-open");
        document.body.classList.remove("filters-open");
        backdrop.hidden = true;
      });
    }
    if (refresh) {
      refresh.addEventListener("click", () => {
        if (typeof window.Raven.refreshPage === "function") window.Raven.refreshPage();
      });
    }
  }
};

document.addEventListener("DOMContentLoaded", () => window.Raven.ui.initShell());
