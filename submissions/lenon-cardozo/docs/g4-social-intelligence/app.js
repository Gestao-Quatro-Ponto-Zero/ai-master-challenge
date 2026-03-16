const overview = {
  posts: 52214,
  strata: 280,
  errRatio: 0.99995,
  shareRatio: 0.99982,
  lowQuartilePosts: 13054,
};

const globalTopCells = [
  {
    platform: "Instagram",
    title: "Vida cotidiana · sem pagar · vídeo longo",
    creator: "50 mil a 200 mil seguidores",
    n: 136,
    reachLift: 46.7,
    errLift: -0.06,
    shareLift: 0.01,
  },
  {
    platform: "YouTube",
    title: "Beleza · sem pagar · vídeo longo",
    creator: "50 mil a 200 mil seguidores",
    n: 147,
    reachLift: 45.4,
    errLift: 0.54,
    shareLift: 0.3,
  },
  {
    platform: "RedNote",
    title: "Vida cotidiana · sem pagar · vídeo longo",
    creator: "50 mil a 200 mil seguidores",
    n: 142,
    reachLift: 40.8,
    errLift: 0.26,
    shareLift: -0.51,
  },
  {
    platform: "Instagram",
    title: "Beleza · sem pagar · vídeo longo",
    creator: "50 mil a 200 mil seguidores",
    n: 174,
    reachLift: 36.3,
    errLift: 0.31,
    shareLift: -0.12,
  },
  {
    platform: "Bilibili",
    title: "Vida cotidiana · sem pagar · vídeo longo",
    creator: "50 mil a 200 mil seguidores",
    n: 152,
    reachLift: 30.4,
    errLift: 0.31,
    shareLift: 0.35,
  },
];

