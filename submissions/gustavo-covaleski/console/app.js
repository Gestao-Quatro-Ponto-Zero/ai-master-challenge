"use strict";
// Console estático do piloto. Todo número vem de window.DADOS (console/data.js, gerado por solution/f10_console_dados.py).
(function () {
  const D = window.DADOS;
  const CATS = D.meta.categorias;
  const ORDEM = ["humano decide", "IA sugere", "IA decide"];
  const SELO = { "IA decide": "selo-decide", "IA sugere": "selo-sugere", "humano decide": "selo-humano" };
  const fmtPct = (x, d = 1) => x == null ? "—" : new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: d, maximumFractionDigits: d }).format(x);
  const fmtNum = (x, d = 0) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }).format(x);
  const fmtBRL = (x) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(x);
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const selo = (f) => `<span class="selo ${SELO[f]}">${esc(f)}</span>`;

  const S = {
    dia: 20, modo: "ativo", pol: "F9", filtro: "todas", sel: 0, catGraf: "Hardware",
    estados: {}, reembolso: {}, ataque: {}, resposta: {}, log: [], duplicados: 0, chaves: new Set(),
    premissas: { ...D.kpis.premissas },
  };

  // ---- log e idempotência (mesma chave de triagem.py: evt:<event_id>; ver solution/tests/test_f8.py)
  const agora = () => new Date().toISOString();
  const chaveDe = (t) => `evt:fila-${t.id}`;
  function registrarDecisao(t, faixa, semSombra, motivo) {
    const chave = chaveDe(t);
    if (S.chaves.has(chave)) return false;
    S.chaves.add(chave);
    S.log.push({ timestamp_utc: agora(), chave, event_id: `fila-${t.id}`, categoria: t.pred, p_max: t.p_max, faixa,
      faixa_sem_sombra: semSombra, motivo, modelo_versao: D.meta.modelo_versao, politica_versao: D.meta.politica_versao,
      latencia_ms: null, erro: null });
    return true;
  }

  // ---- regra da faixa vista na tela
  function faixaDe(t) {
    const base = t.faixas[S.pol].faixa;
    let f = base, motivo = "termos: " + t.termos;
    if (S.reembolso[t.id]) { f = "humano decide"; motivo = "regra de ação: Refund request; " + motivo; }
    const semSombra = f;
    if (S.modo === "sombra") f = "humano decide";
    return { faixa: f, semSombra, base, motivo };
  }
  const visiveis = () => D.fila.filter((t) => t.dia <= S.dia && (S.filtro === "todas" || faixaDe(t).faixa === S.filtro));

  // ---- fila
  function renderFila() {
    const v = visiveis();
    if (S.sel >= v.length) S.sel = Math.max(0, v.length - 1);
    const total = D.fila.filter((t) => t.dia <= S.dia).length;
    $("fila-resumo").textContent = `${fmtNum(v.length)} de ${fmtNum(total)} até o dia ${S.dia}`;
    $("lista").innerHTML = v.map((t, i) => {
      const e = S.estados[t.id];
      const est = e ? (e.tipo === "confirmado" ? "confirmado" : `corrigido → ${e.categoria}`) : "pendente";
      return `<li role="option" id="op-${t.id}" data-i="${i}" aria-selected="${i === S.sel}">
        <span class="lid num">#${t.id}</span>${selo(faixaDe(t).faixa)}<span class="estado ${e ? e.tipo : ""}">${esc(est)}</span>
        <span class="ltexto">${esc(t.texto.slice(0, 90))}</span></li>`;
    }).join("");
    const atual = v[S.sel];
    if (atual) {
      $("lista").setAttribute("aria-activedescendant", `op-${atual.id}`);
      const li = $(`op-${atual.id}`); if (li) li.scrollIntoView({ block: "nearest" });
    }
    v.forEach((t) => { const f = faixaDe(t); registrarDecisao(t, f.faixa, f.semSombra, f.motivo); });
  }

  // ---- detalhe
  function renderDetalhe() {
    const t = visiveis()[S.sel];
    if (!t) { $("detalhe").innerHTML = `<p class="discreto">Nenhum ticket com esse filtro até o dia ${S.dia}.</p>`; $("det-id").textContent = ""; return; }
    $("det-id").textContent = `#${t.id} · dia ${t.dia}`;
    const f = faixaDe(t);
    const pol = D.politicas[S.pol];
    const p1 = t.faixas[S.pol].passos[0], p2 = t.faixas[S.pol].passos[1];
    const cmp = t.p_max >= p1.t_decide ? `≥ limiar de IA decide (${fmtPct(p1.t_decide)})`
      : t.p_max >= p1.t_sugere ? `entre os limiares (${fmtPct(p1.t_sugere)}–${fmtPct(p1.t_decide)})`
      : `< limiar de IA sugere (${fmtPct(p1.t_sugere)})`;
    const passos = [
      `<li>Confiança ${fmtPct(t.p_max)} ${cmp} → ${selo(p1.faixa_global)}</li>`,
      `<li>Teto da política ${esc(pol.nome)} para ${esc(t.pred)}: ${selo(p2.teto)}${p2.rebaixou ? " → rebaixa" : " → mantém"}</li>`,
      S.reembolso[t.id] ? `<li>Regra de ação: tipo Reembolso → ${selo("humano decide")} (regra de negócio)</li>`
        : `<li class="desligado">Regra de ação: sem tipo sensível (reembolso ou cancelamento)</li>`,
      S.modo === "sombra" ? `<li>Modo sombra: devolve ${selo("humano decide")}; o log guarda a faixa real ${selo(f.semSombra)}</li>`
        : `<li class="desligado">Modo sombra: desligado</li>`,
    ].join("");
    const at = S.ataque[t.id];
    let blocoAtaque = "";
    if (at) {
      const a = D.ataques[String(t.id)][at];
      const fa = S.modo === "sombra" ? "humano decide" : a.faixas[S.pol];
      const trocou = a.pred !== t.pred;
      const veredito = trocou && fa === "IA decide" ? `<p class="resposta alerta">Dano silencioso: a categoria mudou para ${esc(a.pred)} e continua em IA decide.</p>`
        : trocou ? `<p class="resposta ok">A categoria mudou para ${esc(a.pred)}, mas a decisão não passa sem humano (${esc(fa)}).</p>`
        : `<p class="resposta ok">Sem efeito na categoria (${esc(a.pred)}).</p>`;
      blocoAtaque = `<p class="resposta">Ataque "${esc(at)}" (alvo: ${esc(a.alvo)}) → ${esc(a.pred)}, confiança ${fmtPct(a.p_max)}, faixa ${selo(fa)}</p>${veredito}`;
    }
    const e = S.estados[t.id];
    $("detalhe").innerHTML = `
      <p class="texto-ticket">${esc(t.texto)}${t.truncado ? "… (trecho)" : ""}</p>
      <div class="resumo">
        <div class="item"><span class="rot">Faixa</span>${selo(f.faixa)}</div>
        <div class="item"><span class="rot">Categoria</span><span class="val">${esc(t.pred)}</span></div>
        <div class="item"><span class="rot">Confiança</span><span class="val num">${fmtPct(t.p_max)}</span></div>
      </div>
      <table class="tabela"><thead><tr><th>Duas mais prováveis</th><th class="dir">Probabilidade</th></tr></thead>
        <tbody>${t.top2.map((x) => `<tr><td>${esc(x.categoria)}</td><td class="dir">${fmtPct(x.p)}</td></tr>`).join("")}</tbody></table>
      <div><h3>Por que esta faixa</h3><ol class="passos">${passos}</ol></div>
      <p class="pequeno"><strong>Termos que mais pesaram:</strong> ${esc(t.termos)}</p>
      <p class="pequeno discreto">Atendente simulado: rótulo original = <strong>${esc(t.rotulo_original)}</strong>${e ? ` · estado: ${esc(e.tipo)}${e.categoria ? " → " + esc(e.categoria) : ""}` : ""}</p>
      <div class="acoes">
        <button type="button" class="botao primario" id="ac-confirmar">Confirmar (Enter)</button>
        <label>Corrigir para… <select id="ac-cat">${CATS.map((c, i) => `<option value="${esc(c)}"${c === t.rotulo_original ? " selected" : ""}>${i + 1}. ${esc(c)}</option>`).join("")}</select></label>
        <button type="button" class="botao" id="ac-corrigir">Corrigir</button>
      </div>
      <div class="acoes">
        <button type="button" class="botao" id="ac-reentregar">Reentregar (webhook)</button>
        <button type="button" class="botao" id="ac-reembolso" aria-pressed="${!!S.reembolso[t.id]}">${S.reembolso[t.id] ? "Remover" : "Simular"} tipo "Reembolso"</button>
        <label>Injetar ataque <select id="ac-ataque"><option value="">—</option>${D.ataques_modelos.map((a) => `<option value="${esc(a.id)}"${a.id === at ? " selected" : ""}>${esc(a.id)}</option>`).join("")}</select></label>
      </div>
      ${S.resposta[t.id] ? `<p class="resposta">${S.resposta[t.id]}</p>` : ""}
      ${blocoAtaque}`;
    $("ac-confirmar").onclick = () => decidir(t, null);
    $("ac-corrigir").onclick = () => decidir(t, $("ac-cat").value);
    $("ac-reentregar").onclick = () => reentregar(t);
    $("ac-reembolso").onclick = () => { S.reembolso[t.id] = !S.reembolso[t.id]; render(); };
    $("ac-ataque").onchange = (ev) => { S.ataque[t.id] = ev.target.value || null; render(); };
  }

  function decidir(t, categoria) {
    if (!t) return;
    const corr = categoria && categoria !== t.pred;
    S.estados[t.id] = corr ? { tipo: "corrigido", categoria } : { tipo: "confirmado" };
    S.log.push({ timestamp_utc: agora(), tipo: corr ? "correcao" : "confirmacao", chave: chaveDe(t),
      categoria_correta: corr ? categoria : t.pred, atendente: "simulado (rótulo original)" });
    S.resposta[t.id] = corr ? `Correção registrada: ${esc(t.pred)} → ${esc(categoria)}. Entra no próximo ciclo de avaliação; não retreina.` : "Confirmação registrada.";
    render();
  }

  function reentregar(t) {
    const chave = chaveDe(t);
    if (S.chaves.has(chave)) {
      S.duplicados += 1;
      S.log.push({ tipo: "duplicado", chave, timestamp_utc: agora() });
      S.resposta[t.id] = `Duplicado: nenhuma nova decisão (chave ${esc(chave)} já reservada). Mesma lógica de triagem.py, testada em test_f8.py.`;
    }
    render();
  }

  // ---- governança
  const govDia = () => D.governanca[S.dia - 1];
  function acao(vigente, regra) {
    if (!regra) return { txt: "sem dados", diverge: false };
    const d = ORDEM.indexOf(regra) - ORDEM.indexOf(vigente);
    return d > 0 ? { txt: `promover → ${regra}`, diverge: true } : d < 0 ? { txt: `rebaixar → ${regra}`, diverge: true } : { txt: `manter (${regra})`, diverge: false };
  }
  function barraIC(c) {
    const lo = 0.85, hi = 1.0, x = (v) => Math.max(0, Math.min(1, (v - lo) / (hi - lo))) * 100;
    const mI = D.meta.meta_ia_decide, mS = D.meta.meta_ia_sugere;
    const ic = c.li == null ? "" : `<rect x="${x(c.li)}" y="4" width="${Math.max(0.8, x(c.ls) - x(c.li))}" height="6" fill="#1d4ed8" opacity=".35"></rect><circle cx="${x(c.precisao)}" cy="7" r="2.4" fill="#1d4ed8"></circle>`;
    return `<svg class="ic" viewBox="0 0 100 14" preserveAspectRatio="none" aria-hidden="true">
      <rect x="0" y="6" width="100" height="2" fill="#e6e9ee"></rect>${ic}
      <line x1="${x(mS)}" x2="${x(mS)}" y1="0" y2="14" stroke="#7a4b00" stroke-width=".7"></line>
      <line x1="${x(mI)}" x2="${x(mI)}" y1="0" y2="14" stroke="#146c2e" stroke-width=".7"></line></svg>`;
  }
  function renderGov() {
    const g = govDia(), pol = D.politicas[S.pol];
    $("gov-dia").textContent = `dia ${S.dia} · ${fmtNum(g.n_total)} tickets acumulados`;
    $("gov-tabela").querySelector("tbody").innerHTML = CATS.map((cat) => {
      const c = g.categorias[cat], vig = pol.por_categoria[cat], a = acao(vig, c.decisao_regra);
      return `<tr data-cat="${esc(cat)}" aria-selected="${cat === S.catGraf}" tabindex="0">
        <td>${esc(cat)}</td><td>${selo(vig)}</td><td class="dir">${fmtNum(c.n_sombra)}</td>
        <td><span class="num">${fmtPct(c.precisao)} (${fmtPct(c.li)}–${fmtPct(c.ls)})</span>${barraIC(c)}</td>
        <td class="regra ${a.diverge ? "diverge" : ""}">${esc(a.txt)}</td></tr>`;
    }).join("");
    $("gov-tabela").querySelectorAll("tbody tr").forEach((tr) => {
      const sel = () => { S.catGraf = tr.dataset.cat; renderGov(); };
      tr.onclick = sel; tr.onkeydown = (ev) => { if (ev.key === "Enter") sel(); };
    });
    renderGrafico(); renderCartoes();
  }
  function renderGrafico() {
    const W = 400, H = 150, L = 34, R = 8, T = 10, B = 22, lo = 0.85, hi = 1.0;
    const x = (d) => L + (d - 1) / 19 * (W - L - R), y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
    const pts = D.governanca.map((g) => [g.dia, g.categorias[S.catGraf].li]).filter((p) => p[1] != null);
    const mI = D.meta.meta_ia_decide, mS = D.meta.meta_ia_sugere;
    const ticks = [0.85, 0.9, 0.95, 1.0].map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="#edf0f3"></line><text x="${L - 4}" y="${y(v) + 3}" text-anchor="end" font-size="9" fill="#5a6475">${fmtNum(v, 2)}</text>`).join("");
    const linha = pts.map((p, i) => `${i ? "L" : "M"}${x(p[0]).toFixed(1)},${y(Math.max(lo, p[1])).toFixed(1)}`).join("");
    const marca = `<line x1="${x(S.dia)}" x2="${x(S.dia)}" y1="${T}" y2="${H - B}" stroke="#1c2430" stroke-dasharray="2 2"></line>`;
    $("graf-titulo").textContent = `Limite inferior por dia — ${S.catGraf}`;
    $("grafico").innerHTML = `${ticks}
      <line x1="${L}" x2="${W - R}" y1="${y(mI)}" y2="${y(mI)}" stroke="#146c2e" stroke-dasharray="4 3"></line>
      <text x="${W - R}" y="${y(mI) - 3}" text-anchor="end" font-size="9" fill="#146c2e">meta IA decide ${fmtNum(mI, 4)}</text>
      <line x1="${L}" x2="${W - R}" y1="${y(mS)}" y2="${y(mS)}" stroke="#7a4b00" stroke-dasharray="4 3"></line>
      <text x="${W - R}" y="${y(mS) + 10}" text-anchor="end" font-size="9" fill="#7a4b00">meta IA sugere ${fmtNum(mS, 4)}</text>
      ${marca}<path d="${linha}" fill="none" stroke="#1d4ed8" stroke-width="1.6"></path>
      ${pts.map((p) => `<circle cx="${x(p[0])}" cy="${y(Math.max(lo, p[1]))}" r="1.8" fill="#1d4ed8"></circle>`).join("")}
      <text x="${L}" y="${H - 6}" font-size="9" fill="#5a6475">dia 1</text><text x="${W - R}" y="${H - 6}" text-anchor="end" font-size="9" fill="#5a6475">dia 20</text>`;
  }
  function coberturaDia(pol) {
    const g = govDia(), fx = g.faixas[pol];
    if (S.modo === "sombra") return { decide: 0, sugere: 0, humano: 1, precisao: null, nDecide: 0, n: g.n_total };
    return { decide: fx["IA decide"].n / g.n_total, sugere: fx["IA sugere"].n / g.n_total, humano: fx["humano decide"].n / g.n_total,
      precisao: fx["IA decide"].n ? fx["IA decide"].acertos / fx["IA decide"].n : null, nDecide: fx["IA decide"].n, n: g.n_total };
  }
  function renderCartoes() {
    const c = coberturaDia(S.pol), p = S.premissas;
    const economia = c.decide * p.volume_ano * p.minutos_triagem / 60 * p.reais_por_hora;
    $("cartoes").innerHTML = `
      <div class="cartao"><div class="rot">Cobertura no dia ${S.dia}</div><div class="valor">${fmtPct(c.decide)} · ${fmtPct(c.sugere)} · ${fmtPct(c.humano)}</div><div class="nota">IA decide · IA sugere · humano</div></div>
      <div class="cartao"><div class="rot">Precisão medida em IA decide</div><div class="valor">${fmtPct(c.precisao)}</div><div class="nota">${fmtNum(c.nDecide)} tickets, contra o rótulo original</div></div>
      <div class="cartao"><div class="rot">Trabalho humano evitado</div><div class="valor">${fmtNum(c.nDecide)} de ${fmtNum(c.n)}</div><div class="nota">tickets roteados sem humano</div></div>
      <div class="cartao"><div class="rot">Economia anual, cenário A</div><div class="valor">${fmtBRL(economia)}</div><div class="nota">premissas abaixo; cenário B: zero</div></div>`;
  }

  // ---- alertas
  function alertas() {
    const out = [], pol = D.politicas[S.pol];
    if (S.modo === "sombra") {
      const base = D.governanca[S.dia - 1].faixas[S.pol]["IA decide"].n / D.governanca[S.dia - 1].n_total;
      out.push({ sev: "alta", txt: `Modo sombra: cobertura de IA decide caiu de ${fmtPct(base)} para ${fmtPct(0)} (queda de ${fmtNum(base * 100, 1)} p.p., acima do limite de 3 p.p.). Tudo vai para humano; o log guarda a faixa real.` });
    }
    const dn = D.kpis.dano_injecao[S.pol];
    out.push(dn.silenciosos > 0
      ? { sev: "alta", txt: `Injeção com ${pol.nome}: ${fmtNum(dn.silenciosos)} de ${fmtNum(dn.n_pares)} ataques mudam a categoria e continuam em IA decide (dano silencioso).` }
      : { sev: "info", txt: `Injeção com ${pol.nome}: 0 de ${fmtNum(dn.n_pares)} ataques mudam uma decisão automática (limite superior ${fmtPct(dn.limite_superior, 2)}); ${fmtNum(dn.saem_de_ia_decide)} saem para humano.` });
    if (S.duplicados) out.push({ sev: "media", txt: `${fmtNum(S.duplicados)} reentrega(s) duplicada(s) descartada(s), sem nova decisão.` });
    const g = govDia();
    CATS.forEach((cat) => {
      const a = acao(pol.por_categoria[cat], g.categorias[cat].decisao_regra);
      if (a.diverge) out.push({ sev: "media", txt: `${cat}: a regra daria "${a.txt}" (limite inferior ${fmtNum(g.categorias[cat].li, 4)}), mas a política vigente é ${pol.por_categoria[cat]}.` });
    });
    return out;
  }
  function renderAlertas() {
    const a = alertas(), n = a.filter((x) => x.sev !== "info").length;
    $("n-alertas").textContent = n;
    $("n-alertas").classList.toggle("ativo", n > 0);
    $("alertas").innerHTML = a.map((x) => `<li class="sev-${x.sev}">${esc(x.txt)}</li>`).join("");
  }

  function renderLog() {
    $("n-log").textContent = S.log.length;
    $("log").textContent = S.log.map((l) => JSON.stringify(l)).join("\n");
  }

  function render() { renderFila(); renderDetalhe(); renderGov(); renderAlertas(); renderLog(); }

  // ---- controles
  $("dia").oninput = (e) => { S.dia = +e.target.value; $("dia-valor").textContent = S.dia; render(); };
  $("modo").onclick = (e) => { S.modo = S.modo === "ativo" ? "sombra" : "ativo"; e.target.textContent = S.modo; e.target.setAttribute("aria-pressed", S.modo === "sombra"); render(); };
  $("politica").onchange = (e) => { S.pol = e.target.value; render(); };
  document.querySelectorAll(".filtro").forEach((b) => b.onclick = () => {
    S.filtro = b.dataset.filtro; S.sel = 0;
    document.querySelectorAll(".filtro").forEach((x) => x.setAttribute("aria-pressed", x === b)); render();
  });
  $("lista").onclick = (e) => { const li = e.target.closest("li"); if (li) { S.sel = +li.dataset.i; render(); $("lista").focus(); } };
  $("lista").onkeydown = (e) => {
    const v = visiveis();
    if (e.key === "ArrowDown") { S.sel = Math.min(v.length - 1, S.sel + 1); e.preventDefault(); render(); }
    else if (e.key === "ArrowUp") { S.sel = Math.max(0, S.sel - 1); e.preventDefault(); render(); }
    else if (e.key === "Enter") { decidir(v[S.sel], null); e.preventDefault(); }
    else if (/^[1-8]$/.test(e.key)) { decidir(v[S.sel], CATS[+e.key - 1]); e.preventDefault(); }
  };
  [["p-reais", "reais_por_hora"], ["p-min", "minutos_triagem"], ["p-vol", "volume_ano"]].forEach(([id, k]) => {
    $(id).value = S.premissas[k];
    $(id).oninput = (e) => { const v = parseFloat(e.target.value); S.premissas[k] = isFinite(v) && v >= 0 ? v : 0; renderCartoes(); };
  });
  function abrir(id) { const d = $(id); d.hidden = false; d.querySelector("[data-fechar]").focus(); }
  function fechar(d) { d.hidden = true; }
  $("abrir-alertas").onclick = () => abrir("dlg-alertas");
  $("abrir-ajuda").onclick = () => abrir("dlg-ajuda");
  document.querySelectorAll(".dialogo").forEach((d) => {
    d.querySelector("[data-fechar]").onclick = () => fechar(d);
    d.onclick = (e) => { if (e.target === d) fechar(d); };
    d.onkeydown = (e) => { if (e.key === "Escape") fechar(d); };
  });

  render();
})();
