import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';
import { ProvedorApp, type Dependencias } from './app/contexto';
import {
  criarClienteHttp,
  criarClienteLocal,
  criarClienteResiliente,
  criarRegistrosHttp,
  criarRepositorioNavegador,
  lerComissao,
  lerPerfil,
  salvarComissao,
  salvarPerfil,
} from './infra';
import './estilo/tokens.css';
import './estilo/motion.css';
import './estilo/app.css';

const deps: Dependencias = {
  cliente: criarClienteResiliente(criarClienteHttp(), criarClienteLocal()),
  repositorio: criarRepositorioNavegador(),
  registros: criarRegistrosHttp(),
  agoraIso: () => new Date().toISOString(),
  perfil: { ler: () => lerPerfil(), salvar: (p) => salvarPerfil(p) },
  comissao: { ler: () => lerComissao(), salvar: (p) => salvarComissao(p) },
};

const raiz = document.getElementById('raiz');
if (raiz) {
  createRoot(raiz).render(
    <StrictMode>
      <ProvedorApp deps={deps}>
        <App />
      </ProvedorApp>
    </StrictMode>,
  );
}
