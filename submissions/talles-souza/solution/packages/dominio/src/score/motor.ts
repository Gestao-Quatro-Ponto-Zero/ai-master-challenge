/**
 * O motor de pontos: descobre no histórico quais fatores mudam a chance de um negócio aberto
 * ganhar nos próximos ~3 meses e quanto cada valor pesa, sem nenhum peso digitado.
 *
 * 1. Fatores candidatos por negócio, todos medidos no corte (o que se sabia naquele dia).
 * 2. Pontos por categoria (método HubSpot, escala log): `escala × ln(taxa suavizada ÷ taxa
 *    geral)`; categoria com n pequeno e "sem dado" valem 0.
 * 3. Replay sem olhar o futuro: treino = abertos em R − `treinoDias`, desfecho até R −
 *    `horizonteDias`; validação = abertos em R − `horizonteDias`, desfecho até R.
 * 4. Seleção gulosa fora da amostra pelo AUC na validação.
 * 5. Pesos finais no recorte mais recente (o da validação), só com os fatores escolhidos.
 * 6. Score 0–100: log-odds da taxa base + soma dos pontos ÷ escala, de volta para chance.
 */
import type { Deal } from '../pipeline';

/** Os fatores candidatos. */
export type IdFator =
  | 'idade'
  | 'produto'
  | 'serie'
  | 'setor'
  | 'porte_receita'
  | 'porte_funcionarios'
  | 'vendedor'
  | 'manager'
  | 'escritorio'
  | 'estagio'
  | 'idade_ciclo_produto'
  | 'idade_ciclo_vendedor'
  | 'conta_ganhos'
  | 'conta_perdas'
  | 'conta_taxa'
  | 'conta_ja_comprou'
  | 'empresa_mae'
  | 'preco_receita'
  | 'carga_vendedor';

/** As regras do método (os pesos não: eles saem do histórico). */
export interface ConfigMotor {
  /** Corte do treino = referência − `treinoDias`. */
  treinoDias: number;
  /** Corte da validação = referência − `horizonteDias`; também é o prazo do desfecho. */
  horizonteDias: number;
  /** Categoria com menos negócios que isso no recorte vale 0 ponto. */
  nMinimo: number;
  /** Negócios fictícios na taxa geral somados a cada categoria. */
  suavizacao: number;
  /** Quanto o AUC do score na validação precisa subir para um fator entrar. */
  ganhoMinimoAuc: number;
  /** `pontos = escala × ln(taxa da categoria ÷ taxa geral)`. */
  escala: number;
  /** Tetos das faixas de idade ÷ mediana do ciclo (a última faixa fica sem teto). */
  faixasCiclo: number[];
  /** Em quantas partes os contadores e as razões se dividem (4 = quartis). */
  quantis: number;
  /** false: negócio sem data de início (Prospecting) fica sem score. */
  pontuarSemData: boolean;
  /**
   * Como a soma dos pontos vira chance. `log_odds`: logit(base) + pontos ÷ escala. `razao`:
   * base × e^(pontos ÷ escala), com teto 1 (os pontos são log de razão de taxas).
   */
  conversao: 'log_odds' | 'razao';
}

/** Uma faixa de idade (teto inclusivo; null = sem teto). */
export interface FaixaDeIdadeDoMotor {
  ateDias: number | null;
}

/** Por que um fator ficou dentro ou fora do score. */
export type MotivoDoFator = 'entrou' | 'nao_melhorou' | 'n_pequeno';

/** Por que uma parcela (ou categoria) vale o que vale. */
export type MotivoDaParcela = 'pontua' | 'sem_dado' | 'n_pequeno' | 'fora_do_score';

/** Uma categoria de um fator, com o que aconteceu com ela num recorte. */
export interface CategoriaDoFator {
  chave: string;
  /** "41 a 50 dias", "GTX Pro", "1º quartil (até 22)". */
  rotulo: string;
  n: number;
  ganhos: number;
  /** `ganhos ÷ n`, sem suavizar. */
  taxa: number;
  pontos: number;
  motivo: MotivoDaParcela;
}

/** Um fator medido pelo motor. */
export interface FatorDoMotor {
  id: IdFator;
  rotulo: string;
  /** Óbvio (está no CRM) ou derivado (calculado do histórico até o corte). */
  tipo: 'obvio' | 'derivado';
  entrou: boolean;
  motivo: MotivoDoFator;
  /** AUC na validação só com este fator (pesos do treino); null sem ganho ou sem perda. */
  aucValidacao: number | null;
  /** O passo da seleção em que entrou (1 = o primeiro); null fora do score. */
  passo: number | null;
  /** O AUC do score na validação logo depois que este fator entrou; null fora do score. */
  aucAoEntrar: number | null;
  /**
   * Quanto o fator subiu o AUC (onde tem dado) no passo em que entrou; fora do score, quanto
   * subiria no passo em que a seleção parou. null se não deu para medir.
   */
  ganhoAuc: number | null;
  /** Os pontos que valem hoje (recorte mais recente); 0 em tudo se o fator ficou fora. */
  categorias: CategoriaDoFator[];
  /** Os pontos do treino, que a seleção usou. */
  categoriasTreino: CategoriaDoFator[];
}

