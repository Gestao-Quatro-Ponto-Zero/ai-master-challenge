# G4 Lead Scorer — Frontend (G4 - Sales Priority, tela do vendedor)

React 18 + TypeScript, somente **class components** (sem hooks). Conversa com uma API através de uma interface (`DealsApi`), hoje com **mock no navegador**; trocar para a API real é uma variável de ambiente.

## Rodar no navegador (com a API do backend)

Requisitos: Node 18+ e Python 3.10+ (backend).

Terminal 1 — API (pasta `backend`):
```bash
cd backend
source .venv/bin/activate      # se ainda não existe: python3 -m venv .venv && make install
make train                     # só na primeira vez (gera artifacts/); o repositório já traz um modelo
make api                       # http://localhost:8000/docs
```

Terminal 2 — frontend (pasta `frontend`):
```bash
cd frontend
npm install
npm run dev                    # abre http://localhost:5173
```

Em desenvolvimento (`npm run dev`) o frontend usa a API real por padrão e entra como o vendedor `vicki-laflamme`. O Vite encaminha `/api` para `http://localhost:8000`, então não há problema de CORS.

Sem backend, rode com dados de exemplo: `npm run dev:mock`.

## Comandos

| Comando | O que faz |
|---|---|
| `npm run dev` | desenvolvimento com a API real (abre o navegador) |
| `npm run dev:mock` | desenvolvimento com dados de exemplo, sem backend |
| `npm test` | testes do frontend (a integração com a API real é pulada) |
| `npm run test:integration` | testes contra a API real (precisa do `make api` rodando; lê `G4_API_URL` do `.env`) |
| `npm run test:watch` | testes em modo contínuo |
| `npm run typecheck` | checagem de tipos |
| `npm run build` | typecheck + build de produção em `dist/` |
| `npm run preview` | serve o build de `dist/` |

## O front não contém regra de negócio

O front só exibe. Faixas de score, abas, limiares de dias, regra de confiança, textos de ação, filtros, ordenação e totais vêm da API: ver `GET /meta` (limiares, níveis de prioridade, abas), `GET /deals` (cada deal traz `view`, `priority_level`, `suggested_action`, `confidence_reason`; filtro, ordem e paginação são do servidor), `GET /summary` (totais por aba) e `GET /filters` (produtos). Enquanto `/meta` não chega, a tela mostra "Carregando…".

No front ficam só formatação (moeda, datas), cores, layout, estado de tela/URL e acessibilidade. A lógica de regras existe apenas em `src/api/mock/` (usada só no modo mock) e o teste `src/architecture.test.ts` falha se literais de regra (138, 104, 41, 80, 40) aparecerem fora dela ou se componentes/lib importarem o mock.

Pendências marcadas como `TODO(api)` (sem endpoint hoje): "Adiar" e "Encerrar como perdido" (estado local no navegador, não é regra de produto), "Marcar feito" em Meu dia, rota "Seu dia" (hoje composta com `GET /deals?view=focus&sort=score`: o dia é o topo do foco da semana, que reúne prioridade Alta e Média), motivo estruturado no feedback.

## Heatmap do funil

O bloco "Funil: onde estão seus deals" mostra produto x tempo no funil (deals ou valor esperado). Os números e as faixas de dias vêm de `GET /summary` (campo `funnel`); o front só desenha. Clicar numa célula filtra a lista pelo produto. Está escondido da página: o componente `FunnelHeatmap` continua em `src/components`; para voltar, renderize-o em `SellerPage` depois dos `KpiCards`. Prospecção fica de fora (sem data) e valor esperado não conta deals a revisar. O backend precisa estar na versão com `funnel` no `/summary` (reinicie a API).

## Mock x API real

| Variável | Padrão | Uso |
|---|---|---|
| `G4_API_URL` | `http://localhost:8000` | URL do backend, definida no `.env` (copie de `.env.example`). Vale para o proxy do `npm run dev` e para `test:integration`. Uma variável de shell sobrescreve o arquivo |
| `G4_API_USER` | `vicki-laflamme` | vendedor usado nos testes de integração |
| `VITE_API_MODE` | `http` no `npm run dev`; `mock` nos demais | `mock` ou `http` |
| `VITE_API_USER` | `vicki-laflamme` | `user_key` usado em `POST /auth/login` (usuários vendedores do `app.db`) |
| `VITE_API_BASE_URL` | `/api/v1` | base da API |
| `VITE_API_PROXY_TARGET` | `http://localhost:8000` | alternativa antiga a `G4_API_URL` (esta tem prioridade) |
| `VITE_MOCK_LATENCY_MS` | `200` | atraso do mock |
| `VITE_SHOW_PROBABILITY` | `false` | só mock; na API real vale `G4_SHOW_PROBABILITY` do backend |

O login é o do MVP da API (troca `user_key` por JWT). Para outro vendedor: `VITE_API_USER=moses-frase npm run dev`.

**O que ainda é local no navegador** (a API não tem essas rotas): "Adiar" e "Marcar como perdido" (ficam escondidos neste navegador; adiar expira no prazo escolhido) e "Marcar feito" em Meu dia. Feedback ("Registrar atividade", "Discordo", "Ignorar") vai para a API.

## Dados de exemplo

O mock guarda no `localStorage` o que você adiou/encerrou e os feedbacks. Para voltar ao início: botão **Restaurar dados de exemplo** no rodapé da lista (ou limpe o localStorage do site).

## Estrutura

```
src/
  api/        DealsApi (interface), MockDealsApi, HttpDealsApi, createApi, tipos
  components/ componentes de apresentação (classes)
  pages/      SellerPage: estado, URL e chamadas à API
  lib/        formatação, tema, constantes, estado na URL
  test/       setup dos testes
docs/PLANO_FRONTEND.md
prototype/    protótipo original em HTML (referência)
```

## Estado na URL

Filtros ficam na URL e sobrevivem a recarregar/compartilhar: `?view=all&tab=review&product=GTK%20500&q=acme&sort=ev&level=high&page=2&size=10&cap=5`. Só valores diferentes do padrão aparecem.
