/**
 * Tela principal: resumo, filtros e o pipeline de deals abertos.
 *
 * Esta página guarda o estado (filtros, dados carregados, deal selecionado)
 * e repassa para os componentes, que só exibem.
 */

import { useEffect, useState } from "react";

import { api } from "../api/cliente";
import CartoesResumo from "../componentes/CartoesResumo";
import ComoFunciona from "../componentes/ComoFunciona";
import DetalheDeal from "../componentes/DetalheDeal";
import FiltrosPipeline from "../componentes/FiltrosPipeline";
import QuadroPipeline from "../componentes/QuadroPipeline";
import TabelaDeals from "../componentes/TabelaDeals";
import { FILTROS_VAZIOS, type DealResumo, type Filtros, type OpcoesFiltro, type Resumo } from "../tipos";

type ModoVisualizacao = "quadro" | "lista";

// Espera o usuário parar de digitar na busca antes de consultar a API.
const ATRASO_BUSCA_MS = 300;

export default function Pipeline() {
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_VAZIOS);
  const [opcoes, setOpcoes] = useState<OpcoesFiltro | null>(null);
  const [deals, setDeals] = useState<DealResumo[]>([]);
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [modo, setModo] = useState<ModoVisualizacao>("quadro");
  const [idSelecionado, setIdSelecionado] = useState<string | null>(null);
  const [mostrarRegras, setMostrarRegras] = useState(false);

  // Opções dos filtros: carregadas uma vez.
  useEffect(() => {
    api.opcoesFiltro().then(setOpcoes).catch(() => setErro("Não foi possível carregar os filtros."));
  }, []);

  // Deals e resumo: recarregados sempre que um filtro muda.
  useEffect(() => {
    let cancelado = false; // evita mostrar resposta antiga se o filtro mudar no meio
    const temporizador = setTimeout(() => {
      setCarregando(true);
      Promise.all([api.pipeline(filtros), api.resumo(filtros)])
        .then(([lista, novoResumo]) => {
          if (cancelado) return;
          setDeals(lista.deals);
          setResumo(novoResumo);
          setErro(null);
        })
        .catch(() => !cancelado && setErro("Não foi possível carregar o pipeline. O servidor está ligado?"))
        .finally(() => !cancelado && setCarregando(false));
    }, ATRASO_BUSCA_MS);

    return () => {
      cancelado = true;
      clearTimeout(temporizador);
    };
  }, [filtros]);

  return (
    <div className="pagina">
      <header className="cabecalho">
        <div>
          <h1>Priorização de Deals</h1>
          <p className="subtitulo">Veja em quais negócios vale a pena focar agora.</p>
        </div>
        <div className="acoes-cabecalho">
          <button className="botao-ajuda" onClick={() => setMostrarRegras(true)}>
            Como funciona a pontuação?
          </button>
          <div className="alternador" role="group" aria-label="Modo de visualização">
            <button className={modo === "quadro" ? "ativo" : ""} onClick={() => setModo("quadro")}>
              Quadro
            </button>
            <button className={modo === "lista" ? "ativo" : ""} onClick={() => setModo("lista")}>
              Lista
            </button>
          </div>
        </div>
      </header>

      <CartoesResumo resumo={resumo} />

      <FiltrosPipeline filtros={filtros} opcoes={opcoes} aoMudar={setFiltros} />

      {erro && <div className="aviso-erro">{erro}</div>}

      <main className={carregando ? "carregando" : ""}>
        {!erro && deals.length === 0 && !carregando && (
          <p className="vazio">Nenhum negócio encontrado com esses filtros.</p>
        )}
        {modo === "quadro" ? (
          <QuadroPipeline deals={deals} aoSelecionar={setIdSelecionado} />
        ) : (
          <TabelaDeals deals={deals} aoSelecionar={setIdSelecionado} />
        )}
      </main>

      {mostrarRegras && <ComoFunciona aoFechar={() => setMostrarRegras(false)} />}
      {idSelecionado && <DetalheDeal id={idSelecionado} aoFechar={() => setIdSelecionado(null)} />}
    </div>
  );
}