/** Um recorte do replay. */
export interface RecorteDoMotor {
  /** Corte (ISO): quem estava aberto nesse dia entra. */
  corte: string;
  /** Até quando conta o ganho (ISO). */
  ate: string;
  n: number;
  ganhos: number;
  /** `ganhos ÷ n`; null se `n` = 0. */
  taxa: number | null;
}

/** O que o motor mediu: a tabela de "Como a nota funciona". */
export interface MotorDePontos {
  referencia: string;
  config: ConfigMotor;
  treino: RecorteDoMotor;
  validacao: RecorteDoMotor;
  /** A taxa do recorte mais recente: o ponto de partida do score (0 pontos = essa chance). */
  taxaBase: number;
  /** Na ordem da lista de candidatos. */
  fatores: FatorDoMotor[];
  /** Os fatores do score, na ordem em que entraram. */
  escolhidos: IdFator[];
  /** AUC do score final na validação (pesos do treino, só os escolhidos). */
  aucScore: number | null;
  /** AUC só da idade na validação (pesos do treino). */
  aucIdade: number | null;
}

/** Uma parcela do score de um negócio: um fator, o valor dele e os pontos. */
export interface ParcelaDoScore {
  fator: IdFator;
  rotulo: string;
  /** O valor do negócio ("45 dias", "GTX Pro"); null sem dado. */
  valor: string | null;
  /** A categoria em que caiu ("41 a 50 dias"); null sem dado. */
  faixa: string | null;
  pontos: number;
  /** true se o fator está no score (mesmo valendo 0 para este negócio). */
  noScore: boolean;
  motivo: MotivoDaParcela;
}

/** O score de um negócio, com a conta por fator. */
export interface ScoreDoDeal {
  /** `round(100 × chance)`. */
  score: number;
  /** A chance (0 a 1), sem arredondar. */
  chance: number;
  /** A soma dos pontos. */
  pontos: number;
  /** As parcelas: as do score (maior |pontos| primeiro) e depois as de fora, na ordem da tabela. */
  parcelas: ParcelaDoScore[];
  /** A parcela que mais somou ou tirou; null se nenhuma mexeu. */
  principal: ParcelaDoScore | null;
}

/** O motor medido e a função que pontua qualquer negócio aberto na referência. */
export interface Pontuador {
  motor: MotorDePontos;
  /** null quando o negócio não tem data de início e a config não pontua sem data. */
  pontuar(deal: Deal): ScoreDoDeal | null;
}

const DIA_MS = 86_400_000;
const inteiro = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

function diaUtc(iso: string): number {
  return Date.parse(iso + 'T00:00:00Z');
}

function iso(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

/** Percentil por interpolação linear entre os vizinhos (o padrão do numpy e do pandas). */
function percentil(ordenados: readonly number[], p: number): number {
  const h = (ordenados.length - 1) * p;
  const baixo = Math.floor(h);
  const a = ordenados[baixo] ?? 0;
  const b = ordenados[Math.min(baixo + 1, ordenados.length - 1)] ?? a;
  return a + (h - baixo) * (b - a);
}

function mediana(valores: readonly number[]): number {
  return percentil(
    [...valores].sort((a, b) => a - b),
    0.5,
  );
}

/**
 * AUC (Mann-Whitney): a chance de um ganho sorteado ter score maior que uma perda sorteada;
 * empate vale meio. null se faltar ganho ou perda.
 */
export function calcularAuc(scores: readonly number[], ganhou: readonly boolean[]): number | null {
  const valor = (i: number) => scores[i] as number;
  const ordem = scores.map((_, i) => i).sort((a, b) => valor(a) - valor(b));
  const postos = new Array<number>(scores.length).fill(0);
  for (let i = 0; i < ordem.length;) {
    let j = i;
    while (j + 1 < ordem.length && valor(ordem[j + 1] as number) === valor(ordem[i] as number)) j++;
    const medio = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) postos[ordem[k] as number] = medio;
    i = j + 1;
  }
  let positivos = 0;
  let soma = 0;
  scores.forEach((_, i) => {
    if (!ganhou[i]) return;
    positivos++;
    soma += postos[i] as number;
  });
  const negativos = scores.length - positivos;
  if (positivos === 0 || negativos === 0) return null;
  return (soma - (positivos * (positivos + 1)) / 2) / (positivos * negativos);
}

