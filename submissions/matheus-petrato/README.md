# Submissao — Matheus Petrato — G4 Compass (Sales Co-Pilot)

## Contexto rapido
G4 Compass e um PWA mobile-first para vendedores B2B com pipeline priorizado, explainability do score e alertas proativos. O foco e ajudar o vendedor a decidir o proximo passo e dar ao manager uma visao macro do time.

---

## O que foi entregue
**Frontend funcional (SvelteKit + Tailwind) com foco mobile-first**
- Briefing (seller + manager)
- Pipeline priorizado com filtros
- Deal Detail com explainability (tabela de fatores)
- Compass (chat) com sugestoes por papel
- Alertas proativos
- Reports do manager
- Imports CSV (manager)
- Configuracao de papel (seller/manager)
- PWA (manifest + service worker)

**Backend**
- Documento de rotas esperadas e guia de API atualizado
- Docker Compose + script para subir stack completa

---

## Como rodar (dev)
Na pasta `submissions/matheus-petrato`:

1. Crie `.env` baseado em `.env.example`
2. Rode:
```
./dev.sh
```

Frontend: `http://localhost:5173`  
Backend: `http://localhost:8080`

---

## Estrutura de telas e permissao
**Seller**
- Briefing / Pipeline / Deal Detail / Compass / Alertas / Configuracoes

**Manager**
- Tudo acima + Reports + Bases (CSV)

O papel e controlado localmente em `Configuracoes` (sera integrado ao JWT no backend).

---

## Principais decisoes
- **Mobile-first** com bottom nav e sidebar somente no desktop.
- **Explainability** como requisito central (tabela de fatores no Deal Detail).
- **Manager view** separada com visao macro por regiao/stage/top sellers.
- **Imports CSV** temporario para manager ate CRM direto.

---

## Documentacao complementar
- `backend-expected-routes.md`: contratos esperados para cada tela.
- `backend/API_GUIDE.md`: guia atualizado de endpoints.
- `processo-de-implementacao.md`: historico e registros do processo.

---

## Process log — Como usei IA (obrigatorio)

### Ferramentas usadas
| Ferramenta | Para que usei |
|---|---|
| Codex (ChatGPT) | Implementacao do frontend, ajustes de design e estrutura, e scaffolding do ambiente dev |
| Git | Log de iteracoes e checkpoints por etapa |

### Workflow (resumo)
1. Li o contexto do produto e defini o escopo das telas principais.
2. Criei uma navegacao por etapas (Briefing, Pipeline, Deal, Alerts, Reports, Imports).
3. Ajustei design system conforme guia (cores, tipografia, mobile-first).
4. Adaptei telas para consumir dados reais da API.
5. Preparei stack de execucao (docker-compose + dev.sh).

### Onde a IA errou e como corrigi
- Ajustes de path e organizacao de arquivos quando a estrutura mudou.
- Padronizacao de rotas/ENV e sincronizacao com o API guide.

### O que eu adicionei que a IA sozinha nao faria
- Priorizacao de telas e fluxo de decisao (foco em vendedor/manager).
- Alinhamento fino do design com contexto do G4 Compass.
- Organização do projeto por entregas incrementalmente commitadas.

---

## Evidencias
- [x] Git history com commits por etapa
- [ ] Screenshots de conversa com IA
- [ ] Screen recording
- [ ] Chat export
- [ ] Outro: __________

---

Submissao enviada em: 2026-03-12
