// Interpretador do filtro em campo livre (ESPEC-TELAS seção 5). Função pura, por regras, sem IA.
// Lê a frase da esquerda para a direita: cada regra que casa "consome" o trecho e vira uma etiqueta;
// o que sobrar (sem palavras de ligação) vira a etiqueta "Contém".
import { CONFIG } from "../config";
import { dinheiro, ROTULO_ICONE, SETORES, semAcento, somarDias } from "../calculos";
import type { Estagio, Icone, Papel, Porte } from "../tipos";
import type { Etiqueta } from "./etiquetas";

export type Modo = "pipeline" | "leads" | "contas";

export interface Contexto {
  modo: Modo;
  papel: Papel;
  hoje: string;
  vendedores: string[];
  managers: string[];
  empresas: string[];
  produtos: string[];
  tags: string[];
  sedes?: string[];
}

export interface Resultado {
  etiquetas: Etiqueta[];
}

const MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const LIGACAO = new Set(["de", "do", "da", "dos", "das", "e", "com", "em", "no", "na", "os", "as", "o", "a", "que", "para", "por", "deals", "deal", "leads", "lead", "empresa", "empresas"]);
const SETOR_PT: [string, string][] = [
  ...Object.entries(SETORES).map(([en, pt]) => [semAcento(pt), en] as [string, string]),
  ...Object.keys(SETORES).map((en) => [en, en] as [string, string]),
  ["saude", "medical"], ["financas", "finance"], ["telecom", "telecommunications"], ["tech", "technology"],
];
const REGIOES: Record<string, string> = { leste: "East", east: "East", oeste: "West", west: "West", central: "Central", centro: "Central" };

function mesIntervalo(ano: number, mes: number): [string, string] {
  const ini = `${ano}-${String(mes + 1).padStart(2, "0")}-01`;
  const fim = somarDias(mes === 11 ? `${ano + 1}-01-01` : `${ano}-${String(mes + 2).padStart(2, "0")}-01`, -1);
  return [ini, fim];
}

function br(iso: string): string {
  const [a, m, d] = iso.split("-");
  return `${d}/${m}/${a}`;
}