const platformData = {
  YouTube: {
    eyebrow: "YouTube",
    title: "No YouTube, vídeos mais longos com perfis médios foram os que mais funcionaram.",
    copy:
      "O melhor resultado veio de vídeos mais longos feitos por perfis de tamanho médio. Pagar pode ajudar, mas só em poucos casos que já mostraram melhora.",
    metrics: [
      { label: "Chegou em mais gente", value: "+45.4%" },
      { label: "Recebeu mais reação", value: "+0.54%" },
      { label: "Tamanho do perfil", value: "50 mil a 200 mil" },
    ],
    cells: [
      {
        title: "Beleza · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 147 posts",
        reachLift: 45.4,
        errLift: 0.54,
        shareLift: 0.3,
      },
      {
        title: "Vida cotidiana · pago · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 104 posts",
        reachLift: 50.8,
        errLift: -0.02,
        shareLift: 0.39,
      },
      {
        title: "Vida cotidiana · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 130 posts",
        reachLift: 34.2,
        errLift: -0.21,
        shareLift: 0.26,
      },
    ],
    paid: {
      positive: {
        title: "Aqui vale tentar com mais força",
        copy:
          "Nesse caso, pagar ajudou de verdade. Foi um dos melhores exemplos do conjunto todo.",
        quarter: "2024 · 3º trimestre",
        metrics: [
          { label: "Recebeu mais reação", value: "+0.59%" },
          { label: "Foi mais compartilhado", value: "+1.32%" },
          { label: "Quantidade de posts", value: "294 posts · leitura segura" },
        ],
      },
      negative: {
        title: "Aqui vale parar",
        copy:
          "Nesse caso, pagar piorou o resultado. O post não respondeu tão bem quanto sem pagar.",
        quarter: "2024 · 3º trimestre",
        metrics: [
          { label: "Recebeu menos reação", value: "-0.55%" },
          { label: "Foi menos compartilhado", value: "-0.97%" },
          { label: "Quantidade de posts", value: "263 posts · leitura segura" },
        ],
      },
    },
    audience: {
      label: "50 anos ou mais",
      title: "Foi a faixa com mais compartilhamentos no YouTube.",
      copy:
        "A idade ajuda no detalhe, não muda a regra principal. Aqui, pessoas mais velhas compartilharam um pouco mais.",
      metrics: [
        { label: "Foi mais compartilhado", value: "+0.28%" },
        { label: "Melhor uso", value: "pequeno ajuste da mensagem" },
      ],
    },
    actions: [
      "Aumentar vídeos longos sem pagar com perfis de 50 mil a 200 mil seguidores.",
      "Pagar só nos poucos grupos que já mostraram melhora clara.",
      "Parar de pagar em grupos parecidos com o caso ruim até o resultado melhorar.",
    ],
  },
  Instagram: {
    eyebrow: "Instagram",
    title: "No Instagram, vídeos mais longos com perfis médios foram os que mais deram certo.",
    copy:
      "O melhor caso veio de vídeos longos, sem pagar, com perfis de tamanho médio. Pagar pode ajudar, mas não deve virar regra.",
    metrics: [
      { label: "Chegou em mais gente", value: "+46.7%" },
      { label: "Reação quase igual", value: "-0.06%" },
      { label: "Tamanho do perfil", value: "50 mil a 200 mil" },
    ],
    cells: [
      {
        title: "Vida cotidiana · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 136 posts",
        reachLift: 46.7,
        errLift: -0.06,
        shareLift: 0.01,
      },
      {
        title: "Beleza · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 174 posts",
        reachLift: 36.3,
        errLift: 0.31,
        shareLift: -0.12,
      },
      {
        title: "Beleza · pago · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 92 posts",
        reachLift: 35.9,
        errLift: -0.19,
        shareLift: -1.01,
      },
    ],
    paid: {
      positive: {
        title: "Aqui pagar ajudou",
        copy:
          "Esse foi o melhor caso pago do Instagram. Houve melhora clara em reação e em compartilhamento.",
        quarter: "2023 · 4º trimestre",
        metrics: [
          { label: "Recebeu mais reação", value: "+0.50%" },
          { label: "Foi mais compartilhado", value: "+1.07%" },
          { label: "Quantidade de posts", value: "272 posts · leitura segura" },
        ],
      },
      negative: {
        title: "Aqui não vale insistir",
        copy:
          "Nesse caso, pagar deixou o resultado um pouco pior do que o normal para esse mesmo grupo.",
        quarter: "2024 · 4º trimestre",
        metrics: [
          { label: "Recebeu menos reação", value: "-0.53%" },
          { label: "Foi menos compartilhado", value: "-0.17%" },
          { label: "Quantidade de posts", value: "271 posts · leitura com cuidado" },
        ],
      },
    },
    audience: {
      label: "19 a 35 anos",
      title: "Aqui a idade ajudou pouco.",
      copy:
        "No Instagram, a idade quase não mudou o jogo. O mais importante continuou sendo o tipo de post e o tamanho do perfil.",
      metrics: [
        { label: "Peso da idade", value: "baixo" },
        { label: "Melhor uso", value: "pequeno ajuste da mensagem" },
      ],
    },
    actions: [
      "Aumentar vídeos longos sem pagar em grupos parecidos com o melhor caso.",
      "Pagar só em grupos muito parecidos com o caso bom de 2023.",
      "Evitar pagar em beleza, com perfis muito grandes, até aparecer melhora clara.",
    ],
  },
  TikTok: {
    eyebrow: "TikTok",
    title: "No TikTok, o melhor caminho é testar com cuidado e evitar exagero.",
    copy:
      "O melhor grupo ainda foi o de perfis médios com vídeo longo. Mesmo assim, o ganho foi menor. E pagar já mostrou queda clara em alguns casos.",
    metrics: [
      { label: "Chegou em mais gente", value: "+28.0%" },
      { label: "Foi mais compartilhado", value: "+0.43%" },
      { label: "Tamanho do perfil", value: "50 mil a 200 mil" },
    ],
    cells: [
      {
        title: "Beleza · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 139 posts",
        reachLift: 28.0,
        errLift: 0.01,
        shareLift: 0.43,
      },
      {
        title: "Beleza · pago · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 98 posts",
        reachLift: 27.9,
        errLift: 0.06,
        shareLift: -0.43,
      },
      {
        title: "Vida cotidiana · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 132 posts",
        reachLift: 23.3,
        errLift: 0.23,
        shareLift: -0.59,
      },
    ],
    paid: {
      positive: {
        title: "Aqui é melhor ir devagar",
        copy:
          "No TikTok, pagar ainda não mostrou um caso tão forte quanto em outras redes. Aqui o melhor é testar pouco.",
        quarter: "Sem caso muito forte",
        metrics: [
          { label: "Reação", value: "misturada" },
          { label: "Compartilhamentos", value: "instáveis" },
          { label: "Leitura geral", value: "sem caso muito claro" },
        ],
      },
      negative: {
        title: "Aqui vale parar já",
        copy:
          "Esse foi um dos piores casos pagos do conjunto todo. Pagar reduziu o resultado em vez de ajudar.",
        quarter: "2024 · 3º trimestre",
        metrics: [
          { label: "Recebeu menos reação", value: "-0.79%" },
          { label: "Foi menos compartilhado", value: "-1.00%" },
          { label: "Quantidade de posts", value: "250 posts · leitura com cuidado" },
        ],
      },
    },
    audience: {
      label: "26 a 35 anos",
      title: "Foi a faixa que mais ajudou no TikTok.",
      copy:
        "Essa faixa foi a melhor da rede. Mesmo assim, isso serve mais para ajustar a mensagem do que para decidir dinheiro.",
      metrics: [
        { label: "Recebeu mais reação", value: "+0.05%" },
        { label: "Foi mais compartilhado", value: "+0.09%" },
      ],
    },
    actions: [
      "Usar o TikTok mais como campo de teste do que como aposta principal.",
      "Parar de pagar em grupos parecidos com o caso ruim de beleza com perfis muito grandes.",
      "Usar a faixa de 26 a 35 anos só para ajustar a mensagem.",
    ],
  },
  RedNote: {
    eyebrow: "RedNote",
    title: "No RedNote, perfis médios levaram o post mais longe, e pagar pode ajudar em poucos casos.",
    copy:
      "Essa rede foi boa para fazer o post andar mais. Pagar pode funcionar, mas ainda pede cuidado.",
    metrics: [
      { label: "Chegou em mais gente", value: "+40.8%" },
      { label: "Recebeu mais reação", value: "+0.26%" },
      { label: "Tamanho do perfil", value: "50 mil a 200 mil" },
    ],
    cells: [
      {
        title: "Vida cotidiana · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 142 posts",
        reachLift: 40.8,
        errLift: 0.26,
        shareLift: -0.51,
      },
      {
        title: "Vida cotidiana · pago · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 101 posts",
        reachLift: 33.5,
        errLift: 0.16,
        shareLift: 0.14,
      },
      {
        title: "Beleza · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 146 posts",
        reachLift: 32.7,
        errLift: 0.01,
        shareLift: -0.53,
      },
    ],
    paid: {
      positive: {
        title: "Pode funcionar, mas com cuidado",
        copy:
          "Esse caso pago mostrou melhora, mas ainda pede atenção. Vale como teste curto e com pouco risco.",
        quarter: "2025 · 1º trimestre",
        metrics: [
          { label: "Recebeu mais reação", value: "+0.46%" },
          { label: "Foi mais compartilhado", value: "+0.68%" },
          { label: "Quantidade de posts", value: "236 posts · leitura com cuidado" },
        ],
      },
      negative: {
        title: "Sem caso ruim tão forte",
        copy:
          "O RedNote não trouxe um caso ruim tão claro quanto outras redes. Mesmo assim, ainda não é motivo para soltar dinheiro sem cuidado.",
        quarter: "Leitura atual",
        metrics: [
          { label: "Regra", value: "teste curto" },
          { label: "Escala", value: "só onde já deu certo" },
          { label: "Quão claro foi o resultado", value: "médio" },
        ],
      },
    },
    audience: {
      label: "19 a 25 anos",
      title: "Foi a melhor faixa do RedNote.",
      copy:
        "Essa faixa teve uma pequena vantagem. Ela pode ajudar no ajuste da mensagem, mas não muda a regra principal.",
      metrics: [
        { label: "Recebeu mais reação", value: "+0.06%" },
        { label: "Foi mais compartilhado", value: "+0.14%" },
      ],
    },
    actions: [
      "Aumentar posts sem pagar nos grupos médios que já foram bem.",
      "Testar pago só em poucos grupos e por pouco tempo.",
      "Usar a faixa de 19 a 25 anos só como pequeno ajuste da mensagem.",
    ],
  },
  Bilibili: {
    eyebrow: "Bilibili",
    title: "No Bilibili, o post até chega longe, mas a resposta das pessoas é mais fraca.",
    copy:
      "Essa rede teve alguns grupos com bom alcance, mas com menos força em reação e em compartilhamento. O caso mais equilibrado foi sem pagar.",
    metrics: [
      { label: "Chegou em mais gente", value: "+34.8%" },
      { label: "Foi mais compartilhado", value: "+0.35%" },
      { label: "Tamanho do perfil", value: "50 mil a 200 mil" },
    ],
    cells: [
      {
        title: "Vida cotidiana · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 152 posts",
        reachLift: 30.4,
        errLift: 0.31,
        shareLift: 0.35,
      },
      {
        title: "Beleza · sem pagar · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 158 posts",
        reachLift: 34.8,
        errLift: -0.24,
        shareLift: -0.22,
      },
      {
        title: "Beleza · pago · vídeo longo",
        subtitle: "50 mil a 200 mil seguidores · 118 posts",
        reachLift: 33.3,
        errLift: -0.5,
        shareLift: -0.13,
      },
    ],
    paid: {
      positive: {
        title: "O mais seguro aqui é não pagar",
        copy:
          "O Bilibili não mostrou um caso pago muito forte. O caminho mais seguro continua sendo testar pouco ou ficar no sem pagar.",
        quarter: "Leitura atual",
        metrics: [
          { label: "Melhor caminho", value: "sem pagar" },
          { label: "Pago", value: "só em teste pequeno" },
          { label: "Quão claro foi o resultado", value: "baixo a médio" },
        ],
      },
      negative: {
        title: "Aqui já deu ruim",
        copy:
          "Nesse caso, pagar fez a reação cair. Foi um alerta claro de que o dinheiro pode ir para o lugar errado.",
        quarter: "2023 · 3º trimestre",
        metrics: [
          { label: "Recebeu menos reação", value: "-0.49%" },
          { label: "Foi menos compartilhado", value: "-1.58%" },
          { label: "Quantidade de posts", value: "293 posts · leitura com cuidado" },
        ],
      },
    },
    audience: {
      label: "Idade com pouco peso",
      title: "Aqui a idade quase não mudou o resultado.",
      copy:
        "No Bilibili, a idade não foi forte o bastante para guiar a decisão. O foco continua no tipo de post e no tamanho do perfil.",
      metrics: [
        { label: "Peso da idade", value: "baixo" },
        { label: "O que mais pesa", value: "tipo de post e perfil" },
      ],
    },
    actions: [
      "Usar o Bilibili como apoio, não como principal aposta de dinheiro pago.",
      "Dar preferência aos grupos sem pagar que já mostraram bom alcance.",
      "Se pagar, fazer isso em testes pequenos e fáceis de parar.",
    ],
  },
};

