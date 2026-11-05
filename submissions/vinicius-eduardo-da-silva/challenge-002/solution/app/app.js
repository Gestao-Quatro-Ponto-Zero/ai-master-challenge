"use strict";

const MODEL = window.TRIAGE_MODEL;
const DATA = window.TRIAGE_DATA;
const RESULTS = DATA.results;

const TABS = [
  { id: "triagem", label: "Triagem ao vivo" },
  { id: "lote", label: "Teste em lote" },
  { id: "diagnostico", label: "Diagnóstico" },
  { id: "fluxo", label: "Fluxo proposto" },
  { id: "roi", label: "Cenário de ROI" },
  { id: "como", label: "Como funciona" },
];

const LANES = {
  rotear: { label: "Rotear sozinho", short: "Rotear" },
  sugerir: { label: "Sugerir ao atendente", short: "Sugerir" },
  humano: { label: "Enviar a um humano", short: "Humano" },
};

const REASONS = {
  sensivel: "Tem uma palavra sensível. Esses casos sempre vão para uma pessoa, seja qual for a confiança.",
  desconhecido: "Boa parte das palavras é desconhecida para o modelo. Este ticket parece estar fora do que ele aprendeu.",
  incerto: "O modelo está inseguro demais até para sugerir uma categoria.",
  categoria_protegida: "A categoria envolve privilégios de acesso. O sistema sugere, mas uma pessoa confirma.",
  confianca_media: "A confiança é média. O atendente confirma com um clique ou troca a categoria.",
  confianca_alta: "A confiança é alta, o vocabulário é conhecido e não há sinal de assunto sensível.",
};

const DEFAULT_ROI = { tickets: 30000, triage: 3, suggested: 1, rework: 15, cost: 45 };
const STORAGE_ROI = "triagem.roi";

const state = {
  tab: "triagem",
  text: DATA.examples[0].text,
  threshold: MODEL.routeConfidence,
  laneFilter: "todos",
  roi: readRoi(),
};

function readRoi() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_ROI) || "{}");
    return { ...DEFAULT_ROI, ...(stored && typeof stored === "object" ? stored : {}) };
  } catch {
    return { ...DEFAULT_ROI };
  }
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]
  ));
}

const percent = (value, digits = 0) => `${(value * 100).toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits })}%`;
const count = (value) => Math.round(value).toLocaleString("pt-BR");
const decimal = (value, digits = 1) => value.toLocaleString("pt-BR", { maximumFractionDigits: digits });

/* Model: must match scoring in training/triage_model.py, checked in tests/ui_check.py */

const wordIndex = new Map(MODEL.words.map((word, index) => [word, index]));
const sensitiveWords = new Set(MODEL.sensitiveWords);
const neverRoute = new Set(MODEL.neverRoute);

function tokenize(text) {
  return String(text).toLowerCase().match(/[\p{L}\p{N}_]{2,}/gu) || [];
}

function decide(confidence, category, knownShare, sensitive) {
  if (sensitive) return ["humano", "sensivel"];
  if (knownShare < MODEL.guard) return ["humano", "desconhecido"];
  if (confidence < MODEL.suggestConfidence) return ["humano", "incerto"];
  if (neverRoute.has(category)) return ["sugerir", "categoria_protegida"];
  if (confidence < MODEL.routeConfidence) return ["sugerir", "confianca_media"];
  return ["rotear", "confianca_alta"];
}

function classify(text) {
  const tokens = tokenize(text);
  const counts = new Map();
  let known = 0;
  for (const token of tokens) {
    const index = wordIndex.get(token);
    if (index !== undefined) {
      known += 1;
      counts.set(index, (counts.get(index) || 0) + 1);
    }
  }
  const entries = [...counts].map(([index, tf]) => [index, (1 + Math.log(tf)) * MODEL.idf[index]]);
  const norm = Math.sqrt(entries.reduce((total, [, value]) => total + value * value, 0)) || 1;
  const scores = MODEL.intercept.slice();
  for (const [index, value] of entries) {
    MODEL.coef[index].forEach((weight, category) => { scores[category] += weight * (value / norm); });
  }
  const largest = Math.max(...scores);
  const exponentials = scores.map((score) => Math.exp(score - largest));
  const total = exponentials.reduce((sum, value) => sum + value, 0);
  const probabilities = exponentials.map((value) => value / total);
  const ranked = MODEL.categories.map((name, index) => ({ name, probability: probabilities[index], index })).sort((a, b) => b.probability - a.probability);
  const top = ranked[0];
  const knownShare = tokens.length ? known / tokens.length : 0;
  const sensitive = tokens.filter((token) => sensitiveWords.has(token));
  const [lane, reason] = decide(top.probability, top.name, knownShare, sensitive.length > 0);
  const drivers = entries
    .map(([index, value]) => ({ word: MODEL.words[index], weight: MODEL.coef[index][top.index] * (value / norm) }))
    .filter((item) => item.weight > 0)
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 6);
  return { ranked, top, lane, reason, knownShare, sensitive: [...new Set(sensitive)], drivers, wordCount: tokens.length };
}

