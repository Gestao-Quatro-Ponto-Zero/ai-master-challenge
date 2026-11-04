# Submissão — Gustavo Covaleski — Challenge 002

## Sobre mim

- **Nome:** Gustavo Covaleski
- **LinkedIn:** https://www.linkedin.com/in/gustavo-henrique-covaleski
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Nesta submissão, eu:

- auditei os dois datasets;
- congelei um holdout separado por grupo de quase-duplicados antes de qualquer modelo;
- comparei um classificador clássico com um LLM;
- transformei o resultado numa política "IA decide / IA sugere / humano decide" por categoria, com um protótipo testado para produção.

O que encontrei:

- **Tempo e satisfação:** os dados de hoje não permitem achar gargalo de tempo nem fator de satisfação, porque o problema é a medição.
- **Automação:** a IA decide sozinha em 13,0% dos tickets, com precisão de 98,9% (em tickets reais de TI; a transferência para a operação de suporte é premissa).
- **Taxonomia:** as 8 categorias seguem convenções que nem um revisor externo (46,7% de concordância) nem um LLM (26,5% na faixa de dúvida) reproduzem.

A recomendação é um piloto de 4 semanas:

- instrumentar 5 eventos;
- ativar a triagem em modo sombra e, depois, só em Access e Purchase;
- escrever a definição das filas com o time;
- **não** contratar LLM para classificar.

Detalhes no [memo de 1 página](docs/memo-diretor.md).

---

## Solução

### Abordagem

- **Fases com portão humano** (F0 a F7). Cada fase tem uma spec escrita no chat do Projeto, executada pelo Claude Code, com report revisado contra os arquivos gerados. As specs e os reports estão em [`process-log/planning/`](process-log/planning/).
- **Regras fixadas antes de ver o resultado:**
  - consequência de cada armadilha dos dados (F1);
  - critério da automação: limite inferior do IC 95% da precisão ≥ 1 − taxa de erro humano (*e*);
  - *e* = o menor entre o *e* da revisão adjudicada e o dos quase-duplicados;
  - regra de faixa por categoria (F4);
  - regra de adoção do detector de injeção (F6).
- **Holdout congelado antes de qualquer modelo**, separado por grupo de quase-duplicados (TF-IDF, cosseno ≥ 0,90). O holdout aleatório foi mantido só para medir vazamento.
- **Os dois datasets cruzados por premissa explícita:** o DS2 (TI interna, texto) mede o roteamento; o DS1 (suporte ao cliente) define a regra de ação e o que não é mensurável. Ver [política](docs/politica.md).

### Resultados / Findings

| Achado | Número | Arquivo |
|---|---|---|
| DS1: resolução antes da 1ª resposta nos tickets fechados | 49,30% | `solution/outputs/f1_ds1_auditoria.json` |
| DS2: texto já pré-processado | 0% de maiúsculas; palavras funcionais em 24,94% | `solution/outputs/f1_ds2_auditoria.json` |
| Vazamento por quase-duplicados | +0,31 p.p. no agregado; localizado: 91,84% (com quase-duplicado no treino) × 84,97% (sem) | `solution/outputs/f3_classico.json` |
| Clássico (TF-IDF + LR), holdout por grupo | acurácia 85,07% (IC 84,34–85,79) | `solution/outputs/f3_classico.json` |
| LLM (Claude Haiku 5.5) × clássico na faixa de dúvida | 26,5% × 69,5% (mesmos 400 tickets); US$ 0,15 por 1.000 | `solution/outputs/f3_llm.json` |
| Ruído de rótulo: "original errado" em que o modelo segue o original | 18 de 21 (convenção da taxonomia, não erro aleatório) | `solution/outputs/f3_h2.json` |
| Faixas com a regra por categoria: IA decide / IA sugere / humano | 12,98% / 31,41% / 55,61% | `solution/outputs/f4_politica.json` |
| Sensibilidade **pós-hoc, não usada na decisão** (categorias humanas → IA sugere) | 12,98% / 52,84% / 34,18% | `solution/outputs/f4_sensibilidade.csv` |
| Injeção (100 pares): troca de rótulo / alvo atingido, clássico | 9% / 3%; em "IA decide": 0 de 6.210 pares (limite superior 0,062%). Mas 898 de 6.210 (14,5%) saíram de "IA decide" para humano: o ataque não engana a decisão automática, mas gera carga humana e reduz a cobertura (chave `dano_ampliado`) | `solution/outputs/f5_injecao.json` |
| Detector de injeção | falso positivo de 4,75% > 1% → **não adotado** | `solution/outputs/f6_detector.json` |
| Latência de ponta a ponta (`triar`, com mascaramento e log) | p50 2,79 ms / p95 5,12 ms | `solution/outputs/f5_latencia.json` |
| Economia de triagem (cenário com etapa separada) | R$ 6.815,62/ano na base (premissas) | `solution/outputs/f4_economia.csv` |