const filterContainer = document.querySelector("#platform-filter");
const globalChart = document.querySelector("#global-top-cells");
const selectedPlatformEyebrow = document.querySelector("#selected-platform-eyebrow");
const selectedPlatformTitle = document.querySelector("#selected-platform-title");
const selectedPlatformCopy = document.querySelector("#selected-platform-copy");
const selectedPlatformMetrics = document.querySelector("#selected-platform-metrics");
const platformCellsChart = document.querySelector("#platform-cells-chart");
const paidPositive = document.querySelector("#paid-positive");
const paidNegative = document.querySelector("#paid-negative");
const audienceCard = document.querySelector("#audience-card");
const actionList = document.querySelector("#action-list");

let currentPlatform = "YouTube";

function formatSignedValue(value, suffix = "%") {
  const signal = value > 0 ? "+" : "";
  const formatted = value.toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1");
  return `${signal}${formatted}${suffix}`;
}

function createSummaryText(row) {
  return `chegou em mais gente ${formatSignedValue(row.reachLift)} · recebeu mais reação ${formatSignedValue(
    row.errLift
  )} · foi mais compartilhado ${formatSignedValue(row.shareLift)}`;
}

function renderBarChart(container, rows) {
  const maxValue = Math.max(...rows.map((row) => row.reachLift));
  container.innerHTML = rows
    .map((row) => {
      const width = `${Math.max(18, (row.reachLift / maxValue) * 100)}%`;
      const tone = row.errLift < 0 && row.shareLift < 0 ? "muted" : "accent";
      return `
        <div class="bar-row">
          <div>
            <span class="bar-title">${row.title}</span>
            <span class="bar-sub">${row.subtitle || `${row.creator} · n=${row.n}`}</span>
          </div>
          <div class="bar-track">
            <span class="bar-fill" data-tone="${tone}" style="--width:${width}"></span>
          </div>
          <div class="bar-value">${createSummaryText(row)}</div>
        </div>
      `;
    })
    .join("");
}

