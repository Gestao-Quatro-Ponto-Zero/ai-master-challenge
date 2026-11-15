// Como chegamos aqui (prancha 09): conteúdo fixo do estudo, sem chamada à API.

const STEPS = [
  { title: 'Conversa', text: 'Como vendedor e gestor usam o CRM no dia a dia.' },
  { title: 'Inventário', text: 'O que a base tem e o que falta, antes de analisar.' },
  { title: 'Hipóteses', text: 'Produto, faturamento e histórico, testados um a um.' },
  { title: 'Score e prova', text: 'Chance por idade e calendário, testada no passado.' },
  { title: 'Telas e crítica', text: 'Desenho das telas e crítica de três revisores de IA.' },
  { title: 'Conferência', text: 'Números refeitos do zero por uma segunda implementação.' },
];

const COLUMNS = [
  {
    id: 'pratica',
    tone: 'gold',
    label: 'Rodrigo Costa · Vivência de CRM',
    title: 'O que só veio da prática',
    items: [
      {
        title: '"Esfriou é menos pior que Perdeu."',
        text: 'O vendedor deixa o deal aberto para não registrar a perda. Virou a faixa Sem desfecho e a taxa de ganho que conta esses deals.',
      },
      {
        title: 'Empurrar a data e registrar atividade',
        text: 'São os jeitos de dar cara de ativo a um deal parado. Por isso o score usa a data de entrada, que ninguém atualiza.',
      },
      {
        title: 'O gestor quer as duas leituras',
        text: 'Pipeline declarado e pipeline real aparecem lado a lado, em vez de um número substituir o outro.',
      },
      {
        title: 'Nem todo vendedor abre o sistema',
        text: 'Para quem só reage ao cliente, o gestor recebe uma mensagem pronta com os deals da semana.',
      },
      {
        title: '"Fácil e rápido de validar"',
        text: 'Daí vieram a Máquina do tempo, o acesso simulado e um app que abre sem instalar nada.',
      },
      {
        title: 'Testar faturamento e histórico de compras',
        text: 'As duas hipóteses não entraram no score. Mas foi o teste delas que revelou que o cliente dos deals abertos não é confiável.',
      },
      {
        title: 'Design e ideia de entrega',
        text: 'A ideia de utilizar o design do G4 OS e simular o app como se fosse um módulo do G4 OS, para que sirva de ideia futura de serviço a ser entregue na plataforma.',
      },
    ],
    note: 'Também vieram dele: o score por deal, os Insights da Gabi, o Pipeline por fase, o filtro com e sem cliente, o painel do cliente e a tela de fontes de dados.',
  },
  {
    id: 'ia',
    tone: 'ink',
    label: 'IA · Claude',
    title: 'O que a IA fez',
    items: [
      {
        title: 'Inventário e limpeza',
        text: 'Leu os 4 arquivos e os 8.800 deals, e corrigiu três nomes com grafia errada.',
      },
      {
        title: 'Teste de cada hipótese',
        text: 'Mediu cada sinal proposto e mostrou o número, também quando a resposta era "não muda nada".',
      },
      {
        title: 'O score',
        text: 'Chance por idade do deal e semana do trimestre, calculada só com o que se sabia em cada data.',
      },
      {
        title: 'A prova',
        text: '22 segundas-feiras, 659 listas de vendedores e três regras comparadas. Depois, uma segunda implementação refez tudo do zero.',
      },
      {
        title: 'As telas e o app',
        text: 'Estudo de telas, crítica de três revisores de IA e a construção do app.',
      },
    ],
  },
  {
    id: 'erros',
    tone: 'loss',
    label: 'Correções no caminho',
    title: 'Onde a IA errou',
    items: [
      {
        title: 'Tempo de fechamento inflado',
        text: 'A primeira tabela ignorou que a base não tem fechamentos antes de março de 2017. Foi refeita.',
      },
      {
        title: 'Ranking de vendedores',
        text: 'Parecia mostrar quem acumula deal parado. Era diferença entre regionais, não entre pessoas. Saiu.',
      },
      {
        title: '"Cliente pequeno fecha menos"',
        text: 'Sinal forte e falso, criado pelo cliente trocado nos deals abertos. Foi descartado.',
      },
      {
        title: '+42% contra um adversário fraco',
        text: 'Comparar só com "ordenar por valor" favorecia o score. A prova ganhou uma regra simples mais dura (+22%) e mostra onde o score empata.',
      },
      {
        title: '"Deal aberto quase nunca tem cliente"',
        text: 'No fim da base, um em cada três tem. O erro estava em duas telas e foi pego quando o app recalculou cada frase a partir do dado.',
      },
    ],
  },
];

function stepsMarkup(html) {
  return html`<ol class="chegamos__steps" aria-label="Etapas do trabalho">
    ${STEPS.map((step, index) => html`<li class="chegamos__step">
      <span class="chegamos__step-num" aria-hidden="true">${index + 1}</span>
      <p class="chegamos__step-title"><span class="sr-only">Etapa ${index + 1}: </span>${step.title}</p>
      <p class="chegamos__step-text">${step.text}</p>
    </li>`)}
  </ol>`;
}

function columnMarkup(html, ui, column) {
  const headingId = `chegamos-${column.id}`;
  return html`<section class="chegamos__col chegamos__col--${column.tone}" aria-labelledby="${headingId}">
    <header class="chegamos__col-head">
      <p class="chegamos__col-label">${column.label}</p>
      <h2 class="chegamos__col-title" id="${headingId}">${column.title}</h2>
    </header>
    <ul class="chegamos__items">
      ${column.items.map((item) => html`<li class="chegamos__item">
        <h3 class="chegamos__item-title">${item.title}</h3>
        <p class="chegamos__item-text">${item.text}</p>
      </li>`)}
    </ul>
    ${column.note ? ui.note(column.note) : ''}
  </section>`;
}

export default {
  id: 'chegamos',
  title: 'Como chegamos aqui',
  roles: ['seller', 'manager'],
  area: 'vendas',

  render(root, ctx) {
    const { dom, ui } = ctx;
    const { html } = dom;
    dom.setHtml(root, html`<div class="chegamos">
      ${ui.screenHeader({
        eyebrow: 'Transparência',
        title: 'Como chegamos aqui',
        subtitle: 'Este módulo foi feito por uma pessoa e uma IA. Aqui está o que cada um trouxe, e onde a IA errou.',
      })}
      ${stepsMarkup(html)}
      <div class="chegamos__cols">
        ${COLUMNS.map((column) => columnMarkup(html, ui, column))}
      </div>
    </div>`);
  },
};
