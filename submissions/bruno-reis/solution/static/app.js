/* ═══════════════════════════════════════════════════════════════
   Ticket Intelligence Dashboard — App Logic
   SPA navigation, Kanban board, detail view, tester
   ═══════════════════════════════════════════════════════════════ */

// ── State ──
let tickets = [];
let selectedId = null;
let currentPage = 'dashboard';
let activeFilter = 'all';
let searchQuery = '';

// ── Action labels & reasons ──
const actionLabels = {
  'Auto-route': 'Auto-rotear',
  'Human review': 'Revisão humana',
  'Escalate': 'Escalar',
};

const actionDescriptions = {
  'Auto-route': 'Confiança alta em categoria não sensível. O ticket pode ser roteado automaticamente para a equipe responsável.',
  'Human review': 'Confiança intermediária ou categoria com risco de confusão. Recomendamos revisão manual antes do roteamento.',
  'Escalate': 'Baixa confiança na classificação. Encaminhar imediatamente para um especialista revisar.',
};

// ── Confidence helpers ──
function confClass(c) {
  if (c >= 0.75) return 'high';
  if (c >= 0.55) return 'mid';
  return 'low';
}

function confColor(c) {
  if (c >= 0.75) return 'var(--accent-green)';
  if (c >= 0.55) return 'var(--accent-amber)';
  return 'var(--accent-red)';
}

function actionCSS(action) {
  if (action === 'Auto-route') return 'auto-route';
  if (action === 'Human review') return 'human-review';
  return 'escalate';
}

// ═══════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════

function navigateTo(page, options = {}) {
  currentPage = page;

  // Update nav items
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === page);
  });

  // Show correct page
  document.querySelectorAll('.page').forEach(p => {
    p.classList.toggle('active', p.id === `page-${page}`);
  });

  // Close mobile sidebar
  document.getElementById('sidebar').classList.remove('open');

  // Page-specific init
  if (page === 'dashboard') renderDashboard();
  if (page === 'kanban') renderKanban();
  if (page === 'detail' && options.ticketId) loadTicketDetail(options.ticketId);
}

// Attach nav clicks
document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
  btn.addEventListener('click', () => navigateTo(btn.dataset.page));
});

// Mobile toggle
document.getElementById('mobile-toggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

// ═══════════════════════════════════════
// DATA LOADING
// ═══════════════════════════════════════

async function loadTickets() {
  try {
    const res = await fetch('/api/tickets');
    tickets = await res.json();
    updateNavBadge();
    renderDashboard();
  } catch {
    console.error('Falha ao carregar tickets');
  }
}

function updateNavBadge() {
  const escalateCount = tickets.filter(t => t.action === 'Escalate').length;
  const badge = document.getElementById('nav-badge-escalate');
  badge.textContent = escalateCount;
  badge.style.display = escalateCount > 0 ? 'inline' : 'none';
}

// ═══════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════

function renderDashboard() {
  const auto = tickets.filter(t => t.action === 'Auto-route').length;
  const review = tickets.filter(t => t.action === 'Human review').length;
  const escalate = tickets.filter(t => t.action === 'Escalate').length;

  animateCount('kpi-total', tickets.length);
  animateCount('kpi-auto', auto);
  animateCount('kpi-review', review);
  animateCount('kpi-escalate', escalate);

  // Category distribution
  const catCounts = {};
  tickets.forEach(t => { catCounts[t.predicted] = (catCounts[t.predicted] || 0) + 1; });
  renderDistBars('chart-categories', catCounts, 'var(--accent-blue)');

  // Action distribution
  const actionCounts = { 'Auto-route': auto, 'Human review': review, 'Escalate': escalate };
  const actionColors = { 'Auto-route': 'var(--accent-green)', 'Human review': 'var(--accent-amber)', 'Escalate': 'var(--accent-red)' };
  renderDistBarsColored('chart-actions', actionCounts, actionColors);
}

function animateCount(elId, target) {
  const el = document.getElementById(elId);
  if (!el) return;
  const current = parseInt(el.textContent) || 0;
  if (current === target) { el.textContent = target; return; }

  const duration = 600;
  const start = performance.now();

  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(current + (target - current) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function renderDistBars(containerId, data, color) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = sorted.length > 0 ? sorted[0][1] : 1;

  container.innerHTML = sorted.map(([label, val]) => `
    <div class="dist-bar-row">
      <div class="dist-bar-label" title="${label}">${label}</div>
      <div class="dist-bar-track">
        <div class="dist-bar-fill" style="width: 0%; background: ${color};" data-width="${(val / max * 100).toFixed(1)}%"></div>
      </div>
      <div class="dist-bar-value">${val}</div>
    </div>
  `).join('');

  // Animate bars
  requestAnimationFrame(() => {
    container.querySelectorAll('.dist-bar-fill').forEach(bar => {
      bar.style.width = bar.dataset.width;
    });
  });
}

function renderDistBarsColored(containerId, data, colors) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = sorted.length > 0 ? sorted[0][1] : 1;

  container.innerHTML = sorted.map(([label, val]) => `
    <div class="dist-bar-row">
      <div class="dist-bar-label" title="${label}">${actionLabels[label] || label}</div>
      <div class="dist-bar-track">
        <div class="dist-bar-fill" style="width: 0%; background: ${colors[label] || 'var(--accent-blue)'};" data-width="${(val / max * 100).toFixed(1)}%"></div>
      </div>
      <div class="dist-bar-value">${val}</div>
    </div>
  `).join('');

  requestAnimationFrame(() => {
    container.querySelectorAll('.dist-bar-fill').forEach(bar => {
      bar.style.width = bar.dataset.width;
    });
  });
}

// ═══════════════════════════════════════
// KANBAN
// ═══════════════════════════════════════

function getFilteredTickets() {
  let filtered = tickets;

  if (activeFilter !== 'all') {
    filtered = filtered.filter(t => t.predicted === activeFilter);
  }

  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    filtered = filtered.filter(t =>
      t.summary.toLowerCase().includes(q) ||
      t.predicted.toLowerCase().includes(q)
    );
  }

  return filtered;
}

