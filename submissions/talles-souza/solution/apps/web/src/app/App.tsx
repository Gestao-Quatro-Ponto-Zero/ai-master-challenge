/** A casca: navegação, banner do modo local e a rota atual (troca instantânea, sem transição). */
import { VisaoManager } from '../pipeline';
import { SegundaFeira } from '../priorizacao';
import { ComoFunciona, NovoLead } from '../qualificacao';
import { TelaDeal } from '../score';
import { useApp } from './contexto';
import { link, useRota, type Rota } from './rotas';

const NAV: { rota: Rota['nome']; href: string; texto: string }[] = [
  { rota: 'segunda', href: link.segunda, texto: 'Onde focar hoje' },
  { rota: 'novo-lead', href: link.novoLead, texto: 'Novo negócio' },
  { rota: 'manager', href: link.manager, texto: 'Acompanhar a equipe' },
  { rota: 'como-funciona', href: link.comoFunciona, texto: 'Como a nota funciona' },
];

/** Aviso do modo local quando a base ainda não carregou (depois, vem dos textos da política). */
const MODO_LOCAL_PADRAO =
  'Sem conexão com o servidor. A lista foi calculada aqui no seu navegador.';

export function App() {
  const { base, modo, respostasCompartilhadas } = useApp();
  const rota = useRota();

  let tela;
  if (base.tipo === 'carregando') {
    tela = (
      <div className="container principal">
        <p aria-live="polite">Carregando os negócios…</p>
      </div>
    );
  } else if (base.tipo === 'erro') {
    tela = (
      <div className="container principal">
        <p className="erro">Não deu para carregar os negócios: {base.mensagem}</p>
      </div>
    );
  } else if (rota.nome === 'segunda') {
    tela = <SegundaFeira base={base.base} />;
  } else if (rota.nome === 'deal') {
    tela = <TelaDeal base={base.base} id={rota.id} />;
  } else if (rota.nome === 'manager') {
    tela = <VisaoManager base={base.base} />;
  } else if (rota.nome === 'novo-lead') {
    tela = <NovoLead base={base.base} />;
  } else if (rota.nome === 'como-funciona') {
    tela = <ComoFunciona base={base.base} />;
  } else {
    tela = (
      <div className="container principal">
        <p>
          Página não encontrada. <a href={link.segunda}>Voltar para a lista</a>.
        </p>
      </div>
    );
  }

  return (
    <>
      <header className="topo">
        <div className="container topo__barra">
          <a className="marca" href={link.segunda}>
            Lead Scorer
          </a>
          <nav className="nav" aria-label="Principal">
            {NAV.map((n) => (
              <a
                key={n.rota}
                href={n.href}
                aria-current={rota.nome === n.rota ? 'page' : undefined}
              >
                {n.texto}
              </a>
            ))}
          </nav>
        </div>
      </header>
      {modo === 'local' ? (
        <div className="banner-local" role="status" data-testid="banner-modo-local">
          <div className="container">
            {base.tipo === 'pronta' ? base.base.textos.avisos.modoLocal : MODO_LOCAL_PADRAO}
          </div>
        </div>
      ) : null}
      <main>{tela}</main>
      <footer className="rodape">
        <div className="container">
          {base.tipo === 'pronta' ? (
            <p data-testid="rodape-referencia">{base.base.textos.avisos.referencia}</p>
          ) : null}
          <p data-testid="rodape-respostas">
            Lead Scorer · dados de vendas de exemplo (Kaggle, CC0)
            {base.tipo === 'pronta'
              ? ' · ' +
                (respostasCompartilhadas
                  ? base.base.politica.textos.respostas.banco
                  : base.base.politica.textos.respostas.local)
              : null}
          </p>
        </div>
      </footer>
    </>
  );
}