/**
 * O que se sabia num corte: os fechados até ele (ciclos e histórico da conta) e os abertos nele
 * (carga do vendedor). Nada depois do corte entra aqui.
 */
interface Retrato {
  corte: number;
  medianaProduto: Map<string, number>;
  medianaVendedor: Map<string, number>;
  conta: Map<string, { ganhos: number; perdas: number }>;
  carga: Map<string, number>;
}

/** Aberto no corte: começou até ele e não fechou até ele. */
function abertoNoCorte(d: Deal, corte: number): boolean {
  if (d.dataEngajamento === null || diaUtc(d.dataEngajamento) > corte) return false;
  return d.dataFechamento === null || diaUtc(d.dataFechamento) > corte;
}

function retratar(deals: readonly Deal[], corte: number): Retrato {
  const ciclosProduto = new Map<string, number[]>();
  const ciclosVendedor = new Map<string, number[]>();
  const conta = new Map<string, { ganhos: number; perdas: number }>();
  const carga = new Map<string, number>();
  const empilhar = (m: Map<string, number[]>, k: string, v: number) => {
    const lista = m.get(k);
    if (lista) lista.push(v);
    else m.set(k, [v]);
  };
  for (const d of deals) {
    if (abertoNoCorte(d, corte)) carga.set(d.vendedor, (carga.get(d.vendedor) ?? 0) + 1);
    if (d.dataFechamento === null || d.dataEngajamento === null) continue;
    const fechou = diaUtc(d.dataFechamento);
    if (fechou > corte) continue;
    if (d.estagio === 'Won') {
      const ciclo = Math.round((fechou - diaUtc(d.dataEngajamento)) / DIA_MS);
      empilhar(ciclosProduto, d.produto, ciclo);
      empilhar(ciclosVendedor, d.vendedor, ciclo);
    }
    if (d.conta !== null && (d.estagio === 'Won' || d.estagio === 'Lost')) {
      const h = conta.get(d.conta) ?? { ganhos: 0, perdas: 0 };
      if (d.estagio === 'Won') h.ganhos++;
      else h.perdas++;
      conta.set(d.conta, h);
    }
  }
  const medianas = (m: Map<string, number[]>) => new Map([...m].map(([k, v]) => [k, mediana(v)]));
  return {
    corte,
    medianaProduto: medianas(ciclosProduto),
    medianaVendedor: medianas(ciclosVendedor),
    conta,
    carga,
  };
}

/** A idade no corte; null sem data de início. */
function idadeNoCorte(d: Deal, corte: number): number | null {
  if (d.dataEngajamento === null) return null;
  return Math.round((corte - diaUtc(d.dataEngajamento)) / DIA_MS);
}

/** Como o valor bruto vira categoria. */
type Faixas = 'categoria' | 'idade' | 'ciclo' | 'quantil' | 'quantil_contas';

interface DefinicaoDoFator {
  id: IdFator;
  rotulo: string;
  tipo: 'obvio' | 'derivado';
  faixas: Faixas;
  /** O valor no corte; null = sem dado. */
  valor(d: Deal, r: Retrato): number | string | null;
  /** O valor do negócio em palavras ("45 dias"). */
  texto(v: number | string, d: Deal, r: Retrato): string;
  /** Formata os limites das faixas por quantil. */
  limite?: (v: number) => string;
}

const sim = (b: boolean) => (b ? 'sim' : 'não');
const dias = (v: number | string) => inteiro.format(v as number) + ' dias';
const vezes = (v: number) => decimal.format(v) + '×';
const milhoes = (v: number) => 'US$ ' + inteiro.format(v) + ' mi';
const porcento = (v: number) => inteiro.format(v * 100) + '%';
const comoTexto = (v: number | string) => String(v);

function razao(a: number | null, b: number | undefined): number | null {
  return a === null || b === undefined || b <= 0 ? null : a / b;
}