/* Shared pieces */

function dot(lane) {
  return `<span class="dot ${lane}" aria-hidden="true"></span>`;
}

function laneStack(rotear, sugerir, humano) {
  const part = (lane, value) => `<i class="${lane}" style="flex:${value} 1 0" title="${LANES[lane].short}: ${percent(value, 1)}"></i>`;
  return `<div class="stack" role="img" aria-label="Rotear ${percent(rotear)}, sugerir ${percent(sugerir)}, humano ${percent(humano)}">${part("rotear", rotear)}${part("sugerir", sugerir)}${part("humano", humano)}</div>`;
}

function columnChart(items, axisLabels, describe) {
  const largest = Math.max(...items.map((item) => item.value));
  const columns = items.map((item) => {
    const height = (item.value / largest) * 82;
    return `<div class="column ${item.kind || ""}" title="${escapeHtml(describe(item))}">
      ${item.label ? `<b style="bottom:calc(${height}% + 2px)">${item.label}</b>` : ""}
      <i style="height:${height}%"></i>
    </div>`;
  }).join("");
  return `<div class="columns" role="img" aria-label="${escapeHtml(items.map(describe).join("; "))}">${columns}</div>
    <div class="axis">${axisLabels.map((label) => `<span>${label}</span>`).join("")}</div>`;
}

/* Triagem ao vivo */

function resultPanel(text) {
  if (!text.trim()) return `<p class="muted">Cole um ticket para ver a decisão.</p>`;
  const result = classify(text);
  const bars = result.ranked.slice(0, 3).map((item, index) => `
    <div class="bar-row ${index === 0 ? "top-row" : ""}">
      <span>${escapeHtml(item.name)}</span>
      <span class="bar-track"><i style="width:${item.probability * 100}%"></i></span>
      <span class="amount">${percent(item.probability)}</span>
    </div>`).join("");
  const drivers = result.drivers.length
    ? result.drivers.map((item) => `<span class="word">${escapeHtml(item.word)}</span>`).join("")
    : `<span class="muted">Nenhuma palavra conhecida pesou a favor.</span>`;
  const mark = (ok) => (ok ? "✓" : "✕");
  return `
    <div class="verdict">
      <div class="verdict-lane" id="live-lane">${dot(result.lane)}${LANES[result.lane].label}</div>
      <p id="live-reason">${REASONS[result.reason]}</p>
    </div>
    <h3>Categoria provável</h3>
    <div id="live-bars">${bars}</div>
    <h3 style="margin-top:12px">Palavras que pesaram</h3>
    <div>${drivers}</div>
    <h3 style="margin-top:12px">Travas</h3>
    <ul class="checks">
      <li>${mark(result.top.probability >= MODEL.routeConfidence)} Confiança de ${percent(result.top.probability)} (mínimo de ${percent(MODEL.routeConfidence)} para rotear)</li>
      <li>${mark(result.knownShare >= MODEL.guard)} ${percent(result.knownShare)} das palavras conhecidas (mínimo de ${percent(MODEL.guard)})</li>
      <li>${mark(result.sensitive.length === 0)} ${result.sensitive.length ? `Palavra sensível: ${result.sensitive.map(escapeHtml).join(", ")}` : "Sem palavra sensível"}</li>
      <li>${mark(!neverRoute.has(result.top.name))} ${neverRoute.has(result.top.name) ? "Categoria protegida" : "Categoria não protegida"}</li>
    </ul>`;
}

function viewTriagem() {
  const examples = DATA.examples.map((example, index) => `<button class="chip-button" data-example="${index}">${escapeHtml(example.label)}</button>`).join("");
  return `
    <h1>Cole um ticket e veja a decisão</h1>
    <p class="lead">O modelo roda aqui no navegador, e nada é enviado para fora. A ação possível é só rotear: o sistema nunca responde ao cliente sozinho.</p>
    <div class="grid-2">
      <section class="card">
        <label for="ticket-text"><h2>Ticket</h2></label>
        <textarea id="ticket-text" spellcheck="false">${escapeHtml(state.text)}</textarea>
        <p class="muted" style="margin-top:10px">Exemplos reais dos dados:</p>
        <div class="chips">${examples}</div>
      </section>
      <section class="card" id="live-result">${resultPanel(state.text)}</section>
    </div>
    <p class="muted" style="margin-top:12px">Os textos do dataset estão pré-processados e em inglês, então o modelo funciona melhor nesse formato. Para outro idioma ou empresa, ele precisaria ser treinado de novo.</p>`;
}

