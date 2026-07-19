/* PAUTA — SPA: router por hash, 4 views, gráficos ECharts (tema 'pauta').
   Consome apenas a API (/api/*) — nenhum número é digitado aqui. */
(function () {
  'use strict';

  const { T, MONO, UI, fmt, tooltip, TOOLTIP_BOX, countUp, REDUCED, fitValues } = window.PAUTA;
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  let B = null;                 // payload do /api/bootstrap
  const charts = {};            // ECharts por id
  const inited = {};            // views já inicializadas

  const debounce = (fn, ms) => {
    let t;
    return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  };

  async function fetchJSON(url, opts) {
    const r = await fetch(url, opts);
    if (!r.ok) throw new Error(`${url} → HTTP ${r.status}`);
    return r.json();
  }

  const postJSON = (url, body) => fetchJSON(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });

  const esc = (s) => String(s).replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function makeChart(id) {
    if (charts[id]) return charts[id];
    const c = echarts.init($('#' + id), 'pauta', { renderer: 'canvas' });
    charts[id] = c;
    return c;
  }
  window.addEventListener('resize', debounce(() => {
    Object.values(charts).forEach((c) => c.resize());
  }, 150));

  function toast(msg, tone = 'ok') {
    const el = $('#toast');
    el.textContent = msg;
    el.className = 'toast' + (tone === 'err' ? ' err' : '');
    el.hidden = false;
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.hidden = true; }, tone === 'err' ? 5000 : 2500);
  }

  function manchete({ kicker, tone, value, unit, sub, lead, id }) {
    const inner = id ? `<span id="${id}">${value}</span>` : value;
    return `<div class="manchete${lead ? ' lead' : ''}">
      <div class="m-kicker">${kicker}${tone ? ` <span class="tone-${tone}">●</span>` : ''}</div>
      <div class="m-value">${inner}${unit ? `<span class="m-unit">${unit}</span>` : ''}</div>
      <div class="m-sub">${sub || ''}</div>
    </div>`;
  }

  const TIER_LABEL = {
    automatizar: '<span class="tier-badge tier-auto">automatizar</span>',
    parcial: '<span class="tier-badge tier-partial">parcial</span>',
    nao_automatizar: '<span class="tier-badge tier-never">não automatizar</span>',
  };
  const STATUS_PILL = {
    'Open': '<span class="status-pill st-open">Open</span>',
    'Pending Customer Response': '<span class="status-pill st-pending">Pending</span>',
    'Closed': '<span class="status-pill st-closed">Closed</span>',
  };

  /* ======================= VISÃO EXECUTIVA ======================= */

  function initExecutivo() {
    const k = B.kpis, s = B.base_scenario;

    $('#ex-manchetes').innerHTML = [
      manchete({
        kicker: 'Volume anual', value: fmt.int(k.tickets_year),
        sub: `premissa do brief<span class="fn" tabindex="0" data-note="O brief declara ~30.000 tickets/ano; o dataset é uma amostra de ${fmt.int(k.sample_size)}. Fator de anualização 3,542 aplicado a toda conversão de volume (D-001)."> ¹</span> · amostra ${fmt.int(k.sample_size)}`,
      }),
      manchete({
        kicker: 'Sem 1ª resposta', tone: 'crit', value: fmt.pct1(k.pct_open),
        sub: 'tickets Open no snapshot — gargalo nº 1',
        id: 'ex-v-open',
      }),
      manchete({
        kicker: 'Satisfação (Closed)', tone: 'warn',
        value: fmt.d2(k.satisfaction), unit: '/5',
        sub: `n=${fmt.int(k.n_rated)} avaliados · ${fmt.pct1(k.pct_detractors)} detratores`,
      }),
      manchete({
        kicker: 'Custo anual estimado', value: fmt.mil(s.cost_year_brl),
        sub: `${fmt.int(s.hours_year)} h · ${fmt.d1(s.fte)} FTE — premissas declaradas<span class="fn" tabindex="0" data-note="Horas = Σ volume anual por tipo × esforço por ticket (AHT por canal × multiplicadores — FASE 2 §3). Custo = horas × R$ 40/h carregado. Os tempos do dataset são sintéticos (D-005): nada aqui é medição."> ²</span>`,
      }),
      manchete({
        kicker: 'Economia potencial', tone: 'good', lead: true,
        value: fmt.mil(s.gross_savings_brl), unit: '/ano',
        sub: `${fmt.int(s.hours_saved)} h · ${fmt.d1(s.fte_saved)} FTE liberados — cenário base<span class="fn" tabindex="0" data-note="Horas de agente liberadas (deflexão + assistência) × custo/hora carregado. Construção interna pelo time de AI — sem investimento de implantação (D-019); descontando o custo de rodar a IA (tokens/plataforma, ~R$ 1/ticket), a economia líquida é ${fmt.mil(s.net_savings_steady_brl)}/ano."> ³</span>`,
      }),
    ].join('');

    // funil editorial
    const total = B.funnel.reduce((a, f) => a + f.n, 0);
    const toneVar = { crit: 'var(--critical)', warn: 'var(--warn)', good: 'var(--good)' };
    $('#ex-funnel').innerHTML = B.funnel.map((f) => {
      const pct = (f.n / total) * 100;
      return `<div class="funnel-row">
        <div class="funnel-head">
          <span class="funnel-label">${f.stage}</span>
          <span class="funnel-nums"><strong>${fmt.int(f.n)}</strong> · ${fmt.pct1(pct)}</span>
        </div>
        <div class="funnel-track"><div class="funnel-fill" data-w="${pct * 2.6}"
             style="background:${toneVar[f.tone]}"></div></div>
        ${f.lever ? `<div class="funnel-lever">alavanca → <em>${f.lever}</em></div>` : ''}
      </div>`;
    }).join('');
    requestAnimationFrame(() =>
      $$('#ex-funnel .funnel-fill').forEach((el) => { el.style.width = el.dataset.w + '%'; }));

    // satisfação por segmento
    $('#ex-sat-mean').textContent = fmt.d2(k.satisfaction) + '/5';
    $('#ex-sat-detr').textContent = fmt.pct1(k.pct_detractors);
    const satChart = makeChart('ex-sat-chart');
    function renderSat(seg) {
      const rows = B.satisfaction_by[seg];
      satChart.setOption({
        grid: { left: 34, right: 8, top: 18, bottom: 26 },
        xAxis: { type: 'category', data: rows.map((r) => r.label) },
        yAxis: { min: 1, max: 5, interval: 1 },
        tooltip: {
          ...TOOLTIP_BOX, trigger: 'item',
          formatter: (p) => {
            const r = rows[p.dataIndex];
            return tooltip(r.label, [
              ['média', fmt.d2(r.mean) + '/5', T.series[0]],
              ['IC 95%', '± ' + fmt.d2(r.ci95)],
              ['avaliados', fmt.int(r.n)],
            ]);
          },
        },
        series: [
          {
            type: 'bar', data: rows.map((r) => r.mean),
            itemStyle: { color: T.series[0], borderRadius: [3, 3, 0, 0] },
            barMaxWidth: 34,
            label: {
              show: true, position: 'top', distance: 14, fontFamily: MONO,
              fontSize: 11, color: T.ink2, formatter: (p) => fmt.d2(p.value),
            },
            markLine: {
              silent: true, symbol: 'none',
              lineStyle: { color: T.ink3, type: [4, 4] },
              label: { show: false },
              data: [{ yAxis: k.satisfaction }],
            },
          },
          {
            type: 'custom', z: 3,
            renderItem: (params, api) => {
              const x = api.coord([api.value(0), 0])[0];
              const yLo = api.coord([0, api.value(1)])[1];
              const yHi = api.coord([0, api.value(2)])[1];
              const st = { stroke: T.ink2, lineWidth: 1.2 };
              return {
                type: 'group', children: [
                  { type: 'line', shape: { x1: x, y1: yLo, x2: x, y2: yHi }, style: st },
                  { type: 'line', shape: { x1: x - 4, y1: yLo, x2: x + 4, y2: yLo }, style: st },
                  { type: 'line', shape: { x1: x - 4, y1: yHi, x2: x + 4, y2: yHi }, style: st },
                ],
              };
            },
            data: rows.map((r, i) => [i, r.mean - r.ci95, r.mean + r.ci95]),
            silent: true,
          },
        ],
      }, true);
    }
    renderSat('Ticket Channel');
    $$('#ex-sat-tabs button').forEach((b) =>
      b.addEventListener('click', () => {
        $$('#ex-sat-tabs button').forEach((x) => x.setAttribute('aria-selected', x === b));
        renderSat(b.dataset.seg);
      }));

    // cenários de economia (performance da automação — D-019)
    const tones = { conservador: T.ink2, base: T.copper, otimista: T.good };
    const capById = { conservador: 'deflexão e assistência no pessimista',
                      base: 'premissas base da matriz FASE 4',
                      otimista: 'deflexão e assistência no otimista' };
    $('#ex-scenarios').innerHTML = ['conservador', 'base', 'otimista'].map((name) => {
      const r = B.savings_scenarios[name];
      return `<div class="scenario${name === 'base' ? ' lead' : ''}">
        <div class="s-name" style="color:${tones[name]}">${name}</div>
        <div class="s-big">${fmt.mil(r.gross_savings_brl)}<span class="m-unit">/ano</span></div>
        <div class="s-cap">${capById[name]}</div>
        <div class="s-row"><span>Horas liberadas/ano</span><span>${fmt.int(r.hours_saved)} h</span></div>
        <div class="s-row"><span>FTE equivalentes</span><span>${fmt.d1(r.fte_saved)}</span></div>
        <div class="s-row"><span>Líquido de tokens/plataforma</span><span>${fmt.mil(r.net_savings_steady_brl)}</span></div>
      </div>`;
    }).join('');
    fitValues('[data-view="executivo"]');
  }

  /* ======================= MESA DE OPERAÇÕES ======================= */

  const opState = { channel: new Set(), type: new Set(), priority: new Set(), status: new Set() };

  function initOperacao() {
    // chips de filtro
    Object.entries(B.filters).forEach(([dim, values]) => {
      const group = $(`#op-filters .filter-group[data-dim="${dim}"]`);
      values.forEach((v) => {
        const btn = document.createElement('button');
        btn.className = 'chip';
        btn.textContent = v === 'Pending Customer Response' ? 'Pending' : v;
        btn.setAttribute('aria-pressed', 'false');
        btn.addEventListener('click', () => {
          const on = opState[dim].has(v);
          on ? opState[dim].delete(v) : opState[dim].add(v);
          btn.setAttribute('aria-pressed', String(!on));
          refreshOp();
        });
        btn.dataset.value = v;
        group.appendChild(btn);
      });
    });
    $('#op-clear').addEventListener('click', () => {
      Object.values(opState).forEach((s) => s.clear());
      $$('#op-filters .chip').forEach((c) => c.setAttribute('aria-pressed', 'false'));
      refreshOp();
    });
    loadOp();
  }

  const refreshOp = debounce(loadOp, 250);

  async function loadOp() {
    const qs = new URLSearchParams();
    Object.entries(opState).forEach(([dim, set]) => set.forEach((v) => qs.append(dim, v)));
    let d;
    try {
      d = await fetchJSON('/api/operational?' + qs.toString());
    } catch (e) {
      toast('Não foi possível atualizar o recorte — os números exibidos são os anteriores.', 'err');
      return;
    }

    const anyFilter = Object.values(opState).some((s) => s.size);
    $('#op-clear').hidden = !anyFilter;
    $('#op-count').textContent = `${fmt.int(d.n)} tickets no recorte`;

    $('#op-kpis').innerHTML = [
      manchete({
        kicker: 'Tickets no recorte', value: fmt.int(d.n),
        sub: `${fmt.pct0((d.n / d.n_total) * 100)} da amostra`,
      }),
      manchete({
        kicker: 'Backlog (Open + Pending)',
        tone: d.pct_backlog > 50 ? 'crit' : null,
        value: d.pct_backlog == null ? '—' : fmt.pct1(d.pct_backlog),
        sub: 'não resolvido no snapshot',
      }),
      manchete({
        kicker: 'Satisfação (Closed)',
        value: d.satisfaction == null ? '—' : fmt.d2(d.satisfaction),
        unit: d.satisfaction == null ? '' : '/5',
        sub: `n=${fmt.int(d.n_rated)} avaliados`,
      }),
      manchete({
        kicker: 'Horas/ano estimadas', value: fmt.int(d.hours_year), unit: 'h',
        sub: `premissa de esforço — FASE 2 §3<span class="fn" tabindex="0" data-note="Volume anualizado do recorte × AHT por canal × multiplicadores de tipo/prioridade. É conversão contábil de premissas declaradas, não medição (os tempos do dataset são sintéticos — D-005)."> ¹</span>`,
      }),
    ].join('');

    // volume por tipo — série única (cobre), rótulos diretos
    makeChart('op-vol-chart').setOption({
      grid: { left: 44, right: 8, top: 24, bottom: 26 },
      xAxis: {
        type: 'category',
        data: d.volume_by_type.map((r) => r.label.replace(' request', '').replace(' inquiry', '')),
        axisLabel: { interval: 0 },
      },
      yAxis: { type: 'value', axisLabel: { formatter: (v) => fmt.int(v) } },
      tooltip: {
        ...TOOLTIP_BOX, trigger: 'item',
        formatter: (p) => tooltip(d.volume_by_type[p.dataIndex].label,
          [['tickets na amostra', fmt.int(p.value), T.series[0]]]),
      },
      animationDurationUpdate: 400,
      series: [{
        type: 'bar', data: d.volume_by_type.map((r) => r.n),
        itemStyle: { color: T.series[0], borderRadius: [3, 3, 0, 0] }, barMaxWidth: 34,
        label: { show: true, position: 'top', fontFamily: MONO, fontSize: 11, color: T.ink2, formatter: (p) => fmt.int(p.value) },
      }],
    }, true);

    // backlog por canal — estados (semânticas), % empilhado
    makeChart('op-backlog-chart').setOption({
      grid: { left: 40, right: 8, top: 24, bottom: 26 },
      xAxis: { type: 'category', data: d.backlog_by_channel.map((r) => r.label) },
      yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      tooltip: {
        ...TOOLTIP_BOX, trigger: 'axis', axisPointer: { type: 'none' },
        formatter: (ps) => tooltip(ps[0].name, ps.map((p) => [
          p.seriesName, fmt.pct1(p.value), p.color,
        ])),
      },
      animationDurationUpdate: 400,
      series: [
        {
          name: 'Open — sem 1ª resposta', type: 'bar', stack: 's',
          data: d.backlog_by_channel.map((r) => r.open),
          itemStyle: { color: T.critical, borderRadius: [0, 0, 3, 3] }, barMaxWidth: 34,
        },
        {
          name: 'Pending — esperando cliente', type: 'bar', stack: 's',
          data: d.backlog_by_channel.map((r) => r.pending),
          itemStyle: { color: T.warn, borderRadius: [3, 3, 0, 0] }, barMaxWidth: 34,
        },
      ],
    }, true);

    // oportunidades de automação
    const maxDefl = Math.max(1, ...d.automation_table.map((r) => r.deflectable_hours));
    $('#op-auto-table tbody').innerHTML = d.automation_table
      .slice()
      .sort((a, b) => b.deflectable_hours - a.deflectable_hours)
      .map((r) => `<tr>
        <td style="color:var(--ink-1);font-weight:500">${r.type}</td>
        <td>${TIER_LABEL[r.tier]}</td>
        <td class="num">${fmt.int(r.tickets_year)}</td>
        <td class="num">${fmt.int(r.hours_year)}</td>
        <td><span class="inline-bar"><span style="width:${r.deflection_base * 100}%"></span></span><span class="mono" style="font-size:12px">${fmt.pct0(r.deflection_base * 100)}</span></td>
        <td class="num" style="color:var(--ink-1)">${fmt.int(r.deflectable_hours)}</td>
        <td class="num" style="color:var(--copper-bright)">${fmt.mil(r.deflectable_brl)}</td>
      </tr>`).join('') ||
      '<tr><td colspan="7" style="text-align:center;color:var(--ink-3);padding:24px">Nenhum ticket no recorte — ajuste os filtros.</td></tr>';

    // amostra de tickets
    $('#op-tickets-table tbody').innerHTML = d.tickets.map((t) => `<tr>
        <td class="num">${t.id}</td>
        <td>${t.type}</td><td>${t.channel}</td><td>${t.priority}</td>
        <td>${STATUS_PILL[t.status] || t.status}</td>
        <td style="max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${t.subject}</td>
        <td class="num">${t.satisfaction == null ? '—' : t.satisfaction}</td>
      </tr>`).join('') ||
      '<tr><td colspan="7" style="text-align:center;color:var(--ink-3);padding:24px">Nenhum ticket no recorte.</td></tr>';
    $('#op-sample-note').innerHTML =
      `Exibindo ${fmt.int(Math.min(200, d.n))} de ${fmt.int(d.n)} tickets do recorte. ` +
      'As descrições do Dataset 1 são texto sintético de template — servem à demonstração, nunca a treino (FASE 1 §1.5).';
    fitValues('[data-view="operacao"]');
  }

  /* ======================= COPILOT ======================= */

  function initCopilot() {
    const mc = B.model_card;
    const sv = mc.serving || {};
    $('#cp-model-metrics').textContent = sv.multilingual
      ? `Embeddings multilíngues (MiniLM-L12) + LogReg · F1 macro ${(sv.f1_macro || 0).toFixed(3).replace('.', ',')} ` +
        `(teste em inglês) · gate ${(sv.threshold || 0.5).toFixed(2).replace('.', ',')} · ` +
        `corpus ${fmt.int(mc.corpus_size)} tickets reais · entende pt-BR`
      : `TF-IDF + Regressão Logística · F1 macro ${mc.f1_macro.toFixed(3).replace('.', ',')} · ` +
        `gate ${mc.threshold.toFixed(2).replace('.', ',')} · corpus ${fmt.int(mc.corpus_size)} tickets reais`;

    // chips de exemplo
    $('#cp-examples').innerHTML = '';
    B.copilot_examples.forEach((ex) => {
      const b = document.createElement('button');
      b.className = 'chip';
      b.textContent = ex.label;
      b.addEventListener('click', () => {
        $('#cp-text').value = ex.text;
        $('#cp-text').focus();
      });
      $('#cp-examples').appendChild(b);
    });

    // status do modelo
    async function pollHealth() {
      try {
        const h = await fetchJSON('/api/health');
        if (h.ready) {
          $('#cp-status').innerHTML = '<span class="pulse"></span> modelos prontos';
          return;
        }
      } catch (e) { /* servidor reiniciando — segue tentando */ }
      setTimeout(pollHealth, 2000);
    }
    pollHealth();

    $('#cp-run').addEventListener('click', runCopilot);
  }

  async function runCopilot() {
    const text = $('#cp-text').value.trim();
    if (!text) { $('#cp-text').focus(); return; }
    const btn = $('#cp-run');
    btn.disabled = true;

    $('#cp-empty').hidden = true;
    $('#cp-results').hidden = true;
    const loading = $('#cp-loading');
    loading.hidden = false;
    const steps = $$('.pipe-step', loading);
    steps.forEach((s) => s.classList.remove('active', 'done'));

    // pipeline honesto: etapas avançam com o tempo, a última só fecha com a resposta
    let step = 0;
    steps[0].classList.add('active');
    const stepTimer = setInterval(() => {
      if (step < steps.length - 1) {
        steps[step].classList.remove('active');
        steps[step].classList.add('done');
        step += 1;
        steps[step].classList.add('active');
      }
    }, REDUCED ? 60 : 550);

    try {
      let d = await fetchJSON('/api/copilot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      while (d.warming) {
        steps[1].querySelector('.pipe-dot').nextSibling.textContent =
          'Consultando o arquivo — aquecendo modelos (primeira análise)…';
        await new Promise((r) => setTimeout(r, 2500));
        d = await fetchJSON('/api/copilot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        });
      }
      clearInterval(stepTimer);
      steps.forEach((s) => { s.classList.remove('active'); s.classList.add('done'); });
      setTimeout(() => {
        loading.hidden = true;
        renderCopilot(d);
      }, REDUCED ? 0 : 350);
    } catch (e) {
      clearInterval(stepTimer);
      loading.hidden = true;
      $('#cp-empty').hidden = false;
      toast('Falha ao analisar — o servidor está de pé?');
    } finally {
      btn.disabled = false;
    }
  }

  function renderCopilot(d) {
    const res = $('#cp-results');
    res.hidden = false;
    $$('.cascade', res).forEach((el, i) => {
      el.style.animation = 'none';
      void el.offsetWidth; // reinicia a animação
      el.style.animation = '';
      el.style.animationDelay = (i * 90) + 'ms';
    });

    const cls = d.classification;
    $('#cp-category').textContent = cls.label;
    $('#cp-team').textContent = `redação sugerida: ${d.routing.team} · prioridade ${d.priority.priority} (${d.priority.reason} — heurística demo)`;

    const stamp = $('#cp-stamp');
    let st;
    if (d.vetoes.length) st = ['VETADO', 'stamp-crit'];
    else if (!cls.auto_ok) st = ['REVISÃO HUMANA', 'stamp-warn'];
    else if (d.routing.tier === 'automatizar') st = ['PUBLICAR', 'stamp-good'];
    else if (d.routing.tier === 'parcial') st = ['EDIÇÃO ASSISTIDA', 'stamp-sage'];
    else st = ['SÓ TRIAGEM', 'stamp-warn'];
    stamp.textContent = st[0];
    stamp.className = 'stamp ' + st[1];
    stamp.style.animation = 'none';
    void stamp.offsetWidth;
    stamp.style.animation = '';

    $('#cp-conf-gate').style.left = (d.threshold * 100) + '%';
    $('#cp-conf-fill').style.width = '0%';
    requestAnimationFrame(() =>
      requestAnimationFrame(() => { $('#cp-conf-fill').style.width = (cls.confidence * 100) + '%'; }));
    $('#cp-conf-val').textContent = fmt.pct0(cls.confidence * 100) +
      (!cls.conf_ok ? ' · abaixo do gate → humano'
        : !cls.evidence_ok ? ' · sem evidência no arquivo → humano'
          : ' · acima do gate');
    $('#cp-top3').textContent = 'alternativas: ' + cls.top3
      .map(([l, p]) => `${l} ${fmt.pct0(p * 100)}`).join(' · ') +
      ` — evidência da busca: ${String((cls.evidence ?? 0).toFixed(2)).replace('.', ',')}` +
      ` (piso 0,55)`;

    const reco = $('#cp-reco');
    const tone = d.vetoes.length ? 'reco-crit' : (!cls.auto_ok || d.routing.tier === 'nao_automatizar') ? 'reco-warn' : '';
    reco.className = 'cp-reco cascade ' + tone;
    reco.innerHTML = `<div class="reco-head">${d.recommendation}</div>
      <div class="reco-note">racional da classe (${cls.label}): ${d.routing.nota}.</div>`;

    $('#cp-vetoes').innerHTML = d.vetoes.map((v) => `<div class="veto">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4z"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="15.5" r=".5" fill="currentColor"/></svg>
        <div><div class="v-rule">${v.regra}</div>
        <div>${v.motivo}.</div>
        <div class="v-action">ação → ${v.acao}</div></div>
      </div>`).join('');

    $('#cp-similar').innerHTML = d.similar.map((s) => `<div class="clip">
        <div class="c-meta"><span class="c-sim">${String(s.similarity.toFixed(2)).replace('.', ',')}</span><span>${s.topic}</span><span>#${s.doc_id}</span></div>
        <div class="c-text">${s.text.slice(0, 190)}${s.text.length > 190 ? '…' : ''}</div>
      </div>`).join('');

    // rascunho — máquina de escrever sobre o texto puro, depois HTML formatado
    const raw = d.suggested_response;
    const [main, foot] = raw.split(/\n\n_(?=Baseado)/);
    const plainMain = main.replace(/\*\*/g, '');
    const html = main
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>') +
      (foot ? `<br><br><span class="draft-foot">${foot.replace(/_$/, '')}</span>` : '');
    const box = $('#cp-draft');
    box._plain = plainMain + (foot ? '\n\n' + foot.replace(/_$/, '') : '');
    if (REDUCED) { box.innerHTML = html; }
    else {
      box.innerHTML = '';
      const speed = Math.min(9, 3200 / plainMain.length);
      let i = 0;
      clearInterval(box._t);
      box._t = setInterval(() => {
        i += 1 + Math.floor(Math.random() * 2);
        if (i >= plainMain.length) {
          clearInterval(box._t);
          box.innerHTML = html;
        } else {
          box.textContent = plainMain.slice(0, i);
          box.insertAdjacentHTML('beforeend', '<span class="caret"></span>');
        }
      }, speed);
    }
    $('#cp-copy').onclick = () => {
      navigator.clipboard.writeText(box._plain).then(() => toast('Rascunho copiado.'));
    };
  }

  /* ======================= PROJEÇÃO DE ROI ======================= */

  const roiCtrls = [
    { key: 'tickets_year', label: 'Volume de tickets/ano', min: 10000, max: 60000, step: 1000,
      fmt: (v) => fmt.int(v) },
    { key: 'agent_cost_hour', label: 'Custo por hora do agente', min: 20, max: 80, step: 5,
      fmt: (v) => 'R$ ' + fmt.int(v) + '/h' },
    { key: 'deflection_scale', label: 'Deflexão vs matriz FASE 4', min: 0, max: 150, step: 5,
      fmt: (v) => fmt.int(v) + '% da base', scale: 100 },
    { key: 'assist_reduction', label: 'Redução de AHT por assistência', min: 0, max: 40, step: 5,
      fmt: (v) => fmt.int(v) + '%', scale: 100 },
    { key: 'ramp_up_year1', label: 'Ramp-up no ano 1', min: 30, max: 100, step: 5,
      fmt: (v) => fmt.int(v) + '%', scale: 100 },
    { key: 'run_cost_per_ticket', label: 'Custo por ticket (run)', min: 0.25, max: 4, step: 0.25,
      fmt: (v) => 'R$ ' + fmt.d2(v) },
  ];
  const roiState = {};

  function initRoi() {
    const dft = B.roi_defaults;
    const defaults = {
      tickets_year: dft.tickets_year,
      agent_cost_hour: dft.agent_cost_hour,
      deflection_scale: 100,
      assist_reduction: dft.assist_reduction * 100,
      ramp_up_year1: dft.ramp_up_year1 * 100,
      run_cost_per_ticket: dft.run_cost_per_ticket,
    };
    roiCtrls.forEach((c) => {
      roiState[c.key] = defaults[c.key];
      const host = $(`.ctrl[data-ctrl="${c.key}"]`);
      host.innerHTML = `<div class="ctrl-head">
          <label class="ctrl-label" for="r-${c.key}">${c.label}</label>
          <span class="ctrl-value" id="rv-${c.key}">${c.fmt(defaults[c.key])}</span>
        </div>
        <input type="range" id="r-${c.key}" min="${c.min}" max="${c.max}" step="${c.step}" value="${defaults[c.key]}">`;
      const input = $(`#r-${c.key}`);
      const setFill = () => {
        const p = ((input.value - c.min) / (c.max - c.min)) * 100;
        input.style.setProperty('--fill', p + '%');
      };
      setFill();
      input.addEventListener('input', () => {
        roiState[c.key] = parseFloat(input.value);
        $(`#rv-${c.key}`).textContent = c.fmt(roiState[c.key]);
        setFill();
        refreshRoi();
      });
    });
    loadRoi();
  }

  const refreshRoi = debounce(loadRoi, 150);

  async function loadRoi() {
    let d;
    try {
      d = await fetchJSON('/api/roi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tickets_year: roiState.tickets_year,
          agent_cost_hour: roiState.agent_cost_hour,
          deflection_scale: roiState.deflection_scale / 100,
          assist_reduction: roiState.assist_reduction / 100,
          ramp_up_year1: roiState.ramp_up_year1 / 100,
          run_cost_per_ticket: roiState.run_cost_per_ticket,
        }),
      });
    } catch (e) {
      toast('Não foi possível recalcular — os números exibidos são os anteriores.', 'err');
      return;
    }

    const kpis = $('#roi-kpis');
    if (!kpis.dataset.built) {
      kpis.dataset.built = '1';
      kpis.innerHTML = [
        manchete({ kicker: 'Horas economizadas/ano', value: '0', unit: 'h', id: 'roi-v-hours', sub: '<span id="roi-s-hours">—</span>' }),
        manchete({ kicker: 'FTE liberados', value: '0', id: 'roi-v-fte', sub: 'capacidade — captura exige realocação<span class="fn" tabindex="0" data-note="Liberar horas não corta custo automaticamente: a captura exige decisão de realocação. Recomendação do diagnóstico: apontar a capacidade liberada para os 33,3% de tickets sem primeira resposta."> ¹</span>' }),
        manchete({ kicker: 'Economia líquida em regime', value: '—', id: 'roi-v-net', sub: 'ano 2+ · após custo recorrente' }),
        manchete({ kicker: 'Payback', value: '—', id: 'roi-v-pay', sub: '<span id="roi-s-roi">—</span>' }),
      ].join('');
    }
    countUp($('#roi-v-hours'), d.hours_saved, (v) => fmt.int(v), 250);
    $('#roi-s-hours').textContent = fmt.pct0((d.hours_saved / d.hours_year) * 100) + ' da carga total em regime';
    countUp($('#roi-v-fte'), d.fte_saved, (v) => fmt.d1(v), 250);
    const net = $('#roi-v-net');
    countUp(net, d.net_savings_steady_brl, (v) => fmt.mil(v), 250);
    net.style.color = d.net_savings_steady_brl >= 0 ? '' : T.critical;
    const pay = $('#roi-v-pay');
    pay.innerHTML = d.payback_months == null
      ? 'nunca'
      : d.payback_months === 0
        ? 'imediato'
        : `${fmt.d1(d.payback_months)}<span class="m-unit"> meses</span>`;
    pay.style.color = d.payback_months != null && d.payback_months <= 24 ? '' : T.critical;
    $('#roi-s-roi').textContent = `ROI ano 1: ${fmt.pct0(d.roi_year1 * 100)} · ano 1 líquido: ${fmt.mil(d.net_savings_year1_brl)}`;

    // gráfico economia × custo
    makeChart('roi-chart').setOption({
      grid: { left: 60, right: 16, top: 24, bottom: 26 },
      xAxis: { type: 'category', data: ['Ano 1', 'Regime (ano 2+)'] },
      yAxis: { type: 'value', axisLabel: { formatter: (v) => fmt.int(v / 1000) + 'k' } },
      tooltip: {
        ...TOOLTIP_BOX, trigger: 'axis', axisPointer: { type: 'none' },
        formatter: (ps) => tooltip(ps[0].name, ps.map((p) => [
          p.seriesName, fmt.money(p.value), p.seriesType === 'scatter' ? T.ink1 : p.color,
        ])),
      },
      animationDurationUpdate: 400,
      series: [
        {
          name: 'Economia bruta', type: 'bar',
          data: [d.savings_year1_brl, d.gross_savings_brl],
          itemStyle: { color: T.copper, borderRadius: [3, 3, 0, 0] }, barMaxWidth: 44,
        },
        {
          name: 'Custo da solução', type: 'bar',
          data: [d.solution_cost_year1_brl, d.run_cost_year_brl],
          itemStyle: { color: T.ink3, borderRadius: [3, 3, 0, 0] }, barMaxWidth: 44,
        },
        {
          name: 'Líquido', type: 'scatter', symbol: 'diamond', symbolSize: 13,
          data: [d.net_savings_year1_brl, d.net_savings_steady_brl],
          itemStyle: { color: T.ink1 },
          label: {
            show: true, position: 'right', distance: 10, fontFamily: MONO,
            fontSize: 11.5, color: T.ink1, formatter: (p) => fmt.mil(p.value),
          },
          z: 5,
        },
      ],
    });

    renderTornado();
    renderPremises(d);
    setTimeout(() => fitValues('[data-view="roi"]'), 340);
  }

  let tornadoDone = false;
  function renderTornado() {
    if (tornadoDone) return;
    tornadoDone = true;
    const rows = B.tornado.slice().reverse(); // maior amplitude no topo
    const base = rows[0] ? rows[0].net_base : 0;
    makeChart('roi-tornado').setOption({
      grid: { left: 200, right: 30, top: 8, bottom: 26 },
      xAxis: {
        type: 'value',
        axisLabel: { formatter: (v) => fmt.int(v / 1000) + 'k' },
      },
      yAxis: {
        type: 'category',
        data: rows.map((r) => r.premissa),
        axisLabel: { fontFamily: UI, fontSize: 12, color: T.ink2 },
      },
      tooltip: {
        ...TOOLTIP_BOX, trigger: 'item',
        formatter: (p) => {
          const r = rows[p.dataIndex];
          return tooltip(r.premissa, [
            ['premissa no low', fmt.money(r.net_low)],
            ['premissa no high', fmt.money(r.net_high)],
            ['amplitude', fmt.money(r.amplitude), T.copper],
          ]);
        },
      },
      series: [
        { // deslocamento invisível até o menor valor
          type: 'bar', stack: 't', silent: true,
          itemStyle: { color: 'transparent' },
          data: rows.map((r) => Math.min(r.net_low, r.net_high)),
        },
        {
          type: 'bar', stack: 't', barMaxWidth: 16,
          itemStyle: { color: T.copper, opacity: 0.75, borderRadius: 3 },
          data: rows.map((r) => Math.abs(r.net_high - r.net_low)),
        },
      ],
      // linha do cenário base
      graphic: [],
    });
    const ch = charts['roi-tornado'];
    ch.setOption({
      series: [{}, {
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: T.ink3, type: [4, 4] },
          label: {
            fontFamily: MONO, fontSize: 10, color: T.ink3,
            formatter: 'base ' + fmt.mil(base), position: 'end',
          },
          data: [{ xAxis: base }],
        },
      }],
    });
  }

  function renderPremises(d) {
    const dft = B.roi_defaults;
    $('#roi-premises').innerHTML = `
      <p><strong>Deflexão aplicada por tipo</strong> (matriz FASE 4 × escala do controle):<br>
      <span class="mono">${Object.entries(d.deflection_applied)
        .map(([t, v]) => `${t} ${fmt.pct0(v * 100)}`).join(' · ')}</span></p>
      <p style="margin-top:10px"><strong>AHT por canal</strong> (premissa FASE 2 §3, minutos de agente):<br>
      <span class="mono">${Object.entries(dft.aht_by_channel)
        .map(([c, v]) => `${c} ${fmt.int(v)} min`).join(' · ')}</span></p>
      <p style="margin-top:10px"><strong>Fórmulas</strong> —
      horas = Σ volume×AHT/60 · economia = (h defletidas + h assistidas)×R$/h ·
      ROI ano 1 = (economia×ramp − custo ano 1)/custo ano 1 ·
      payback = imediato quando o líquido do ano 1 é positivo; caso contrário, nunca.</p>
      <p style="margin-top:10px"><strong>Implantação incremental fixa em R$ 0</strong> — construção
      interna pelo próprio AI Master (premissa canônica desta proposta, D-019). O break-even do
      ano 1 só com deflexão é ${fmt.pct1(B.break_even_deflection * 100)} uniforme, já considerando
      o custo recorrente de operação. Modelo completo e testado:
      <code>src/roi_model.py</code> · limitações: <code>docs/diagnostic_report.md §3.5</code>.</p>`;
  }

  /* ======================= PORTAL (CLIENTE) ======================= */

  const PT_EXAMPLES = [
    'Não consigo acessar minha conta depois de redefinir a senha — continua dando credenciais inválidas.',
    'Estou sem espaço no drive compartilhado, preciso de mais cota para salvar os arquivos do projeto.',
    'Meu monitor não liga mais, já testei o cabo e a tomada.',
    'Cobrança não autorizada apareceu de novo, é a terceira vez. Se não resolverem hoje vou procurar meu advogado.',
  ];
  let ptState = null;

  function initPortal() {
    const ex = $('#pt-examples');
    PT_EXAMPLES.forEach((t) => {
      const b = document.createElement('button');
      b.className = 'chip-row';
      b.textContent = t;
      b.addEventListener('click', () => { $('#pt-text').value = t; $('#pt-text').focus(); });
      ex.appendChild(b);
    });
    $('#pt-run').addEventListener('click', portalAsk);
    $('#pt-ticket-back').addEventListener('click', () => {
      $('#pt-ticket-form').hidden = true;
      $('#pt-answer').hidden = false;
    });
    $('#pt-ticket-send').addEventListener('click', portalTicket);
  }

  async function portalAsk() {
    const text = $('#pt-text').value.trim();
    if (!text) { $('#pt-text').focus(); return; }
    const btn = $('#pt-run');
    btn.disabled = true;
    ['pt-empty', 'pt-answer', 'pt-ticket-form', 'pt-success'].forEach((id) => { $('#' + id).hidden = true; });
    const loading = $('#pt-loading');
    loading.hidden = false;
    const steps = $$('.pipe-step', loading);
    steps.forEach((s) => s.classList.remove('active', 'done'));
    let step = 0;
    steps[0].classList.add('active');
    const timer = setInterval(() => {
      if (step < steps.length - 1) {
        steps[step].classList.replace('active', 'done');
        step += 1;
        steps[step].classList.add('active');
      }
    }, REDUCED ? 60 : 500);
    try {
      let d = await postJSON('/api/portal/ask', { text });
      while (d.warming) {
        await new Promise((r) => setTimeout(r, 2500));
        d = await postJSON('/api/portal/ask', { text });
      }
      clearInterval(timer);
      steps.forEach((s) => { s.classList.remove('active'); s.classList.add('done'); });
      setTimeout(() => { loading.hidden = true; renderPortalAnswer(d); }, REDUCED ? 0 : 300);
    } catch (e) {
      clearInterval(timer);
      loading.hidden = true;
      $('#pt-empty').hidden = false;
      toast('Não foi possível analisar agora — tente novamente.', 'err');
    } finally {
      btn.disabled = false;
    }
  }

  function renderPortalAnswer(d) {
    ptState = d;
    const box = $('#pt-answer');
    const confTxt = fmt.pct0(d.confidence * 100);
    const kbHtml = (d.kb || []).map((k) => `<div class="kb-hit">
        <div class="kb-tag">Resolvido pela nossa equipe · similaridade ${String(k.similarity.toFixed(2)).replace('.', ',')}</div>
        <div>${esc(k.resolution)}</div></div>`).join('');
    const simHtml = (d.similar || []).length ? `
      <div class="kicker" style="margin-top:16px">Casos parecidos no arquivo
        <span style="text-transform:none;letter-spacing:0">(corpus real, em inglês)</span></div>
      <div class="cp-similar">${d.similar.map((s) => `<div class="clip">
        <div class="c-meta"><span class="c-sim">${String(s.similarity.toFixed(2)).replace('.', ',')}</span><span>${esc(s.topic)}</span></div>
        <div class="c-text">${esc(s.text)}…</div></div>`).join('')}</div>` : '';

    let inner = '';
    if (d.mode === 'veto') {
      inner = `<div class="cp-verdict cascade">
        <div class="kicker">Encaminhamento imediato</div>
        <div class="cp-category" style="font-size:24px">Este caso vai direto para a nossa equipe.</div>
        <div class="pt-answer-text">Identificamos um contexto sensível — resposta automática não é
        o caminho certo aqui. Seu chamado entra com <strong>prioridade ${esc(d.priority)}</strong> e
        um atendente humano assume.</div>
        ${d.vetoes.map((v) => `<div class="veto">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4z"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="15.5" r=".5" fill="currentColor"/></svg>
          <div><div class="v-rule">${esc(v.regra)}</div></div></div>`).join('')}
        <div class="pt-actions"><button class="btn-primary" id="pt-open">Abrir chamado com prioridade</button></div>
      </div>`;
    } else if (d.mode === 'low_conf') {
      inner = `<div class="cp-verdict cascade">
        <div class="kicker">Melhor um humano ver isso</div>
        <div class="cp-category" style="font-size:24px">Prefiro não arriscar uma resposta errada.</div>
        <div class="pt-answer-text">Seu relato não se encaixa com confiança suficiente em nenhum
        caso conhecido (confiança ${confTxt}, abaixo do nosso padrão de qualidade). O caminho mais
        rápido é abrir um chamado — ele já vai com o seu texto e a triagem inicial feita.</div>
        ${kbHtml}
        <div class="pt-actions"><button class="btn-primary" id="pt-open">Abrir chamado</button></div>
      </div>`;
    } else {
      inner = `<div class="cp-verdict cascade">
        <div class="pt-verdict-head">
          <div>
            <div class="kicker">O que encontrei para o seu caso</div>
            <div class="cp-category" style="font-size:24px">${esc(d.category)}</div>
          </div>
          <span class="chip chip-inline" style="color:var(--sage);background:var(--sage-dim);margin-top:6px">confiança ${confTxt}</span>
        </div>
        <div class="pt-answer-text">${esc(d.playbook)}</div>
        ${kbHtml}${simHtml}
        <div class="pt-actions">
          <button class="btn-ghost" id="pt-helped">Isso resolveu ✓</button>
          <button class="btn-primary" id="pt-open">Não resolveu — abrir chamado</button>
        </div>
      </div>`;
    }
    box.innerHTML = inner;
    box.hidden = false;
    const open = $('#pt-open');
    if (open) open.addEventListener('click', showTicketForm);
    const helped = $('#pt-helped');
    if (helped) helped.addEventListener('click', portalHelped);
  }

  function showTicketForm() {
    $('#pt-answer').hidden = true;
    $('#pt-ticket-summary').textContent =
      `${ptState.category} · prioridade ${ptState.priority} · confiança ${fmt.pct0(ptState.confidence * 100)}\n\n` +
      $('#pt-text').value.trim();
    $('#pt-ticket-form').hidden = false;
  }

  async function portalTicket() {
    const btn = $('#pt-ticket-send');
    btn.disabled = true;
    try {
      const r = await postJSON('/api/portal/ticket', { extra: $('#pt-extra').value.trim() });
      $('#pt-ticket-form').hidden = true;
      $('#pt-extra').value = '';
      $('#pt-success').innerHTML = `<div class="cp-verdict cascade">
        <div class="kicker">Chamado aberto</div>
        <div class="cp-category" style="font-size:24px">#${r.id} — recebido.</div>
        <div class="pt-answer-text">Seu chamado entrou na fila como <strong>${esc(r.category)}</strong>,
        prioridade <strong>${esc(r.priority)}</strong>, com todo o contexto da conversa.
        Um atendente humano assume a partir daqui.</div>
        <div class="pt-actions"><button class="btn-ghost" id="pt-new">Fazer outra pergunta</button></div>
      </div>`;
      $('#pt-success').hidden = false;
      $('#pt-new').addEventListener('click', resetPortal);
    } catch (e) {
      toast('Não foi possível abrir o chamado — tente novamente.', 'err');
    } finally {
      btn.disabled = false;
    }
  }

  function resetPortal() {
    $('#pt-text').value = '';
    ['pt-answer', 'pt-ticket-form', 'pt-success'].forEach((id) => { $('#' + id).hidden = true; });
    $('#pt-empty').hidden = false;
  }

  async function portalHelped() {
    try { await postJSON('/api/portal/feedback', { helped: true }); } catch (e) { /* demo */ }
    toast('Que bom que resolveu! Registramos para melhorar o atendimento.');
    resetPortal();
  }

  /* ======================= FILA DE CHAMADOS (ADMIN) ======================= */

  function initFila() { loadFila(); }

  async function loadFila() {
    let d;
    try {
      d = await fetchJSON('/api/admin/queue');
    } catch (e) {
      toast('Não foi possível carregar a fila.', 'err');
      return;
    }
    $('#fila-stats').innerHTML = [
      manchete({ kicker: 'Abertos', value: fmt.int(d.stats.open),
                 tone: d.stats.open ? 'warn' : null, sub: 'aguardando resolução humana' }),
      manchete({ kicker: 'Resolvidos', value: fmt.int(d.stats.resolved),
                 sub: 'pela equipe, nesta demo' }),
      manchete({ kicker: 'Defletidos', value: fmt.int(d.stats.deflected), tone: 'good',
                 sub: '"isso resolveu" no portal — sem chamado' }),
      manchete({ kicker: 'Aprendizados', value: fmt.int(d.stats.kb_count),
                 sub: 'resoluções na base de conhecimento' }),
    ].join('');
    fitValues('[data-view="fila"]');

    $('#fila-table tbody').innerHTML = d.tickets.map((t) => {
      const prob = (t.question || '') + (t.extra ? ' · ' + t.extra : '');
      const resolCell = t.status === 'Aberto'
        ? `<div class="fila-resolve">
             <textarea id="res-${t.id}" maxlength="900"
               placeholder="Descreva a resolução validada — ela vira conhecimento da IA"></textarea>
             <button class="btn-ghost" data-resolve="${t.id}">Salvar resolução</button></div>`
        : esc(t.resolution || '—');
      return `<tr>
        <td class="num">${t.id}</td>
        <td class="mono" style="font-size:11.5px;white-space:nowrap">${esc(t.created_at || '')}</td>
        <td><span class="status-pill ${t.status === 'Aberto' ? 'st-aberto' : 'st-resolvido'}">${esc(t.status)}</span></td>
        <td>${esc(t.priority || '—')}</td>
        <td>${esc(t.category || '—')}</td>
        <td style="max-width:320px">${esc(prob.slice(0, 180))}${prob.length > 180 ? '…' : ''}</td>
        <td>${resolCell}</td>
      </tr>`;
    }).join('') || `<tr><td colspan="7" style="text-align:center;color:var(--ink-3);padding:24px">
        Nenhum chamado ainda — abra um pelo perfil <strong>Cliente</strong>.</td></tr>`;
    $$('#fila-table [data-resolve]').forEach((b) =>
      b.addEventListener('click', () => resolveTicket(b.dataset.resolve)));

    $('#fila-kb tbody').innerHTML = d.kb.map((k) => `<tr>
        <td class="mono" style="font-size:11.5px;white-space:nowrap">${esc(k.created_at || '')}</td>
        <td>${esc(k.category || '')}</td>
        <td style="max-width:300px">${esc((k.problem || '').slice(0, 140))}</td>
        <td style="max-width:360px">${esc((k.resolution || '').slice(0, 220))}</td>
      </tr>`).join('') || `<tr><td colspan="4" style="text-align:center;color:var(--ink-3);padding:24px">
        Nenhuma resolução validada ainda — resolva um chamado acima.</td></tr>`;

    const navCount = $('#nav-fila-count');
    navCount.hidden = !d.stats.open;
    navCount.textContent = d.stats.open;
  }

  async function resolveTicket(id) {
    const ta = $('#res-' + id);
    const resolution = ta.value.trim();
    if (resolution.length < 10) {
      toast('Descreva a resolução com mais detalhe (mín. 10 caracteres).', 'err');
      ta.focus();
      return;
    }
    try {
      await postJSON('/api/admin/resolve', { ticket_id: Number(id), resolution });
      toast('Resolução salva — a base de conhecimento aprendeu.');
      loadFila();
    } catch (e) {
      toast('Não foi possível salvar a resolução.', 'err');
    }
  }

  /* ======================= LOGIN ======================= */

  function initLogin() {
    let role = 'cliente';
    $$('.role-card').forEach((c) => c.addEventListener('click', () => {
      role = c.dataset.role;
      $$('.role-card').forEach((x) => x.setAttribute('aria-pressed', String(x === c)));
    }));
    async function submit() {
      const err = $('#login-error');
      err.hidden = true;
      try {
        await postJSON('/api/login', { role, password: $('#login-pass').value });
        location.hash = '';
        location.reload();
      } catch (e) {
        err.textContent = 'Perfil ou senha inválidos — confira e tente de novo.';
        err.hidden = false;
      }
    }
    $('#login-btn').addEventListener('click', submit);
    $('#login-pass').addEventListener('keydown', (e) => { if (e.key === 'Enter') submit(); });
  }

  /* ======================= ROUTER ======================= */

  const VIEWS = {
    portal: initPortal,
    executivo: initExecutivo,
    operacao: initOperacao,
    fila: initFila,
    copilot: initCopilot,
    roi: initRoi,
  };
  const ROLE_VIEWS = { admin: ['executivo', 'operacao', 'fila', 'copilot', 'roi'],
                       cliente: ['portal'] };
  const ROLE_HOME = { admin: 'executivo', cliente: 'portal' };
  let ROLE = null;

  function showView(name) {
    $$('.view').forEach((s) => { s.hidden = s.dataset.view !== name; });
    $$('.nav a').forEach((a) => a.classList.toggle('active', a.dataset.route === name));
  }

  function route() {
    if (!ROLE) { showView('login'); return; }
    let name = location.hash.replace('#/', '') || ROLE_HOME[ROLE];
    if (!ROLE_VIEWS[ROLE].includes(name)) name = ROLE_HOME[ROLE];
    showView(name);
    if (!inited[name]) { inited[name] = true; VIEWS[name](); }
    else if (name === 'fila') loadFila();      // fila sempre atualizada
    setTimeout(() => {
      Object.entries(charts).forEach(([id, c]) => {
        const el = $('#' + id);
        if (el && !el.closest('.view').hidden) c.resize();
      });
      fitValues('[data-view="' + name + '"]');
    }, 30);
  }

  /* ======================= BOOT ======================= */

  async function boot() {
    try {
      ROLE = (await fetchJSON('/api/me')).role;
    } catch (e) {
      ROLE = null;
    }
    document.body.classList.toggle('noshell', !ROLE);
    $$('.nav a').forEach((a) => { a.hidden = !ROLE || a.dataset.roles !== ROLE; });
    $('#logout-link').hidden = !ROLE;
    $('#logout-link').addEventListener('click', async () => {
      try { await postJSON('/api/logout'); } catch (e) { /* sessão local some no reload */ }
      location.hash = '';
      location.reload();
    });

    if (!ROLE) {
      initLogin();
      showView('login');
      return;
    }
    if (ROLE === 'admin') {
      try {
        B = await fetchJSON('/api/bootstrap');
        $('#foot-status').textContent =
          `edição: ${fmt.int(B.kpis.sample_size)} tickets · ${fmt.int(B.kpis.tickets_year)}/ano`;
      } catch (e) {
        $('#foot-status').textContent = 'falha ao carregar a API';
        $('#main').insertAdjacentHTML('afterbegin', `<div class="boot-error" id="boot-error">
          <h2>A edição não chegou.</h2>
          <p>Não foi possível carregar <code>/api/bootstrap</code>. Verifique se o servidor
          está de pé (<code>python app.py</code>) e tente de novo.</p>
          <button class="btn-primary" id="boot-retry">Tentar novamente</button></div>`);
        $('#boot-retry').addEventListener('click', () => {
          $('#boot-error').remove();
          boot();
        });
        return;
      }
    } else {
      $('#foot-status').textContent = 'central de ajuda · sessão cliente';
    }
    window.addEventListener('hashchange', route);
    route();
  }

  boot();
})();