/** Os fatores candidatos, na ordem da tabela. */
const FATORES: readonly DefinicaoDoFator[] = [
  {
    id: 'idade',
    rotulo: 'Idade',
    tipo: 'obvio',
    faixas: 'idade',
    valor: (d, r) => idadeNoCorte(d, r.corte),
    texto: dias,
  },
  {
    id: 'produto',
    rotulo: 'Produto',
    tipo: 'obvio',
    faixas: 'categoria',
    valor: (d) => d.produto,
    texto: comoTexto,
  },
  {
    id: 'serie',
    rotulo: 'Série',
    tipo: 'obvio',
    faixas: 'categoria',
    valor: (d) => d.serie,
    texto: comoTexto,
  },
  {
    id: 'setor',
    rotulo: 'Setor',
    tipo: 'obvio',
    faixas: 'categoria',
    valor: (d) => d.setor,
    texto: comoTexto,
  },
  {
    id: 'porte_receita',
    rotulo: 'Receita da conta',
    tipo: 'obvio',
    faixas: 'quantil_contas',
    valor: (d) => d.receitaConta,
    texto: (v) => milhoes(v as number),
    limite: milhoes,
  },
  {
    id: 'porte_funcionarios',
    rotulo: 'Funcionários da conta',
    tipo: 'obvio',
    faixas: 'quantil_contas',
    valor: (d) => d.funcionarios,
    texto: (v) => inteiro.format(v as number) + ' funcionários',
    limite: (v) => inteiro.format(v),
  },
  {
    id: 'vendedor',
    rotulo: 'Vendedor',
    tipo: 'obvio',
    faixas: 'categoria',
    valor: (d) => d.vendedor,
    texto: comoTexto,
  },
  {
    id: 'manager',
    rotulo: 'Gerente',
    tipo: 'obvio',
    faixas: 'categoria',
    valor: (d) => d.manager,
    texto: comoTexto,
  },
  {
    id: 'escritorio',
    rotulo: 'Escritório',
    tipo: 'obvio',
    faixas: 'categoria',
    valor: (d) => d.regiao,
    texto: comoTexto,
  },
  {
    id: 'estagio',
    rotulo: 'Estágio',
    tipo: 'obvio',
    faixas: 'categoria',
    // o estágio no corte: com data de início até o corte, já estava em andamento
    valor: (d, r) =>
      d.dataEngajamento !== null && diaUtc(d.dataEngajamento) <= r.corte
        ? 'em andamento'
        : 'em prospecção',
    texto: comoTexto,
  },
  {
    id: 'idade_ciclo_produto',
    rotulo: 'Idade ÷ ciclo do produto',
    tipo: 'derivado',
    faixas: 'ciclo',
    valor: (d, r) => razao(idadeNoCorte(d, r.corte), r.medianaProduto.get(d.produto)),
    texto: (v, d, r) =>
      vezes(v as number) +
      ' o tempo típico de um ganho de ' +
      d.produto +
      ' (' +
      inteiro.format(r.medianaProduto.get(d.produto) ?? 0) +
      ' dias)',
  },
  {
    id: 'idade_ciclo_vendedor',
    rotulo: 'Idade ÷ ciclo do vendedor',
    tipo: 'derivado',
    faixas: 'ciclo',
    valor: (d, r) => razao(idadeNoCorte(d, r.corte), r.medianaVendedor.get(d.vendedor)),
    texto: (v, d, r) =>
      vezes(v as number) +
      ' o tempo típico de um ganho de ' +
      d.vendedor +
      ' (' +
      inteiro.format(r.medianaVendedor.get(d.vendedor) ?? 0) +
      ' dias)',
  },
  {
    id: 'conta_ganhos',
    rotulo: 'Ganhos anteriores da conta',
    tipo: 'derivado',
    faixas: 'quantil',
    valor: (d, r) => (d.conta === null ? null : (r.conta.get(d.conta)?.ganhos ?? 0)),
    texto: (v) => inteiro.format(v as number) + ' ganhos antes',
    limite: (v) => inteiro.format(v),
  },
  {
    id: 'conta_perdas',
    rotulo: 'Perdas anteriores da conta',
    tipo: 'derivado',
    faixas: 'quantil',
    valor: (d, r) => (d.conta === null ? null : (r.conta.get(d.conta)?.perdas ?? 0)),
    texto: (v) => inteiro.format(v as number) + ' perdas antes',
    limite: (v) => inteiro.format(v),
  },
  {
    id: 'conta_taxa',
    rotulo: 'Taxa de ganho da conta',
    tipo: 'derivado',
    faixas: 'quantil',
    valor: (d, r) => {
      const h = d.conta === null ? undefined : r.conta.get(d.conta);
      return h === undefined || h.ganhos + h.perdas === 0 ? null : h.ganhos / (h.ganhos + h.perdas);
    },
    texto: (v) => porcento(v as number) + ' dos negócios fechados',
    limite: porcento,
  },
  {
    id: 'conta_ja_comprou',
    rotulo: 'Conta já comprou',
    tipo: 'derivado',
    faixas: 'categoria',
    valor: (d, r) => (d.conta === null ? null : sim((r.conta.get(d.conta)?.ganhos ?? 0) > 0)),
    texto: comoTexto,
  },
  {
    id: 'empresa_mae',
    rotulo: 'Conta tem empresa-mãe',
    tipo: 'derivado',
    faixas: 'categoria',
    valor: (d) => (d.conta === null ? null : sim(d.empresaMae !== null)),
    texto: comoTexto,
  },
  {
    id: 'preco_receita',
    rotulo: 'Preço ÷ receita da conta',
    tipo: 'derivado',
    faixas: 'quantil',
    // a receita vem em milhões de US$: a razão sai em US$ por milhão de receita
    valor: (d) =>
      d.receitaConta === null || d.receitaConta <= 0 ? null : d.precoTabela / d.receitaConta,
    texto: (v) => 'US$ ' + decimal.format(v as number) + ' por milhão de receita',
    limite: (v) => decimal.format(v),
  },
  {
    id: 'carga_vendedor',
    rotulo: 'Carga do vendedor',
    tipo: 'derivado',
    faixas: 'quantil',
    valor: (d, r) => r.carga.get(d.vendedor) ?? 0,
    texto: (v) => inteiro.format(v as number) + ' negócios abertos',
    limite: (v) => inteiro.format(v),
  },
];