/* Teste em lote */

function policyAt(threshold) {
  let routed = 0;
  let routedRight = 0;
  let suggested = 0;
  let suggestedRight = 0;
  for (const [confidence, predicted, label, known, sensitive] of DATA.replay) {
    const category = MODEL.categories[predicted];
    let lane = "rotear";
    if (sensitive || !known || confidence < MODEL.suggestConfidence) lane = "humano";
    else if (neverRoute.has(category) || confidence < threshold) lane = "sugerir";
    if (lane === "rotear") {
      routed += 1;
      if (predicted === label) routedRight += 1;
    } else if (lane === "sugerir") {
      suggested += 1;
      if (predicted === label) suggestedRight += 1;
    }
  }
  const total = DATA.replay.length;
  return {
    routedShare: routed / total,
    suggestedShare: suggested / total,
    humanShare: (total - routed - suggested) / total,
    accuracy: routed ? routedRight / routed : 0,
    errorsPer100: routed ? (1 - routedRight / routed) * 100 : 0,
    errorsPerThousand: (routed - routedRight) / total * 1000,
  };
}

function sliderResult() {
  const policy = policyAt(state.threshold);
  return `
    <div class="tiles" style="margin:12px 0 4px">
      <div class="tile"><div class="label">Roteados sozinhos</div><div class="number" id="slider-coverage">${percent(policy.routedShare, 1)}</div><div class="detail">do total de tickets</div></div>
      <div class="tile"><div class="label">Acerto nos roteados</div><div class="number" id="slider-accuracy">${percent(policy.accuracy, 1)}</div><div class="detail">nas últimas 20% das linhas</div></div>
      <div class="tile"><div class="label">Erros por 100 roteados</div><div class="number">${decimal(policy.errorsPer100)}</div><div class="detail">vão para o time errado</div></div>
    </div>
    ${laneStack(policy.routedShare, policy.suggestedShare, policy.humanShare)}
    <div class="legend">
      <span>${dot("rotear")}Rotear ${percent(policy.routedShare)}</span>
      <span>${dot("sugerir")}Sugerir ${percent(policy.suggestedShare)}</span>
      <span>${dot("humano")}Humano ${percent(policy.humanShare)}</span>
    </div>`;
}

function ticketRow(ticket) {
  const check = ticket.label === null
    ? `<span class="muted">Sem categoria real para comparar</span>`
    : ticket.label === ticket.predicted
      ? `<span class="right">✓ ${escapeHtml(ticket.predicted)}</span>`
      : `<span class="wrong">✕ ${escapeHtml(ticket.predicted)}, era ${escapeHtml(ticket.label)}</span>`;
  return `
    <article class="ticket">
      <div class="ticket-head">
        <span class="ticket-lane">${dot(ticket.lane)}${LANES[ticket.lane].short} · ${percent(ticket.confidence)}</span>
        ${check}
      </div>
      <p class="ticket-text">${escapeHtml(ticket.text)}${ticket.fullText ? "" : "…"}</p>
      <button class="chip-button" data-try="${escapeHtml(ticket.text)}">Testar na triagem</button>
    </article>`;
}

function batchList() {
  const filter = state.laneFilter;
  const source = filter === "clientes" ? DATA.customerSamples : DATA.samples;
  const shown = source.filter((ticket) => {
    if (filter === "todos" || filter === "clientes") return true;
    if (filter === "erros") return ticket.lane === "rotear" && ticket.label !== ticket.predicted;
    return ticket.lane === filter;
  });
  return shown.slice(0, 40).map(ticketRow).join("") || `<p class="muted">Nenhum ticket neste filtro.</p>`;
}