function renderSponsorCard(container, card) {
  container.innerHTML = `
    <div class="detail-card">
      <div class="bar-sub">${card.quarter}</div>
      <h4>${card.title}</h4>
      <p>${card.copy}</p>
      <div class="detail-list">
      ${card.metrics
        .map(
          (metric) => `
            <div class="detail-item">
              <span>${metric.label}</span>
              <strong>${metric.value}</strong>
            </div>
          `
        )
        .join("")}
      </div>
    </div>
  `;
}

function renderAudienceCard(data) {
  audienceCard.innerHTML = `
    <span class="audience-tag">${data.label}</span>
    <h4>${data.title}</h4>
    <p>${data.copy}</p>
    <div class="detail-list">
      ${data.metrics
        .map(
          (metric) => `
            <div class="detail-item">
              <span>${metric.label}</span>
              <strong>${metric.value}</strong>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderActions(items) {
  actionList.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
}

function renderPlatform(platform) {
  currentPlatform = platform;
  const data = platformData[platform];

  selectedPlatformEyebrow.textContent = data.eyebrow;
  selectedPlatformTitle.textContent = data.title;
  selectedPlatformCopy.textContent = data.copy;

  selectedPlatformMetrics.innerHTML = data.metrics
    .map(
      (metric) => `
        <div class="metric-card">
          <span class="panel-label">${metric.label}</span>
          <strong>${metric.value}</strong>
        </div>
      `
    )
    .join("");

  renderBarChart(platformCellsChart, data.cells);
  renderSponsorCard(paidPositive, data.paid.positive);
  renderSponsorCard(paidNegative, data.paid.negative);
  renderAudienceCard(data.audience);
  renderActions(data.actions);

  document.querySelectorAll(".filter-chip").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.platform === platform);
    button.setAttribute("aria-pressed", String(button.dataset.platform === platform));
  });
}

function setupFilters() {
  const platforms = Object.keys(platformData);
  filterContainer.innerHTML = platforms
    .map(
      (platform) => `
        <button
          type="button"
          class="filter-chip ${platform === currentPlatform ? "is-active" : ""}"
          data-platform="${platform}"
          aria-pressed="${platform === currentPlatform}"
        >
          ${platform}
        </button>
      `
    )
    .join("");

  filterContainer.addEventListener("click", (event) => {
    const target = event.target.closest(".filter-chip");
    if (!target) return;
    renderPlatform(target.dataset.platform);
  });
}

function revealOnScroll() {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reducedMotion) {
    document.querySelectorAll(".reveal").forEach((element) => element.classList.add("is-visible"));
    return;
  }
  requestAnimationFrame(() => {
    document.querySelectorAll(".reveal").forEach((element, index) => {
      window.setTimeout(() => element.classList.add("is-visible"), index * 40);
    });
  });
}

renderBarChart(globalChart, globalTopCells);
setupFilters();
renderPlatform(currentPlatform);
revealOnScroll();