/** Os ids dos fatores candidatos, na ordem da tabela. */
export const FATORES_CANDIDATOS: readonly IdFator[] = FATORES.map((f) => f.id);

/** Uma categoria atribuída a um negócio. */
interface Atribuida {
  chave: string;
  rotulo: string;
  ordem: number;
  valor: string;
}

type Categorizar = (d: Deal) => Atribuida | null;

interface ContextoDoMotor {
  faixasIdade: readonly FaixaDeIdadeDoMotor[];
  config: ConfigMotor;
  /** Todos os deals (só os atributos fixos das contas saem daqui). */
  todos: readonly Deal[];
}

function rotuloDaIdade(de: number, ate: number | null): string {
  return ate === null
    ? 'acima de ' + inteiro.format(de - 1) + ' dias'
    : inteiro.format(de) + ' a ' + inteiro.format(ate) + ' dias';
}

/** Rótulo de uma faixa por tetos: "até X", "X a Y", "acima de Y". */
function rotuloPorTetos(tetos: readonly number[], i: number, f: (v: number) => string): string {
  const baixo = tetos[i - 1];
  const alto = tetos[i];
  if (baixo === undefined) return 'até ' + f(alto as number);
  if (alto === undefined) return 'acima de ' + f(baixo);
  return f(baixo) + ' a ' + f(alto);
}

function indiceDoTeto(tetos: readonly number[], v: number): number {
  const i = tetos.findIndex((t) => v <= t);
  return i === -1 ? tetos.length : i;
}

/** Os tetos dos quantis de uma lista de valores (q − 1 tetos). */
function tetosDosQuantis(valores: readonly number[], quantis: number): number[] {
  if (valores.length === 0) return [];
  const ordenados = [...valores].sort((a, b) => a - b);
  return Array.from({ length: quantis - 1 }, (_, k) => percentil(ordenados, (k + 1) / quantis));
}

/**
 * Monta como um fator vira categoria num corte. Os quantis saem só dos valores da população no
 * corte (sem desfecho); o porte, dos atributos fixos das contas.
 */
function categorizador(
  def: DefinicaoDoFator,
  r: Retrato,
  populacao: readonly Deal[],
  contexto: ContextoDoMotor,
): Categorizar {
  const { faixasIdade, config } = contexto;
  const formatar = def.limite ?? ((v: number) => decimal.format(v));
  let tetos: number[] = [];
  if (def.faixas === 'idade')
    tetos = faixasIdade.flatMap((f) => (f.ateDias === null ? [] : [f.ateDias]));
  if (def.faixas === 'ciclo') tetos = config.faixasCiclo;
  if (def.faixas === 'quantil') {
    const valores = populacao
      .map((d) => def.valor(d, r))
      .filter((v): v is number => typeof v === 'number');
    tetos = tetosDosQuantis(valores, config.quantis);
  }
  if (def.faixas === 'quantil_contas') {
    const porConta = new Map<string, number>();
    for (const d of contexto.todos) {
      const v = def.valor(d, r);
      if (d.conta !== null && typeof v === 'number') porConta.set(d.conta, v);
    }
    tetos = tetosDosQuantis([...porConta.values()], config.quantis);
  }
  return (d) => {
    const v = def.valor(d, r);
    if (v === null) return null;
    const valor = def.texto(v, d, r);
    if (def.faixas === 'categoria') return { chave: String(v), rotulo: String(v), ordem: 0, valor };
    const i = indiceDoTeto(tetos, v as number);
    const chave = 'F' + (i + 1);
    if (def.faixas === 'idade') {
      const de = i === 0 ? 0 : (tetos[i - 1] as number) + 1;
      return { chave, rotulo: rotuloDaIdade(de, tetos[i] ?? null), ordem: i, valor };
    }
    if (def.faixas === 'ciclo')
      return { chave, rotulo: rotuloPorTetos(tetos, i, vezes) + ' o ciclo', ordem: i, valor };
    return {
      chave,
      rotulo: i + 1 + 'º quartil (' + rotuloPorTetos(tetos, i, formatar) + ')',
      ordem: i,
      valor,
    };
  };
}