function viewLote() {
  const { lanes, routedErrorsPer100: errors, transfer, accuracy, categories, drift } = RESULTS;
  const filters = [
    ["todos", "Todos"], ["rotear", "Roteados"], ["erros", "Roteados errados"], ["sugerir", "Sugeridos"], ["humano", "Humano"], ["clientes", "Tickets de clientes"],
  ].map(([id, label]) => `<button class="filter" data-filter="${id}" aria-pressed="${state.laneFilter === id}">${label}</button>`).join("");
  const categoryRows = categories.map((row) => `
    <tr>
      <td>${escapeHtml(row.category)}</td>
      <td>${count(row.tickets)}</td>
      <td>${percent(row.recall)}</td>
      <td>${percent(row.routedShare)}</td>
      <td>${row.routedPrecision === null ? "Nunca roteado" : percent(row.routedPrecision)}</td>
    </tr>`).join("");
  const driftItems = drift.map((row) => ({ value: row.accuracy, label: percent(row.accuracy), block: row.block, share: row.hardwareShare }));
  return `
    <h1>O que aconteceu com ${count(RESULTS.tickets.test)} tickets nunca vistos</h1>
    <p class="lead">O modelo aprendeu com as primeiras 80% das linhas e foi testado nas últimas 20%. A divisão aleatória, mais otimista, daria ${percent(accuracy.randomSplit, 1)} de acerto; nesta, foram ${percent(accuracy.orderSplit, 1)}. Chutar sempre a maior categoria daria ${percent(accuracy.majority, 1)}.</p>

    <section class="card">
      <h2>Onde parar a automação?</h2>
      <p class="muted">Mova a confiança mínima para rotear e veja o custo de automatizar mais. As demais travas continuam valendo. A proposta usa ${percent(MODEL.routeConfidence)}.</p>
      <label for="threshold" class="slider-value" id="threshold-label">${percent(state.threshold)}</label>
      <input id="threshold" type="range" min="0.5" max="0.99" step="0.01" value="${state.threshold}">
      <div id="slider-result">${sliderResult()}</div>
    </section>

    <div class="grid-2" style="margin-bottom:16px">
      <section class="card">
        <h2>Tickets de clientes: a trava funcionou</h2>
        <p>Sem a trava, o modelo rotearia ${percent(transfer.routedWithoutGuard)} dos ${count(transfer.tickets)} tickets de clientes, um assunto que ele nunca viu. Ele diria Hardware para ${percent(transfer.hardwareShare)} deles, seja qual for o tipo.</p>
        <div class="result-line">${percent(transfer.lanes.humano, 1)} vão para um humano</div>
        <p class="muted" style="margin-top:6px">Roteados com a trava: ${percent(transfer.routedWithGuard, 2)}. Tickets de TI bloqueados: ${percent(transfer.itGuardBlocked, 1)}.</p>
      </section>
      <section class="card">
        <h2>Acerto ao longo do arquivo</h2>
        <p class="muted">Cada barra testa um décimo das linhas, com treino nas anteriores. A ordem é só uma aproximação do tempo. A queda coincide com a alta de Hardware, de ${percent(drift[0].hardwareShare)} para ${percent(drift[drift.length - 1].hardwareShare)}.</p>
        ${columnChart(driftItems, drift.map((row) => row.block), (item) => `Bloco ${item.block}: ${percent(item.value, 1)} de acerto`)}
      </section>
    </div>

    <h2 class="section-title">Por categoria</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Categoria</th><th>Tickets no teste</th><th>Encontrados</th><th>Roteados sozinhos</th><th>Acerto quando roteado</th></tr></thead>
      <tbody>${categoryRows}</tbody>
    </table></div>
    <p class="muted" style="margin-top:8px">Atenção: Purchase quase some no fim do arquivo e tem só ${categories.find((row) => row.category === "Purchase").tickets} tickets no teste, com baixo acerto. Em produção, isso dispararia um alerta de deriva.</p>

    <h2 class="section-title">Veja os tickets</h2>
    <div class="toolbar" role="group" aria-label="Filtrar tickets">${filters}</div>
    <div id="batch-list">${batchList()}</div>
    <p class="muted" style="margin-top:8px">Amostra aleatória de ${count(DATA.samples.length)} tickets do teste, mostrando até 40. Acerto dos roteados na base inteira: ${percent(lanes.rotear.accuracy, 1)}, ou ${decimal(errors)} erros por 100.</p>`;
}

/* Diagnóstico */

