// Tela do Lead Scorer "Segunda-feira". Lê window.DADOS (gerado por solution/motor/nota.py).
(function () {
  const { meta, vendas } = window.DADOS;
  const CHAVE_MARCAS = "segunda.marcacoes";
  const CHAVE_VENDEDOR = "segunda.vendedor";
  const POR_PAGINA = 20;

  const STATUS = {
    risco: { nome: "Fase de risco", classe: "s-risco" },
    ativa: { nome: "Ativa", classe: "s-ativa" },
    esfriando: { nome: "Esfriando", classe: "s-esfriando" },
    prospeccao: { nome: "Prospecção", classe: "s-prospeccao" },
    revisar: { nome: "Parada", classe: "s-revisar" },
    cadastro: { nome: "Sem cliente", classe: "s-cadastro" },
  };

  // Botões de cada lista: [valor salvo, texto do botão, texto depois de marcado]
  const BOTOES = {
    semana: [["feito", "✓ Feito", "Feito esta semana"]],
    outras: [["feito", "✓ Feito", "Feito esta semana"]],
    revisar: [["viva", "Ainda viva", "Confirmada: ainda viva"], ["encerrar", "Encerrar", "Marcada para encerrar"]],
    cadastro: [["cadastrado", "✓ Cadastrado", "Cliente cadastrado"]],
  };

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const dinheiro = (v) => "US$ " + Math.round(v).toLocaleString("pt-BR");
  const milhoes = (v) => "US$ " + (v / 1e6).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " mi";
  const pct = (v) => Math.round(v * 100) + "%";
  const sinal = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(Math.round(v * 100)) + "%";
  const dataBR = (s) => s.split("-").reverse().join("/");
  const unicos = (lista, campo) => [...new Set(lista.map((v) => v[campo]))].sort();
  const PRIORIDADE = ["risco", "ativa", "esfriando", "prospeccao"];

  // ---------- memória deste navegador ----------
  function ler(chave, padrao) {
    try { return JSON.parse(localStorage.getItem(chave)) ?? padrao; } catch (e) { return padrao; }
  }
  function gravar(chave, valor) {
    try { localStorage.setItem(chave, JSON.stringify(valor)); } catch (e) { /* sem armazenamento: vale só nesta visita */ }
  }
  let marcas = ler(CHAVE_MARCAS, {});

  // ---------- desenho de uma venda ----------
  function classeNota(n) { return n >= 80 ? "alta" : n >= 50 ? "media" : ""; }

  function item(v, lista) {
    const marca = marcas[v.id];
    let caixa;
    if (lista === "semana" || lista === "outras") caixa = `<div class="nota ${classeNota(v.nota)}" title="Nota de 0 a 100">${v.nota}<small>nota</small></div>`;
    else if (v.dias !== null) caixa = `<div class="nota parada">${v.dias}<small>dias</small></div>`;
    else caixa = `<div class="nota">—<small>prosp.</small></div>`;
    const cliente = v.cliente ? `${esc(v.cliente)}${v.setor ? " · " + esc(v.setor) : ""}` : "Cliente não cadastrado";
    const valores = lista === "semana" || lista === "outras"
      ? `<b>${dinheiro(v.valor_esperado)}</b>esperado · chance ${pct(v.chance)}<br>preço ${dinheiro(v.preco)}`
      : `<b>${dinheiro(v.preco)}</b>${lista === "revisar" ? "parados" : "em aberto"}`;
    const botoes = marca
      ? `<span class="feito">${BOTOES[lista].find((b) => b[0] === marca)?.[2] ?? "Marcada"}</span> <button class="link" data-id="${esc(v.id)}" data-marca="">Desfazer</button>`
      : BOTOES[lista].map(([val, txt]) => `<button class="btn" data-id="${esc(v.id)}" data-marca="${val}">${txt}</button>`).join(" ");
    return `<li class="venda${marca ? " marcada" : ""}">
      ${caixa}
      <div>
        <div class="titulo">${esc(v.produto)} <span class="status ${STATUS[v.status].classe}">${STATUS[v.status].nome}</span></div>
        <div class="quem">${cliente} · ${esc(v.id)}${v.inicio ? " · desde " + dataBR(v.inicio) : ""}</div>
        <ul class="motivos">${v.motivos.map((m) => `<li>${esc(m)}</li>`).join("")}</ul>
        <div class="acao"><b>Próxima ação:</b> ${esc(v.acao)}</div>
        <div class="botoes">${botoes}</div>
      </div>
      <div class="valores">${valores}</div>
    </li>`;
  }

  const naoMarcadasPrimeiro = (ordem) => (a, b) => (!!marcas[a.id] - !!marcas[b.id]) || ordem(a, b);
  const qtd = { outras: POR_PAGINA, revisar: POR_PAGINA, cadastro: POR_PAGINA };

  function listar(id, lista, tipo, limite) {
    const el = $(id);
    const mostrar = limite ? lista.slice(0, limite) : lista;
    el.innerHTML = mostrar.length ? mostrar.map((v) => item(v, tipo)).join("") : `<li class="vazio">Nenhuma venda aqui.</li>`;
    if (limite && lista.length > limite) {
      el.insertAdjacentHTML("beforeend", `<li><button class="btn mais" data-mais="${tipo}">Mostrar mais (${lista.length - limite} restantes)</button></li>`);
    }
  }

  // ---------- aba Vendedor ----------
  const vendedores = unicos(vendas, "vendedor");
  // Na primeira visita, abre num exemplo completo: quem tem negociação em andamento, mais vendas na semana e maior valor esperado.
  const daSemana = (nome) => vendas.filter((v) => v.vendedor === nome && v.semana);
  const valorSemana = (nome) => daSemana(nome).reduce((s, v) => s + v.valor_esperado, 0);
  const negocia = (nome) => vendas.some((v) => v.vendedor === nome && ["risco", "ativa", "esfriando"].includes(v.status));
  let vendedor = ler(CHAVE_VENDEDOR, null);
  if (!vendedores.includes(vendedor)) {
    vendedor = [...vendedores].sort((a, b) => negocia(b) - negocia(a) || daSemana(b).length - daSemana(a).length
      || valorSemana(b) - valorSemana(a))[0];
  }

  function desenharVendedor() {
    const minhas = vendas.filter((v) => v.vendedor === vendedor);
    const semana = minhas.filter((v) => v.semana).sort(naoMarcadasPrimeiro((a, b) => b.valor_esperado - a.valor_esperado));
    const outras = minhas.filter((v) => PRIORIDADE.includes(v.status) && !v.semana)
      .sort(naoMarcadasPrimeiro((a, b) => b.valor_esperado - a.valor_esperado));
    const revisar = minhas.filter((v) => v.status === "revisar").sort(naoMarcadasPrimeiro((a, b) => b.preco - a.preco || b.dias - a.dias));
    const cadastro = minhas.filter((v) => v.status === "cadastro").sort(naoMarcadasPrimeiro((a, b) => b.preco - a.preco));

    const aFazer = semana.filter((v) => !marcas[v.id]).length;
    const esperado = semana.reduce((s, v) => s + v.valor_esperado, 0);
    const limpar = [...revisar, ...cadastro].filter((v) => !marcas[v.id]).length;
    $("resumo-vendedor").innerHTML = `
      <div class="card destaque"><div class="n">${aFazer}<small> de ${semana.length}</small></div><div class="r">vendas da semana a fazer</div></div>
      <div class="card"><div class="n">${dinheiro(esperado)}</div><div class="r">valor esperado das 5 da semana em 90 dias</div></div>
      <div class="card"><div class="n">${limpar}</div><div class="r">vendas para limpar: ${revisar.length} paradas + ${cadastro.length} sem cliente</div></div>`;

    const negociando = minhas.filter((v) => ["risco", "ativa", "esfriando"].includes(v.status)).length;
    const alerta = $("alerta");
    alerta.hidden = negociando > 0;
    if (!negociando) {
      alerta.innerHTML = `<b>Nenhuma negociação em andamento.</b> ` + (semana.length
        ? `As vendas da semana são prospecções: o primeiro contato é o passo mais importante.`
        : `Sua carteira só tem vendas para limpar. Comece por elas.`);
    }

    listar("lista-semana", semana, "semana");
    $("n-outras").textContent = outras.length;
    listar("lista-outras", outras, "outras", qtd.outras);
    $("n-revisar").textContent = revisar.length;
    listar("lista-revisar", revisar, "revisar", qtd.revisar);
    $("n-cadastro").textContent = cadastro.length;
    listar("lista-cadastro", cadastro, "cadastro", qtd.cadastro);
  }

  // ---------- aba Chefe de vendas ----------
  const filtroChefe = { regiao: "", gerente: "" };

  function preencher(select, valores, atual, vazio) {
    select.innerHTML = `<option value="">${vazio}</option>` + valores.map((x) => `<option${x === atual ? " selected" : ""}>${esc(x)}</option>`).join("");
  }

  function desenharChefe() {
    const porRegiao = vendas.filter((v) => !filtroChefe.regiao || v.regiao === filtroChefe.regiao);
    const gerentes = unicos(porRegiao, "gerente");
    if (!gerentes.includes(filtroChefe.gerente)) filtroChefe.gerente = "";
    preencher($("f-regiao"), unicos(vendas, "regiao"), filtroChefe.regiao, "Todas");
    preencher($("f-gerente"), gerentes, filtroChefe.gerente, "Todos");
    const lista = porRegiao.filter((v) => !filtroChefe.gerente || v.gerente === filtroChefe.gerente);

    const soma = (l, campo) => l.reduce((s, v) => s + v[campo], 0);
    const crm = soma(lista, "preco");
    const previsao = soma(lista, "valor_esperado");
    const paradas = lista.filter((v) => v.status === "revisar");
    const semCliente = lista.filter((v) => v.status === "cadastro");
    $("resumo-chefe").innerHTML = `
      <div class="card"><div class="n">${milhoes(crm)}</div><div class="r">o CRM mostra em ${lista.length} vendas abertas</div></div>
      <div class="card destaque"><div class="n">${milhoes(previsao)}</div><div class="r">o que deve entrar nos próximos 90 dias (vendas vivas e com cliente)</div></div>
      <div class="card"><div class="n">${milhoes(soma(paradas, "preco"))}</div><div class="r">parado há mais de ${meta.prazo_maximo} dias (${paradas.length} vendas)</div></div>
      <div class="card"><div class="n">${semCliente.length}</div><div class="r">vendas sem cliente cadastrado (${milhoes(soma(semCliente, "preco"))})</div></div>`;

    const vivas = lista.filter((v) => PRIORIDADE.includes(v.status));
    const porque = `Por que a previsão é tão menor que o CRM? Das ${milhoes(crm)}, ${milhoes(soma(paradas, "preco"))} estão em vendas paradas e ${milhoes(soma(semCliente, "preco"))} em vendas sem cliente: nenhuma venda assim fechou na história. ` +
      `Sobram ${milhoes(soma(vivas, "preco"))} em ${vivas.length} vendas vivas, e a previsão é a parte delas que deve fechar em 90 dias. `;
    const prev = meta.teste ? meta.teste.previsao : [];
    if (prev.length) {
      const vezes = prev.map((p) => p.crm / p.real);
      const erro = prev.map((p) => p.previsao / p.real - 1);
      $("explica-previsao").innerHTML = porque + `No teste com 4 datas do passado, o CRM mostrava <b>${Math.min(...vezes).toFixed(0)} a ${Math.max(...vezes).toFixed(0)} vezes</b> o que entrou de fato. ` +
        `A previsão da ferramenta errou <b>entre ${sinal(Math.min(...erro))} e ${sinal(Math.max(...erro))}</b>. Detalhes em "Como a nota funciona".`;
    }

    const linhas = unicos(lista, "vendedor").map((nome) => {
      const dele = lista.filter((v) => v.vendedor === nome);
      const p = dele.filter((v) => v.status === "revisar");
      const c = dele.filter((v) => v.status === "cadastro");
      const s = dele.filter((v) => v.semana);
      const negociando = dele.filter((v) => ["risco", "ativa", "esfriando"].includes(v.status)).length;
      const partes = [];
      if (!negociando) partes.push("sem negociação em andamento: abrir as prospecções");
      if (p.length) partes.push(`revisar ${p.length} parada${p.length > 1 ? "s" : ""} (${dinheiro(soma(p, "preco"))})`);
      if (c.length) partes.push(`cadastrar o cliente de ${c.length} venda${c.length > 1 ? "s" : ""}`);
      const passo = partes.length ? partes.join("; ").replace(/^./, (x) => x.toUpperCase()) + "." : "Acompanhar as vendas da semana.";
      return { nome, gerente: dele[0].gerente, previsao: soma(dele, "valor_esperado"), semana: soma(s, "valor_esperado"),
               nSemana: s.length, p, c, passo };
    }).sort((a, b) => b.previsao - a.previsao);

    document.querySelector("#tabela-vendedores tbody").innerHTML = linhas.length ? linhas.map((l) => `
      <tr>
        <td><b>${esc(l.nome)}</b><br><span class="quem">${esc(l.gerente)}</span></td>
        <td class="num">${dinheiro(l.previsao)}</td>
        <td class="num">${l.nSemana} venda${l.nSemana === 1 ? "" : "s"}<br><span class="quem">${dinheiro(l.semana)}</span></td>
        <td class="num">${l.p.length}<br><span class="quem">${dinheiro(soma(l.p, "preco"))}</span></td>
        <td class="num">${l.c.length}</td>
        <td class="passo">${esc(l.passo)}</td>
      </tr>`).join("") : `<tr><td colspan="6">Nenhum vendedor com esses filtros.</td></tr>`;
  }

  // ---------- aba Como funciona ----------
  function desenharComo() {
    $("n-fotos").textContent = meta.fotos_do_passado;
    $("r-ja").textContent = pct(meta.relacao.ja_ganhou);
    $("r-sem").textContent = pct(meta.relacao.sem_historico);
    if (meta.ajuste_base) {
      $("aj-prev").textContent = meta.ajuste_base.previstas.toLocaleString("pt-BR");
      $("aj-ganhas").textContent = meta.ajuste_base.ganhas.toLocaleString("pt-BR");
      $("aj-fator").textContent = pct(meta.ajuste);
    }
    $("grafico").innerHTML = meta.tabela_chance.map((f) => {
      const rotulo = f.ate > 10000 ? `mais de ${f.de - 1} dias` : `${f.de} a ${f.ate} dias`;
      const tipo = f.de > meta.prazo_maximo ? "rev" : f.de > meta.inicio_esfriar ? "esf" : "";
      return `<div class="linha-g ${tipo}"><span>${rotulo}</span><span class="b" style="--v:${f.chance * 100 * 1.5}"></span><b>${pct(f.chance)}</b></div>`;
    }).join("");

    if (!meta.teste) return;
    const nomes = [["nota", "Nota do Lead Scorer"], ["so_tempo", "Nota só pelo tempo aberta"], ["preco", "Só o maior preço"],
                   ["obvia", "Nota óbvia: taxa do vendedor no produto × preço"], ["acaso", 'Ao acaso ("feeling")']];
    $("teste-foco").innerHTML = nomes.map(([k, nome]) =>
      `<div class="barra${k === "nota" ? " nossa" : ""}"><span>${nome}</span><span class="b" style="--v:${meta.teste.foco[k] * 100}"></span><b>${pct(meta.teste.foco[k])}</b></div>`).join("") +
      `<p class="sub">A nota ganhou de cada um dos outros jeitos nas 4 datas.</p>`;
    document.querySelector("#teste-previsao tbody").innerHTML = meta.teste.previsao.map((p) => `
      <tr><td>${dataBR(p.data)}</td><td class="num">${milhoes(p.crm)}</td><td class="num">${milhoes(p.previsao)}</td><td class="num">${milhoes(p.real)}</td></tr>`).join("");
  }

  // ---------- eventos ----------
  function desenhar() { desenharVendedor(); desenharChefe(); }

  preencher($("f-vendedor"), vendedores, vendedor, "Escolha seu nome");
  $("f-vendedor").addEventListener("change", (e) => {
    if (!e.target.value) return;
    vendedor = e.target.value;
    gravar(CHAVE_VENDEDOR, vendedor);
    Object.keys(qtd).forEach((k) => { qtd[k] = POR_PAGINA; });
    desenharVendedor();
  });
  $("f-regiao").addEventListener("change", (e) => { filtroChefe.regiao = e.target.value; desenharChefe(); });
  $("f-gerente").addEventListener("change", (e) => { filtroChefe.gerente = e.target.value; desenharChefe(); });

  $("aba-vendedor").addEventListener("click", (e) => {
    const mais = e.target.closest("button[data-mais]");
    if (mais) { qtd[mais.dataset.mais] += POR_PAGINA; desenharVendedor(); return; }
    const b = e.target.closest("button[data-id]");
    if (!b) return;
    if (b.dataset.marca) marcas[b.dataset.id] = b.dataset.marca;
    else delete marcas[b.dataset.id];
    gravar(CHAVE_MARCAS, marcas);
    desenharVendedor();
  });

  document.querySelectorAll(".aba").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((x) => x.classList.toggle("ativa", x === b));
    ["vendedor", "chefe", "como"].forEach((a) => { $("aba-" + a).hidden = a !== b.dataset.aba; });
  }));
  $("limpar").addEventListener("click", () => { marcas = {}; gravar(CHAVE_MARCAS, marcas); desenhar(); });

  // ---------- início ----------
  $("hoje").textContent = dataBR(meta.hoje);
  document.querySelectorAll(".prazo").forEach((x) => { x.textContent = meta.prazo_maximo; });
  document.querySelectorAll(".nota-minima").forEach((x) => { x.textContent = meta.nota_minima; });
  desenharComo();
  desenhar();
})();
