// Números do Painel (ESPEC-TELAS 4.3 e 4.4). Função pura sobre os deals do escopo.
import { CONFIG } from "./config";
import { somarDias } from "./calculos";
import type { DealVisao, Estagio } from "./tipos";

export interface NumerosPainel {
  data: string;
  leadsHoje: number;
  leadsJanela: number;
  leadsJanelaAnterior: number;
  emNegociacao: number;
  emNegociacaoValor: number;
  fechamentosHoje: number;
  fechamentosHojeValor: number;
  fechamentosJanela: number;
  fechamentosJanelaAnterior: number;
  receitaJanela: number;
  receitaJanelaAnterior: number;
  perdidosJanela: number;
  perdidosJanelaAnterior: number;
  conversaoJanela: number | null;
  conversaoJanelaAnterior: number | null;
  pipelineAbertoValor: number;
  pipelinePeloPrecoDeTabela: boolean;
  totalLeads: number;
  emRisco: number;
  esfriou: number;
  fimDeTrimestre: boolean;
}

export function numerosPainel(deals: DealVisao[], hoje: string): NumerosPainel {
  const j = CONFIG.janelaPainelDias;
  const iniJ = somarDias(hoje, -(j - 1));
  const iniA = somarDias(hoje, -(2 * j - 1));
  const fimA = somarDias(hoje, -j);
  const naJ = (d: string | null) => !!d && d >= iniJ && d <= hoje;
  const naA = (d: string | null) => !!d && d >= iniA && d <= fimA;
  const aberto = (d: DealVisao) => d.estagio === "Prospecting" || d.estagio === "Engaging";
  const soma = (l: DealVisao[], f: (d: DealVisao) => number | null) => l.reduce((a, d) => a + (f(d) ?? 0), 0);
  const won = deals.filter((d) => d.estagio === "Won");
  const lost = deals.filter((d) => d.estagio === "Lost");
  const wJ = won.filter((d) => naJ(d.closeDate));
  const wA = won.filter((d) => naA(d.closeDate));
  const lJ = lost.filter((d) => naJ(d.closeDate)).length;
  const lA = lost.filter((d) => naA(d.closeDate)).length;
  const eng = deals.filter((d) => d.estagio === "Engaging");
  const abertos = deals.filter(aberto);
  return {
    data: hoje,
    leadsHoje: deals.filter((d) => d.dataAbertura === hoje).length,
    leadsJanela: deals.filter((d) => naJ(d.dataAbertura)).length,
    leadsJanelaAnterior: deals.filter((d) => naA(d.dataAbertura)).length,
    emNegociacao: eng.length,
    emNegociacaoValor: soma(eng, (d) => d.valorEsperado),
    fechamentosHoje: won.filter((d) => d.closeDate === hoje).length,
    fechamentosHojeValor: soma(won.filter((d) => d.closeDate === hoje), (d) => d.closeValue),
    fechamentosJanela: wJ.length,
    fechamentosJanelaAnterior: wA.length,
    receitaJanela: soma(wJ, (d) => d.closeValue),
    receitaJanelaAnterior: soma(wA, (d) => d.closeValue),
    perdidosJanela: lJ,
    perdidosJanelaAnterior: lA,
    conversaoJanela: wJ.length + lJ ? wJ.length / (wJ.length + lJ) : null,
    conversaoJanelaAnterior: wA.length + lA ? wA.length / (wA.length + lA) : null,
    pipelineAbertoValor: soma(abertos, (d) => d.valorEsperado),
    pipelinePeloPrecoDeTabela: abertos.some((d) => d.valorPeloPrecoDeTabela),
    totalLeads: deals.length,
    emRisco: deals.filter((d) => d.icone === "em_risco").length,
    esfriou: deals.filter((d) => d.icone === "esfriou").length,
    fimDeTrimestre: [3, 6, 9, 12].includes(Number(hoje.slice(5, 7))),
  };
}

export interface BarraFunil {
  estagio: Estagio;
  quantidade: number;
  valor: number;
}

export function funil(deals: DealVisao[]): BarraFunil[] {
  const ordem: Estagio[] = ["Prospecting", "Engaging", "Won", "Lost"];
  return ordem.map((e) => {
    const l = deals.filter((d) => d.estagio === e);
    const valor = l.reduce((a, d) => a + (e === "Won" ? (d.closeValue ?? 0) : e === "Lost" ? d.preco : (d.valorEsperado ?? 0)), 0);
    return { estagio: e, quantidade: l.length, valor };
  });
}