function viewDiagnostico() {
  const { support } = RESULTS;
  const { bottleneck, satisfaction } = support;
  const gapItems = bottleneck.histogram.map((bin) => ({
    value: bin.count,
    from: bin.from,
    to: bin.to,
    kind: bottleneck.observedGap >= bin.from && bottleneck.observedGap < bin.to ? "hit" : "",
  }));
  const hoursItems = support.hoursHistogram.map((bin) => ({ value: bin.count, label: count(bin.count), from: bin.from, to: bin.to, kind: bin.to <= 0 ? "hit" : "" }));
  const ratingItems = Object.entries(satisfaction.distribution).map(([rating, value]) => ({ value, rating, label: count(value) }));
  return `
    <h1>O que os dados de suporte permitem responder</h1>
    <p class="lead">Foram analisados ${count(support.rows)} tickets, não os ~30.000 descritos. Cada padrão foi comparado com dados embaralhados, para não apresentar ruído como descoberta. <strong>Nestes dados, as três perguntas não têm resposta confiável.</strong></p>

    <section class="card">
      <span class="answer-tag">! Sem resposta confiável</span>
      <h2>1. Onde o fluxo trava?</h2>
      <p class="claim">Parece ser ${escapeHtml(bottleneck.worst.name)}: ${decimal(bottleneck.worst.hours)}h, contra ${decimal(bottleneck.best.hours)}h na melhor combinação.</p>
      <p>Mas a diferença de ${decimal(bottleneck.observedGap)}h é o que o acaso produz. Com os tempos embaralhados, ela fica em ${decimal(bottleneck.shuffledMean)}h em média (p = ${decimal(bottleneck.pValue, 2)}). Atacar essa combinação seria perseguir ruído.</p>
      ${columnChart(gapItems, gapItems.map((item, index) => (index % 2 === 0 ? decimal(item.from) : "")), (item) => `${decimal(item.from)} a ${decimal(item.to)}h: ${count(item.value)} embaralhamentos`)}
      <div class="legend"><span><i class="swatch plain"></i>Diferença em ${count(2000)} embaralhamentos, em horas</span><span><i class="swatch hit"></i>Faixa da diferença real, ${decimal(bottleneck.observedGap)}h</span></div>
    </section>

    <section class="card">
      <span class="answer-tag">! Sem resposta confiável</span>
      <h2>2. O que impacta a satisfação?</h2>
      <p class="claim">Nada do que está no arquivo se distingue do acaso.</p>
      <p>As notas se distribuem por igual. Nenhum dos ${satisfaction.testsRun} fatores testados é relevante (menor p = ${decimal(satisfaction.smallestP, 2)}), e a correlação com o tempo de resolução é de ${decimal(satisfaction.hoursCorrelation, 2)}. Um modelo não supera rótulos embaralhados (R² de ${decimal(satisfaction.r2, 2)} contra ${decimal(satisfaction.r2Shuffled, 2)}).</p>
      ${columnChart(ratingItems, ratingItems.map((item) => `Nota ${item.rating}`), (item) => `Nota ${item.rating}: ${count(item.value)} tickets`)}
    </section>

    <section class="card">
      <span class="answer-tag">! Não dá para medir</span>
      <h2>3. Quanto estamos desperdiçando?</h2>
      <p class="claim">${percent(support.negativeShare)} dos tickets encerrados são resolvidos antes da primeira resposta.</p>
      <p>Isso não faz sentido em uma operação real. Além disso, não existe data de abertura, e as primeiras respostas se concentram em ${decimal(support.firstResponseSpanHours, 0)} horas. Sem um relógio confiável, qualquer número de horas desperdiçadas seria inventado.</p>
      ${columnChart(hoursItems, hoursItems.map((item) => item.from), (item) => `${item.from} a ${item.to}h: ${count(item.value)} tickets`)}
      <div class="legend"><span><i class="swatch hit"></i>Resolução antes da primeira resposta</span><span><i class="swatch plain"></i>Resolução depois</span><span>Horas entre a primeira resposta e a resolução</span></div>
    </section>

    <section class="card">
      <h2>Os textos também não ajudam</h2>
      <p>${percent(support.text.placeholderShare)} das descrições têm o marcador literal <code>{product_purchased}</code>, e as resoluções não têm relação com o problema, como: <em>"${escapeHtml(support.text.exampleResolution)}"</em> Por isso, não dá para treinar um classificador de tickets de clientes com este arquivo.</p>
    </section>

    <section class="card">
      <h2>O que capturar para responder de verdade</h2>
      <ul class="plain">
        <li><strong>Datas confiáveis:</strong> abertura, primeira resposta, cada transferência e encerramento.</li>
        <li><strong>Tempo de trabalho:</strong> tempo ativo do atendente, separado do tempo de espera do cliente.</li>
        <li><strong>Transferências:</strong> quantas vezes o ticket mudou de fila, a causa mais provável de retrabalho.</li>
        <li><strong>Satisfação:</strong> taxa de resposta da pesquisa, já que só tickets encerrados têm nota.</li>
        <li><strong>Texto real:</strong> descrição e resolução, com dados pessoais removidos, para treinar e medir o modelo.</li>
      </ul>
    </section>`;
}

