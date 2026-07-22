# Process Log — Mapa de Evidências

Registro de como a IA foi usada nesta submissão. Três ferramentas, três papéis, três tipos de evidência.

## Ferramentas e papéis

| Ferramenta | Papel | Evidência |
|---|---|---|
| Claude (claude.ai) | Arquitetura da solução, instruções parametrizadas, validação cética de cada número contra os CSVs | `chat-exports/claude_sessao_arquitetura.pdf` |
| Agente de código no VS Code ("Codinho") | Execução das instruções nos notebooks, com reporte de retorno | Threads em `dev-log/` |
| Perplexity Pro | Pesquisa de mercado externa para furar o viés de confirmação da dupla | `chat-exports/perplexity_pesquisa_mercado.pdf` |

## dev-log/ — threads de execução

Cada arquivo é uma thread completa: instrução parametrizada, retorno do agente, correção quando houve, fechamento.

| Arquivo | Cobre |
|---|---|
| `1.0_scaffold_notebook.md` | Fundação do notebook de EDA |
| `1.1-1.6_auditoria.md` | Auditoria adversarial das duas fontes (Bloco 1) |
| `2.1-2.4_diagnostico.md` | Diagnóstico operacional (Bloco 2) |
| `4.1-4.3_prototipo.md` | Protótipo do classificador com abstenção (Bloco 4) |

O Bloco 3 (proposta de automação) é documento de julgamento arquitetural, produzido sem execução de código; a decisão está registrada em `../docs/PLAN.md`.

## chat-exports/ — sessões com IA

- `claude_sessao_arquitetura.pdf` — trechos da sessão de arquitetura: contrato de trabalho entre arquiteto e IA, instruções ao agente executor, momentos de correção mútua (inclusive hipóteses da IA refutadas pelos dados).
- `perplexity_pesquisa_mercado.pdf` — prompt e resposta íntegros da pesquisa sobre o que diferencia submissões vencedoras em challenges de contratação.

## screenshots/ — protótipo executando

- `notebook04_setup.png` — notebook 04 em execução: setup do classificador (TF-IDF, regressão logística, split estratificado).
- `notebook04_resultado_final.png` — célula final do notebook 04 com as métricas em holdout: F1-macro 0,856 (baseline 0,055), fração automatizada 0,931, cobertura 76,7%.
- `pipeline_inspector_html_01.png` a `_03.png` — vitrine `pipeline_inspector.html` renderizada no navegador: registro cru auditado, gates de qualidade, cards de inferência com o caso de abstenção.

## Onde a IA errou e o processo corrigiu

Três exemplos, todos rastreáveis na evidência acima:

1. A hipótese da IA de que o desvio para revisão humana seria liderado pela categoria Miscellaneous foi refutada pelos dados: Hardware lidera o desvio. O achado está assumido no notebook 04 e no README principal.
2. O agente executor reincidiu três vezes em construção de escrita vetada pelo padrão do projeto; corrigido em loop de revisão, registrado nas threads do dev-log.
3. A IA atribuiu duração a campos que são timestamps absolutos (First Response Time, Time to Resolution); o agente executor detectou, e o diagnóstico do Bloco 2 incorporou o achado.
