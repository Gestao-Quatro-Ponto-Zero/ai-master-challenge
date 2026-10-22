/**
 * Painel "Como funciona a pontuação": explica ao vendedor, sem jargão,
 * de onde vem a nota, o que significa cada prioridade e como a lógica
 * foi testada com o histórico.
 *
 * Os números vêm da API (/api/regras e /api/validacao), então este texto
 * se atualiza sozinho quando alguém muda backend/app/config.py ou os dados.
 */

import { useEffect, useState } from "react";

import { api } from "../api/cliente";
import type { RegrasPontuacao, Validacao } from "../tipos";
import { formatarMoeda, formatarNumero, formatarPorcentagem } from "../utils/formatadores";
import SeloPrioridade from "./SeloPrioridade";

interface Props {
  aoFechar: () => void;
}

export default function ComoFunciona({ aoFechar }: Props) {
  const [regras, setRegras] = useState<RegrasPontuacao | null>(null);
  const [validacao, setValidacao] = useState<Validacao | null>(null);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    Promise.all([api.regras(), api.validacao()])
      .then(([novasRegras, novaValidacao]) => {
        setRegras(novasRegras);
        setValidacao(novaValidacao);
      })
      .catch(() => setErro(true));
  }, []);

  // Fecha com a tecla Esc.
  useEffect(() => {
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && aoFechar();
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [aoFechar]);

  const alta = validacao?.por_prioridade.find((p) => p.prioridade === "Alta");
  const media = validacao?.por_prioridade.find((p) => p.prioridade === "Média");

  return (
    <div className="fundo-painel" onClick={aoFechar}>
      <aside className="painel" onClick={(e) => e.stopPropagation()} aria-label="Como funciona a pontuação">
        <button className="botao-fechar" onClick={aoFechar} aria-label="Fechar">
          ×
        </button>
        <h2>Como funciona a pontuação</h2>

        {erro && <p className="aviso-erro">Não foi possível carregar as regras.</p>}
        {!regras && !erro && <p>Carregando…</p>}

        {regras && validacao && (
          <>
            <p className="introducao">
              Cada negócio aberto recebe uma nota de <strong>0 a 100</strong>, que é a soma de três partes.
            </p>

            <div className="regras-fator">
              <h4>
                <span>Situação do negócio</span>
                <span>até {regras.pontos_maximos.situacao} pts</span>
              </h4>
              <p>
                No histórico, <strong>todo negócio se resolveu (ganho ou perdido) em até {regras.limite_dias} dias</strong>.
                Em negociação dentro desse prazo: {regras.pontos_maximos.situacao} pontos. Em prospecção (ainda não
                começou): {regras.pontos_prospeccao} pontos. Aberto há mais tempo que isso está <strong>parado</strong>:
                0 pontos e prioridade baixa.
              </p>
            </div>

            <div className="regras-fator">
              <h4>
                <span>Valor do negócio</span>
                <span>até {regras.pontos_maximos.valor} pts</span>
              </h4>
              <p>
                Quanto mais caro o produto, mais pontos. Os preços vão de {formatarMoeda(regras.preco_minimo)} a{" "}
                {formatarMoeda(regras.preco_maximo)}.
              </p>
            </div>

            <div className="regras-fator">
              <h4>
                <span>Reta final</span>
                <span>até {regras.pontos_maximos.reta_final} pts</span>
              </h4>
              <p>
                Quanto mais perto dos {regras.limite_dias} dias, mais urgente é conduzir o cliente à decisão, antes que
                o negócio fique parado.
              </p>
            </div>

            <h3>O que a nota significa</h3>
            <div className="regras-faixas">
              <div>
                <SeloPrioridade prioridade="Alta" />
                <span>{regras.limite_alta} pontos ou mais: foque nestes primeiro.</span>
              </div>
              <div>
                <SeloPrioridade prioridade="Média" />
                <span>
                  De {regras.limite_media} a {regras.limite_alta - 1} pontos: acompanhe regularmente.
                </span>
              </div>
              <div>
                <SeloPrioridade prioridade="Baixa" />
                <span>Menos de {regras.limite_media} pontos, ou parado: atualize, encerre ou deixe para depois.</span>
              </div>
            </div>

            <h3>Testado com o histórico</h3>
            <p className="introducao">
              Voltamos a {validacao.datas_corte.length} datas do passado e aplicamos a pontuação aos negócios abertos
              em cada uma, comparando com o que aconteceu depois:
            </p>
            <ul className="evidencias">
              <li>
                <strong>
                  Dos {formatarNumero(validacao.parados)} negócios parados, {validacao.parados_fechados_depois} foram
                  fechados depois.
                </strong>{" "}
                Insistir neles não trouxe resultado.
              </li>
              {alta && media && (
                <li>
                  Negócios de prioridade alta renderam em média <strong>{formatarMoeda(alta.receita_media)}</strong>,
                  contra {formatarMoeda(media.receita_media)} nos de prioridade média.
                </li>
              )}
              <li>
                Vendedor, produto, setor, conta, porte e região <strong>não mudaram a chance de ganhar</strong>: todos
                acertaram tanto quanto um sorteio. Por isso a chance usada é a média da empresa (
                {formatarPorcentagem(regras.taxa_vitoria_geral)}) e não entra na nota.
              </li>
            </ul>

            <h3>Como ler um negócio</h3>
            <p className="introducao">
              Em cada cartão aparece o <strong>principal motivo</strong> da nota: o ponto forte (▲) nos negócios de
              prioridade alta e o que segurou a nota (▼) nos demais. Clique no negócio para ver os pontos de cada parte
              e o que fazer.
            </p>
          </>
        )}
      </aside>
    </div>
  );
}