function renderKanban() {
  const filtered = getFilteredTickets();

  const columns = [
    { key: 'Escalate', label: 'Escalar', dotClass: 'red', tickets: [] },
    { key: 'Human review', label: 'Revisão Humana', dotClass: 'amber', tickets: [] },
    { key: 'Auto-route', label: 'Auto-rotear', dotClass: 'green', tickets: [] },
  ];

  filtered.forEach(t => {
    const col = columns.find(c => c.key === t.action);
    if (col) col.tickets.push(t);
  });

  // Build filter chips
  const categories = [...new Set(tickets.map(t => t.predicted))].sort();
  const chipsContainer = document.getElementById('filter-chips');
  chipsContainer.innerHTML = `<button class="chip ${activeFilter === 'all' ? 'active' : ''}" data-filter="all">Todos</button>` +
    categories.map(c => `<button class="chip ${activeFilter === c ? 'active' : ''}" data-filter="${c}">${c}</button>`).join('');

  chipsContainer.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      activeFilter = chip.dataset.filter;
      renderKanban();
    });
  });

  // Build columns
  const board = document.getElementById('kanban-board');
  board.innerHTML = columns.map(col => `
    <div class="kanban-column">
      <div class="kanban-col-header">
        <div class="kanban-col-title">
          <div class="col-dot ${col.dotClass}"></div>
          <span>${col.label}</span>
        </div>
        <span class="col-count">${col.tickets.length}</span>
      </div>
      <div class="kanban-cards">
        ${col.tickets.length === 0
          ? '<div class="empty-state"><p>Nenhum ticket nesta coluna.</p></div>'
          : col.tickets.map((t, i) => renderKanbanCard(t, i)).join('')
        }
      </div>
    </div>
  `).join('');

  // Attach card clicks
  board.querySelectorAll('.kanban-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = parseInt(card.dataset.id);
      navigateTo('detail', { ticketId: id });
    });
  });
}

function renderKanbanCard(t, index) {
  const cc = confClass(t.confidence);
  return `
    <div class="kanban-card" data-id="${t.id}" style="animation-delay: ${index * 0.04}s">
      <div class="card-top">
        <span class="card-id">#${t.id}</span>
        ${t.sensitivity ? '<span class="meta-badge sensitive" style="font-size:10px;padding:2px 6px;">🔒 Sensível</span>' : ''}
      </div>
      <div class="card-summary">${t.summary}</div>
      <div class="card-footer">
        <span class="card-category">${t.predicted}</span>
        <div class="confidence-mini">
          <div class="confidence-mini-bar">
            <div class="confidence-mini-fill fill-${cc}" style="width: ${(t.confidence * 100).toFixed(0)}%"></div>
          </div>
          <span class="confidence-mini-text conf-${cc}">${(t.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  `;
}

// Search
const searchInput = document.getElementById('search-input');
if (searchInput) {
  let debounce;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      searchQuery = searchInput.value;
      renderKanban();
    }, 200);
  });
}

// ═══════════════════════════════════════
// DETAIL
// ═══════════════════════════════════════

