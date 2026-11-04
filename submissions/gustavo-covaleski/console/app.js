"use strict";
// Console do piloto (F12): implementação das pranchas aprovadas em planning/F12-design.
// Todo número vem de window.DADOS (console/data.js, gerado por solution/f10_console_dados.py).
(function () {
  const D = window.DADOS;
  const CATS = D.meta.categorias;
  const ORDEM = ["humano decide", "IA sugere", "IA decide"];
  const POL = { F9: "Atual", F8: "Sem confirmação no teste", F4: "Inicial" };
  const ATAQUE = { categoria_repetida: "Repetição de categoria", ignore_instrucoes: "Ignorar instruções",
    falsa_mensagem_sistema: "Falsa mensagem de sistema", json_pronto: "JSON pronto", portugues: "Ordem em português" };
  const CEN = [
    ["injecao", "Injeção de instrução", "5 ataques versionados"],
    ["duplicado", "Evento duplicado", "Reentrega do webhook"],
    ["reembolso", "Regra de reembolso", "Tipo sensível vai para humano"],
    ["sombra", "Modo sombra", "Desligamento imediato"],
    ["politica", "Troca de política", "Rollback para a versão anterior"],
  ];
  const FX = {
    "IA decide": { cls: "decide", nome: "IA decide", curto: "IA decide", barra: "#0F7B6C", grande: "IA decide · sem revisão" },
    "IA sugere": { cls: "sugere", nome: "IA sugere", curto: "IA sugere", barra: "#D98A1E", grande: "IA sugere · revisão humana" },
    "humano decide": { cls: "humano", nome: "Humano decide", curto: "Humano", barra: "#7A8699", grande: "Humano decide · triagem manual" },
  };
  const META_D = D.meta.meta_ia_decide, META_S = D.meta.meta_ia_sugere;
  const TICKET_REEMBOLSO = 22129;
  // prancha MobileVisao: rótulos dos gráficos a 22 no viewBox de 600 para ficarem legíveis a 390 px
  const FS = () => (window.matchMedia("(max-width: 767px)").matches ? 22 : 11);

  const pct = (x, d = 1) => x == null || !isFinite(x) ? "—" : new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: d, maximumFractionDigits: d }).format(x);
  const num = (x) => new Intl.NumberFormat("pt-BR").format(x);
  const brl = (x) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(x);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  function wilson(k, n) {
    if (!n) return [null, null];
    const z = 1.959964, p = k / n, c = (p + z * z / (2 * n)) / (1 + z * z / n);
    const m = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n);
    return [c - m, c + m];
  }

  // ícones (SVG de traço, como nas pranchas)
  const sv = (d, w = 20, extra = "") => `<svg class="ic" aria-hidden="true" width="${w}" height="${w}" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"${extra}>${d}</svg>`;
  const IC = {
    marca: '<path d="M3 6h14M6 10h8M9 14h2"/>',
    info: '<circle cx="10" cy="10" r="8"/><path d="M10 9v5M10 6.5v.2"/>',
    alerta: '<path d="M10 3l8 14H2z"/><path d="M10 8v4M10 14.5v.2"/>',
    olho: '<path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z"/><circle cx="10" cy="10" r="2.5"/>',
    check: '<path d="M4 10l4 4 8-8"/>',
    pessoa: '<circle cx="10" cy="7" r="3"/><path d="M4 17c1-3 3-5 6-5s5 2 6 5"/>',
    x: '<path d="M5 5l10 10M15 5L5 15"/>',
    voltar: '<path d="M12 4l-6 6 6 6"/>',
    visao: '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="11" y="3" width="6" height="6" rx="1"/><rect x="3" y="11" width="6" height="6" rx="1"/><rect x="11" y="11" width="6" height="6" rx="1"/>',
    fila: '<path d="M3 12l2-7h10l2 7v4H3z"/><path d="M3 12h4l1 2h4l1-2h4"/>',
    gov: '<path d="M10 2l7 3v5c0 4-3 7-7 8-4-1-7-4-7-8V5z"/>',
    rob: '<path d="M2 10h4l2-5 4 10 2-5h4"/>',
  };
  const ICFX = { "IA decide": IC.check, "IA sugere": IC.olho, "humano decide": IC.pessoa };
  const selo = (f, texto, grande = false) => `<span class="selo ${FX[f].cls}${grande ? " grande" : ""}">${grande ? sv(ICFX[f], 16) : ""}${esc(texto || FX[f].nome)}</span>`;

  // ---- estado global
  const S = {
    tela: "visao", sub: null, modo: "ativo", pol: "F9", dia: 20, premissas: { ...D.kpis.premissas },
    filtro: "todas", busca: "", estados: {}, feedback: {}, corrigindo: false,
    log: [], chaves: new Set(), duplicados: 0,
    inj: { ataque: "categoria_repetida", ticket: 10244, executado: true },
    dupRodou: null, reembolsoRodou: false, sobreAberto: false,
  };
  const celular = window.matchMedia("(max-width: 767px)");

  // ---- dados derivados
  const gov = () => D.governanca[S.dia - 1];
  const politica = () => D.politicas[S.pol];
  function faixas(polK = S.pol, dia = S.dia) {
    const g = D.governanca[dia - 1], fx = g.faixas[polK];
    if (S.modo === "sombra") return { n: g.n_total, d: { n: 0, a: 0 }, s: { n: 0, a: 0 }, h: { n: g.n_total, a: fx["IA decide"].acertos + fx["IA sugere"].acertos + fx["humano decide"].acertos } };
    return { n: g.n_total, d: { n: fx["IA decide"].n, a: fx["IA decide"].acertos }, s: { n: fx["IA sugere"].n, a: fx["IA sugere"].acertos }, h: { n: fx["humano decide"].n, a: fx["humano decide"].acertos } };
  }
  function faixaTicket(t) {
    const base = t.faixas[S.pol].faixa;
    return { faixa: S.modo === "sombra" ? "humano decide" : base, semSombra: base };
  }
  function acaoRegra(vig, regra) {
    if (!regra) return { txt: "—", cor: "var(--texto-3)" };
    const d = ORDEM.indexOf(regra) - ORDEM.indexOf(vig);
    if (d > 0) return { txt: "Promover", cor: "var(--decide-tx)" };
    // queda numa fila automática é rebaixamento; numa fila com sugestão, o humano ainda revisa
    if (d < 0) return vig === "IA decide" ? { txt: "Rebaixar", cor: "var(--dano)" } : { txt: "Revisar", cor: "var(--sugere-tx)" };
    return { txt: "Manter", cor: "var(--texto-3)" };
  }
  function alertas() {
    const out = [], g = gov(), p = politica();
    if (S.modo === "sombra") out.push({ html: "<strong>Modo sombra</strong> ligado: automação suspensa; todos os tickets vão para triagem humana.", link: "#robustez/sombra", rot: "Ver cenário" });
    const dn = D.kpis.dano_injecao[S.pol];
    if (dn.silenciosos > 0) out.push({ html: `<strong>Política ${esc(POL[S.pol].toLowerCase())}</strong>: ${num(dn.silenciosos)} de ${num(dn.n_pares)} injeções passam sem revisão.`, link: "#robustez/politica", rot: "Ver cenário" });
    if (S.duplicados) out.push({ html: `<strong>${num(S.duplicados)} reentrega(s)</strong> descartada(s) como duplicada(s), sem nova decisão.`, link: "#robustez/duplicado", rot: "Ver cenário" });
    CATS.forEach((c) => {
      const k = g.categorias[c], vig = p.por_categoria[c];
      if (ORDEM.indexOf(k.decisao_regra) < ORDEM.indexOf(vig)) {
        const decide = vig === "IA decide";
        out.push({ html: `<strong>${esc(c)}</strong> abaixo da meta de ${decide ? "decisão" : "sugestão"}: limite inferior ${pct(k.li)} (meta ${pct(decide ? META_D : META_S)}, n = ${num(k.n_sombra)}).`, link: `#governanca/${encodeURIComponent(c)}`, rot: "Revisar fila" });
      }
    });
    return out;
  }

  // ---- log e idempotência (mesma chave de triagem.py: evt:<event_id>; ver solution/tests/test_f8.py)
  const agora = () => new Date().toISOString();
  const chave = (t) => `evt:fila-${t.id}`;
  function linhaDecisao(t, faixa, semSombra, motivo) {
    return { timestamp_utc: agora(), chave: chave(t), event_id: `fila-${t.id}`, categoria: t.pred, p_max: t.p_max, faixa,
      faixa_sem_sombra: semSombra, motivo, modelo_versao: D.meta.modelo_versao, politica_versao: D.meta.politica_versao, latencia_ms: null, erro: null };
  }
  function registrar(t) {
    if (S.chaves.has(chave(t))) return;
    S.chaves.add(chave(t));
    const f = faixaTicket(t);
    S.log.push(linhaDecisao(t, f.faixa, f.semSombra, "termos: " + t.termos));
  }
  function reentregar(t) {
    registrar(t);
    S.duplicados += 1;
    const l = { tipo: "duplicado", chave: chave(t), timestamp_utc: agora() };
    S.log.push(l);
    return l;
  }

  // ---- roteamento
  function lerHash() {
    const [tela, ...resto] = location.hash.replace(/^#/, "").split("/");
    S.tela = ["visao", "fila", "governanca", "robustez"].includes(tela) ? tela : "visao";
    S.sub = resto.length ? decodeURIComponent(resto.join("/")) : null;
    S.corrigindo = false;
    render();
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", lerHash);
  celular.addEventListener("change", () => render());

  // ---- cabeçalho e navegação
  const ABAS = [["visao", "Visão geral", IC.visao], ["fila", "Fila", IC.fila], ["governanca", "Governança", IC.gov], ["robustez", "Robustez", IC.rob]];
  function renderTopo() {
    const t = S.tela === "fila" && celular.matches && S.sub ? ticketPorId(S.sub) : null;
    if (t) {
      const f = faixaTicket(t).faixa, n = visiveis().filter((x) => faixaTicket(x).faixa === f).length;
      $("#topo").innerHTML = `<div class="topo-int"><a class="voltar" href="#fila" aria-label="Voltar para a fila">${sv(IC.voltar)}</a>
        <span class="mono" style="font-size:16px;font-weight:500">#${t.id}</span>
        <span class="status" style="font-size:12px;color:#9FB0C8">${num(n)} em ${esc(FX[f].nome)}</span></div>`;
      return;
    }
    $("#topo").innerHTML = `<div class="topo-int">
      <div class="marca"><span class="marca-ico">${sv(IC.marca, 16, ' stroke="#FFFFFF" stroke-width="2"')}</span><span class="marca-nome">Triagem</span><span class="marca-sub">Piloto</span></div>
      <nav class="abas" aria-label="Seções">${ABAS.map(([k, r]) => `<a class="aba" href="#${k}"${S.tela === k ? ' aria-current="page"' : ""}>${r}</a>`).join("")}</nav>
      <div class="status">
        <span class="chip-status chip-modo"><span class="ponto-modo${S.modo === "sombra" ? " sombra" : ""}"></span>${S.modo === "sombra" ? "Modo sombra" : "Modo ativo"}</span>
        <span class="chip-status">${celular.matches ? `<span class="ponto-modo${S.modo === "sombra" ? " sombra" : ""}"></span>Dia ${S.dia}` : `Dia ${S.dia} de 20`}</span>
        <button type="button" class="botao-info" id="abrir-sobre" aria-label="Sobre os dados">${sv(IC.info, 18)}</button>
      </div></div>`;
    $("#abrir-sobre").onclick = abrirSobre;
  }
  function renderNav() {
    $("#nav-inferior").innerHTML = ABAS.map(([k, r, ic]) => `<a href="#${k}"${S.tela === k ? ' aria-current="page"' : ""}>${sv(ic, 22)}${r}</a>`).join("");
  }

  function render() {
    document.body.classList.toggle("com-acao", false);
    $("#barra-acao").hidden = true;
    renderTopo(); renderNav();
    ({ visao: telaVisao, fila: telaFila, governanca: telaGov, robustez: telaRob })[S.tela]();
    if (S.sobreAberto) renderSobre();
  }

  // ---- visão geral
  function telaVisao() {
    const f = faixas(), al = alertas(), p = politica(), g = gov();
    const [li, ls] = wilson(f.d.a, f.d.n), precD = f.d.n ? f.d.a / f.d.n : null, precS = f.s.n ? f.s.a / f.s.n : null, precH = f.h.n ? f.h.a / f.h.n : null;
    const dn = D.kpis.dano_injecao[S.pol];
    const kpis = [
      ["Automação", pct(f.d.n / f.n), `${num(f.d.n)} de ${num(f.n)} tickets sem triagem humana`, "var(--decide)", pct(f.d.n / f.n, 2)],
      ["Precisão da automação", pct(precD), f.d.n ? `Meta ≥ ${pct(META_D)} · IC 95% ${pct(li).replace("%", "")}–${pct(ls)}` : "Sem tickets na faixa IA decide", "var(--texto)", pct(precD, 2)],
      ["Sugestão com revisão", pct(f.s.n / f.n), `${num(f.s.n)} tickets · precisão ${pct(precS)}`, "var(--sugere-tx)", pct(f.s.n / f.n, 2)],
      ["Injeções sem revisão", num(dn.silenciosos), `de ${num(dn.n_pares)} tentativas`, dn.silenciosos ? "var(--dano)" : "var(--texto)", `${num(dn.silenciosos)} de ${num(dn.n_pares)}`],
    ];
    const linhas = [["IA decide", "IA decide", f.d, precD], ["IA sugere", "IA sugere, humano confirma", f.s, precS], ["humano decide", "Humano decide", f.h, precH]];
    const grupos = ["IA decide", "IA sugere", "humano decide"].map((fx) => ({ fx, cats: CATS.filter((c) => p.por_categoria[c] === fx) }));
    const alertaCats = new Set(al.filter((a) => a.link.startsWith("#governanca/")).map((a) => decodeURIComponent(a.link.split("/")[1])));
    $("#conteudo").innerHTML = `
      <div class="cab-tela"><div><h1 class="titulo">Visão geral</h1><p class="subtitulo">${num(g.n_total)} tickets triados · holdout por grupo</p></div>
        <a class="botao primario" href="#fila">Abrir a fila</a></div>
      ${al.map((a) => `<div class="alerta" role="status"><span style="color:var(--sugere-tx);display:flex">${sv(IC.alerta, 18)}</span><span class="alerta-tx">${a.html}</span><a class="link-forte" href="${a.link}">${a.rot}</a></div>`).join("")}
      <section class="kpis" aria-label="Indicadores">${kpis.map(([r, v, d, c, exato]) => `<div class="kpi"><span class="kpi-rot">${r}</span><span class="kpi-val" style="color:${c}" title="${esc(exato)}" data-exato="${esc(exato)}">${v}</span><span class="kpi-det">${d}</span></div>`).join("")}</section>
      <section class="duas-col">
        <div class="cartao col-7">
          <div class="cartao-cab"><h2 class="h2">Distribuição por faixa</h2><span class="legenda">% do volume · precisão contra o rótulo</span></div>
          <div class="barra-faixas" role="img" aria-label="IA decide ${pct(f.d.n / f.n)}, IA sugere ${pct(f.s.n / f.n)}, humano decide ${pct(f.h.n / f.n)}">${linhas.map(([k, , x]) => x.n ? `<div style="width:${(100 * x.n / f.n).toFixed(2)}%;background:${FX[k].barra}"></div>` : "").join("")}</div>
          <div>${linhas.map(([k, nome, x, pr]) => `<div class="linha-faixa"><span class="nome"><span class="quad" style="background:${FX[k].barra}"></span><span>${nome}</span></span><span class="dir" style="font-weight:600">${pct(x.n / f.n)}</span><span class="dir mono n-col" style="color:var(--texto-2)">${num(x.n)}</span><span class="dir">${pct(pr)}</span></div>`).join("")}</div>
        </div>
        <div class="cartao col-5">
          <div class="cartao-cab"><h2 class="h2">Precisão da automação por dia</h2><span class="legenda">acumulada · faixa IA decide</span></div>
          ${graficoPrecisao()}
        </div>
      </section>
      <section class="cartao" style="display:flex;flex-direction:column;gap:16px">
        <div class="cartao-cab"><h2 class="h2">Filas por política</h2><a class="link-forte" style="font-weight:500" href="#governanca">Ver governança</a></div>
        <div class="grupos">${grupos.map((gr) => `<div class="grupo">${selo(gr.fx, `${FX[gr.fx].nome} · ${gr.cats.length}`)}${gr.cats.map((c) => `<div class="grupo-fila"><span style="font-weight:500">${esc(c)}${alertaCats.has(c) ? '<span class="revisar"> · revisar</span>' : ""}</span><span style="color:var(--texto-2)">${pct(g.categorias[c].precisao)}</span></div>`).join("") || '<span class="legenda">Nenhuma fila</span>'}</div>`).join("")}</div>
      </section>
      <p class="nota">Dados: holdout do DS2 (TI interna). Correção do atendente simulada pelo rótulo original. Fontes em <span class="mono">solution/outputs/</span>.</p>`;
  }
  function graficoPrecisao() {
    if (S.modo === "sombra") return '<p class="legenda">Modo sombra: nenhuma decisão automática no período.</p>';
    const pts = D.governanca.map((g) => { const x = g.faixas[S.pol]["IA decide"]; return x.n ? x.acertos / x.n : null; });
    const minimo = Math.min(...pts.filter((v) => v != null), META_D);
    const lo = Math.min(0.96, Math.floor((minimo - 0.002) * 100) / 100), hi = 1;
    const y = (v) => 8 + (hi - v) / (hi - lo) * 160, x = (i) => 40 + i * (560 / 19);
    const ticks = [hi, (hi + lo) / 2, lo];
    const linha = pts.map((v, i) => v == null ? "" : `${x(i).toFixed(1)},${y(v).toFixed(1)}`).filter(Boolean).join(" ");
    const g = D.governanca[S.dia - 1].faixas[S.pol]["IA decide"], [li, ls] = wilson(g.acertos, g.n), pd = g.n ? g.acertos / g.n : null;
    return `<svg class="grafico" role="img" aria-label="Precisão acumulada da automação por dia; dia ${S.dia}: ${pct(pd)}; meta ${pct(META_D)}" viewBox="0 -16 600 216">
      <g font-family="IBM Plex Sans, sans-serif" font-size="${FS()}" fill="#5F6B7A">${ticks.map((v) => `<text x="0" y="${(y(v) + 4).toFixed(1)}">${pct(v, 0)}</text>`).join("")}</g>
      ${ticks.map((v) => `<line x1="40" y1="${y(v)}" x2="600" y2="${y(v)}" stroke="#EEF1F5"/>`).join("")}
      <line x1="40" y1="${y(META_D)}" x2="600" y2="${y(META_D)}" stroke="#B42318" stroke-dasharray="5 4" stroke-width="1.5"/>
      <text x="596" y="${y(META_D) - 6}" text-anchor="end" font-family="IBM Plex Sans, sans-serif" font-size="${FS()}" fill="#B42318">meta ${pct(META_D)}</text>
      <polyline fill="none" stroke="#0F7B6C" stroke-width="2.5" stroke-linejoin="round" points="${linha}"/>
      ${pd != null ? `<circle cx="${x(S.dia - 1)}" cy="${y(pd)}" r="4" fill="#0F7B6C"/>` : ""}
      <g font-family="IBM Plex Sans, sans-serif" font-size="${FS()}" fill="#5F6B7A"><text x="40" y="194">dia 1</text><text x="600" y="194" text-anchor="end">dia 20</text></g></svg>
      <p class="nota" style="font-size:13px">Dia ${S.dia}: <strong style="color:var(--texto);font-weight:600" data-exato="${esc(pct(pd, 2))}">${pct(pd)}</strong> · IC 95% ${pct(li).replace("%", "")}–${pct(ls)}</p>`;
  }

  // ---- fila
  const ticketPorId = (id) => D.fila.find((t) => String(t.id) === String(id).replace(/^#/, ""));
  const doDia = () => D.fila.filter((t) => t.dia <= S.dia);
  function visiveis() {
    const q = S.busca.trim().toLowerCase().replace(/^#/, "");
    return doDia().filter((t) => (S.filtro === "todas" || faixaTicket(t).faixa === S.filtro)
      && (!q || String(t.id).startsWith(q) || t.texto.toLowerCase().includes(q) || t.pred.toLowerCase().includes(q)));
  }
  function telaFila() {
    const base = doDia();
    base.forEach(registrar);
    const cont = (f) => base.filter((t) => faixaTicket(t).faixa === f).length;
    const v = visiveis();
    const sel = (S.sub && ticketPorId(S.sub)) || v[0];
    const soDetalhe = celular.matches && S.sub && sel;
    const soLista = celular.matches && !S.sub;
    const filtros = [["todas", `Todos ${base.length}`], ["IA decide", `IA decide ${cont("IA decide")}`], ["IA sugere", `IA sugere ${cont("IA sugere")}`], ["humano decide", `Humano ${cont("humano decide")}`]];
    $("#conteudo").innerHTML = `
      ${soDetalhe ? "" : `<div class="cab-tela"><div><h1 class="titulo">Fila</h1><p class="subtitulo">${base.length} tickets do holdout · dias 1 a ${S.dia}</p></div>
        <div class="segmentado" role="group" aria-label="Filtrar por faixa">${filtros.map(([k, r]) => `<button type="button" data-f="${esc(k)}" aria-pressed="${S.filtro === k}">${r}</button>`).join("")}</div></div>`}
      <div class="fila-layout">
        ${soDetalhe ? "" : `<section class="lista-cartao" aria-label="Tickets">
          <div class="busca"><input id="busca" type="search" aria-label="Buscar por #id ou termo" placeholder="Buscar por #id ou termo" value="${esc(S.busca)}"></div>
          <div class="lista" id="lista">${v.length ? v.map((t) => {
            const f = faixaTicket(t).faixa, e = S.estados[t.id];
            return `<a class="item" href="#fila/${t.id}"${sel && t.id === sel.id && !celular.matches ? ' aria-current="true"' : ""}>
              <span class="item-cab"><span class="item-id">#${t.id}</span>${selo(f, FX[f].curto)}</span>
              <span class="item-tx truncar">${esc(t.texto)}</span>
              <span class="item-meta">${esc(t.pred)} · ${pct(t.p_max)}${e ? ` · ${e.tipo === "confirmado" ? "confirmado" : "corrigido"}` : ""}</span></a>`;
          }).join("") : '<p class="lista-vazia">Nenhum ticket com este filtro.</p>'}</div></section>`}
        ${soLista || !sel ? "" : detalheTicket(sel)}
      </div>`;
    $$(".segmentado [data-f]").forEach((b) => b.onclick = () => { S.filtro = b.dataset.f; render(); });
    const busca = $("#busca");
    if (busca) busca.oninput = () => { S.busca = busca.value; const pos = busca.selectionStart; render(); const b2 = $("#busca"); b2.focus(); b2.setSelectionRange(pos, pos); };
    if (sel && !soLista) ligarDetalhe(sel);
    if (soDetalhe) {
      document.body.classList.add("com-acao");
      $("#barra-acao").hidden = false;
      $("#barra-acao").innerHTML = `<button type="button" class="botao primario" id="m-confirmar">Confirmar</button><button type="button" class="botao secundario" id="m-corrigir">Corrigir</button>`;
      $("#m-confirmar").onclick = () => decidir(sel, null);
      $("#m-corrigir").onclick = () => { S.corrigindo = !S.corrigindo; render(); const s = $("#sel-cat"); if (s) s.focus(); };
    }
  }
  function motivo(t) {
    const p = politica(), td = p.t_decide, ts = p.t_sugere, teto = p.por_categoria[t.pred];
    const nomePol = `A política ${POL[S.pol].toLowerCase()}`;
    if (S.modo === "sombra") return `Modo sombra ligado: o ticket vai para triagem humana; a faixa calculada é ${FX[faixaTicket(t).semSombra].nome}.`;
    if (t.p_max >= td) {
      if (teto === "IA decide") return `Confiança acima do limiar de decisão. ${nomePol} libera ${t.pred} para automação.`;
      return `Confiança acima do limiar de decisão. ${nomePol} limita ${t.pred} a ${teto === "IA sugere" ? "sugestão" : "triagem humana"}.`;
    }
    if (t.p_max >= ts) return teto === "humano decide" ? `Confiança entre os limiares. ${nomePol} limita ${t.pred} a triagem humana.` : "Confiança entre os limiares de sugestão e decisão.";
    return "Confiança abaixo do limiar de sugestão.";
  }
  function detalheTicket(t) {
    const f = faixaTicket(t).faixa, p = politica(), e = S.estados[t.id], segunda = t.top2[1];
    const L = (v) => `${(100 * v).toFixed(1)}%`;
    return `<section class="detalhe" id="detalhe" aria-label="Ticket selecionado">
      <div class="det-cab"><div class="det-id"><span class="mono">#${t.id}</span><span class="rot">Dia ${t.dia} do piloto</span></div>${selo(f, FX[f].grande, true)}</div>
      <p class="texto-ticket">${esc(t.texto)}${t.truncado ? "… (trecho)" : ""}</p>
      <div class="det-grade">
        <div style="display:flex;flex-direction:column;gap:6px"><span class="rot">Categoria sugerida</span><span class="cat-sug">${esc(t.pred)}</span></div>
        <div>
          <div class="conf-cab"><span class="rot">Confiança</span><strong>${pct(t.p_max)}</strong></div>
          <div class="trilho" role="img" aria-label="Confiança ${pct(t.p_max)}; limiar de sugestão ${pct(p.t_sugere, 0)}, limiar de decisão ${pct(p.t_decide, 0)}">
            <div class="enche" style="width:${L(t.p_max)}"></div><div class="marca-limiar" style="left:${L(p.t_sugere)}"></div><div class="marca-limiar" style="left:${L(p.t_decide)}"></div></div>
          <div class="rotulos-limiar"><span style="left:${L(p.t_sugere)};transform:translateX(-100%);padding-right:4px">${pct(p.t_sugere, 0)} sugere</span><span style="left:${L(p.t_decide)};padding-left:4px">${pct(p.t_decide, 0)} decide</span></div>
        </div>
      </div>
      <div class="motivo"><span class="motivo-rot">Motivo da faixa</span><span class="motivo-tx">${esc(motivo(t))}</span></div>
      <div class="acoes acoes-desk">
        <button type="button" class="botao primario grande" id="bt-confirmar">Confirmar ${esc(t.pred)}</button>
        <button type="button" class="botao secundario grande" id="bt-corrigir" aria-expanded="${S.corrigindo}">Corrigir categoria</button>
        <span class="atalhos"><kbd>Enter</kbd> confirma · <kbd>1–8</kbd> corrige</span>
      </div>
      ${S.corrigindo ? `<div class="corrigir"><div class="campo"><label for="sel-cat">Categoria correta</label><select id="sel-cat">${CATS.map((c, i) => `<option value="${esc(c)}"${c === t.rotulo_original ? " selected" : ""}>${i + 1}. ${esc(c)}</option>`).join("")}</select></div><button type="button" class="botao primario" id="bt-aplicar">Aplicar correção</button></div>` : ""}
      ${S.feedback[t.id] ? `<p class="feedback" role="status">${esc(S.feedback[t.id])}</p>` : ""}
      ${e ? "" : ""}
      <details class="detalhes"><summary>Detalhes do modelo</summary><div class="detalhes-corpo">
        <span>2ª opção: ${esc(segunda.categoria)} · ${pct(segunda.p)}</span>
        <span>Termos de maior peso: ${esc(t.termos.replace(/ \(-?[\d.]+\)/g, ""))}</span>
        <span>Rótulo histórico (correção simulada): ${esc(t.rotulo_original)}</span></div></details>
    </section>`;
  }
  function ligarDetalhe(t) {
    const c = $("#bt-confirmar"); if (c) c.onclick = () => decidir(t, null);
    const k = $("#bt-corrigir"); if (k) k.onclick = () => { S.corrigindo = !S.corrigindo; render(); const s = $("#sel-cat"); if (s) s.focus(); };
    const a = $("#bt-aplicar"); if (a) a.onclick = () => decidir(t, $("#sel-cat").value);
  }
  function decidir(t, cat) {
    if (!t) return;
    const corr = cat && cat !== t.pred;
    S.estados[t.id] = corr ? { tipo: "corrigido", categoria: cat } : { tipo: "confirmado" };
    S.log.push({ timestamp_utc: agora(), tipo: corr ? "correcao" : "confirmacao", chave: chave(t), categoria_correta: corr ? cat : t.pred, atendente: "simulado (rótulo original)" });
    S.feedback[t.id] = corr ? `Corrigido para ${cat}. A correção entra no próximo ciclo de avaliação.` : `Confirmado: ${t.pred}.`;
    S.corrigindo = false;
    render();
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (S.sobreAberto) { fecharSobre(); return; }
      if (S.tela === "governanca" && S.sub) { location.hash = "#governanca"; return; }
    }
    if (S.tela !== "fila" || S.sobreAberto) return;
    const alvo = e.target.tagName;
    if (["INPUT", "SELECT", "TEXTAREA", "BUTTON", "SUMMARY"].includes(alvo)) return;
    const v = visiveis(), atual = (S.sub && ticketPorId(S.sub)) || v[0];
    if (!atual) return;
    const i = v.indexOf(atual);
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      const prox = v[Math.max(0, Math.min(v.length - 1, i + (e.key === "ArrowDown" ? 1 : -1)))];
      if (prox) { e.preventDefault(); history.replaceState(null, "", `#fila/${prox.id}`); S.sub = String(prox.id); render(); const it = $(`.item[href="#fila/${prox.id}"]`); if (it) { it.focus(); it.scrollIntoView({ block: "nearest" }); } }
    } else if (e.key === "Enter") { e.preventDefault(); decidir(atual, null); }
    else if (/^[1-8]$/.test(e.key)) { e.preventDefault(); decidir(atual, CATS[+e.key - 1]); }
  });

  // ---- governança
  function barraIC(k, fxVig) {
    const pos = (v) => `${(Math.max(0, Math.min(1, (v - 0.85) / 0.15)) * 100).toFixed(2)}%`;
    const cores = { "IA decide": ["rgba(15,123,108,0.28)", "#0F7B6C"], "IA sugere": ["rgba(217,138,30,0.30)", "#B86A0C"], "humano decide": ["rgba(122,134,153,0.30)", "#5B6678"] }[fxVig];
    return `<span class="ic" role="img" aria-label="Precisão ${pct(k.precisao)}, intervalo ${pct(k.li)} a ${pct(k.ls)}">
      <span class="ic-trilho"></span>
      <span class="ic-meta" style="left:${pos(META_S)};border-left:1px dashed #D98A1E"></span>
      <span class="ic-meta" style="left:${pos(META_D)};border-left:1px dashed #0F7B6C"></span>
      ${k.li != null ? `<span class="ic-faixa" style="left:${pos(k.li)};width:${((k.ls - Math.max(k.li, 0.85)) / 0.15 * 100).toFixed(2)}%;background:${cores[0]}"></span>
      <span class="ic-ponto" style="left:${pos(k.precisao)};border-color:${cores[1]}"></span>` : ""}</span>`;
  }
  function telaGov() {
    const g = gov(), p = politica(), cat = S.sub && CATS.includes(S.sub) ? S.sub : null;
    $("#conteudo").innerHTML = `
      <div><h1 class="titulo">Governança</h1><p class="subtitulo">Limite inferior do IC 95% ≥ ${pct(META_D)} libera decisão; ≥ ${pct(META_S)} libera sugestão. A regra só rebaixa.</p></div>
      <div class="gov-layout">
        <section class="gov-tabela" aria-label="Filas"><div class="rolavel"><div class="gov-grade">
          <div class="gov-linha gov-cab"><span>Fila</span><span>Política</span>
            <span class="gov-cab-ic"><span>Precisão · IC 95%</span><span><span style="color:var(--sugere-tx)">┆ ${pct(META_S)}</span>  <span style="color:var(--decide-tx)">┆ ${pct(META_D)}</span></span></span>
            <span style="text-align:right">n</span><span>Ação</span></div>
          ${CATS.map((c) => {
            const k = g.categorias[c], vig = p.por_categoria[c], a = acaoRegra(vig, k.decisao_regra);
            return `<a class="gov-linha" href="#governanca/${encodeURIComponent(c)}"${c === cat ? ' aria-current="true"' : ""}>
              <span class="gov-nome">${esc(c)}</span>${selo(vig)}
              <span class="ic-celula">${barraIC(k, vig)}<span class="ic-prec">${pct(k.precisao)}</span></span>
              <span class="gov-n">${num(k.n_sombra)}</span><span class="gov-acao" style="color:${a.cor}">${a.txt}</span></a>`;
          }).join("")}
        </div></div></section>
        ${cat ? painelCategoria(cat) : ""}
      </div>`;
    if (cat) {
      $("#fechar-painel").onclick = () => { location.hash = "#governanca"; };
      $("#dia").oninput = (e) => { S.dia = +e.target.value; render(); const d = $("#dia"); if (d) d.focus(); };
      if (celular.matches) $("#fechar-painel").focus();
    }
  }
  function veredito(cat) {
    const k = gov().categorias[cat], vig = politica().por_categoria[cat];
    if (k.li == null) return ["Sem dados.", "Nenhum ticket com confiança acima do limiar até este dia."];
    let r;
    if (k.decisao_regra === "IA decide") r = ["Elegível para decisão.", `Limite inferior ${pct(k.li)} acima da meta de ${pct(META_D)}.`];
    else if (k.decisao_regra === "IA sugere") r = ["Elegível para sugestão.", `Limite inferior ${pct(k.li)} entre ${pct(META_S)} e ${pct(META_D)}.`];
    else r = ["Não elegível para sugestão.", `Limite inferior ${pct(k.li)} abaixo da meta de ${pct(META_S)}.`];
    if (ORDEM.indexOf(k.decisao_regra) < ORDEM.indexOf(vig)) r[1] += ` A política atual mantém ${FX[vig].nome.toLowerCase()} até a revisão.`;
    return r;
  }
  function painelCategoria(cat) {
    const k = gov().categorias[cat], vig = politica().por_categoria[cat], [vb, vt] = veredito(cat);
    const y = (v) => 180 - (Math.max(0.85, Math.min(1, v)) - 0.85) * 1200, x = (i) => 40 + i * (540 / 19);
    const pts = D.governanca.map((g, i) => g.categorias[cat].li == null ? "" : `${x(i).toFixed(1)},${y(g.categorias[cat].li).toFixed(1)}`).filter(Boolean).join(" ");
    return `<aside class="painel${celular.matches ? " tela-cheia" : ""}" id="painel" aria-label="Detalhe da fila ${esc(cat)}">
      <div class="painel-cab"><div><h2>${esc(cat)}</h2>${selo(vig)}</div>
        <button type="button" class="fechar" id="fechar-painel" aria-label="Fechar painel">${sv(IC.x, 14, ' stroke-width="2"')}</button></div>
      <div class="tres"><div><span>Precisão</span><span>${pct(k.precisao)}</span></div><div><span>Limite inferior</span><span>${pct(k.li)}</span></div><div><span>Tickets</span><span>${num(k.n_sombra)}</span></div></div>
      <div class="veredito"><strong style="font-weight:600">${esc(vb)}</strong> ${esc(vt)}</div>
      <div class="bloco"><span style="font-size:14px;font-weight:600">Limite inferior por dia</span>
        <svg class="grafico" role="img" aria-label="Limite inferior de ${esc(cat)} por dia; dia ${S.dia}: ${pct(k.li)}" viewBox="0 -18 600 228">
          <g font-family="IBM Plex Sans, sans-serif" font-size="${FS()}" fill="#5F6B7A"><text x="0" y="10">100%</text><text x="0" y="64">95%</text><text x="0" y="124">90%</text><text x="0" y="182">85%</text></g>
          <line x1="40" y1="60" x2="580" y2="60" stroke="#EEF1F5"/><line x1="40" y1="120" x2="580" y2="120" stroke="#EEF1F5"/><line x1="40" y1="180" x2="580" y2="180" stroke="#EEF1F5"/>
          <line x1="40" y1="${y(META_D)}" x2="580" y2="${y(META_D)}" stroke="#0F7B6C" stroke-dasharray="5 4" stroke-width="1.5"/>
          <line x1="40" y1="${y(META_S)}" x2="580" y2="${y(META_S)}" stroke="#D98A1E" stroke-dasharray="5 4" stroke-width="1.5"/>
          <text x="580" y="${y(META_D) - 5}" text-anchor="end" font-family="IBM Plex Sans, sans-serif" font-size="${FS()}" fill="#0B6B5E">decide ${pct(META_D)}</text>
          <text x="580" y="${y(META_S) - 4}" text-anchor="end" font-family="IBM Plex Sans, sans-serif" font-size="${FS()}" fill="#8F4A00">sugere ${pct(META_S)}</text>
          <polyline fill="none" stroke="#2457D6" stroke-width="2.5" stroke-linejoin="round" points="${pts}"/>
          ${k.li != null ? `<circle cx="${x(S.dia - 1)}" cy="${y(k.li)}" r="4" fill="#2457D6"/>` : ""}
          <g font-family="IBM Plex Sans, sans-serif" font-size="${FS()}" fill="#5F6B7A"><text x="40" y="204">dia 1</text><text x="580" y="204" text-anchor="end">dia 20</text></g></svg></div>
      <div class="bloco"><label for="dia" class="dia-rot"><span>Dia do piloto</span><strong>${S.dia}</strong></label><input id="dia" type="range" min="1" max="20" value="${S.dia}"></div>
    </aside>`;
  }

  // ---- robustez
  function idsInjecao() {
    const ids = [10244];
    D.fila.forEach((t) => {
      if (ids.length >= 8 || ids.includes(t.id)) return;
      const a = D.ataques[String(t.id)];
      if (Object.values(a).some((x) => x.pred !== t.pred && x.faixas.F8 === "IA decide")) ids.push(t.id);
    });
    return ids;
  }
  function textoInjetado(t, ataqueId, alvo) {
    const tpl = D.ataques_modelos.find((m) => m.id === ataqueId).texto;
    // o modelo usa a sintaxe de str.format do Python: {alvo} e chaves dobradas
    const inj = tpl.replace(/\{alvo\}/g, alvo).replace(/\{\{/g, "{").replace(/\}\}/g, "}");
    return `${esc(t.texto)}${t.truncado ? "…" : ""} <span class="injetado">${esc(inj)}</span>`;
  }
  function telaRob() {
    const cen = CEN.some(([k]) => k === S.sub) ? S.sub : "injecao";
    $("#conteudo").innerHTML = `
      <div><h1 class="titulo">Robustez</h1><p class="subtitulo">Cenários de falha executados sobre tickets reais. Resultados pré-calculados pelo classificador.</p></div>
      <div class="sel-cen campo"><label for="sel-cen">Cenário</label><select id="sel-cen">${CEN.map(([k, n]) => `<option value="${k}"${k === cen ? " selected" : ""}>${n}</option>`).join("")}</select></div>
      <div class="rob-layout">
        <nav class="menu-cen rolavel" aria-label="Cenários">${CEN.map(([k, n, s]) => `<a class="cen" href="#robustez/${k}"${k === cen ? ' aria-current="true"' : ""}><span class="cen-nome">${n}</span><span class="cen-sub">${s}</span></a>`).join("")}</nav>
        <section class="cenario" aria-label="${esc(CEN.find(([k]) => k === cen)[1])}">${({ injecao: cenInjecao, duplicado: cenDuplicado, reembolso: cenReembolso, sombra: cenSombra, politica: cenPolitica })[cen]()}</section>
      </div>
      <details class="log"><summary>Log da sessão (${num(S.log.length)} linhas, sem texto)</summary><pre>${esc(S.log.map((l) => JSON.stringify(l)).join("\n")) || "Sem eventos ainda."}</pre></details>`;
    $("#sel-cen").onchange = (e) => { location.hash = `#robustez/${e.target.value}`; };
    ({ injecao: ligarInjecao, duplicado: ligarDuplicado, reembolso: ligarReembolso, sombra: ligarSombra, politica: ligarPolitica })[cen]();
  }
  function cartaoComp(polK, t, a) {
    const fa = S.modo === "sombra" ? "humano decide" : a.faixas[polK], trocou = a.pred !== t.pred;
    const tipo = trocou && fa === "IA decide" ? "dano" : trocou ? "contido" : "neutro";
    const ver = { dano: [IC.alerta, "Passa sem revisão humana"], contido: [IC.check, "Retido para revisão humana"], neutro: [IC.check, "Sem efeito na categoria"] }[tipo];
    return `<div class="comp ${tipo === "neutro" ? "" : tipo}"><span class="comp-rot">Política ${esc(POL[polK].toLowerCase())}</span>
      <div class="comp-res"><span class="comp-cat">${esc(a.pred)}</span><span class="legenda">${pct(a.p_max)}</span>${selo(fa)}</div>
      <span class="veredito-linha ${tipo}">${sv(ver[0], 16, ' stroke-width="2"')}${ver[1]}</span></div>`;
  }
  function cenInjecao() {
    const I = S.inj, t = ticketPorId(I.ticket), a = D.ataques[String(t.id)][I.ataque], dn = D.kpis.dano_injecao;
    return `<div><h2>Injeção de instrução</h2><p class="subtitulo">Texto adversarial anexado ao ticket para forçar outra fila.</p></div>
      <div class="controles">
        <div class="campo"><label for="ataque">Ataque</label><select id="ataque">${Object.entries(ATAQUE).map(([k, n]) => `<option value="${k}"${k === I.ataque ? " selected" : ""}>${n}</option>`).join("")}</select></div>
        <div class="campo" style="flex:1 1 160px"><label for="ticket">Ticket</label><select id="ticket" class="mono">${idsInjecao().map((id) => `<option value="${id}"${id === I.ticket ? " selected" : ""}>#${id}</option>`).join("")}</select></div>
        <button type="button" class="botao primario grande" id="executar">Executar</button></div>
      ${I.executado ? `<div class="bloco"><span class="legenda">Ticket #${t.id} · original: ${esc(t.pred)}, ${pct(t.p_max)}</span><p class="texto-ataque">${textoInjetado(t, I.ataque, a.alvo)}</p></div>
        <div class="comparacao">${cartaoComp("F8", t, a)}${cartaoComp("F9", t, a)}</div>` : '<p class="legenda">Escolha o ataque e o ticket e execute.</p>'}
      <div class="agregado"><span style="font-size:14px;font-weight:600">Resultado agregado · 5 ataques sobre a faixa IA decide</span>
        <div class="rolavel"><table class="tab-agregado"><thead><tr><th scope="col">Política</th><th scope="col" class="dir">Tentativas</th><th scope="col" class="dir">Sem revisão</th><th scope="col" class="dir">Retiradas da automação</th></tr></thead>
          <tbody>${["F9", "F8", "F4"].map((k) => `<tr><td style="font-weight:600">${POL[k]}</td><td class="dir mono">${num(dn[k].n_pares)}</td><td class="dir" style="font-weight:600;color:${dn[k].silenciosos ? "var(--dano)" : "var(--decide-tx)"}">${num(dn[k].silenciosos)}</td><td class="dir mono" style="color:var(--texto-3)">${num(dn[k].saem_de_ia_decide)}</td></tr>`).join("")}</tbody></table></div></div>`;
  }
  function ligarInjecao() {
    $("#ataque").onchange = (e) => { S.inj.ataque = e.target.value; S.inj.executado = false; render(); };
    $("#ticket").onchange = (e) => { S.inj.ticket = +e.target.value; S.inj.executado = false; render(); };
    $("#executar").onclick = () => { S.inj.executado = true; render(); };
  }
  function cenDuplicado() {
    const t = ticketPorId(10244);
    return `<div><h2>Evento duplicado</h2><p class="subtitulo">Reentrega do webhook com o mesmo <span class="mono">event_id</span> (fila-${t.id}).</p></div>
      <div class="controles"><button type="button" class="botao primario grande" id="reentregar">Reentregar evento</button></div>
      ${S.dupRodou ? `<p class="resultado"><strong>Duplicado: nenhuma nova decisão.</strong> A chave já estava reservada; a decisão original segue valendo.</p><p class="codigo">${esc(JSON.stringify(S.dupRodou))}</p>` : ""}`;
  }
  function ligarDuplicado() { $("#reentregar").onclick = () => { S.dupRodou = reentregar(ticketPorId(10244)); render(); }; }
  function cenReembolso() {
    const t = ticketPorId(TICKET_REEMBOLSO), f = faixaTicket(t).faixa;
    return `<div><h2>Regra de reembolso</h2><p class="subtitulo">Tipo sensível vai para triagem humana, mesmo com confiança alta.</p></div>
      <p class="resultado">Ticket <span class="mono">#${t.id}</span> · ${esc(t.pred)}, ${pct(t.p_max)} · faixa ${selo(f)}</p>
      <div class="controles"><button type="button" class="botao primario grande" id="reembolso">Marcar como reembolso</button></div>
      ${S.reembolsoRodou ? `<p class="resultado">Faixa com o tipo reembolso: ${selo("humano decide")}</p><p class="legenda">Reembolso e cancelamento movimentam dinheiro e são difíceis de reverter.</p>` : ""}`;
  }
  function ligarReembolso() {
    $("#reembolso").onclick = () => {
      const t = ticketPorId(TICKET_REEMBOLSO);
      S.reembolsoRodou = true;
      S.log.push(linhaDecisao(t, "humano decide", "humano decide", "regra de ação: Refund request; termos: " + t.termos));
      render();
    };
  }
  function cenSombra() {
    const g = gov(), base = g.faixas[S.pol]["IA decide"].n / g.n_total;
    return `<div><h2>Modo sombra</h2><p class="subtitulo">Desliga as decisões automáticas e mantém o registro do que seria decidido.</p></div>
      <label class="chave"><input type="checkbox" id="sombra"${S.modo === "sombra" ? " checked" : ""}> Modo sombra ${S.modo === "sombra" ? "ligado" : "desligado"}</label>
      ${S.modo === "sombra" ? `<p class="resultado">Automação: <strong>${pct(base)} → ${pct(0)}</strong>. Alerta emitido na visão geral. O log continua registrando a faixa calculada em <span class="mono">faixa_sem_sombra</span>.</p>${S.log.length ? `<p class="codigo">${esc(JSON.stringify(S.log[S.log.length - 1]))}</p>` : ""}` : `<p class="resultado">Automação atual: <strong>${pct(base)}</strong>.</p>`}`;
  }
  function ligarSombra() {
    $("#sombra").onchange = (e) => {
      S.modo = e.target.checked ? "sombra" : "ativo";
      if (S.modo === "sombra") { const t = ticketPorId(10244); S.log.push(linhaDecisao(t, "humano decide", t.faixas[S.pol].faixa, "modo sombra")); }
      render(); $("#sombra").focus();
    };
  }
  function cenPolitica() {
    const dn = D.kpis.dano_injecao, g = gov();
    return `<div><h2>Troca de política</h2><p class="subtitulo">Voltar para a política atual é o rollback.</p></div>
      <div class="segmentado" role="group" aria-label="Política">${["F9", "F8", "F4"].map((k) => `<button type="button" data-pol="${k}" aria-pressed="${S.pol === k}">${POL[k]}</button>`).join("")}</div>
      <div class="rolavel"><table class="tab-agregado"><thead><tr><th scope="col">Política</th><th scope="col" class="dir">Automação</th><th scope="col" class="dir">Injeções sem revisão</th></tr></thead>
        <tbody>${["F9", "F8", "F4"].map((k) => `<tr${k === S.pol ? ' style="background:var(--selecionado)"' : ""}><td style="font-weight:600">${POL[k]}${k === S.pol ? " (em uso)" : ""}</td><td class="dir">${pct(S.modo === "sombra" ? 0 : g.faixas[k]["IA decide"].n / g.n_total)}</td><td class="dir" style="font-weight:600;color:${dn[k].silenciosos ? "var(--dano)" : "var(--decide-tx)"}">${num(dn[k].silenciosos)} de ${num(dn[k].n_pares)}</td></tr>`).join("")}</tbody></table></div>`;
  }
  function ligarPolitica() { $$("[data-pol]").forEach((b) => b.onclick = () => { S.pol = b.dataset.pol; render(); }); }

  // ---- painel "Sobre os dados"
  let focoAntes = null;
  function abrirSobre() { focoAntes = document.activeElement; S.sobreAberto = true; $("#veu").hidden = false; $("#sobre").hidden = false; renderSobre(); $("#fechar-sobre").focus(); }
  function fecharSobre() { S.sobreAberto = false; $("#veu").hidden = true; $("#sobre").hidden = true; if (focoAntes && document.body.contains(focoAntes)) focoAntes.focus(); else { const b = $("#abrir-sobre"); if (b) b.focus(); } }
  function economia() {
    const f = faixas(), p = S.premissas;
    return (f.d.n / f.n) * p.volume_ano * p.minutos_triagem / 60 * p.reais_por_hora;
  }
  function renderSobre() {
    const p = S.premissas;
    $("#sobre").innerHTML = `<div class="painel-cab"><div><h2 id="sobre-titulo">Sobre os dados</h2></div><button type="button" class="fechar" id="fechar-sobre" aria-label="Fechar">${sv(IC.x, 14, ' stroke-width="2"')}</button></div>
      <ul>
        <li>Origem: holdout por grupo do DS2 (TI interna, ${num(D.governanca[19].n_total)} tickets); fila com 300 tickets sorteados.</li>
        <li>A correção do atendente é simulada pelo rótulo original, que tem ruído próprio.</li>
        <li>A transferência para a operação de suporte é premissa, não resultado.</li>
        <li>Políticas: Atual = F9; Sem confirmação no teste = F8; Inicial = F4.</li>
      </ul>
      <div class="premissas">
        <div class="campo"><label for="p-reais">R$/h</label><input id="p-reais" type="number" min="0" step="1" value="${p.reais_por_hora}"></div>
        <div class="campo"><label for="p-min">min/ticket</label><input id="p-min" type="number" min="0" step="0.5" value="${p.minutos_triagem}"></div>
        <div class="campo"><label for="p-vol">tickets/ano</label><input id="p-vol" type="number" min="0" step="1000" value="${p.volume_ano}"></div>
      </div>
      <p class="resultado" id="eco">Economia anual estimada (cenário A): <strong>${brl(economia())}</strong>. Cenário B: zero.</p>
      <a class="link-forte" href="https://github.com/covaleski13-tech/ai-master-challenge/blob/submission/gustavo-covaleski/submissions/gustavo-covaleski/README.md">README da submissão</a>`;
    $("#fechar-sobre").onclick = fecharSobre;
    [["p-reais", "reais_por_hora"], ["p-min", "minutos_triagem"], ["p-vol", "volume_ano"]].forEach(([id, k]) => {
      $(`#${id}`).oninput = (e) => { const v = parseFloat(e.target.value); S.premissas[k] = isFinite(v) && v >= 0 ? v : 0; $("#eco").innerHTML = `Economia anual estimada (cenário A): <strong>${brl(economia())}</strong>. Cenário B: zero.`; };
    });
  }
  $("#veu").onclick = fecharSobre;

  lerHash();
})();