/** Um recorte pronto: a população, o desfecho e as categorias de cada fator. */
interface Amostra {
  recorte: RecorteDoMotor;
  populacao: Deal[];
  ganhou: boolean[];
  /** Por fator, a categoria de cada negócio da população (mesma ordem). */
  categorias: Map<IdFator, (Atribuida | null)[]>;
}

function amostrar(
  deals: readonly Deal[],
  corte: number,
  ate: number,
  contexto: ContextoDoMotor,
): Amostra {
  const populacao = deals.filter((d) => abertoNoCorte(d, corte));
  const r = retratar(deals, corte);
  const ganhou = populacao.map(
    (d) => d.estagio === 'Won' && d.dataFechamento !== null && diaUtc(d.dataFechamento) <= ate,
  );
  const categorias = new Map<IdFator, (Atribuida | null)[]>();
  for (const def of FATORES)
    categorias.set(def.id, populacao.map(categorizador(def, r, populacao, contexto)));
  const ganhos = ganhou.filter(Boolean).length;
  return {
    recorte: {
      corte: iso(corte),
      ate: iso(ate),
      n: populacao.length,
      ganhos,
      taxa: populacao.length === 0 ? null : ganhos / populacao.length,
    },
    populacao,
    ganhou,
    categorias,
  };
}

/**
 * Os pontos de cada categoria de um fator num recorte (a categoria "sem dado" fica por último).
 * A taxa geral é a de quem tem o dado: sem isso, um dado que só falta nos negócios ainda abertos
 * (a conta, por exemplo) daria pontos a toda categoria conhecida, e o "sem dado" viraria sinal.
 */
function pontuarCategorias(
  categorias: readonly (Atribuida | null)[],
  ganhou: readonly boolean[],
  config: ConfigMotor,
): CategoriaDoFator[] {
  const grupos = new Map<string, { a: Atribuida; n: number; ganhos: number }>();
  let semDado = 0;
  let ganhosSemDado = 0;
  categorias.forEach((c, i) => {
    if (c === null) {
      semDado++;
      if (ganhou[i]) ganhosSemDado++;
      return;
    }
    const g = grupos.get(c.chave) ?? { a: c, n: 0, ganhos: 0 };
    g.n++;
    if (ganhou[i]) g.ganhos++;
    grupos.set(c.chave, g);
  });
  const comDado = categorias.length - semDado;
  const taxaGeral = comDado === 0 ? 0 : (ganhou.filter(Boolean).length - ganhosSemDado) / comDado;
  const lista: CategoriaDoFator[] = [...grupos.values()]
    .sort((x, y) => x.a.ordem - y.a.ordem || x.a.chave.localeCompare(y.a.chave, 'pt-BR'))
    .map(({ a, n, ganhos }) => {
      const poucos = n < config.nMinimo;
      const suavizada = (ganhos + config.suavizacao * taxaGeral) / (n + config.suavizacao);
      const pontos =
        poucos || taxaGeral <= 0 || suavizada <= 0
          ? 0
          : Math.round(config.escala * Math.log(suavizada / taxaGeral));
      return {
        chave: a.chave,
        rotulo: a.rotulo,
        n,
        ganhos,
        taxa: ganhos / n,
        // + 0 tira o -0 do arredondamento
        pontos: pontos + 0,
        motivo: poucos ? 'n_pequeno' : 'pontua',
      };
    });
  if (semDado > 0)
    lista.push({
      chave: 'sem_dado',
      rotulo: 'sem dado',
      n: semDado,
      ganhos: ganhosSemDado,
      taxa: ganhosSemDado / semDado,
      pontos: 0,
      motivo: 'sem_dado',
    });
  return lista;
}

function pontosPorChave(categorias: readonly CategoriaDoFator[]): Map<string, number> {
  return new Map(categorias.map((c) => [c.chave, c.pontos]));
}

/** A soma dos pontos de cada negócio da amostra, com os fatores e os pesos dados. */
function somar(
  amostra: Amostra,
  fatores: readonly IdFator[],
  pesos: ReadonlyMap<IdFator, Map<string, number>>,
): number[] {
  const soma = new Array<number>(amostra.ganhou.length).fill(0);
  for (const id of fatores) {
    const p = pesos.get(id);
    (amostra.categorias.get(id) ?? []).forEach((c, i) => {
      if (c !== null) soma[i] = (soma[i] as number) + (p?.get(c.chave) ?? 0);
    });
  }
  return soma;
}

function logit(p: number): number {
  return Math.log(p / (1 - p));
}

