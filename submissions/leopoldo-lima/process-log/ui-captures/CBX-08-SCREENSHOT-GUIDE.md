# CBX-08 — Guia de screenshots (Gestor comercial / combobox)

Capturar com o servidor a servir a UI (`public/`) e dataset acessível (ex.: `real_dataset` por defeito).

**Pasta sugerida:** commitar PNGs em `artifacts/process-log/ui-captures/cbx-08/` com os nomes abaixo (ou anexar ao relatório de submissão).

| # | arquivo sugerido | O que mostrar |
|---|-------------------|----------------|
| 1 | `cbx-08-01-combobox-inicial.png` | Campo «Gestor comercial» com helper **Digite 3 letras para buscar** (sem dropdown). |
| 1b | `cbx-08-01b-menos-tres-letras.png` | Com 2 caracteres: **sem** lista de sugestões (validação &lt;3 letras). |
| 2 | `cbx-08-02-tres-letras-sugestoes.png` | Após 3+ letras de um gestor **real** da API: dropdown com sugestões alinhado ao cockpit. |
| 3 | `cbx-08-03-sem-resultados.png` | Texto **Nenhum gestor encontrado** (query inventada, ex. `zzz`). |
| 4 | `cbx-08-04-gestor-selecionado.png` | Nome completo no input + hint de seleção; opcional: ranking filtrado após **Aplicar filtros**. |
| 5 | `cbx-08-05-apos-limpar.png` | Após **Limpar filtros**: input vazio, helper inicial, sem valor no filtro. |
| 6 | `cbx-08-06-a-carregar.png` | (Opcional, rede lenta ou throttle) **A carregar gestores…** + `aria-busy` visível no inspetor. |

**Automático:** com Playwright instalado, `python scripts/capture_cbx08_screenshots.py` grava os arquivos 1, 1b, 2–5 na pasta `cbx-08/` (sobe o servidor na porta `8799`).

## Checklist manual (Definition of Done)
1. Menos de 3 letras → sem lista de sugestões.  
2. 3+ letras válidas → sugestões.  
3. Seleção com rato.  
4. Seleção com Enter (setas + Enter).  
5. Esc fecha o dropdown.  
6. Tab passa para o controlo seguinte sem bloquear o formulário.  
7. Clicar fora fecha o dropdown.  
8. Aplicar filtro com gestor selecionado envia `manager` na listagem.  
9. Limpar filtros repõe o campo.