/* Fluxo */

function evidenceExample(title, explanation, text) {
  return `
    <article class="ticket">
      <h3>${title}</h3>
      <p class="ticket-text" style="color:var(--ink)">${explanation}</p>
      <p class="ticket-text">${escapeHtml(text)}</p>
    </article>`;
}

function viewFluxo() {
  const { lanes } = RESULTS;
  const confidentMistake = DATA.samples.find((ticket) => ticket.lane === "rotear" && ticket.label !== ticket.predicted && ticket.fullText);
  const step = (number, title, text) => `<div class="step"><span class="step-number">${number}</span><div><h3>${title}</h3><p>${text}</p></div></div>`;
  return `
    <h1>Como funcionaria na prática</h1>
    <p class="lead">A IA decide só para onde o ticket vai. A resposta ao cliente continua com uma pessoa.</p>
    <div class="flow">
      ${step(1, "O ticket entra", "Por e-mail, chat, telefone ou redes sociais, e o texto é registrado. Dados pessoais são removidos antes do modelo.")}
      ${step(2, "Trava de assunto sensível", "Palavras como demissão, salário, assédio ou fraude levam o ticket direto a uma pessoa.")}
      ${step(3, "Trava de ticket desconhecido", `Se menos de ${percent(MODEL.guard)} das palavras forem conhecidas, o ticket vai para uma pessoa, pois a confiança do modelo não vale fora do que ele aprendeu.`)}
      ${step(4, "O modelo classifica", "Ele indica a categoria, a confiança e as palavras que pesaram na decisão.")}
      ${step(5, "A política decide a fila", "O sistema roteia, sugere ou envia a um humano, conforme as regras abaixo.")}
      ${step(6, "O humano corrige, e o sistema aprende", "Cada correção vira um dado de treino. Acerto e deriva são acompanhados toda semana.")}
    </div>

    <div class="lanes">
      <div class="lane-card rotear"><h3>Rotear sozinho</h3><div class="number">${percent(lanes.rotear.share)}</div><p>Confiança de ${percent(MODEL.routeConfidence)} ou mais. Acerto de ${percent(lanes.rotear.accuracy, 1)} no teste.</p></div>
      <div class="lane-card sugerir"><h3>Sugerir ao atendente</h3><div class="number">${percent(lanes.sugerir.share)}</div><p>A categoria certa está nas 2 primeiras opções em ${percent(lanes.sugerir.top2, 1)} dos casos.</p></div>
      <div class="lane-card humano"><h3>Enviar a um humano</h3><div class="number">${percent(lanes.humano.share)}</div><p>Assunto sensível, ticket desconhecido ou modelo inseguro.</p></div>
    </div>

    <div class="grid-2">
      <section class="card">
        <h2>O que automatizar</h2>
        <ul class="plain">
          <li><strong>Roteamento</strong> dos tickets em que o modelo é confiável.</li>
          <li><strong>Sugestão de categoria</strong> para o atendente confirmar.</li>
          <li><strong>Alerta de deriva</strong>, quando o acerto ou a mistura de categorias muda.</li>
        </ul>
      </section>
      <section class="card">
        <h2>O que não automatizar</h2>
        <ul class="plain">
          <li><strong>A resposta ao cliente.</strong> As resoluções do dataset não têm sentido, então não há como treinar isso nem medir a qualidade.</li>
          <li><strong>Assuntos sensíveis.</strong> Um erro com demissão ou assédio afeta uma pessoa. Isso é julgamento nosso, não vem dos dados.</li>
          <li><strong>Acessos de administrador.</strong> Envolvem privilégios, e essa categoria foi das mais instáveis no teste.</li>
          <li><strong>A prioridade.</strong> A prioridade registrada não se relaciona com o texto nos dados, então não há como aprendê-la.</li>
        </ul>
      </section>
    </div>

    <h2 class="section-title">Exemplos reais dos dados</h2>
    ${evidenceExample("Assunto sensível: vai para uma pessoa", "Tem uma palavra da lista sensível, então a confiança do modelo não é considerada.", DATA.examples[2].text)}
    ${evidenceExample("Acesso de administrador: só sugestão", "Mesmo que o modelo acerte, conceder privilégio exige a confirmação de uma pessoa.", DATA.examples[3].text)}
    ${evidenceExample("Ticket de cliente: bloqueado pela trava", "O modelo até escolhe uma categoria, mas o assunto está fora do que ele aprendeu.", DATA.examples[4].text)}
    ${confidentMistake ? evidenceExample(`Por que há um humano no ciclo: confiança de ${percent(confidentMistake.confidence)} e erro`, `O modelo roteou como ${escapeHtml(confidentMistake.predicted)}, mas o correto era ${escapeHtml(confidentMistake.label)}. Por isso, as correções precisam voltar para o sistema.`, confidentMistake.text) : ""}

    <section class="card" style="margin-top:16px">
      <h2>Como começar: modo sombra</h2>
      <p>O modelo foi treinado com tickets internos de TI e não funciona nos tickets de clientes. O caminho seguro é:</p>
      <ul class="plain">
        <li><strong>Coletar:</strong> reunir tickets reais, com a fila correta, e treinar o modelo de novo.</li>
        <li><strong>Modo sombra:</strong> o sistema decide em paralelo, sem afetar nenhum cliente, e comparamos com o que os atendentes fizeram.</li>
        <li><strong>Ligar por etapas:</strong> primeiro a sugestão, depois o roteamento nas categorias que atingirem o acerto definido com o Diretor.</li>
      </ul>
    </section>`;
}

