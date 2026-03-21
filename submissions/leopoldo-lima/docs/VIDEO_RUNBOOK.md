# Runbook — vídeo com Chromium (CRP-VID-02)

## Objetivo

Gerar evidência visual **reproduzível** da demo (WebM + capturas PNG) usando **Chromium** via Playwright, sem depender de gravação manual ad hoc.

## Pré-requisitos

- Python 3.11+
- Dependências do projeto: `python scripts/tasks.py install`
- Playwright:

```text
pip install playwright
python -m playwright install chromium
```

- arquivos do dataset oficial em `data/*.csv` (modo `real_dataset` por omissão — ver `docs/RUNTIME_DEFAULTS.md`).

## Comando

Na raiz do repositório:

```text
python scripts/record_demo_chromium.py
python scripts/record_demo_chromium.py --pace fast
```

Por omissão usa **`--pace slow`**: pausas maiores e **digitação caractere a caractere** (teclas visíveis no WebM), adequado a vídeo de demo.

Saídas (por omissão):

- `artifacts/process-log/screen-recordings/demo-cockpit.webm`
- `artifacts/process-log/screen-recordings/demo-01` … `demo-07` (PNG)

Opções:

- `--pace slow|fast` — lento (recomendado para gravar narrativa) vs rápido (smoke)
- `--no-video` — só screenshots
- `--no-screenshots` — só WebM
- `--port 8808` — porta do Uvicorn levantado pelo script (evitar conflito com `8787` do `tasks.py dev`)

## O que o script faz

1. Arranca `uvicorn src.api.app:app` em `127.0.0.1:<porta>`.
2. Abre Chromium headless, carrega `/`.
3. Espera KPIs (`#kpi-strip`) e linhas no ranking.
4. Com **`--pace slow`**, **rola** (smooth) para KPIs e depois para o **ranking** — mostra que os dados carregaram.
5. Para cada alteração de filtro: **rola para o painel de filtros** → muda o controlo → clica **Aplicar filtros** → espera o ranking sair de «a carregar» → **rola de novo para o ranking** e centra a **contagem de resultados** (`#result-count`), para ficar óbvio que o conjunto mudou.
6. **Escritório regional** — 2.º da lista se existir (passos do ponto 5).
7. **Estágio** — prioriza `Engaging` / `Prospecting` quando disponível.
8. **Faixa de prioridade** — `Alta`.
9. **Pesquisa** — fragmento real via API; digitação lenta em «Conta, ID ou título».
10. **Gestor** — digitação lenta, clique na primeira sugestão, **Aplicar filtros** + rolagem para o ranking.
11. Se, após todos os filtros, **não houver linhas**, clica **Limpar filtros**, espera o ranking e continua (evita timeout e ainda mostra o reset).
12. Clica a primeira linha, **rola** para o **painel de detalhe** (explicabilidade).

**Nota:** a UI só atualiza o ranking após **Aplicar filtros** (ou Limpar); o script segue esse fluxo, não apenas mudar `<select>` em silêncio.

## Ferramenta de gravação

- **Vídeo:** API `record_video_dir` do Playwright (um `.webm` por contexto, renomeado para `demo-cockpit.webm`).
- **Screenshots:** `page.screenshot` e recorte do painel de filtros.

## Problemas comuns

| Sintoma | Ação |
|---------|------|
| `playwright` não encontrado | `pip install playwright` no mesmo venv que corre o script |
| Chromium não instalado | `python -m playwright install chromium` |
| Timeout em health | Porta ocupada — use `--port` diferente |
| Lista de gestores vazia | Verificar API `/api/dashboard/filter-options` e arquivos em `data/` |

## Roteiro falado

Ver [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md).
