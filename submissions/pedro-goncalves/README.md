# Support Copilot: Challenge 002

## Sobre mim

- **Nome:** Pedro Gonçalves
- **LinkedIn:** não informado
- **Formação:** Engenharia de Produção, Unicamp
- **Challenge:** 002, Redesign de Suporte

## Resumo executivo

O diagnóstico encontrou um problema anterior à automação: o Dataset 1 possui **8.469 tickets**, não os aproximadamente 30 mil descritos no contexto, e seus campos temporais não permitem medir FRT, TTR ou touch time. Em **49,3% dos 2.769 pares temporais**, a resolução aparece antes da primeira resposta. Em vez de inventar ROI, construí um **copiloto de triagem em shadow mode**: classificador calibrado, abstenção, categorias human-only, máscara de PII, audit log e kill switch.

No Dataset 2, o classificador atingiu **macro-F1 0,868** no teste final de 7.176 tickets. O threshold 0,75 foi escolhido apenas na validação e, no teste final, cobriu 69,7% com 96,6% de acurácia nos cobertos. Isso é uma prova técnica no domínio de TI, não uma validação para a G4.

## A decisão em uma frase

**Medir o fluxo real, rodar a IA em paralelo ao humano e só ampliar autonomia depois que erro, risco e capacidade forem observados.**

## Achados

| Achado | Evidência | Consequência |
|---|---:|---|
| Volume real do Dataset 1 | 8.469 tickets | Não usar 30 mil como denominador |
| Pares temporais inválidos | 1.365 de 2.769 | Vetar FRT, TTR e ROI observado |
| Texto templado | 8.469 descrições com placeholder | Vetar inferência semântica operacional |
| Sinal de CSAT | Efeitos nulos ou desprezíveis | Não priorizar segmento por causalidade |
| Prova técnica | Macro-F1 0,868 | Classificação é tecnicamente viável no Dataset 2 |
| Abstenção | 69,7% de cobertura a 96,6% de acurácia no teste final | Expor a troca entre escala e erro |

![Ausência de dados por status](solution/artifacts/figures/support-missingness-by-status.png)

![Cobertura e acurácia](solution/artifacts/figures/coverage-vs-accuracy.png)

## Matriz de decisão

Escala de 1 a 5. A nota ponderada não supera veto crítico.

| Alternativa | Evidência 30% | Impacto 25% | Segurança 20% | Viabilidade 15% | Diferenciação 10% | Nota | Veto |
|---|---:|---:|---:|---:|---:|---:|---|
| Resposta autônoma | 1,0 | 4,0 | 1,0 | 2,0 | 3,0 | 2,1 | Sim |
| Roteamento automático | 4,0 | 4,0 | 3,0 | 4,0 | 4,0 | 3,8 | Produção |
| Copiloto em shadow mode | 5,0 | 3,5 | 5,0 | 5,0 | 4,5 | **4,6** | Não |
| Dashboard isolado | 3,0 | 2,0 | 5,0 | 5,0 | 2,0 | 3,4 | Não |

## O que funciona

O protótipo Streamlit:

- recebe texto e mascara padrões de PII;
- classifica em oito categorias;
- mostra confiança e alternativas;
- abstém abaixo do threshold;
- bloqueia categorias sensíveis;
- força revisão com kill switch;
- registra decisão sem guardar texto bruto;
- calcula capacidade apenas com premissas explícitas.

## Rodar

Requer Python 3.11 ou superior e [uv](https://docs.astral.sh/uv/).

```bash
cd solution
uv sync
uv run streamlit run app.py
```

Abra `http://localhost:8501`.

## Testar

```bash
cd solution
uv run python -m unittest discover -s tests -v
```

Resultado validado: **16 testes aprovados**.

## Reproduzir a análise

Baixe os dois arquivos CC0 indicados no challenge e posicione:

```text
data/raw/customer-support/customer_support_tickets.csv
data/raw/it-service/all_tickets_processed_improved_v3.csv
```

Depois:

```bash
cd solution
uv run python scripts/data_audit.py
uv run python scripts/train_classifier.py
uv run python scripts/build_figures.py
uv run python scripts/build_notebook.py
```

O notebook executado está em `notebooks/challenge-002-analysis.ipynb`. Os dados brutos não são versionados.

## Recomendações

1. **Instrumentar antes de automatizar:** criação, primeira resposta, touch time, resolução, reabertura e override.
2. **Shadow mode:** comparar IA e humano no domínio real sem impacto no cliente.
3. **Assistência controlada:** exibir sugestão, manter confirmação humana e medir retrabalho.
4. **Canário restrito:** somente ações reversíveis depois dos gates de segurança.

## Limitações

- O Dataset 1 não mede tempos operacionais de forma válida.
- O Dataset 2 representa suporte interno de TI, não atendimento da G4.
- Não há dados da G4, validação temporal ou experimento em produção.
- Regex não detecta todo tipo de PII.
- Threshold validado em dados públicos não autoriza produção.
- ROI permanece cenário até touch time, custos, adoção e retrabalho serem medidos.

## Mapa da entrega

- `docs/gate-1/`: auditoria, diagnóstico e decisão
- `docs/gate-2/`: modelo, arquitetura, claims e medição
- `artifacts/`: métricas, tabelas, figuras e modelo
- `notebooks/`: análise executada
- `src/`: política, inferência, privacidade, auditoria e ROI
- `tests/`: testes da política e da interface
- `process-log/`: uso de IA, erros e correções

## Process log

Leia [`process-log/README.md`](process-log/README.md).

Submissão preparada em 24/07/2026.
