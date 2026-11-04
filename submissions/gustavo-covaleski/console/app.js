"use strict";
// Console do piloto (F11). Todo número vem de window.DADOS (console/data.js, gerado por solution/f10_console_dados.py).
(function () {
  const D = window.DADOS;
  const CATS = D.meta.categorias;
  const ORDEM = ["humano decide", "IA sugere", "IA decide"];
  const CLASSE = { "IA decide": "decide", "IA sugere": "sugere", "humano decide": "humano" };
  const ICONE = {
    "IA decide": '<path d="M5 12l4 4 10-10"/>',
    "IA sugere": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "humano decide": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>',
  };
  const INFO = '<svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>';
  const ALERTA = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/></svg>';
  const X = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>';

  const pct = (x, d = 1) => x == null ? "—" : new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: d, maximumFractionDigits: d }).format(x);
  const num = (x, d = 0) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }).format(x);
  const brl = (x) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(x);
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const selo = (f, extra = "", grande = false) => `<span class="selo ${CLASSE[f]}${grande ? " grande" : ""}"><svg aria-hidden="true" viewBox="0 0 24 24">${ICONE[f]}</svg>${esc(f)}${extra}</span>`;

  const S = {
    tela: "saude", dia: 20, modo: "ativo", pol: "F9", filtro: "todas", sel: 0, comeceFechado: false,
    estados: {}, resposta: {}, corrigindo: false, log: [], chaves: new Set(), duplicados: 0,
    premissas: { ...D.kpis.premissas }, painelCat: null, focoAntes: null,
    r: { ticket: 10244, ataque: "categoria_repetida", rodouAtaque: false, rodouDup: false, rodouReembolso: false },
  };

  // ---- dados derivados
  const gov = () => D.governanca[S.dia - 1];
  const pol = () => D.politicas[S.pol];
  function cobertura(polK = S.pol) {
    const g = gov(), fx = g.faixas[polK];
    if (S.modo === "sombra") return { decide: 0, sugere: 0, humano: g.n_total, n: g.n_total, acertos: 0 };
    return { decide: fx["IA decide"].n, sugere: fx["IA sugere"].n, humano: fx["humano decide"].n, n: g.n_total, acertos: fx["IA decide"].acertos };
  }
  function faixaTicket(t, polK = S.pol) {
    const base = t.faixas[polK].faixa;
    return { faixa: S.modo === "sombra" ? "humano decide" : base, semSombra: base };
  }
  function regraVs(vig, regra) {
    if (!regra) return { txt: "sem dados", cls: "mantem" };
    const d = ORDEM.indexOf(regra) - ORDEM.indexOf(vig);
    return d > 0 ? { txt: "pode subir", cls: "sobe" } : d < 0 ? { txt: "alerta", cls: "alerta" } : { txt: "mantém", cls: "mantem" };
  }

  // ---- log e idempotência (mesma chave de triagem.py: evt:<event_id>; ver solution/tests/test_f8.py)
  const agora = () => new Date().toISOString();
  const chave = (t) => `evt:fila-${t.id}`;
  function registrar(t) {
    const k = chave(t);
    if (S.chaves.has(k)) return false;
    S.chaves.add(k);
    const f = faixaTicket(t);
    S.log.push({ timestamp_utc: agora(), chave: k, event_id: `fila-${t.id}`, categoria: t.pred, p_max: t.p_max, faixa: f.faixa,
      faixa_sem_sombra: f.semSombra, motivo: "termos: " + t.termos, modelo_versao: D.meta.modelo_versao,
      politica_versao: D.meta.politica_versao, latencia_ms: null, erro: null });
    return true;
  }
  function reentregar(t) {
    if (!S.chaves.has(chave(t))) registrar(t);
    S.duplicados += 1;
    const linha = { tipo: "duplicado", chave: chave(t), timestamp_utc: agora() };
    S.log.push(linha);
    return linha;
  }

  // ---- alertas
  function alertas() {
    const out = [], p = pol(), g = gov();
    if (S.modo === "sombra") {
      const base = g.faixas[S.pol]["IA decide"].n / g.n_total;
      out.push({ txt: `Modo sombra ligado: a cobertura de IA decide caiu de ${pct(base)} para ${pct(0)} (mais de 3 p.p.). Tudo vai para humano; o log continua.`, ir: "#robustez" });
    }
    const dn = D.kpis.dano_injecao[S.pol];
    if (dn.silenciosos > 0) out.push({ txt: `Com ${p.nome}, ${num(dn.silenciosos)} de ${num(dn.n_pares)} ataques simulados mudam a categoria e continuam sem humano.`, ir: "#robustez" });
    if (S.duplicados) out.push({ txt: `${num(S.duplicados)} reentrega(s) duplicada(s) descartada(s), sem nova decisão.`, ir: "#robustez" });
    CATS.forEach((c) => {
      const r = regraVs(p.por_categoria[c], g.categorias[c].decisao_regra);
      if (r.cls === "alerta") out.push({ txt: `${c}: limite inferior de ${pct(g.categorias[c].li)}, abaixo da meta da faixa atual.`, cat: c });
    });
    return out;
  }

  // ---- navegação
  function irPara(tela) {
    S.tela = ["saude", "fila", "governanca", "robustez"].includes(tela) ? tela : "saude";
    document.querySelectorAll(".tela").forEach((s) => { s.hidden = s.dataset.tela !== S.tela; });
    document.querySelectorAll(".nav-itens a").forEach((a) => { if (a.dataset.tela === S.tela) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    render();
  }
  window.addEventListener("hashchange", () => irPara(location.hash.slice(1)));

  function render() {
    $("#nav-estado").textContent = `${pol().nome} · modo ${S.modo} · dia ${S.dia} de 20`;
    ({ saude: telaSaude, fila: telaFila, governanca: telaGov, robustez: telaRobustez })[S.tela]();
    if (S.painelCat) renderPainel();
  }

  // ---- tela 1
  function telaSaude() {
    const c = cobertura(), p = pol(), al = alertas();
    const prec = c.decide ? c.acertos / c.decide : null, meta = D.meta.meta_ia_decide;
    const pr = S.premissas, eco = (c.decide / c.n) * pr.volume_ano * pr.minutos_triagem / 60 * pr.reais_por_hora;
    const grupos = ORDEM.slice().reverse().map((f) => ({ f, cats: CATS.filter((k) => p.por_categoria[k] === f) }));
    const nomes = { "IA decide": "Automáticas", "IA sugere": "Com sugestão", "humano decide": "Com humano" };
    const w = (n) => `${(100 * n / c.n).toFixed(2)}%`;
    $("#tela-saude").innerHTML = `
      <h1 class="pergunta" id="h-saude">O piloto está saudável?</h1>
      <p class="subtitulo">Triagem automática de tickets com um classificador treinado nos rótulos históricos. Dia ${S.dia} de 20 do piloto, política ${esc(p.nome)}.</p>
      ${S.comeceFechado ? "" : `<div class="comece" role="region" aria-label="Comece aqui"><strong>Comece aqui</strong>
        <ol>
          <li><a href="#fila"><span class="num-passo">1</span>Veja um ticket ser triado</a></li>
          <li><a href="#governanca"><span class="num-passo">2</span>Veja por que a IA não decide tudo</a></li>
          <li><a href="#robustez"><span class="num-passo">3</span>Tente quebrar o sistema</a></li>
        </ol>
        <button type="button" class="botao texto fechar" id="fechar-comece">Dispensar</button></div>`}
      ${al.length ? `<div class="alerta-faixa" role="status">${ALERTA}<div><strong>${al.length === 1 ? "1 alerta ativo" : `${al.length} alertas ativos`}</strong><ul>${al.map((a, i) => `<li>${esc(a.txt)} <a href="${a.ir || "#governanca"}" data-alerta="${i}">ver</a></li>`).join("")}</ul></div></div>` : ""}
      <div class="kpis">
        <div class="cartao kpi"><h3>Tickets que a IA resolve sozinha</h3>
          <div class="valor">${pct(c.decide / c.n, 2)}</div>
          <p class="explica">Parte do volume roteada sem nenhum humano (faixa IA decide).</p></div>
        <div class="cartao kpi"><h3>Precisão medida contra a meta</h3>
          <div class="valor">${pct(prec, 2)}${prec != null && prec >= meta ? `<span class="meta-ok"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12l4 4 10-10"/></svg>acima da meta</span>` : ""}</div>
          <p class="explica">Acertos na faixa IA decide; a meta é ${pct(meta)} (1 − taxa de erro humano).</p></div>
        <div class="cartao kpi"><h3>Trabalho humano evitado</h3>
          <div class="valor">${num(c.decide)} <span class="unidade">de ${num(c.n)}</span></div>
          <p class="explica">Tickets que não precisaram de triagem humana.</p>
          <details class="premissas"><summary>Ver economia e premissas</summary>
            <div class="campos">
              <label>Custo do atendente (R$/h) <input type="number" min="0" step="1" data-p="reais_por_hora" value="${pr.reais_por_hora}"></label>
              <label>Triagem manual (min/ticket) <input type="number" min="0" step="0.5" data-p="minutos_triagem" value="${pr.minutos_triagem}"></label>
              <label>Volume (tickets/ano) <input type="number" min="0" step="1000" data-p="volume_ano" value="${pr.volume_ano}"></label>
            </div>
            <p class="eco" id="eco">Economia anual com etapa separada de triagem: <strong>${brl(eco)}</strong>. Sem etapa separada: zero.</p>
          </details></div>
      </div>
      <div class="grade-2">
        <div class="cartao"><h3>Para onde vai cada ticket?</h3>
          <div class="barra-empilhada" role="img" aria-label="IA decide ${pct(c.decide / c.n)}, IA sugere ${pct(c.sugere / c.n)}, humano decide ${pct(c.humano / c.n)}">
            ${c.decide ? `<div class="decide" style="width:${w(c.decide)}">${pct(c.decide / c.n)}</div>` : ""}
            ${c.sugere ? `<div class="sugere" style="width:${w(c.sugere)}">${pct(c.sugere / c.n)}</div>` : ""}
            <div class="humano" style="width:${w(c.humano)}">${pct(c.humano / c.n)}</div></div>
          <ul class="legenda">${["IA decide", "IA sugere", "humano decide"].map((f) => `<li>${selo(f)} <strong>${num({ "IA decide": c.decide, "IA sugere": c.sugere, "humano decide": c.humano }[f])}</strong> tickets</li>`).join("")}</ul>
          <p class="leitura">O que este gráfico diz: a IA decide sozinha numa fatia pequena e segura; a maior parte ainda passa por um humano, que confirma a sugestão ou classifica.</p></div>
        <div class="cartao"><h3>Quais filas já estão automatizadas?</h3>
          <div class="grupos">${grupos.map((g) => `<div class="grupo"><h4>${nomes[g.f]} (${g.cats.length})</h4><div class="chips">${g.cats.map((k) => `<button type="button" class="chip" data-cat="${esc(k)}"><span class="ponto" style="background:var(--${CLASSE[g.f]})" aria-hidden="true"></span>${esc(k)}</button>`).join("") || '<span class="leitura">nenhuma</span>'}</div></div>`).join("")}</div>
          <p class="leitura">Clique numa fila para ver a precisão comprovada dela contra a meta.</p></div>
      </div>`;
    const fc = $("#fechar-comece"); if (fc) fc.onclick = () => { S.comeceFechado = true; render(); };
    document.querySelectorAll("#tela-saude .chip").forEach((b) => b.onclick = () => { location.hash = "#governanca"; abrirPainel(b.dataset.cat, b); });
    document.querySelectorAll("#tela-saude [data-alerta]").forEach((a) => {
      const al2 = al[+a.dataset.alerta];
      if (al2.cat) a.onclick = (e) => { e.preventDefault(); location.hash = "#governanca"; abrirPainel(al2.cat, a); };
    });
    document.querySelectorAll("#tela-saude [data-p]").forEach((inp) => inp.oninput = () => {
      const v = parseFloat(inp.value); S.premissas[inp.dataset.p] = isFinite(v) && v >= 0 ? v : 0;
      const pr2 = S.premissas, e2 = (c.decide / c.n) * pr2.volume_ano * pr2.minutos_triagem / 60 * pr2.reais_por_hora;
      $("#eco").innerHTML = `Economia anual com etapa separada de triagem: <strong>${brl(e2)}</strong>. Sem etapa separada: zero.`;
    });
  }

  // ---- tela 2
  const visiveis = () => D.fila.filter((t) => t.dia <= S.dia && (S.filtro === "todas" || faixaTicket(t).faixa === S.filtro));
  function telaFila() {
    const v = visiveis();
    if (S.sel >= v.length) S.sel = Math.max(0, v.length - 1);
    v.forEach(registrar);
    const t = v[S.sel];
    const filtros = [["todas", "Todas"], ["IA decide", "IA decide"], ["IA sugere", "IA sugere"], ["humano decide", "Humano"]];
    $("#tela-fila").innerHTML = `
      <h1 class="pergunta" id="h-fila">Como um ticket é triado?</h1>
      <p class="subtitulo">A fila do atendente: escolha um ticket e veja a decisão. Enter confirma; as teclas 1 a 8 corrigem.</p>
      <div class="fila-layout">
        <div class="cartao">
          <div class="segmentado" role="group" aria-label="Filtrar por faixa">${filtros.map(([k, r]) => `<button type="button" data-f="${esc(k)}" aria-pressed="${S.filtro === k}">${r}</button>`).join("")}</div>
          <ul class="lista" id="lista" role="listbox" tabindex="0" aria-label="Tickets da fila">${v.map((x, i) => {
            const e = S.estados[x.id];
            return `<li role="option" id="op-${x.id}" data-i="${i}" aria-selected="${i === S.sel}"><span class="lid">#${x.id}</span>${selo(faixaTicket(x).faixa)}<span class="ltexto">${esc(x.texto.slice(0, 80))}</span>${e ? `<span class="lestado">${e.tipo === "confirmado" ? "confirmado" : "corrigido para " + esc(e.categoria)}</span>` : ""}</li>`;
          }).join("")}</ul>
        </div>
        <div class="cartao" id="cartao-ticket">${t ? cartaoTicket(t) : `<p>Nenhum ticket nesta faixa até o dia ${S.dia}. Troque o filtro.</p>`}</div>
      </div>`;
    document.querySelectorAll("#tela-fila .segmentado button").forEach((b) => b.onclick = () => { S.filtro = b.dataset.f; S.sel = 0; render(); });
    const lista = $("#lista");
    lista.onclick = (e) => { const li = e.target.closest("li"); if (li) { S.sel = +li.dataset.i; S.corrigindo = false; render(); $("#lista").focus(); } };
    lista.onkeydown = (e) => {
      if (e.key === "ArrowDown") { S.sel = Math.min(v.length - 1, S.sel + 1); S.corrigindo = false; e.preventDefault(); render(); $("#lista").focus(); }
      else if (e.key === "ArrowUp") { S.sel = Math.max(0, S.sel - 1); S.corrigindo = false; e.preventDefault(); render(); $("#lista").focus(); }
      else if (e.key === "Enter") { decidir(v[S.sel], null); e.preventDefault(); $("#lista").focus(); }
      else if (/^[1-8]$/.test(e.key)) { decidir(v[S.sel], CATS[+e.key - 1]); e.preventDefault(); $("#lista").focus(); }
    };
    if (t) {
      lista.setAttribute("aria-activedescendant", `op-${t.id}`);
      const li = $(`#op-${t.id}`); if (li) li.scrollIntoView({ block: "nearest" });
      $("#bt-confirmar").onclick = () => decidir(t, null);
      $("#bt-corrigir").onclick = () => { S.corrigindo = !S.corrigindo; render(); if (S.corrigindo) $("#sel-cat").focus(); };
      const ap = $("#bt-aplicar"); if (ap) ap.onclick = () => decidir(t, $("#sel-cat").value);
    }
  }
  function cartaoTicket(t) {
    const f = faixaTicket(t), p = pol(), e = S.estados[t.id];
    const td = p.t_decide, ts = p.t_sugere;
    const g = t.p_max >= td ? "IA decide" : t.p_max >= ts ? "IA sugere" : "humano decide";
    const teto = p.por_categoria[t.pred];
    const passos = [
      `Confiança de ${pct(t.p_max)} ${t.p_max >= td ? `≥ limiar de IA decide (${pct(td)})` : t.p_max >= ts ? `entre os limiares (${pct(ts)} e ${pct(td)})` : `abaixo do limiar de sugestão (${pct(ts)})`}: pela confiança, ${g}.`,
      `A fila ${esc(t.pred)} está em ${esc(teto)} na política ${esc(p.nome)}${ORDEM.indexOf(teto) < ORDEM.indexOf(g) ? `, então a decisão é rebaixada para ${esc(teto)}` : ", então a decisão se mantém"}.`,
      "Nenhuma regra de ação se aplica (reembolso e cancelamento sempre vão para humano).",
      S.modo === "sombra" ? `Modo sombra ligado: o ticket vai para humano; o log guarda a faixa real (${esc(f.semSombra)}).` : "Modo sombra desligado.",
    ];
    return `
      <div class="cab-ticket"><span>Ticket #${t.id} · dia ${t.dia} do piloto</span>${e ? `<span>${e.tipo === "confirmado" ? "Confirmado" : "Corrigido para " + esc(e.categoria)}</span>` : ""}</div>
      <p class="texto-ticket">${esc(t.texto)}${t.truncado ? "… (trecho)" : ""}</p>
      <div class="decisao">${selo(f.faixa, ` → ${esc(t.pred)}`, true)}</div>
      <div class="confianca"><span>Confiança do modelo: <strong>${pct(t.p_max)}</strong></span>
        <div class="trilho" role="img" aria-label="Confiança ${pct(t.p_max)}; limiar de sugestão ${pct(ts)}; limiar de decisão ${pct(td)}">
          <div class="enche" style="width:${(100 * t.p_max).toFixed(1)}%"></div>
          <div class="marca" style="left:${(100 * ts).toFixed(1)}%"><span>sugere ${pct(ts, 0)}</span></div>
          <div class="marca" style="left:${(100 * td).toFixed(1)}%"><span>decide ${pct(td, 0)}</span></div></div></div>
      <div class="acoes">
        <button type="button" class="botao primario" id="bt-confirmar">Confirmar</button>
        <button type="button" class="botao" id="bt-corrigir" aria-expanded="${S.corrigindo}">Corrigir</button>
        ${S.corrigindo ? `<label>Para <select id="sel-cat">${CATS.map((c, i) => `<option value="${esc(c)}"${c === t.rotulo_original ? " selected" : ""}>${i + 1}. ${esc(c)}</option>`).join("")}</select></label><button type="button" class="botao" id="bt-aplicar">Aplicar correção</button>` : ""}
      </div>
      ${S.resposta[t.id] ? `<p class="feedback" role="status">${S.resposta[t.id]}</p>` : ""}
      <p class="nota">${INFO}<span>Piloto simulado: a resposta do atendente é o rótulo original do dataset (aqui: ${esc(t.rotulo_original)}), que tem ruído próprio.</span></p>
      <details class="porque"><summary>Por que esta decisão</summary>
        <ol class="passos">${passos.map((s) => `<li>${s}</li>`).join("")}</ol>
        <table class="mini-tabela"><caption class="leitura" style="text-align:left">As duas categorias mais prováveis</caption>
          <tbody>${t.top2.map((x) => `<tr><td>${esc(x.categoria)}</td><td class="dir">${pct(x.p)}</td></tr>`).join("")}</tbody></table>
        <p class="leitura"><strong>Termos que mais pesaram:</strong> ${esc(t.termos)}</p>
        <p class="leitura">Detalhe técnico: modelo ${esc(D.meta.modelo_versao)}, política ${esc(D.meta.politica_versao)}, chave ${esc(chave(t))}.</p>
      </details>`;
  }
  function decidir(t, cat) {
    if (!t) return;
    const corr = cat && cat !== t.pred;
    S.estados[t.id] = corr ? { tipo: "corrigido", categoria: cat } : { tipo: "confirmado" };
    S.log.push({ timestamp_utc: agora(), tipo: corr ? "correcao" : "confirmacao", chave: chave(t), categoria_correta: corr ? cat : t.pred, atendente: "simulado (rótulo original)" });
    S.resposta[t.id] = corr ? `Correção registrada: ${esc(t.pred)} → ${esc(cat)}. Entra no próximo ciclo de avaliação; o modelo não retreina sozinho.` : "Decisão confirmada.";
    S.corrigindo = false;
    render();
  }

  // ---- tela 3
  function barraIC(c) {
    const lo = 0.85, hi = 1, x = (v) => 4 + Math.max(0, Math.min(1, (v - lo) / (hi - lo))) * 232;
    const mI = D.meta.meta_ia_decide, mS = D.meta.meta_ia_sugere;
    const ic = c.li == null ? "" : `<rect x="${x(c.li)}" y="11" width="${Math.max(2, x(c.ls) - x(c.li))}" height="10" rx="5" fill="#0369A1" opacity=".25"/><circle cx="${x(c.precisao)}" cy="16" r="5" fill="#0369A1"/>`;
    return `<svg class="barra-ic" viewBox="0 0 240 34" role="img" aria-label="Precisão ${pct(c.precisao)}, intervalo ${pct(c.li)} a ${pct(c.ls)}; metas ${pct(mS)} e ${pct(mI)}">
      <rect x="4" y="15" width="232" height="2" fill="#E2E8F0" stroke="none"/>${ic}
      <line x1="${x(mS)}" x2="${x(mS)}" y1="6" y2="26" stroke="#B45309" stroke-width="2"/>
      <line x1="${x(mI)}" x2="${x(mI)}" y1="6" y2="26" stroke="#0F766E" stroke-width="2"/>
      <text x="${x(mS) - 3}" y="33" font-size="8" text-anchor="end" fill="#B45309" stroke="none">sugere</text>
      <text x="${x(mI) + 3}" y="33" font-size="8" fill="#0F766E" stroke="none">decide</text></svg>`;
  }
  function telaGov() {
    const g = gov(), p = pol();
    $("#tela-governanca").innerHTML = `
      <h1 class="pergunta" id="h-governanca">Por que a IA não decide tudo?</h1>
      <p class="subtitulo">Cada fila só é automatizada quando a precisão comprovada supera a meta humana.</p>
      <div class="cartao">
        <div class="tab-gov-envelope"><table class="tab-gov"><caption class="leitura" style="text-align:left;margin:0 0 12px">Precisão de cada fila contra as metas (ponto: precisão; faixa clara: intervalo de 95%; traços: metas de sugestão e de decisão). Dia ${S.dia} do piloto.</caption>
          <thead><tr><th scope="col">Fila</th><th scope="col" class="col-politica">Política</th><th scope="col">Precisão comprovada</th><th scope="col">Regra</th></tr></thead>
          <tbody>${CATS.map((c) => {
            const k = g.categorias[c], r = regraVs(p.por_categoria[c], k.decisao_regra);
            return `<tr tabindex="0" data-cat="${esc(c)}" title="${esc(c)}: ${num(k.n_sombra)} tickets, ${pct(k.precisao)} de precisão, intervalo ${pct(k.li)}–${pct(k.ls)}">
              <td class="nome">${esc(c)}</td><td class="col-politica">${selo(p.por_categoria[c])}</td><td>${barraIC(k)}</td>
              <td><span class="decisao-regra ${r.cls}">${r.txt}</span></td></tr>`;
          }).join("")}</tbody></table></div>
        <p class="leitura">O que esta tabela diz: só as filas cujo intervalo inteiro fica à direita do traço de decisão são automáticas. Clique numa fila para ver a evolução e o dia do piloto.</p>
      </div>`;
    document.querySelectorAll("#tela-governanca tbody tr").forEach((tr) => {
      tr.onclick = () => abrirPainel(tr.dataset.cat, tr);
      tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrirPainel(tr.dataset.cat, tr); } };
    });
  }
  function frase(cat) {
    const k = gov().categorias[cat], vig = pol().por_categoria[cat], regra = k.decisao_regra;
    const mI = D.meta.meta_ia_decide, mS = D.meta.meta_ia_sugere;
    if (k.li == null) return `${cat}: ainda sem tickets com confiança suficiente para medir.`;
    const base = `${cat}: ${pct(k.precisao)} de precisão`;
    const d = ORDEM.indexOf(regra) - ORDEM.indexOf(vig);
    if (d < 0) return `${base}, mas o limite inferior (${pct(k.li)}) ficou abaixo da meta de ${vig === "IA decide" ? `decisão (${pct(mI)})` : `sugestão (${pct(mS)})`}. A regra rebaixaria para ${regra}; a política vigente mantém ${vig} até a decisão do supervisor.`;
    if (d > 0) return `${base}, e o limite inferior (${pct(k.li)}) já supera a meta de ${regra === "IA decide" ? `decisão (${pct(mI)})` : `sugestão (${pct(mS)})`}. Pode subir para ${regra} se se mantiver até o fim do piloto.`;
    if (regra === "humano decide") return `${base}, mas o limite inferior (${pct(k.li)}) não alcança a meta de sugestão (${pct(mS)}). Continua com humano.`;
    if (regra === "IA sugere") return `${base}; o limite inferior (${pct(k.li)}) fica entre a meta de sugestão (${pct(mS)}) e a de decisão (${pct(mI)}). Continua com sugestão e confirmação humana.`;
    return `${base}; o limite inferior (${pct(k.li)}) supera a meta de decisão (${pct(mI)}). Continua automática.`;
  }
  function grafico(cat) {
    const W = 460, H = 200, L = 40, R = 12, T = 12, B = 26, lo = 0.85, hi = 1;
    const x = (d) => L + (d - 1) / 19 * (W - L - R), y = (v) => T + (1 - (Math.max(lo, v) - lo) / (hi - lo)) * (H - T - B);
    const pts = D.governanca.map((g) => [g.dia, g.categorias[cat].li]).filter((p) => p[1] != null);
    const mI = D.meta.meta_ia_decide, mS = D.meta.meta_ia_sugere, atual = gov().categorias[cat].li;
    return `<svg class="grafico" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="graf-t">
      ${[0.85, 0.9, 0.95, 1].map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="#E2E8F0" stroke-width="1"/><text x="${L - 6}" y="${y(v) + 4}" font-size="11" text-anchor="end" fill="#475569" stroke="none">${pct(v, 0)}</text>`).join("")}
      <line x1="${L}" x2="${W - R}" y1="${y(mI)}" y2="${y(mI)}" stroke="#0F766E" stroke-dasharray="5 4" stroke-width="1.5"/>
      <text x="${W - R}" y="${y(mI) - 5}" font-size="11" text-anchor="end" fill="#0F766E" stroke="none">meta de decisão ${pct(mI)}</text>
      <line x1="${L}" x2="${W - R}" y1="${y(mS)}" y2="${y(mS)}" stroke="#B45309" stroke-dasharray="5 4" stroke-width="1.5"/>
      <text x="${W - R}" y="${y(mS) + 14}" font-size="11" text-anchor="end" fill="#B45309" stroke="none">meta de sugestão ${pct(mS)}</text>
      <line x1="${x(S.dia)}" x2="${x(S.dia)}" y1="${T}" y2="${H - B}" stroke="#94A3B8" stroke-dasharray="2 3"/>
      <path d="${pts.map((p, i) => `${i ? "L" : "M"}${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join("")}" stroke="#0F172A" stroke-width="2"/>
      ${atual != null ? `<circle cx="${x(S.dia)}" cy="${y(atual)}" r="4.5" fill="#0F172A" stroke="#fff" stroke-width="2"/><text x="${Math.min(x(S.dia) + 8, W - 60)}" y="${y(atual) + 16}" font-size="12" font-weight="600" fill="#0F172A" stroke="none">${pct(atual)}</text>` : ""}
      <text x="${L}" y="${H - 6}" font-size="11" fill="#475569" stroke="none">dia 1</text><text x="${W - R}" y="${H - 6}" font-size="11" text-anchor="end" fill="#475569" stroke="none">dia 20</text></svg>`;
  }
  function renderPainel() {
    const cat = S.painelCat, k = gov().categorias[cat], vig = pol().por_categoria[cat];
    $("#painel").innerHTML = `
      <div class="topo"><div><h2 id="painel-titulo">${esc(cat)}</h2><p class="leitura">Política vigente: ${selo(vig)}</p></div>
        <button type="button" class="fechar-x" id="fechar-painel" aria-label="Fechar painel (Esc)">${X}</button></div>
      <p class="frase">${esc(frase(cat))}</p>
      <h3 id="graf-t" style="font-size:16px;margin:16px 0 4px">O limite inferior já alcançou a meta?</h3>
      ${grafico(cat)}
      <p class="leitura">O que este gráfico diz: a linha é o pior caso plausível da precisão (limite inferior de 95%), acumulado dia a dia. A fila só sobe de faixa quando a linha passa da meta tracejada.</p>
      <div class="controle-dia"><label for="dia">Dia do piloto</label><input id="dia" type="range" min="1" max="20" value="${S.dia}"><strong>${S.dia}</strong></div>
      <p class="leitura">${num(k.n_sombra)} tickets com confiança acima do limiar até o dia ${S.dia}; ${num(k.acertos)} acertos; intervalo de ${pct(k.li)} a ${pct(k.ls)}.</p>`;
    $("#fechar-painel").onclick = fecharPainel;
    $("#dia").oninput = (e) => { S.dia = +e.target.value; render(); $("#dia").focus(); };
  }
  function abrirPainel(cat, origem) {
    S.painelCat = cat; S.focoAntes = origem || document.activeElement;
    $("#painel").hidden = false; $("#veu").hidden = false;
    renderPainel(); $("#fechar-painel").focus();
  }
  function fecharPainel() {
    S.painelCat = null; $("#painel").hidden = true; $("#veu").hidden = true;
    render();
    if (S.focoAntes && document.body.contains(S.focoAntes)) S.focoAntes.focus();
  }
  $("#veu").onclick = fecharPainel;
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && S.painelCat) fecharPainel(); });

  // ---- tela 4
  function telaRobustez() {
    const r = S.r, t = D.fila.find((x) => x.id === r.ticket);
    const a = D.ataques[String(r.ticket)][r.ataque];
    const dn = D.kpis.dano_injecao;
    const lado = (pk) => {
      const fa = a.faixas[pk], troca = a.pred !== t.pred;
      const veredito = troca && fa === "IA decide" ? `<span class="ruim">Dano silencioso:</span> a fila mudou para ${esc(a.pred)} e ninguém confere.`
        : troca ? `<span class="bom">Contido:</span> a fila mudou para ${esc(a.pred)}, mas um humano confere (${esc(fa)}).` : `<span class="bom">Sem efeito:</span> a fila continua ${esc(a.pred)}.`;
      return `<div><h4>${esc(D.politicas[pk].nome)}</h4>${selo(fa, ` → ${esc(a.pred)}`)}<p class="resultado">${veredito}</p>
        <p class="fonte-num">Em ${num(dn[pk].n_pares)} ataques simulados: ${num(dn[pk].silenciosos)} com dano silencioso (f5_injecao.json).</p></div>`;
    };
    const reemb = D.fila.filter((x) => x.faixas.F9.faixa === "IA decide").sort((p, q) => q.p_max - p.p_max)[0];
    const cob = (pk) => { const fx = gov().faixas[pk]; return fx["IA decide"].n / gov().n_total; };
    const base = gov().faixas[S.pol]["IA decide"].n / gov().n_total;
    const ultimoLog = S.log.length ? JSON.stringify(S.log[S.log.length - 1]) : "";
    $("#tela-robustez").innerHTML = `
      <h1 class="pergunta" id="h-robustez">O que acontece se…?</h1>
      <p class="subtitulo">Cinco testes de estresse. Cada um roda com dados reais do piloto e mostra o resultado e a fonte.</p>
      <div class="cenarios">
        <article class="cartao cenario" style="grid-column:1 / -1"><h3>…alguém tentar enganar a IA?</h3>
          <p class="leitura">Um texto malicioso é colado no fim do ticket para empurrar a classificação. Compare a política de seleção (F8) com a implantada (F9).</p>
          <div class="controles">
            <label>Ataque <select id="r-ataque">${D.ataques_modelos.map((m) => `<option value="${esc(m.id)}"${m.id === r.ataque ? " selected" : ""}>${esc(m.id.replace(/_/g, " "))}</option>`).join("")}</select></label>
            <label>Ticket <select id="r-ticket">${D.fila.map((x) => `<option value="${x.id}"${x.id === r.ticket ? " selected" : ""}>#${x.id}</option>`).join("")}</select></label>
            <button type="button" class="botao primario" id="r-rodar-ataque">Rodar ataque</button></div>
          ${r.rodouAtaque ? `<p class="resultado">Sem ataque, o ticket #${t.id} vai para ${esc(t.pred)} com ${pct(t.p_max)} de confiança. Com o ataque "${esc(r.ataque.replace(/_/g, " "))}" (alvo: ${esc(a.alvo)}), o modelo responde ${esc(a.pred)} com ${pct(a.p_max)}.</p><div class="lado-a-lado">${lado("F8")}${lado("F9")}</div>` : ""}
        </article>
        <article class="cartao cenario"><h3>…o webhook entregar duas vezes?</h3>
          <p class="leitura">O mesmo evento chega de novo, com o mesmo identificador.</p>
          <div class="controles"><button type="button" class="botao" id="r-rodar-dup">Reentregar o evento</button></div>
          ${r.rodouDup ? `<p class="resultado"><span class="bom">Duplicado, nenhuma nova decisão.</span> A chave já estava reservada (mesma lógica de triagem.py, testada em test_f8.py).</p><p class="fonte-num"><code>${esc(r.linhaDup)}</code></p>` : ""}
        </article>
        <article class="cartao cenario"><h3>…o ticket for um reembolso?</h3>
          <p class="leitura">Ticket #${reemb.id}, com ${pct(reemb.p_max)} de confiança em ${esc(reemb.pred)}, marcado como pedido de reembolso.</p>
          <div class="controles"><button type="button" class="botao" id="r-rodar-reembolso">Marcar como reembolso</button></div>
          ${r.rodouReembolso ? `<p class="resultado">Antes: ${selo("IA decide")} → Depois: ${selo("humano decide")}</p><p class="leitura">Regra de ação: reembolso e cancelamento movimentam dinheiro e são difíceis de reverter; vão para humano mesmo com confiança alta.</p>` : ""}
        </article>
        <article class="cartao cenario"><h3>…precisarmos desligar a IA agora?</h3>
          <p class="leitura">O modo sombra manda tudo para humano e continua registrando o que a IA teria feito. É o rollback imediato.</p>
          <div class="controles"><label class="chave"><input type="checkbox" id="r-sombra" ${S.modo === "sombra" ? "checked" : ""}> Modo sombra ${S.modo === "sombra" ? "ligado" : "desligado"}</label></div>
          ${S.modo === "sombra" ? `<p class="resultado"><span class="ruim">Alerta disparado:</span> a cobertura de IA decide caiu de ${pct(base)} para ${pct(0)}. O log continua, com a faixa real em <code>faixa_sem_sombra</code>.</p>${ultimoLog ? `<p class="fonte-num"><code>${esc(ultimoLog)}</code></p>` : ""}` : ""}
        </article>
        <article class="cartao cenario"><h3>…uma política nova for pior?</h3>
          <p class="leitura">Troque a política e veja o efeito. Voltar para a F9 é o rollback.</p>
          <div class="controles"><div class="segmentado" role="group" aria-label="Política">${["F9", "F8", "F4"].map((k) => `<button type="button" data-pol="${k}" aria-pressed="${S.pol === k}">${esc(D.politicas[k].nome)}</button>`).join("")}</div></div>
          <p class="resultado">Com ${esc(pol().nome)}: a IA decide sozinha em <strong>${pct(cob(S.pol))}</strong> dos tickets; ${dn[S.pol].silenciosos ? `<span class="ruim">${num(dn[S.pol].silenciosos)} de ${num(dn[S.pol].n_pares)} ataques passam sem humano</span>` : `<span class="bom">0 de ${num(dn[S.pol].n_pares)} ataques passam sem humano</span>`}.</p>
          <p class="fonte-num">Fontes: governança do dia ${S.dia} (data.js) e f5_injecao.json.</p>
        </article>
        <details class="log"><summary>Log da tela (${num(S.log.length)} linhas, mesmos campos de decisoes.jsonl, sem texto)</summary><pre>${esc(S.log.map((l) => JSON.stringify(l)).join("\n"))}</pre></details>
      </div>`;
    $("#r-ataque").onchange = (e) => { r.ataque = e.target.value; r.rodouAtaque = false; render(); };
    $("#r-ticket").onchange = (e) => { r.ticket = +e.target.value; r.rodouAtaque = false; render(); };
    $("#r-rodar-ataque").onclick = () => { r.rodouAtaque = true; render(); };
    $("#r-rodar-dup").onclick = () => { r.linhaDup = JSON.stringify(reentregar(t)); r.rodouDup = true; render(); };
    $("#r-rodar-reembolso").onclick = () => { r.rodouReembolso = true; S.log.push({ timestamp_utc: agora(), chave: chave(reemb), event_id: `fila-${reemb.id}`, categoria: reemb.pred, p_max: reemb.p_max, faixa: "humano decide", faixa_sem_sombra: "humano decide", motivo: "regra de ação: Refund request; termos: " + reemb.termos, modelo_versao: D.meta.modelo_versao, politica_versao: D.meta.politica_versao, latencia_ms: null, erro: null }); render(); };
    $("#r-sombra").onchange = (e) => {
      S.modo = e.target.checked ? "sombra" : "ativo";
      if (S.modo === "sombra") { const f = faixaTicket(t); S.log.push({ timestamp_utc: agora(), chave: chave(t), event_id: `fila-${t.id}`, categoria: t.pred, p_max: t.p_max, faixa: "humano decide", faixa_sem_sombra: f.semSombra, motivo: "modo sombra", modelo_versao: D.meta.modelo_versao, politica_versao: D.meta.politica_versao, latencia_ms: null, erro: null }); }
      render(); $("#r-sombra").focus();
    };
    document.querySelectorAll("#tela-robustez [data-pol]").forEach((b) => b.onclick = () => { S.pol = b.dataset.pol; render(); });
  }

  irPara(location.hash.slice(1) || "saude");
})();
