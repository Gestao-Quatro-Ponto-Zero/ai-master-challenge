"use strict";

/*
 * Gráficos em HTML e CSS, sem biblioteca.
 *
 * Regras seguidas: uma medida por gráfico e um só eixo; barras finas com a
 * ponta arredondada; grade discreta; rótulo direto só no que importa (o maior e
 * o último); o valor exato aparece ao passar o mouse; e todo gráfico pode ser
 * trocado pela tabela dos mesmos números (botão no canto do cartão), para não
 * depender de cor nem de mouse. A tabela ocupa a altura do gráfico: nada pula.
 */
const Charts = (() => {
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function dataTable(headers, rows) {
    return `
      <div class="chart-data" hidden>
        <table>
          <thead><tr>${headers.map((h, i) => `<th${i ? ' class="num"' : ""}>${esc(h)}</th>`).join("")}</tr></thead>
          <tbody>${rows.map((row) => `<tr>${row.map((cell, i) => `<td${i ? ' class="num"' : ""}>${esc(cell)}</td>`).join("")}</tr>`).join("")}</tbody>
        </table>
      </div>`;
  }

  /* Colunas ao longo do tempo. points: [{ label, value }]. */
  function columns(points, { format, name }) {
    const max = Math.max(...points.map((p) => p.value), 1);
    const peak = points.reduce((best, p, i) => (p.value > points[best].value ? i : best), 0);
    const cols = points.map((p, i) => `
      <div class="col" data-tip="${esc(`${p.label}: ${format(p.value)}`)}">
        ${i === peak || i === points.length - 1 ? `<span class="col-label">${format(p.value)}</span>` : ""}
        <i style="height:${Math.max((p.value / max) * 100, p.value ? 1.5 : 0)}%"></i>
      </div>`).join("");
    return `
      <div class="chart" role="img" aria-label="${esc(name)}">
        <div class="cols">${cols}</div>
        <div class="xaxis">${points.map((p) => { const [month, year] = String(p.label).split("/"); return `<span>${esc(month)}${year ? `<small>/${esc(year)}</small>` : ""}</span>`; }).join("")}</div>
      </div>
      ${dataTable(["Mês", name], points.map((p) => [p.label, format(p.value)]))}`;
  }

  /* Barras horizontais de uma medida só. rows: [{ label, value }]. */
  function bars(rows, { format, name, first = "Item" }) {
    const max = Math.max(...rows.map((r) => r.value), 1);
    return `
      <div class="chart" role="img" aria-label="${esc(name)}">
        ${rows.map((r) => `
          <div class="hbar" data-tip="${esc(`${r.label}: ${format(r.value)}`)}">
            <span class="hbar-label">${esc(r.label)}</span>
            <div class="hbar-track"><i style="width:${(r.value / max) * 100}%"></i></div>
            <span class="hbar-value">${format(r.value)}</span>
          </div>`).join("")}
      </div>
      ${dataTable([first, name], rows.map((r) => [r.label, format(r.value)]))}`;
  }

  /* Barras empilhadas: a composição de cada linha. series: [{ key, label, tone }]. */
  function stacked(rows, series, { name, first = "Item" }) {
    const max = Math.max(...rows.map((r) => series.reduce((sum, s) => sum + r[s.key], 0)), 1);
    const legend = series.map((s) => `<span><i class="tone-${s.tone}"></i>${esc(s.label)}</span>`).join("");
    const body = rows.map((r) => {
      const total = series.reduce((sum, s) => sum + r[s.key], 0);
      const segments = series.filter((s) => r[s.key]).map((s) =>
        `<i class="tone-${s.tone}" style="flex:${r[s.key]}" data-tip="${esc(`${r.label} · ${s.label}: ${r[s.key]}`)}"></i>`).join("");
      return `
        <div class="hbar">
          <span class="hbar-label">${esc(r.label)}</span>
          <div class="hbar-track"><div class="stack-row" style="width:${(total / max) * 100}%">${segments}</div></div>
          <span class="hbar-value">${total.toLocaleString("pt-BR")}</span>
        </div>`;
    }).join("");
    return `
      <div class="chart" role="img" aria-label="${esc(name)}">
        <div class="legend-row">${legend}</div>
        ${body}
      </div>
      ${dataTable([first, ...series.map((s) => s.label), "Total"], rows.map((r) => [r.label, ...series.map((s) => r[s.key]), series.reduce((sum, s) => sum + r[s.key], 0)]))}`;
  }

  /* Uma dica só, que acompanha o ponteiro em qualquer marca com data-tip. */
  function installTooltip() {
    const tip = document.createElement("div");
    tip.className = "chart-tip";
    tip.hidden = true;
    document.body.appendChild(tip);
    document.addEventListener("pointermove", (event) => {
      const mark = event.target.closest ? event.target.closest("[data-tip]") : null;
      if (!mark) {
        tip.hidden = true;
        return;
      }
      tip.textContent = mark.dataset.tip;
      tip.hidden = false;
      const width = tip.offsetWidth;
      tip.style.left = `${Math.min(Math.max(event.clientX - width / 2, 8), window.innerWidth - width - 8)}px`;
      tip.style.top = `${Math.max(event.clientY - tip.offsetHeight - 12, 8)}px`;
    });
    document.addEventListener("pointerleave", () => { tip.hidden = true; });
    document.addEventListener("click", (event) => {
      const button = event.target.closest ? event.target.closest("[data-chart-view]") : null;
      if (!button) return;
      const card = button.closest(".chart-card");
      const chart = card.querySelector(".chart");
      const data = card.querySelector(".chart-data");
      const showTable = data.hidden;
      if (showTable) data.style.height = `${chart.offsetHeight}px`;
      chart.hidden = showTable;
      data.hidden = !showTable;
      button.setAttribute("aria-pressed", showTable);
      button.innerHTML = showTable ? '<i class="ph ph-chart-bar"></i>Gráfico' : '<i class="ph ph-table"></i>Tabela';
    });
  }

  return { columns, bars, stacked, installTooltip };
})();
