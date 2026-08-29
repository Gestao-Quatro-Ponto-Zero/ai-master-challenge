(() => {
  const body = document.body;
  const sidebar = document.querySelector("#app-sidebar");
  const openButton = document.querySelector("#mobile-nav");
  const closeButton = document.querySelector("#close-mobile-nav");
  const backdrop = document.querySelector("#mobile-nav-backdrop");
  const scroller = document.querySelector(".framework-workspace");
  const dimensionLinks = [...document.querySelectorAll(".framework-tabs [data-dimension]")];
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const setNavigationOpen = (isOpen) => {
    body.classList.toggle("mobile-sidebar-open", isOpen);
    openButton?.setAttribute("aria-expanded", String(isOpen));
    if (backdrop) backdrop.hidden = !isOpen;
    if (isOpen) {
      window.requestAnimationFrame(() => closeButton?.focus());
    } else if (document.activeElement && sidebar?.contains(document.activeElement)) {
      openButton?.focus();
    }
  };

  openButton?.addEventListener("click", () => setNavigationOpen(true));
  closeButton?.addEventListener("click", () => setNavigationOpen(false));
  backdrop?.addEventListener("click", () => setNavigationOpen(false));
  sidebar?.addEventListener("click", (event) => {
    if (event.target.closest("a") && window.matchMedia("(max-width: 720px)").matches) {
      setNavigationOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setNavigationOpen(false);
  });

  const dimensions = [
    { key: "pp", start: document.querySelector("#power-priority") },
    { key: "p", start: document.querySelector("#propensity") },
    { key: "o", start: document.querySelector("#opportunity-value") },
    { key: "w", start: document.querySelector("#warmth") },
    { key: "e", start: document.querySelector("#execution-fit") },
    { key: "r", start: document.querySelector("#recommendation") },
  ].filter((item) => item.start);

  const updateCurrentSection = () => {
    const marker = (scroller?.getBoundingClientRect().top || 0) + 160;
    let activeDimension = dimensions[0]?.key;

    dimensions.forEach((item) => {
      if (item.start.getBoundingClientRect().top <= marker) activeDimension = item.key;
    });

    dimensionLinks.forEach((link) => {
      const isActive = link.dataset.dimension === activeDimension;
      link.classList.toggle("is-active", isActive);
      if (isActive) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  };

  let ticking = false;
  scroller?.addEventListener(
    "scroll",
    () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        updateCurrentSection();
        ticking = false;
      });
    },
    { passive: true },
  );

  dimensionLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      const target = document.querySelector(link.getAttribute("href"));
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ block: "start", behavior: reduceMotion.matches ? "auto" : "smooth" });
      window.history.replaceState(null, "", link.getAttribute("href"));
      updateCurrentSection();
    });
  });

  updateCurrentSection();
})();