/** A chance (0 a 1) de uma soma de pontos, pela conversão do config, a partir da taxa base. */
export function chanceDosPontos(motor: MotorDePontos, pontos: number): number {
  const { taxaBase, config } = motor;
  if (taxaBase <= 0 || taxaBase >= 1) return taxaBase;
  return config.conversao === 'razao'
    ? Math.min(1, taxaBase * Math.exp(pontos / config.escala))
    : 1 / (1 + Math.exp(-(logit(taxaBase) + pontos / config.escala)));
}

/** A chance de uma faixa de idade do motor (só os pontos da idade). */
export interface ChanceDaFaixa {
  /** "41 a 50 dias". */
  rotulo: string;
  /** A chance da faixa (0 a 1), pela conversão do config. */
  chance: number;
}

/**
 * A chance de cada faixa de idade, só com os pontos da idade (os pesos finais; faixa com n
 * pequeno vale 0 ponto, a taxa base). A faixa "sem dado" fica fora. É daqui que sai a parte do
 * dado no score de qualidade: a chance da faixa ÷ a maior chance entre as faixas.
 */
export function chancesDaIdade(motor: MotorDePontos): ChanceDaFaixa[] {
  const idade = motor.fatores.find((f) => f.id === 'idade');
  return (idade?.categorias ?? [])
    .filter((c) => c.motivo !== 'sem_dado')
    .map((c) => ({
      rotulo: c.rotulo,
      chance: chanceDosPontos(motor, idade?.entrou && c.motivo === 'pontua' ? c.pontos : 0),
    }));
}

/**
 * As categorias de cada fator para os negócios abertos num corte, só com o que se sabia nele
 * (`chave|valor`; null = sem dado). Serve ao teste de vazamento: apagar tudo o que veio depois
 * do corte não pode mudar nada aqui.
 */
export function fatoresNoCorte(
  deals: readonly Deal[],
  corteIso: string,
  faixasIdade: readonly FaixaDeIdadeDoMotor[],
  config: ConfigMotor,
): Map<string, Record<IdFator, string | null>> {
  const corte = diaUtc(corteIso);
  const amostra = amostrar(deals, corte, corte, { faixasIdade, config, todos: deals });
  return new Map(
    amostra.populacao.map((d, i) => [
      d.id,
      Object.fromEntries(
        FATORES.map((f) => {
          const c = amostra.categorias.get(f.id)?.[i] ?? null;
          return [f.id, c === null ? null : c.chave + '|' + c.valor];
        }),
      ) as Record<IdFator, string | null>,
    ]),
  );
}

/**
 * Mede o motor no histórico e devolve a função que pontua os negócios abertos na referência.
 * Determinístico: os mesmos deals dão os mesmos fatores, pontos e scores.
 */
