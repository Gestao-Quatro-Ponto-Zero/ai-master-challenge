window.Raven = window.Raven || {};

const ravenPlotlyLayout = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: {
    family: "Inter, system-ui, sans-serif",
    color: "#475569",
    size: 12
  },
  margin: { l: 48, r: 20, t: 18, b: 48 },
  hoverlabel: {
    bgcolor: "#0F172A",
    bordercolor: "#0F172A",
    font: { color: "#FFFFFF" }
  },
  xaxis: { gridcolor: "#EEF2F7", zerolinecolor: "#E2E8F0" },
  yaxis: { gridcolor: "#EEF2F7", zerolinecolor: "#E2E8F0" }
};

const ravenPlotlyConfig = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"]
};

window.Raven.charts = {
  colors: {
    blue: "#2563EB",
    navy: "#0F172A",
    green: "#16A34A",
    amber: "#D97706",
    red: "#DC2626",
    purple: "#7C3AED",
    muted: "#94A3B8"
  },
  baseLayout(extra = {}) {
    return { ...ravenPlotlyLayout, ...extra };
  },
  config: ravenPlotlyConfig,
  empty(id) {
    const element = document.getElementById(id);
    if (element) element.innerHTML = window.Raven.ui.emptyState();
  },
  hasPlotly() {
    return typeof window.Plotly !== "undefined" && typeof window.Plotly.newPlot === "function";
  },
  bar(id, rows, x, y, color = "#2563EB", options = {}) {
    if (!rows || !rows.length) return this.empty(id);
    fallbackBar(id, rows, x, y, color, options);
    if (!this.hasPlotly()) return;
    const formatter = options.formatter || window.Raven.format.number;
    return safePlot(
      id,
      [{
        x: rows.map((row) => row[x]),
        y: rows.map((row) => row[y]),
        customdata: rows.map((row) => formatter(row[y])),
        type: "bar",
        marker: { color },
        hovertemplate: "%{x}<br>%{customdata}<extra></extra>"
      }],
      this.baseLayout(options.layout || {}),
      this.config,
      () => fallbackBar(id, rows, x, y, color, options)
    );
  },
  horizontalBar(id, rows, label, value, color = "#2563EB", options = {}) {
    if (!rows || !rows.length) return this.empty(id);
    const limited = rows.slice(0, options.limit || 10).reverse();
    fallbackHorizontalBar(id, limited, label, value, color, options);
    if (!this.hasPlotly()) return;
    const formatter = options.formatter || window.Raven.format.number;
    return safePlot(
      id,
      [{
        x: limited.map((row) => row[value]),
        y: limited.map((row) => row[label]),
        customdata: limited.map((row) => formatter(row[value])),
        type: "bar",
        orientation: "h",
        marker: { color },
        hovertemplate: "%{y}<br>%{customdata}<extra></extra>"
      }],
      this.baseLayout({ margin: { l: 120, r: 20, t: 14, b: 38 }, ...(options.layout || {}) }),
      this.config,
      () => fallbackHorizontalBar(id, limited, label, value, color, options)
    );
  },
  dualAxisTimeline(id, rows) {
    if (!rows || !rows.length) return this.empty(id);
    fallbackTimeline(id, rows);
    if (!this.hasPlotly()) return;
    return safePlot(
      id,
      [
        {
          x: rows.map((row) => row.month),
          y: rows.map((row) => row.churn_events),
          name: "Eventos de churn",
          type: "bar",
          marker: { color: this.colors.blue },
          hovertemplate: "%{x}<br>%{y} eventos<extra></extra>"
        },
        {
          x: rows.map((row) => row.month),
          y: rows.map((row) => row.lost_mrr),
          name: "MRR perdido",
          type: "scatter",
          mode: "lines+markers",
          yaxis: "y2",
          line: { color: this.colors.red, width: 3 },
          marker: { color: this.colors.red },
          hovertemplate: "%{x}<br>$ %{y:,.2f}<extra></extra>"
        }
      ],
      this.baseLayout({
        legend: { orientation: "h", y: 1.08 },
        yaxis2: { overlaying: "y", side: "right", gridcolor: "rgba(0,0,0,0)" }
      }),
      this.config,
      () => fallbackTimeline(id, rows)
    );
  },
  segment(id, rows) {
    if (!rows || !rows.length) return this.empty(id);
    const limited = rows.slice(0, 8);
    fallbackSegment(id, limited);
    if (!this.hasPlotly()) return;
    return safePlot(
      id,
      [
        {
          x: limited.map((row) => row.segment),
          y: limited.map((row) => row.churned_accounts),
          name: "Contas churn",
          type: "bar",
          marker: { color: this.colors.red }
        },
        {
          x: limited.map((row) => row.segment),
          y: limited.map((row) => row.churn_rate),
          name: "Taxa",
          type: "scatter",
          yaxis: "y2",
          mode: "lines+markers",
          line: { color: this.colors.blue, width: 3 }
        }
      ],
      this.baseLayout({
        legend: { orientation: "h", y: 1.08 },
        yaxis2: { overlaying: "y", side: "right", ticksuffix: "%", gridcolor: "rgba(0,0,0,0)" }
      }),
      this.config,
      () => fallbackSegment(id, limited)
    );
  }
};