function escapar(t: string): string {
  return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function numero(t: string, mil?: string): number {
  const n = Number(t.replace(/\./g, "").replace(",", "."));
  return mil ? Math.round(n * 1000) : n;
}

export function interpretar(frase: string, ctx: Contexto): Resultado {
  let txt = ` ${semAcento(frase).replace(/\s+/g, " ").trim()} `;
  const etiquetas: Etiqueta[] = [];
  const ano = Number(ctx.hoje.slice(0, 4));
  const add = (e: Etiqueta) => etiquetas.push(e);

  /** Aplica a regra a todas as ocorrências e apaga o trecho casado. */
  const regra = (re: RegExp, fn: (m: RegExpExecArray) => void) => {
    const g = new RegExp(re.source, "g");
    txt = txt.replace(g, (...args) => {
      const m = args.slice(0, -2) as unknown as RegExpExecArray;
      fn(m);
      return " ";
    });
  };

  const podeVendedor = ctx.papel !== "vendedor";
  const podeManager = ctx.papel === "admin";

  if (ctx.modo === "contas") {
    regra(/\bna janela( de compra)?\b/, () => add({ chave: "padroes", valor: ["na_janela"], rotulo: "Padrão: na janela de compra" }));
    regra(/\bfora da janela( de compra)?\b/, () => add({ chave: "padroes", valor: ["fora_da_janela"], rotulo: "Padrão: fora da janela" }));
    regra(/\bsem padrao\b/, () => add({ chave: "padroes", valor: ["sem_padrao"], rotulo: "Sem padrão" }));
    regra(/\b(mais de|acima de|>) ?(\d+) compras\b/, (m) => add({ chave: "compras_min", valor: Number(m[2]) + 1, rotulo: `Compras > ${m[2]}` }));
    regra(/\bsem deals? abertos?\b/, () => add({ chave: "sem_aberto", valor: true, rotulo: "Sem deal aberto" }));
    regra(/\bcom deals? abertos?\b/, () => add({ chave: "com_aberto", valor: true, rotulo: "Com deal aberto" }));
    regra(/\breceita (acima de|maior que|mais de) ((?:us|r)\$ ?)?([\d.,]+)( mil)?\b/, (m) => {
      const v = numero(m[3] ?? "0", m[4]);
      add({ chave: "receita_min", valor: v, rotulo: `Receita ganha ≥ ${dinheiro(v)}` });
    });
    regra(/\bsubsidiarias?\b/, () => add({ chave: "subsidiaria", valor: true, rotulo: "Subsidiárias" }));
    regra(/\bindependentes?\b/, () => add({ chave: "independente", valor: true, rotulo: "Independentes" }));
    regra(/\bbonus (acima de|maior que|>=?) ?(\d+)\b/, (m) => add({ chave: "bonus_min", valor: Number(m[2]), rotulo: `Bonus ≥ ${m[2]}` }));
    for (const sede of ctx.sedes ?? []) {
      regra(new RegExp(`\\b(sede )?${escapar(semAcento(sede))}\\b`), () => add({ chave: "sedes", valor: [sede], rotulo: `Sede: ${sede}` }));
    }
  }

  // Nota
  regra(/\b(nota|score) (acima de|maior que|a partir de|>=?) ?(\d{1,3})\b/, (m) => add({ chave: "nota_min", valor: Number(m[3]), rotulo: `Nota ≥ ${m[3]}` }));
  regra(/\b(nota|score) (abaixo de|menor que|<) ?(\d{1,3})\b/, (m) => add({ chave: "nota_max", valor: Number(m[3]) - 1, rotulo: `Nota < ${m[3]}` }));
  regra(/\bnota alta\b/, () => add({ chave: "nota_min", valor: CONFIG.faixasNota.alta, rotulo: `Nota ≥ ${CONFIG.faixasNota.alta}` }));
  regra(/\bnota media\b/, () => {
    add({ chave: "nota_min", valor: CONFIG.faixasNota.media, rotulo: `Nota ≥ ${CONFIG.faixasNota.media}` });
    add({ chave: "nota_max", valor: CONFIG.faixasNota.alta - 1, rotulo: `Nota < ${CONFIG.faixasNota.alta}` });
  });
  regra(/\bnota baixa\b/, () => add({ chave: "nota_max", valor: CONFIG.faixasNota.media - 1, rotulo: `Nota < ${CONFIG.faixasNota.media}` }));
  regra(/\bsem nota\b/, () => add({ chave: "sem_nota", valor: true, rotulo: "Sem nota ainda" }));

  // Contato
  regra(/\bsem contato principal\b/, () => add({ chave: "sem_contato_principal", valor: true, rotulo: "Sem contato principal" }));
  regra(/\b(sem contato|parados?) (ha |faz )?(mais de )?(\d+) dias?\b/, (m) =>
    add({ chave: "contato_ha_dias_min", valor: Number(m[4]), rotulo: `Último contato há ${m[4]}+ dias` }));
  regra(/\bcontato (nesta|esta|na) semana\b/, () => add({ chave: "contato_ha_dias_max", valor: 7, rotulo: "Contato nos últimos 7 dias" }));
  regra(/\b(nunca contatados?|sem contato)\b/, () => add({ chave: "sem_contato", valor: true, rotulo: "Sem contato registrado" }));

  // Abertura e idade
  regra(/\b(nao iniciados?|sem data de abertura)\b/, () => add({ chave: "sem_abertura", valor: true, rotulo: "Não iniciado (sem abertura)" }));
  regra(/\b(ha mais de|aberto ha mais de) (\d+) dias( no pipeline)?\b/, (m) =>
    add({ chave: "dias_aberto_min", valor: Number(m[2]), rotulo: `Aberto há mais de ${m[2]} dias` }));
  regra(new RegExp(`\\b(aberto|abertos|entrou|entraram|entrada) (em|no mes de) (${MESES.join("|")})\\b`), (m) => {
    const [de, ate] = mesIntervalo(ano, MESES.indexOf(m[3] ?? ""));
    add({ chave: "abertura_de", valor: de, rotulo: `Abertura de ${br(de)}` });
    add({ chave: "abertura_ate", valor: ate, rotulo: `até ${br(ate)}` });
  });
  regra(/\b(aberto|abertos|entrou|entrada) (depois de|a partir de|apos) (\d{1,2})\/(\d{1,2})\b/, (m) => {
    const de = `${ano}-${(m[4] ?? "1").padStart(2, "0")}-${(m[3] ?? "1").padStart(2, "0")}`;
    add({ chave: "abertura_de", valor: de, rotulo: `Abertura ≥ ${br(de)}` });
  });
  regra(new RegExp(`\\b(aberto|abertos|entrou|entrada) (depois de|a partir de|apos) (${MESES.join("|")})\\b`), (m) => {
    const [de] = mesIntervalo(ano, MESES.indexOf(m[3] ?? ""));
    add({ chave: "abertura_de", valor: de, rotulo: `Abertura ≥ ${br(de)}` });
  });

  // Fechamento (Leads)
  if (ctx.modo === "leads") {
    regra(new RegExp(`\\bfechou em (${MESES.join("|")})\\b`), (m) => {
      const [de, ate] = mesIntervalo(ano, MESES.indexOf(m[1] ?? ""));
      add({ chave: "fechamento_de", valor: de, rotulo: `Fechou de ${br(de)}` });
      add({ chave: "fechamento_ate", valor: ate, rotulo: `até ${br(ate)}` });
    });
    regra(/\b(ganhos?|perdidos?|fechados?|fechou) em (\d{4})\b/, (m) => {
      if ((m[1] ?? "").startsWith("ganho")) add({ chave: "estagios", valor: ["Won"], rotulo: "Estágio: Ganho" });
      if ((m[1] ?? "").startsWith("perdido")) add({ chave: "estagios", valor: ["Lost"], rotulo: "Estágio: Perdido" });
      add({ chave: "fechamento_de", valor: `${m[2]}-01-01`, rotulo: `Fechou de 01/01/${m[2]}` });
      add({ chave: "fechamento_ate", valor: `${m[2]}-12-31`, rotulo: `até 31/12/${m[2]}` });
    });
  }

  // Ícones e ação sugerida
  const icone = (i: Icone) => add({ chave: "icones", valor: [i], rotulo: `Ícone: ${ROTULO_ICONE[i].toLowerCase()}` });
  regra(/\b(super hot|quentes?)\b/, () => icone("super_hot"));
  regra(/\b(em risco|esfriando)\b/, () => icone("em_risco"));
  regra(/\b(esfriou|esfriaram|esfriados?|parados?)\b/, () => icone("esfriou"));
  regra(/\b(para focar|focar)\b/, () => add({ chave: "acoes_sugeridas", valor: ["focar"], rotulo: "Ação sugerida: focar" }));
  regra(/\brequalificar\b/, () => add({ chave: "acoes_sugeridas", valor: ["requalificar"], rotulo: "Ação sugerida: requalificar" }));
  regra(/\bdesistir\b/, () => add({ chave: "acoes_sugeridas", valor: ["desistir"], rotulo: "Ação sugerida: desistir" }));

  // Estágios
  const estagio = (e: Estagio[], r: string) => add({ chave: "estagios", valor: e, rotulo: `Estágio: ${r}` });
  regra(/\b(prospeccao|prospecting)\b/, () => estagio(["Prospecting"], "Prospecção"));
  regra(/\b(em negociacao|negociando|engaging)\b/, () => estagio(["Engaging"], "Em negociação"));
  if (ctx.modo === "leads") {
    regra(/\babertos\b/, () => estagio(["Prospecting", "Engaging"], "abertos"));
    regra(/\b(ganhos?|won)\b/, () => estagio(["Won"], "Ganho"));
    regra(/\b(perdidos?|lost)\b/, () => estagio(["Lost"], "Perdido"));
  }

  // Valor
  regra(/\b(valor )?(acima de|mais de|maior que) ((?:us|r)\$ ?)?([\d.,]+)( mil)?\b/, (m) => {
    const v = numero(m[4] ?? "0", m[5]);
    add({ chave: "valor_min", valor: v, rotulo: `Valor ≥ ${dinheiro(v)}` });
  });

  // Tags e comentários
  regra(/\bsem tags?\b/, () => add({ chave: "sem_tag", valor: true, rotulo: "Sem tag" }));
  regra(/(?:#|\btag )([a-z0-9_-]+)/, (m) => {
    const t = ctx.tags.find((x) => semAcento(x) === m[1]) ?? m[1] ?? "";
    add({ chave: "tags", valor: [t], rotulo: `Tag: #${t}` });
  });
  regra(/\bcom comentarios?\b/, () => add({ chave: "com_comentario", valor: true, rotulo: "Tem comentário" }));

  // Perfil da empresa
  regra(/\bsem empresa\b/, () => add({ chave: "sem_empresa", valor: true, rotulo: "Empresa: não preenchida" }));
  const porte = (p: Porte, r: string) => add({ chave: "portes", valor: [p], rotulo: `Porte: ${r}` });
  regra(/\b(empresas? |porte )(grandes?)\b/, () => porte("grande", "grande"));
  regra(/\b(empresas? |porte )(pequenas?)\b/, () => porte("pequena", "pequena"));
  regra(/\b(empresas? |porte )(medias?)\b/, () => porte("media", "média"));
  for (const [nome, en] of SETOR_PT) {
    regra(new RegExp(`\\b(setor )?${escapar(nome)}\\b`), () => add({ chave: "setores", valor: [en], rotulo: `Setor: ${SETORES[en] ?? en}` }));
  }

  // Equipe
  if (podeManager) {
    regra(/\bregiao (leste|oeste|central|centro|east|west)\b/, (m) =>
      add({ chave: "regioes", valor: [REGIOES[m[1] ?? ""] ?? ""], rotulo: `Região: ${REGIOES[m[1] ?? ""]}` }));
    regra(/\b(east|west)\b/, (m) => add({ chave: "regioes", valor: [REGIOES[m[1] ?? ""] ?? ""], rotulo: `Região: ${REGIOES[m[1] ?? ""]}` }));
    for (const man of ctx.managers) {
      const [primeiro] = semAcento(man).split(" ");
      regra(new RegExp(`\\btime d[oa] (${escapar(semAcento(man))}|${escapar(primeiro ?? "")})\\b`), () =>
        add({ chave: "managers", valor: [man], rotulo: `Time de ${man}` }));
    }
  }
  if (podeVendedor) {
    for (const v of ctx.vendedores) {
      const completo = escapar(semAcento(v));
      const [primeiro] = semAcento(v).split(" ");
      const unico = ctx.vendedores.filter((x) => semAcento(x).split(" ")[0] === primeiro).length === 1;
      const alvo = unico ? `${completo}|${escapar(primeiro ?? "")}` : completo;
      regra(new RegExp(`\\b(?:(?:do|da|vendedora?) )?(${alvo})\\b`), () => add({ chave: "vendedores", valor: [v], rotulo: `Vendedor: ${v}` }));
    }
  }

  // Produtos e empresas (nomes do cadastro)
  regra(/\bserie (gtx|mg|gtk)\b/, (m) => add({ chave: "series", valor: [(m[1] ?? "").toUpperCase()], rotulo: `Série: ${(m[1] ?? "").toUpperCase()}` }));
  for (const p of [...ctx.produtos].sort((a, b) => b.length - a.length)) {
    regra(new RegExp(`\\b${escapar(semAcento(p))}\\b`), () => add({ chave: "produtos", valor: [p], rotulo: `Produto: ${p}` }));
  }
  for (const e of [...ctx.empresas].sort((a, b) => b.length - a.length)) {
    regra(new RegExp(`(?<![a-z0-9])${escapar(semAcento(e))}(?![a-z0-9])`), () => add({ chave: "empresas", valor: [e], rotulo: `Empresa: ${e}` }));
  }

  // O que sobrou vira "Contém"
  const resto = txt.split(" ").filter((p) => p && !LIGACAO.has(p)).join(" ").trim();
  if (resto) add({ chave: "contem", valor: resto, rotulo: `Contém "${resto}"` });

  return { etiquetas };
}