Mais detalhes:
- [diagnóstico](docs/diagnostico.md);
- [instrumentação](docs/instrumentacao.md);
- [política](docs/politica.md);
- [fluxo](docs/fluxo.md);
- [produção](docs/producao.md);
- capturas do protótipo em [`process-log/screenshots/`](process-log/screenshots/).

### Recomendações

1. **Instrumentar os 5 eventos** (`ticket_criado`, `resposta_agente`, `status_mudou`, `reatribuido`, `csat_respondido`). Sem eles, nenhum diagnóstico de tempo é possível ([instrumentação](docs/instrumentacao.md)).
2. **Rodar a triagem em modo sombra** por 2 a 3 semanas, medindo a precisão pelas correções e o tempo de confirmação em "IA sugere".
3. **Ativar "IA decide" só em Access e Purchase**, se a meta se confirmar. Hardware e Administrative rights ficam com humano. Hardware sobe para "IA sugere" se as correções do piloto mostrarem precisão ≥ meta (hoje 95,9%; `solution/outputs/f4_politica_por_categoria.csv`).
4. **Escrever com o time a definição das 8 filas.** Administrative rights teve 6 de 6 rótulos contestados na revisão.
5. **Não contratar LLM para classificar.** Ele acerta menos (26,5% × 69,5%) e não é determinístico.

### Limitações

- **DS1 sintético:** tempos invertidos, CSAT uniforme, texto com template não preenchido. Ele entra só por metadados e por regra de negócio.
- **DS2 de outro domínio** (TI interna) **e pré-processado.** A transferência para o suporte ao cliente é premissa, não resultado.
- **Revisão de rótulos com um único revisor** (60 tickets).
- **Taxa de erro humano:** o *e* usado na decisão (3,82%) vem da discordância entre quase-duplicados, como estimativa do erro humano. O *e* da revisão adjudicada foi de 31,79%.
- **Precisão medida contra rótulos com ruído próprio:** conservador se o ruído for aleatório, otimista se for sistemático.
- **LLM testado com 1 exemplo por categoria** e sem `temperature = 0`, que o Haiku 5.5 não aceita: não é determinístico.
- **Ganho da faixa "IA sugere" não quantificado:** o tempo de confirmação deve ser medido no piloto.
- **Câmbio:** a grade de câmbio que aparece em `f3_*.json` não foi usada em nenhuma conclusão.
- **Retreino** de 21,5 s a 78,2 s, na mesma máquina.
- **Export da sessão:** contém os mesmos 2 trechos do DS2 de `docs/politica.md`; mantido sem edição para preservar a evidência.
- **Tempo total acima do orçamento:** ver o [process log](process-log/process-log.md).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude, no chat do Projeto | Planejamento, crítica, especificação de cada fase, revisão dos números nos arquivos gerados e condução dos portões |
| Claude Code | Execução das specs: código, testes, medições e reports |
| Claude Haiku 5.5 (API) | Braço LLM do experimento (F3) e do teste de injeção (F5); fora do caminho de decisão |

### Workflow

1. **F0:** reescrever o pedido em 3 perguntas mensuráveis, ranquear hipóteses e escolher o escopo, num portão humano.
2. **F1:** auditar os dados, congelar grupos e holdout, e preparar a planilha cega de revisão.
3. **F2:** diagnóstico com MDE e instrumentação.
4. **F3:** revisão cega e adjudicação (humano); depois, o experimento clássico × LLM e as faixas.
5. **F4:** política por categoria e fluxo.
6. **F5:** protótipo com prontidão testada.
7. **F6:** lacunas da F5, detector de injeção e rollback.
8. **F7:** comunicação.

Cada fase seguiu o mesmo ciclo: spec → execução → report → revisão → decisão registrada.

### Onde a IA errou e como corrigi

Resumo da tabela do [process log](process-log/process-log.md):

