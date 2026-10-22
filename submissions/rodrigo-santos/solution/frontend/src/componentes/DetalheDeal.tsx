/**
 * Painel lateral com o detalhe de um negócio: o que fazer, por quê,
 * e quantos pontos cada parte deu à nota.
 */

import { useEffect, useState } from "react";

import { api } from "../api/cliente";
import type { DealDetalhe } from "../tipos";
import { formatarDias, formatarMoeda, formatarPorcentagem, NOMES_ETAPA, tituloDeal } from "../utils/formatadores";
import SeloPrioridade from "./SeloPrioridade";

interface Props {
  id: string;
  aoFechar: () => void;
}

const ICONES_MOTIVO = { positivo: "▲", negativo: "▼", neutro: "•" };


export default function DetalheDeal({ id, aoFechar }: Props) {
  const [deal, setDeal] = useState<DealDetalhe | null>(null);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    setDeal(null);
    setErro(false);
    api.deal(id).then(setDeal).catch(() => setErro(true));
  }, [id]);

  // Fecha com a tecla Esc.
  useEffect(() => {
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && aoFechar();
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [aoFechar]);

  return (
    <div className="fundo-painel" onClick={aoFechar}>
      <aside className="painel" onClick={(e) => e.stopPropagation()} aria-label="Detalhe do negócio">
        <button className="botao-fechar" onClick={aoFechar} aria-label="Fechar">
          ×
        </button>

        {erro && <p className="aviso-erro">Não foi possível carregar este negócio.</p>}
        {!deal && !erro && <p>Carregando…</p>}

        {deal && (
          <>
            <header className="painel-cabecalho">
              <SeloPrioridade prioridade={deal.prioridade} />
              <h2>{tituloDeal(deal)}</h2>
              <p>
                {deal.produto} · {formatarMoeda(deal.valor)} · {NOMES_ETAPA[deal.etapa]}
              </p>
            </header>

            <div className="pontuacao-grande">
              <strong>{deal.score}</strong>
              <span>de 100 pontos</span>
            </div>

            <div className={`sugestao sugestao-${deal.prioridade === "Alta" ? "alta" : deal.parado ? "alerta" : "neutra"}`}>
              <span className="rotulo">O que fazer</span>
              <p>{deal.sugestao}</p>
            </div>

            <h3>Por quê?</h3>
            <ul className="motivos">
              {deal.motivos.map((motivo) => (
                <li key={motivo.texto} className={`motivo-${motivo.tipo}`}>
                  <span aria-hidden>{ICONES_MOTIVO[motivo.tipo]}</span> {motivo.texto}
                </li>
              ))}
            </ul>

            <h3>Como chegamos a {deal.score} pontos</h3>
            <div className="fatores">
              {deal.partes.map((parte) => (
                <div key={parte.chave} className="fator">
                  <div className="fator-titulo">
                    <span>{parte.nome}</span>
                    <strong>
                      {parte.pontos} de {parte.maximo} pts
                    </strong>
                  </div>
                  <div className="barra">
                    <div className="barra-preenchida" style={{ width: `${(parte.pontos / parte.maximo) * 100}%` }} />
                  </div>
                  <small>{parte.explicacao}</small>
                </div>
              ))}
              <div className="fator-total">
                <span>Total</span>
                <strong>
                  {deal.partes.map((p) => p.pontos).join(" + ")} = {deal.score} pontos
                </strong>
              </div>
            </div>

            <h3>Dados do negócio</h3>
            <dl className="dados">
              <dt>Chance de fechar</dt>
              <dd>{formatarPorcentagem(deal.chance)}</dd>
              <dt>Valor esperado</dt>
              <dd>{formatarMoeda(deal.valor_esperado)}</dd>
              <dt>Tempo aberto</dt>
              <dd>{formatarDias(deal.dias_aberto)}</dd>
              <dt>Vendedor</dt>
              <dd>{deal.vendedor}</dd>
              <dt>Gerente</dt>
              <dd>{deal.manager}</dd>
              <dt>Escritório</dt>
              <dd>{deal.escritorio}</dd>
              <dt>Setor</dt>
              <dd>{deal.setor ?? "Não informado"}</dd>
              <dt>Código</dt>
              <dd>{deal.id}</dd>
            </dl>
          </>
        )}
      </aside>
    </div>
  );
}