async function loadTicketDetail(id) {
  selectedId = id;

  document.getElementById('detail-breadcrumb').textContent = `Ticket #${id}`;
  document.getElementById('detail-page-title').textContent = `Ticket #${id}`;

  try {
    const res = await fetch(`/api/tickets/${id}`);
    const data = await res.json();

    if (data.error) {
      document.getElementById('detail-body').textContent = 'Ticket não encontrado.';
      return;
    }

    // Recommendation card
    const recCard = document.getElementById('rec-card');
    recCard.className = `recommendation-card ${actionCSS(data.action)}`;
    document.getElementById('rec-action-text').textContent = actionLabels[data.action] || data.action;
    document.getElementById('rec-reason-text').textContent =
      data.risk_reason || actionDescriptions[data.action] || '';

    // Metadata
    const metaRow = document.getElementById('meta-row');
    metaRow.innerHTML = `
      <span class="meta-badge category">🏷️ ${data.predicted}</span>
      <span class="meta-badge owner">👤 ${data.owner}</span>
      ${data.sensitivity ? '<span class="meta-badge sensitive">🔒 Sensível</span>' : ''}
    `;

    // Confidence
    const confPct = (data.confidence * 100).toFixed(1);
    const cc = confClass(data.confidence);
    document.getElementById('conf-value').textContent = `${confPct}%`;
    document.getElementById('conf-value').className = `confidence-value conf-${cc}`;
    const fill = document.getElementById('conf-fill');
    fill.style.width = '0%';
    fill.className = `confidence-bar-fill fill-${cc}`;
    requestAnimationFrame(() => {
      fill.style.width = `${confPct}%`;
    });

    // Text
    document.getElementById('detail-body').textContent = data.text;

    // Similar
    renderSimilar(data.similar || []);

    // Desc
    document.getElementById('detail-page-desc').textContent =
      `${data.predicted} · Confiança ${confPct}% · ${data.owner}`;

  } catch {
    document.getElementById('detail-body').textContent = 'Erro ao carregar ticket.';
  }
}

function renderSimilar(list) {
  const grid = document.getElementById('similar-grid');
  if (!list.length) {
    grid.innerHTML = '<div class="empty-state"><p>Nenhum similar encontrado.</p></div>';
    return;
  }
  grid.innerHTML = list.map(s => `
    <div class="similar-card">
      <div class="sim-header">
        <span class="sim-label">${s.label}</span>
        <span class="sim-score">${(s.score * 100).toFixed(0)}% similar</span>
      </div>
      <div class="sim-text">${s.text}</div>
    </div>
  `).join('');
}

// Action buttons
document.getElementById('action-buttons').addEventListener('click', async (ev) => {
  const btn = ev.target.closest('.action-btn');
  if (!btn || !selectedId) return;

  const action = btn.dataset.action;
  try {
    await fetch(`/api/tickets/${selectedId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    });
    showToast(`✅ Ação registrada: ${action}`);
    // Reload ticket list
    await loadTickets();
    loadTicketDetail(selectedId);
  } catch {
    showToast('❌ Erro ao registrar ação.');
  }
});

// ═══════════════════════════════════════
// TESTER
// ═══════════════════════════════════════

document.getElementById('tester-run').addEventListener('click', async () => {
  const text = document.getElementById('tester-text').value.trim();
  const resultEl = document.getElementById('tester-result');

  if (!text) {
    showToast('⚠️ Digite o texto do ticket.');
    return;
  }

  resultEl.innerHTML = '<div class="result-placeholder"><div class="spinner"></div><p>Classificando...</p></div>';

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    if (data.error) {
      resultEl.innerHTML = `<div class="result-placeholder"><p>${data.error}</p></div>`;
      return;
    }

    const cc = confClass(data.confidence);
    const confPct = (data.confidence * 100).toFixed(1);

    resultEl.innerHTML = `
      <div class="result-content">
        <div class="recommendation-card ${actionCSS(data.action)}" style="margin-bottom:4px">
          <div class="rec-eyebrow">Ação Recomendada</div>
          <div class="rec-action">${actionLabels[data.action] || data.action}</div>
          <div class="rec-reason">${data.risk_reason || actionDescriptions[data.action] || ''}</div>
        </div>
        <div class="result-row"><div class="result-label">Categoria</div><div class="result-value">${data.predicted}</div></div>
        <div class="result-row"><div class="result-label">Confiança</div><div class="result-value conf-${cc}">${confPct}%</div></div>
        <div class="result-row"><div class="result-label">Owner</div><div class="result-value">${data.owner}</div></div>
        <div class="result-row"><div class="result-label">Recomendação</div><div class="result-value">${data.recommendation}</div></div>
        ${data.similar && data.similar.length > 0 ? `
          <div style="margin-top:8px">
            <div class="result-label" style="margin-bottom:8px">Tickets Similares</div>
            ${data.similar.slice(0, 3).map(s => `
              <div class="similar-card" style="margin-bottom:6px">
                <div class="sim-header">
                  <span class="sim-label">${s.label}</span>
                  <span class="sim-score">${(s.score * 100).toFixed(0)}%</span>
                </div>
                <div class="sim-text">${s.text}</div>
              </div>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `;
  } catch {
    resultEl.innerHTML = '<div class="result-placeholder"><p>Erro ao conectar com o servidor.</p></div>';
  }
});

// ═══════════════════════════════════════
// TOAST
// ═══════════════════════════════════════

function showToast(msg) {
  const container = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = `<span class="toast-icon">ℹ️</span><span>${msg}</span>`;
  container.appendChild(t);
  setTimeout(() => t.remove(), 2500);
}

// ═══════════════════════════════════════
// INIT
// ═══════════════════════════════════════

loadTickets();