/* ROI */

function roiResult() {
  const { tickets, triage, suggested, rework, cost } = state.roi;
  const { lanes, routedErrorsPer100 } = RESULTS;
  const errorRate = routedErrorsPer100 / 100;
  const routedTickets = tickets * lanes.rotear.share;
  const suggestedTickets = tickets * lanes.sugerir.share;
  const savedRouted = (routedTickets * triage) / 60;
  const savedSuggested = (suggestedTickets * Math.max(triage - suggested, 0)) / 60;
  const lost = (routedTickets * errorRate * rework) / 60;
  const net = savedRouted + savedSuggested - lost;
  const breakEven = routedTickets > 0 ? ((savedRouted + savedSuggested) * 60) / (routedTickets * errorRate) : 0;
  return `
    <div class="result-line" id="roi-net">${net >= 0 ? "" : "Perda de "}${count(Math.abs(net))} horas por ano${net >= 0 ? " economizadas" : ""}</div>
    <p style="margin-top:6px">Cerca de ${count(Math.abs(net) / 12)} horas por mês, ou R$ ${count(Math.abs(net) * cost)} por ano.</p>
    <div class="table-wrap"><table>
      <tbody>
        <tr><td>Triagem evitada nos roteados (${percent(lanes.rotear.share)})</td><td>+${count(savedRouted)} h</td></tr>
        <tr><td>Triagem mais rápida nos sugeridos (${percent(lanes.sugerir.share)})</td><td>+${count(savedSuggested)} h</td></tr>
        <tr><td>Retrabalho nos roteados errados (${decimal(routedErrorsPer100)} em 100)</td><td>−${count(lost)} h</td></tr>
      </tbody>
    </table></div>
    <p class="muted" style="margin-top:8px">A economia acaba se cada erro custar mais de ${count(breakEven)} minutos de retrabalho.</p>`;
}

function viewRoi() {
  const field = (key, label, note) => `
    <label>${label}
      <input type="number" min="0" step="1" value="${state.roi[key]}" data-roi="${key}">
      <small>${note}</small>
    </label>`;
  return `
    <h1>Cenário de ROI</h1>
    <p class="lead">Os dados não têm tempo de trabalho nem custo, então <strong>este é um cenário, não uma medição</strong>. Só as taxas de acerto e de cobertura vêm do teste.</p>
    <section class="card" style="border-left:4px solid var(--warning)">
      <strong>Importante:</strong> essas taxas vêm de tickets internos de TI. Nos tickets de clientes, o modelo atual não roteia quase nada. O cenário vale só depois de treinar com tickets reais e confirmar as taxas em modo sombra.
    </section>
    <section class="card">
      <h2>Premissas: ajuste com o time</h2>
      <div class="inputs">
        ${field("tickets", "Tickets por ano", "Do enunciado")}
        ${field("triage", "Minutos para triar um ticket", "Premissa, não medida")}
        ${field("suggested", "Minutos com a sugestão pronta", "Premissa, não medida")}
        ${field("rework", "Minutos de retrabalho por erro", "Premissa, não medida")}
        ${field("cost", "Custo da hora, em R$", "Premissa, não medida")}
      </div>
    </section>
    <section class="card" id="roi-result">${roiResult()}</section>`;
}

/* Como funciona */

