"use strict";

const DATA = window.ENSAIO_DATA;
const STORAGE = "filaCerta.ensaio";
const state = { index: 0, startedAt: 0, results: [] };

const qs = (selector) => document.querySelector(selector);

function esc(text) {
  return String(text).replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]
  ));
}

function readSaved() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE) || "null");
    return Array.isArray(saved) ? saved : null;
  } catch {
    return null;
  }
}

function save() {
  try {
    localStorage.setItem(STORAGE, JSON.stringify(state.results));
  } catch {
    // Private windows can block storage. The trial still works in this visit.
  }
}

function show(id) {
  for (const section of ["intro", "trial", "done"]) qs("#" + section).hidden = section !== id;
}

function begin(saved) {
  state.results = saved || [];
  state.index = state.results.length;
  if (state.index >= DATA.tickets.length) return finish();
  show("trial");
  renderTicket();
}

function renderTicket() {
  if (state.index >= DATA.tickets.length) return finish();
  const ticket = DATA.tickets[state.index];
  qs("#progress").textContent = `Ticket ${state.index + 1} de ${DATA.tickets.length} · ${ticket.arm === "assistido" ? "com sugestão" : "sem sugestão"}`;
  qs("#ticket-text").textContent = ticket.text;
  const suggestion = qs("#suggestion");
  if (ticket.arm === "assistido") {
    suggestion.hidden = false;
    suggestion.innerHTML = `
      <p style="margin:0 0 10px">Sugestão do sistema: <strong>${esc(ticket.predicted)}</strong> · confiança ${Math.round(ticket.confidence * 100)}%${ticket.words.length ? ` · palavras: ${ticket.words.map(esc).join(", ")}` : ""}</p>
      <button id="use-suggestion" class="action-button primary">Usar sugestão (Enter)</button>`;
  } else {
    suggestion.hidden = true;
    suggestion.innerHTML = "";
  }
  qs("#cats").innerHTML = DATA.categories.map((category, index) => (
    `<button class="cat-button action-button" data-cat="${esc(category)}">${index + 1}. ${esc(category)}</button>`
  )).join("");
  state.startedAt = performance.now();
}

function choose(category, usedSuggestion) {
  const ticket = DATA.tickets[state.index];
  state.results.push({
    arm: ticket.arm,
    label: ticket.label,
    chosen: category,
    correct: category === ticket.label,
    predicted: ticket.predicted,
    suggestionUsed: Boolean(usedSuggestion),
    seconds: Math.round(performance.now() - state.startedAt) / 1000,
  });
  save();
  state.index += 1;
  renderTicket();
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return 0;
  return (sorted[(sorted.length - 1) >> 1] + sorted[sorted.length >> 1]) / 2;
}

function armStats(arm) {
  const rows = state.results.filter((row) => row.arm === arm);
  return {
    n: rows.length,
    median: median(rows.map((row) => row.seconds)),
    mean: rows.reduce((sum, row) => sum + row.seconds, 0) / (rows.length || 1),
    accuracy: rows.filter((row) => row.correct).length / (rows.length || 1),
    suggestionUsed: rows.filter((row) => row.suggestionUsed).length,
  };
}

function finish() {
  const manual = armStats("manual");
  const assisted = armStats("assistido");
  const seconds = (value) => value.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " s";
  const percent = (value) => Math.round(value * 100) + "%";
  const payload = { design: DATA.design, finishedAt: new Date().toISOString(), results: state.results };
  qs("#done").innerHTML = `
    <h1>Resultado do ensaio</h1>
    <div class="table-wrap" style="margin:12px 0"><table>
      <thead><tr><th>Braço</th><th>Tickets</th><th>Mediana</th><th>Média</th><th>Acerto</th><th>Usou a sugestão</th></tr></thead>
      <tbody>
        <tr><td>Sem sugestão</td><td>${manual.n}</td><td>${seconds(manual.median)}</td><td>${seconds(manual.mean)}</td><td>${percent(manual.accuracy)}</td><td>—</td></tr>
        <tr><td>Com sugestão</td><td>${assisted.n}</td><td>${seconds(assisted.median)}</td><td>${seconds(assisted.mean)}</td><td>${percent(assisted.accuracy)}</td><td>${assisted.suggestionUsed} de ${assisted.n}</td></tr>
      </tbody>
    </table></div>
    <p>Envie o JSON abaixo ao Claude para atualizar o cenário de ROI e o process log. Lembrete: n = 1, sem feedback durante o ensaio.</p>
    <textarea id="trial-json" class="export" readonly>${esc(JSON.stringify(payload))}</textarea>
    <div class="toolbar" style="margin-top:10px">
      <button id="download" class="action-button primary">Baixar JSON</button>
      <button id="restart" class="action-button">Recomeçar do zero</button>
    </div>`;
  show("done");
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  if (target.id === "start-fresh") {
    try { localStorage.removeItem(STORAGE); } catch { /* see save() */ }
    begin([]);
  } else if (target.id === "resume") {
    begin(readSaved() || []);
  } else if (target.id === "use-suggestion") {
    choose(DATA.tickets[state.index].predicted, true);
  } else if (target.dataset.cat) {
    choose(target.dataset.cat, false);
  } else if (target.id === "download") {
    const blob = new Blob([qs("#trial-json").value], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "ensaio-fila-certa.json";
    link.click();
    URL.revokeObjectURL(link.href);
  } else if (target.id === "restart" && confirm("Apagar as respostas e recomeçar?")) {
    try { localStorage.removeItem(STORAGE); } catch { /* see save() */ }
    begin([]);
  }
});

document.addEventListener("keydown", (event) => {
  if (qs("#trial").hidden) return;
  if (event.key === "Enter") {
    qs("#use-suggestion")?.click();
    return;
  }
  const number = Number(event.key);
  if (number >= 1 && number <= DATA.categories.length) qs("#cats").children[number - 1]?.click();
});

const saved = readSaved();
if (saved && saved.length > 0 && saved.length < DATA.tickets.length) qs("#resume").hidden = false;
if (saved && saved.length >= DATA.tickets.length) {
  state.results = saved;
  finish();
}