export function medirMotor(
  deals: readonly Deal[],
  referencia: string,
  faixasIdade: readonly FaixaDeIdadeDoMotor[],
  config: ConfigMotor,
): Pontuador {
  const R = diaUtc(referencia);
  const C1 = R - config.treinoDias * DIA_MS;
  const C2 = R - config.horizonteDias * DIA_MS;
  const contexto: ContextoDoMotor = { faixasIdade, config, todos: deals };
  const treino = amostrar(deals, C1, C2, contexto);
  const validacao = amostrar(deals, C2, R, contexto);
  const taxaBase = validacao.recorte.taxa ?? 0;

  // pontos do treino, por fator
  const pesosTreino = new Map<IdFator, Map<string, number>>();
  const categoriasTreino = new Map<IdFator, CategoriaDoFator[]>();
  for (const def of FATORES) {
    const cats = pontuarCategorias(treino.categorias.get(def.id) ?? [], treino.ganhou, config);
    categoriasTreino.set(def.id, cats);
    pesosTreino.set(def.id, pontosPorChave(cats));
  }

  // AUC na validação e seleção gulosa. O efeito de um fator se mede só nos negócios que têm o
  // dado dele: quem não tem conta nunca fechou neste histórico, então medir na população inteira
  // premiaria qualquer fator de conta por separar "tem conta" de "sem dado".
  const auc = (fatores: readonly IdFator[], com: IdFator | null = null) => {
    const soma = somar(validacao, fatores, pesosTreino);
    const tem = (i: number) => com === null || validacao.categorias.get(com)?.[i] != null;
    const idx = soma.map((_, i) => i).filter(tem);
    return calcularAuc(
      idx.map((i) => soma[i] as number),
      idx.map((i) => validacao.ganhou[i] as boolean),
    );
  };
  const aucIndividual = new Map(FATORES.map((f) => [f.id, auc([f.id], f.id)]));
  const escolhidos: IdFator[] = [];
  const aucAoEntrar = new Map<IdFator, number>();
  const ganhoAuc = new Map<IdFator, number>();
  let atual: number | null = null;
  for (;;) {
    // o primeiro é o de maior AUC sozinho; depois, o que mais sobe o AUC onde tem dado
    let melhor: { id: IdFator; ganho: number } | null = null;
    for (const def of FATORES) {
      if (escolhidos.includes(def.id)) continue;
      const depois = auc([...escolhidos, def.id], def.id);
      const antes = escolhidos.length === 0 ? 0.5 : auc(escolhidos, def.id);
      if (depois === null || antes === null) continue;
      const ganho = depois - antes;
      ganhoAuc.set(def.id, ganho);
      if (melhor === null || ganho > melhor.ganho) melhor = { id: def.id, ganho };
    }
    if (melhor === null) break;
    if (melhor.ganho < config.ganhoMinimoAuc) break;
    escolhidos.push(melhor.id);
    atual = auc(escolhidos);
    if (atual !== null) aucAoEntrar.set(melhor.id, atual);
  }

  // pesos finais no recorte mais recente, só com os escolhidos
  const fatores: FatorDoMotor[] = FATORES.map((def) => {
    const entrou = escolhidos.includes(def.id);
    const treinoCats = categoriasTreino.get(def.id) ?? [];
    const medidas = pontuarCategorias(
      validacao.categorias.get(def.id) ?? [],
      validacao.ganhou,
      config,
    );
    const pontuaveis = treinoCats.filter((c) => c.motivo === 'pontua').length;
    return {
      id: def.id,
      rotulo: def.rotulo,
      tipo: def.tipo,
      entrou,
      motivo: entrou ? 'entrou' : pontuaveis < 2 ? 'n_pequeno' : 'nao_melhorou',
      aucValidacao: aucIndividual.get(def.id) ?? null,
      passo: entrou ? escolhidos.indexOf(def.id) + 1 : null,
      aucAoEntrar: aucAoEntrar.get(def.id) ?? null,
      ganhoAuc: ganhoAuc.get(def.id) ?? null,
      categorias: entrou
        ? medidas
        : medidas.map((c) => ({
            ...c,
            pontos: 0,
            motivo: c.motivo === 'sem_dado' ? c.motivo : ('fora_do_score' as const),
          })),
      categoriasTreino: treinoCats,
    };
  });

  const motor: MotorDePontos = {
    referencia,
    config,
    treino: treino.recorte,
    validacao: validacao.recorte,
    taxaBase,
    fatores,
    escolhidos,
    aucScore: atual,
    aucIdade: aucIndividual.get('idade') ?? null,
  };

  // o score dos abertos na referência: categorias medidas em R, pesos do recorte recente
  const r = retratar(deals, R);
  const populacaoFinal = deals.filter((d) => d.aberto);
  const categorizar = new Map(
    FATORES.map((def) => [def.id, categorizador(def, r, populacaoFinal, contexto)]),
  );
  const porId = new Map(fatores.map((f) => [f.id, f]));
  const entrou = (p: ParcelaDoScore) => p.noScore;

  function pontuar(deal: Deal): ScoreDoDeal | null {
    if (deal.dataEngajamento === null && !config.pontuarSemData) return null;
    const parcelas = FATORES.map((def): ParcelaDoScore => {
      const c = categorizar.get(def.id)?.(deal) ?? null;
      const fator = porId.get(def.id);
      const base = {
        fator: def.id,
        rotulo: def.rotulo,
        valor: c?.valor ?? null,
        faixa: c?.rotulo ?? null,
        noScore: fator?.entrou === true,
      };
      if (c === null) return { ...base, pontos: 0, motivo: 'sem_dado' };
      if (!fator?.entrou) return { ...base, pontos: 0, motivo: 'fora_do_score' };
      const cat = fator.categorias.find((x) => x.chave === c.chave);
      if (cat === undefined || cat.motivo === 'n_pequeno')
        return { ...base, pontos: 0, motivo: 'n_pequeno' };
      return { ...base, pontos: cat.pontos, motivo: 'pontua' };
    });
    const dentro = parcelas
      .filter(entrou)
      .sort(
        (a, b) =>
          Math.abs(b.pontos) - Math.abs(a.pontos) ||
          escolhidos.indexOf(a.fator) - escolhidos.indexOf(b.fator),
      );
    const pontos = dentro.reduce((s, p) => s + p.pontos, 0);
    const chance = chanceDosPontos(motor, pontos);
    return {
      score: Math.round(100 * chance),
      chance,
      pontos,
      parcelas: [...dentro, ...parcelas.filter((p) => !entrou(p))],
      principal: dentro.find((p) => p.pontos !== 0) ?? null,
    };
  }

  return { motor, pontuar };
}