- **Critério da Q2 invertido:** a IA comparou precisão com taxa de erro. Corrigido no portão F0.
- **Critério de "confirmada" das armadilhas definido depois de ver os dados.** Registrado como tal.
- **Ruído de rótulo inflado:** "360 tickets em grupos com conflito". O recálculo deu 118 (3,8%).
- **Spec de CSV sem prever o Excel online:** a leitura da revisão quebrou e foi convertida sem alterar o conteúdo.
- **Previsão do F0 de que o vazamento seria "número de capa":** a medição derrubou a hipótese (+0,31 p.p.).

### O que eu adicionei que a IA sozinha não faria

Registrado como decisão minha no [process log](process-log/process-log.md):

- **Premissas de custo:** premissas editáveis com sensibilidade obrigatória.
- **Preço do LLM:** consultado na fonte oficial.
- **Revisão de rótulos:** cega, feita por mim e sem sugestão pré-preenchida, seguida de adjudicação.
- **Regra de automação:** regra de decisão em 3 faixas amarrada ao IC do erro humano.
- **Cenário B:** cenário sem etapa de triagem (economia zero), que justifica o evento `reatribuido`.
- **Repasse e conferência:** divisão de trabalho com repasse por arquivo e conferência dos números.
- **Repositório:** regras de repositório e de segredo.
- **Deploy:** cortado.
- **Regra registrada:** mantida na F4, mesmo com a cobertura caindo de 57% para 13%.

Também meus, anteriores à execução ou fora das tabelas de decisão:
- **Raio-x das 57 submissões do 002** antes de planejar, para separar o que já é baseline do que diferencia.
- **As 7 hipóteses de diferenciação** que orientaram o escopo e foram ranqueadas no portão F0.
- **Ordem de corte definida antes de estourar:** amostra do LLM de 400 para 150 chamadas, curva com 3 limiares, e os testes de falha da F5 nunca cortados.
- **Plano B:** manter o escopo cheio e declarar o estouro de tempo, em vez de fundir política e protótipo.
- **Planilha adjudicada no repositório** como evidência da revisão humana.
- **Coluna "Já vi em produção"** da [matriz de falhas](docs/producao.md): três falhas que já sustentei em produção (webhook duplicado, robô travando, injeção em triagem de documentos), cada uma ligada ao teste que a cobre aqui.

---

## Evidências

- [x] Process log com decisões por fase: [`process-log/process-log.md`](process-log/process-log.md)
- [x] Specs e reports de cada fase: [`process-log/planning/`](process-log/planning/)
- [x] Revisão de rótulos adjudicada: [`process-log/revisao_rotulos_adjudicada.csv`](process-log/revisao_rotulos_adjudicada.csv)
- [x] Screenshots do protótipo: [`process-log/screenshots/`](process-log/screenshots/)
- [x] Chat export da sessão do Claude Code (F1 a F7): [`process-log/chat-exports/claude-code-f1-a-f7.md`](process-log/chat-exports/claude-code-f1-a-f7.md)
- [x] Git history: um commit por fase na branch `submission/gustavo-covaleski`

---

## Como rodar

1. **Ambiente:** Python 3.11+.
   ```
   python -m venv .venv
   .venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
   ```
2. **Dados:** baixe os 2 CSVs ([Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) e [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset)) para `../../../data/`, relativo a esta pasta, ou defina `DATA_DIR`.
3. **`.env` (opcional):** fica fora do repositório, em `../../../.env`, com `ANTHROPIC_API_KEY`. Só os scripts de LLM (`f3_llm.py`, `f5_injecao.py`) o usam.
4. **Scripts, em ordem:**
   - F1: `f1_verificar_dados.py`, `f1_auditoria_ds1.py`, `f1_auditoria_ds2.py`, `f1_planilha_revisao.py`. `f1_auditoria_ds2.py` gera `f1_splits.csv`, o holdout oficial (não regenere).
   - F2: `f2_diagnostico.py`.
   - F3: `f3_classico.py`, `f3_faixas.py`, `f3_h2.py`, `f3_llm.py`, depois `f3_faixas.py` de novo.
   - F4: `f4_politica.py`.
   - F5 e F6: `f5_injecao.py` (`--so-classico`, `--dano-ampliado`), `f5_latencia.py`, `f6_detector.py`.

   Todos ficam em `solution/` e rodam com `python solution/<script>.py`.
5. **Testes:** `pytest solution/tests -q`. O golden set e o portão de qualidade estão incluídos.
6. **Protótipo:** `streamlit run solution/app.py`. A primeira execução treina o modelo e o guarda em `modelo_cache/`.

---

_Submissão enviada em: 04/11/2026_