function safePlot(id, traces, layout, config, fallback) {
  try {
    const result = Plotly.newPlot(id, traces, layout, config);
    if (result && typeof result.catch === "function") {
      result.catch(() => fallback());
    }
    return result;
  } catch (error) {
    return fallback();
  }
}

function fallbackBar(id, rows, labelKey, valueKey, color, options = {}) {
  const element = document.getElementById(id);
  if (!element) return;
  const formatter = options.formatter || window.Raven.format.number;
  const values = rows.map((row) => Number(row[valueKey] || 0));
  const max = Math.max(...values, 1);
  element.innerHTML = `<div class="fallback-chart vertical-chart">
    ${rows.map((row) => {
      const value = Number(row[valueKey] || 0);
      const height = Math.max((value / max) * 180, 3);
      return `<div class="fallback-column">
        <div class="fallback-bar" style="height:${height}px;background:${color}"></div>
        <span title="${row[labelKey]}">${row[labelKey]}</span>
        <strong>${formatter(value)}</strong>
      </div>`;
    }).join("")}
  </div>`;
}

function fallbackHorizontalBar(id, rows, labelKey, valueKey, color, options = {}) {
  const element = document.getElementById(id);
  if (!element) return;
  const formatter = options.formatter || window.Raven.format.number;
  const values = rows.map((row) => Number(row[valueKey] || 0));
  const max = Math.max(...values, 1);
  element.innerHTML = `<div class="fallback-chart horizontal-chart">
    ${rows.map((row) => {
      const value = Number(row[valueKey] || 0);
      const width = Math.max((value / max) * 100, 2);
      return `<div class="fallback-row">
        <span title="${row[labelKey]}">${row[labelKey]}</span>
        <div><i style="width:${width}%;background:${color}"></i></div>
        <strong>${formatter(value)}</strong>
      </div>`;
    }).join("")}
  </div>`;
}

function fallbackTimeline(id, rows) {
  const element = document.getElementById(id);
  if (!element) return;
  const values = rows.map((row) => Number(row.churn_events || 0));
  const max = Math.max(...values, 1);
  element.innerHTML = `<div class="fallback-chart vertical-chart timeline-fallback">
    ${rows.slice(-12).map((row) => {
      const value = Number(row.churn_events || 0);
      const height = Math.max((value / max) * 220, 3);
      return `<div class="fallback-column">
        <div class="fallback-bar" style="height:${height}px;background:#2563EB"></div>
        <span title="${row.month}">${row.month}</span>
        <strong>${window.Raven.format.number(value)}</strong>
      </div>`;
    }).join("")}
  </div>`;
}

function fallbackSegment(id, rows) {
  const element = document.getElementById(id);
  if (!element) return;
  const max = Math.max(...rows.map((row) => Number(row.churned_accounts || 0)), 1);
  element.innerHTML = `<div class="fallback-chart horizontal-chart">
    ${rows.map((row) => {
      const value = Number(row.churned_accounts || 0);
      const width = Math.max((value / max) * 100, 2);
      return `<div class="fallback-row">
        <span title="${row.segment}">${row.segment}</span>
        <div><i style="width:${width}%;background:#DC2626"></i></div>
        <strong>${window.Raven.format.number(value)} | ${window.Raven.format.percent(row.churn_rate, 1)}</strong>
      </div>`;
    }).join("")}
  </div>`;
}
