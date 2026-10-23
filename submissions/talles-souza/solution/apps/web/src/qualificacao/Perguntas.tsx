import type {
  PerguntaFato,
  RespostasDoDeal,
  ValorResposta,
} from '@lead-scorer/dominio/qualificacao';

/**
 * As perguntas opcionais do método, cada uma com Sim/Não. Responder é um extra: a resposta
 * soma ou tira do score ("Sim" sobe, "Não" desce) e o "não" troca a ação pela frase da pergunta;
 * nenhuma resposta muda o grupo nem a ordem da tela, e deixar em branco não muda nada.
 */
export function Perguntas({
  perguntas,
  respostas,
  aoResponder,
  rotulos,
}: {
  perguntas: readonly PerguntaFato[];
  respostas: RespostasDoDeal | null;
  aoResponder: (perguntaId: string, valor: ValorResposta) => void;
  /** "Sim" e "Não", dos textos da política. */
  rotulos: { sim: string; nao: string };
}) {
  if (perguntas.length === 0)
    return <p className="aviso">Nenhuma pergunta vale para este grupo.</p>;
  return (
    <div>
      {perguntas.map((p) => {
        const resposta = respostas?.respostas.find((r) => r.perguntaId === p.id) ?? null;
        const atual = resposta?.valor ?? null;
        const idTexto = 'pergunta-texto-' + p.id;
        return (
          <div
            key={p.id}
            className="pergunta"
            data-testid={'pergunta-' + p.id}
            role="group"
            aria-labelledby={idTexto}
          >
            <p className="pergunta__texto" id={idTexto}>
              {p.pergunta}
            </p>
            {p.ajuda ? <p className="aviso">{p.ajuda}</p> : null}
            <div className="sim-nao">
              {(['sim', 'nao'] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  className="ls-t-colors"
                  aria-pressed={atual === v}
                  data-testid={'pergunta-' + p.id + '-' + v}
                  onClick={() => aoResponder(p.id, v)}
                >
                  {v === 'sim' ? rotulos.sim : rotulos.nao}
                </button>
              ))}
            </div>
            {atual === 'nao' && p.acaoSeNao ? (
              <p className="pergunta__acao" data-testid={'pergunta-' + p.id + '-acao'}>
                {p.acaoSeNao}
              </p>
            ) : null}
            {resposta ? (
              <p className="aviso">
                Respondido em {resposta.respondidoEm.slice(0, 10).split('-').reverse().join('/')}.
              </p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
