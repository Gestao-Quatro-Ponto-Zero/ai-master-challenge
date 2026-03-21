import { listAllOrFilterManagers } from "../../shared/filter-options-utils.js";

/**
 * Combobox de gestor: lista completa ao focar + filtro incremental (CRP-FIN-01/02, evolui CBX-08).
 * @param {{
 *   rootEl: HTMLElement,
 *   searchInput: HTMLInputElement,
 *   hiddenInput: HTMLInputElement,
 *   listEl: HTMLUListElement,
 *   hintEl: HTMLElement | null,
 *   emptyEl: HTMLElement | null,
 *   getOptions: () => string[],
 *   defaultHint?: string,
 * }} cfg
 */
export function wireManagerCombobox(cfg) {
  const getOptions = cfg.getOptions;
  const defaultHint =
    cfg.defaultHint ?? "Clique ou foco para ver todos os gestores. Digite para filtrar.";
  const rootEl = cfg.rootEl;
  const searchInput = cfg.searchInput;
  const hiddenInput = cfg.hiddenInput;
  const listEl = cfg.listEl;
  const hintEl = cfg.hintEl;
  const emptyEl = cfg.emptyEl;

  let panelOpen = false;
  /** @type {{ value: string, label: string }[]} */
  let displayOptions = [];
  let activeIndex = -1;
  let debounceTimer = 0;
  let blurCloseTimer = 0;
  const ac = new AbortController();
  const { signal } = ac;

  function clearBlurTimer() {
    if (blurCloseTimer) {
      window.clearTimeout(blurCloseTimer);
      blurCloseTimer = 0;
    }
  }

  function showHint(text) {
    if (hintEl) hintEl.textContent = text;
    if (emptyEl) emptyEl.hidden = true;
  }

  function showEmpty(msg) {
    if (emptyEl) {
      emptyEl.textContent = msg;
      emptyEl.hidden = false;
    }
    listEl.hidden = true;
  }

  function hideEmpty() {
    if (emptyEl) emptyEl.hidden = true;
  }

  function rebuildDisplayOptions() {
    const all = getOptions();
    const t = searchInput.value.trim();
    const matches = listAllOrFilterManagers(all, t);
    if (!all.length) {
      displayOptions = [];
      return;
    }
    displayOptions = [
      { value: "", label: "Todos os gestores" },
      ...matches.map((v) => ({ value: v, label: v })),
    ];
  }

  function setActiveDescendant() {
    if (activeIndex >= 0 && displayOptions[activeIndex]) {
      searchInput.setAttribute("aria-activedescendant", `manager-opt-${activeIndex}`);
    } else {
      searchInput.removeAttribute("aria-activedescendant");
    }
  }

  function updateActiveVisual() {
    Array.from(listEl.querySelectorAll("li")).forEach((li, i) => {
      const on = i === activeIndex;
      li.classList.toggle("is-active", on);
      li.setAttribute("aria-selected", on ? "true" : "false");
    });
    setActiveDescendant();
  }

  function paintList() {
    listEl.replaceChildren();
    const q = searchInput.value.trim();
    if (!panelOpen) {
      listEl.hidden = true;
      searchInput.setAttribute("aria-expanded", "false");
      hideEmpty();
      searchInput.removeAttribute("aria-activedescendant");
      return;
    }

    rebuildDisplayOptions();

    if (displayOptions.length === 0) {
      showEmpty(q.length ? "Nenhum gestor encontrado" : "Nenhum gestor disponível");
      searchInput.setAttribute("aria-expanded", "true");
      activeIndex = -1;
      searchInput.removeAttribute("aria-activedescendant");
      return;
    }

    hideEmpty();
    activeIndex = 0;
    displayOptions.forEach((opt, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === 0 ? "true" : "false");
      li.id = `manager-opt-${i}`;
      li.textContent = opt.label;
      li.className = "combobox-option";
      if (i === activeIndex) li.classList.add("is-active");
      li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        selectOption(opt);
      });
      listEl.appendChild(li);
    });
    listEl.hidden = false;
    searchInput.setAttribute("aria-expanded", "true");
    updateActiveVisual();
  }

  function openPanel() {
    panelOpen = true;
    paintList();
  }

  function closePanel() {
    panelOpen = false;
    listEl.hidden = true;
    searchInput.setAttribute("aria-expanded", "false");
    hideEmpty();
    searchInput.removeAttribute("aria-activedescendant");
  }

  function selectOption(opt) {
    if (opt.value === "") {
      hiddenInput.value = "";
      searchInput.value = "";
      showHint("Sem filtro de gestor — todas as equipas (sujeito a outros filtros).");
    } else {
      hiddenInput.value = opt.value;
      searchInput.value = opt.label;
      showHint("Gestor selecionado. Limpar filtros repõe «Todos».");
    }
    closePanel();
  }

  searchInput.addEventListener(
    "input",
    () => {
      window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(() => {
        const q = searchInput.value;
        if (hiddenInput.value && q !== hiddenInput.value) {
          hiddenInput.value = "";
        }
        panelOpen = true;
        paintList();
      }, 120);
    },
    { signal },
  );

  searchInput.addEventListener(
    "keydown",
    (e) => {
      if (e.key === "Tab") {
        return;
      }
      if (e.key === "Escape") {
        closePanel();
        e.preventDefault();
        return;
      }
      if (!panelOpen && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
        e.preventDefault();
        openPanel();
        return;
      }
      if (listEl.hidden || displayOptions.length === 0) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        activeIndex = Math.min(activeIndex + 1, displayOptions.length - 1);
        updateActiveVisual();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        updateActiveVisual();
      } else if (e.key === "Enter") {
        if (activeIndex >= 0 && displayOptions[activeIndex]) {
          e.preventDefault();
          selectOption(displayOptions[activeIndex]);
        }
      }
    },
    { signal },
  );

  searchInput.addEventListener(
    "blur",
    () => {
      clearBlurTimer();
      blurCloseTimer = window.setTimeout(() => {
        blurCloseTimer = 0;
        closePanel();
      }, 150);
    },
    { signal },
  );

  searchInput.addEventListener(
    "focus",
    () => {
      showHint(defaultHint);
      openPanel();
    },
    { signal },
  );

  function closeFromOutside(ev) {
    if (!rootEl.contains(/** @type {Node} */ (ev.target))) {
      closePanel();
    }
  }
  document.addEventListener("pointerdown", closeFromOutside, true);

  return {
    reset() {
      searchInput.value = "";
      hiddenInput.value = "";
      displayOptions = [];
      listEl.replaceChildren();
      closePanel();
      showHint(defaultHint);
      searchInput.removeAttribute("aria-activedescendant");
    },
    getValue: () => hiddenInput.value.trim() || "",
    destroy() {
      window.clearTimeout(debounceTimer);
      clearBlurTimer();
      ac.abort();
      document.removeEventListener("pointerdown", closeFromOutside, true);
    },
  };
}