function viewComo() {
  const { tickets, guard, accuracy } = RESULTS;
  return `<section class="card" style="max-width:800px">
    <h1>Como funciona</h1>
    <h2 style="margin-top:16px">O modelo</h2>
    <p>Regressão logística sobre as ${count(MODEL.words.length)} palavras mais frequentes. Escolhemos um modelo simples porque ele roda no navegador, permite ver as palavras que pesaram e ficou perto dos mais complexos testados (cerca de 1 ponto de diferença).</p>
    <h2 style="margin-top:16px">Como foi testado</h2>
    <p>Treino com ${count(tickets.train)} tickets das primeiras 80% das linhas. A trava foi calibrada em ${count(tickets.validation)} tickets separados, e o teste usa os ${count(tickets.test)} das últimas 20%. A divisão por ordem é mais exigente que a aleatória: ${percent(accuracy.orderSplit, 1)} contra ${percent(accuracy.randomSplit, 1)}.</p>
    <h2 style="margin-top:16px">Como os dois datasets se cruzam</h2>
    <p>O dataset de suporte tem as métricas, e o de TI tem textos classificados. Cruzá-los mostrou o principal risco: um modelo pode parecer confiante em tickets que nunca viu. Daí veio a trava de ticket desconhecido, calibrada em ${percent(guard, 1)} das palavras conhecidas.</p>
    <h2 style="margin-top:16px">Limitações</h2>
    <ul class="plain">
      <li><strong>Os dados de suporte parecem artificiais.</strong> Não é possível dizer nada sobre uma operação real a partir deles.</li>
      <li><strong>O modelo não serve hoje para tickets de clientes.</strong> Só funciona no domínio de TI em que foi treinado.</li>
      <li><strong>A ordem das linhas é só uma aproximação do tempo,</strong> pois o arquivo não tem datas.</li>
      <li><strong>Os limites foram escolhidos vendo o teste.</strong> O 0,9 e as categorias protegidas passaram por decisão humana depois de ver esses resultados, então o acerto pode ser um pouco otimista.</li>
      <li><strong>As palavras sensíveis são uma lista fixa, curta e em inglês.</strong> Uma lista real precisaria ser definida com RH e jurídico.</li>
      <li><strong>O ROI é um cenário,</strong> com premissas que não vêm dos dados.</li>
    </ul>
  </section>`;
}

/* Rendering and events */

function renderTabs() {
  document.getElementById("tabs").innerHTML = TABS.map((tab) => (
    `<button class="tab" role="tab" data-tab="${tab.id}" aria-selected="${state.tab === tab.id}">${tab.label}</button>`
  )).join("");
}

function renderView() {
  const views = { triagem: viewTriagem, lote: viewLote, diagnostico: viewDiagnostico, fluxo: viewFluxo, roi: viewRoi, como: viewComo };
  document.getElementById("view").innerHTML = views[state.tab]();
}

function render() {
  renderTabs();
  renderView();
}

document.getElementById("tabs").addEventListener("click", (event) => {
  const button = event.target.closest("[data-tab]");
  if (!button) return;
  state.tab = button.dataset.tab;
  render();
  window.scrollTo(0, 0);
  document.querySelector(`[data-tab="${state.tab}"]`).focus();
});

const view = document.getElementById("view");

view.addEventListener("input", (event) => {
  const { target } = event;
  if (target.id === "ticket-text") {
    state.text = target.value;
    document.getElementById("live-result").innerHTML = resultPanel(state.text);
  } else if (target.id === "threshold") {
    state.threshold = Number(target.value);
    document.getElementById("threshold-label").textContent = percent(state.threshold);
    document.getElementById("slider-result").innerHTML = sliderResult();
  } else if (target.dataset.roi) {
    const value = Number(target.value);
    state.roi[target.dataset.roi] = Number.isFinite(value) && value >= 0 ? value : 0;
    try {
      localStorage.setItem(STORAGE_ROI, JSON.stringify(state.roi));
    } catch {
      // Private windows can block storage. The page keeps working for this visit.
    }
    document.getElementById("roi-result").innerHTML = roiResult();
  }
});

view.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  const { dataset } = target;
  if (dataset.example !== undefined) {
    state.text = DATA.examples[Number(dataset.example)].text;
    renderView();
  } else if (dataset.filter) {
    state.laneFilter = dataset.filter;
    view.querySelectorAll("[data-filter]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.filter === state.laneFilter)));
    document.getElementById("batch-list").innerHTML = batchList();
  } else if (dataset.try !== undefined) {
    state.text = dataset.try;
    state.tab = "triagem";
    render();
    window.scrollTo(0, 0);
  }
});

render();
