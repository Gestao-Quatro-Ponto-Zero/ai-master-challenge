# Documentação técnica — Triagem inteligente de suporte (versão final R9 v4)

## Resumo

- **Classificador:** TF-IDF (1–2-gramas, até 50 mil features) + LinearSVC (`C=0,5`, `class_weight='balanced'`) + calibração isotônica.
- **Dataset de treino:** Dataset 2 — IT Service Ticket Classification Dataset.
- **Teste:** n = 6.766.
- **F1-macro do classificador:** 0,8403 (baseline ingênuo: 0,0556).
- **F1-macro em exemplos sem quase-vizinho no treino:** 0,8204 (n = 5.740).
- **Categoria mais fraca:** Administrative rights (F1 = 0,7597; recall = 0,673).
- **Decisão operacional final:** 0 AUTOMATIC; 7 ASSISTED; 6 HUMAN_REQUIRED; 2 ESCALATE nos 15 casos da suíte.
- **Casos aprovados:** 12/15 segundo os critérios registrados em `test_cases.json`.

As métricas do classificador são distintas das métricas da política operacional. Os arquivos `evaluation/coverage_precision_*.csv` medem somente o classificador de categoria com limiares 0,55 e 0,70, antes da regra R9 final. Não representam cobertura ou precisão do roteamento final.

## Arquitetura

1. `domain_detector.py`: estima o domínio (IT_INTERNAL, FINANCIAL_COMMERCIAL, OUT_OF_SCOPE ou INDETERMINATE). **Não validado em amostra representativa**; não deve ser tratado como prova confiável de domínio.
2. `classifier_pipeline.pkl`: classifica tickets de TI em oito categorias e retorna probabilidades/top-3.
3. `priority_estimator.py`: estima prioridade por regras explícitas, pois não há rótulo confiável de prioridade nos dados.
4. `security_rules.py`: aplica R1–R7 e R9 para definir ESCALATE, HUMAN_REQUIRED ou ASSISTED.
5. `inference.py` e `api/main.py`: orquestram inferência e expõem os resultados para a interface.

### Política de segurança final

- R1: indício de comprometimento de conta → ESCALATE.
- R2: domínio diferente de IT_INTERNAL → HUMAN_REQUIRED.
- R3: prioridade CRITICAL com confiança abaixo do limiar alto → ESCALATE.
- R4: privilégio administrativo ou termos de privilégio → HUMAN_REQUIRED.
- R5: confiança abaixo do limiar baixo → HUMAN_REQUIRED.
- R6: prioridade CRITICAL com confiança suficiente → ASSISTED, nunca automático.
- R7: confiança intermediária → ASSISTED.
- R9: o domínio não possui validação representativa; portanto, qualquer caso que chegaria a AUTOMATIC é rebaixado para ASSISTED. A regra R8 permanece documentada como ramo de intenção, mas é inalcançável enquanto R9 estiver ativa.

O limiar intermediário de similaridade 0,49 utilizado numa versão anterior foi removido. A auditoria mostrou que esse valor era a mediana de uma população mista (IT + fora de domínio) e que similaridade não discriminava domínio. Nenhum limiar substituto foi inventado.

## Métricas do classificador por categoria

| Categoria | Precisão | Recall | F1 | Suporte |
|---|---:|---:|---:|---:|
| Access | 0,899 | 0,881 | 0,890 | 1.057 |
| Storage | 0,878 | 0,833 | 0,855 | 389 |
| HR Support | 0,849 | 0,869 | 0,859 | 1.551 |
| Purchase | 0,873 | 0,836 | 0,854 | 214 |
| Internal Project | 0,870 | 0,832 | 0,851 | 315 |
| Hardware | 0,816 | 0,843 | 0,829 | 1.934 |
| Miscellaneous | 0,816 | 0,834 | 0,825 | 1.043 |
| Administrative rights | 0,872 | 0,673 | 0,760 | 263 |

## Falhas conhecidas da suíte ponta a ponta

1. **Pedido de compra:** “I need to order 5 new monitors for the team” → Hardware, quando o esperado era Purchase. A decisão final é ASSISTED por R9, mas a categoria permanece incorreta.
2. **Privilégio administrativo:** “Please give me admin access to the server” → HR Support, quando o esperado era Administrative rights. R4 exige revisão humana, portanto a categoria errada não libera ação.
3. **Fora de escopo:** “What time is the company lunch today?” → IT_INTERNAL / HR Support e ASSISTED; deveria ser reconhecido como OUT_OF_SCOPE/INDETERMINATE e exigir revisão humana.

A suíte final está em `test_results_pos_ajuste.json`. O histórico anterior em `test_results.json` foi preservado e não deve ser confundido com o resultado final.

## Limitações e uso responsável

- O detector de domínio não foi validado com amostra representativa de tickets não-TI.
- O classificador foi treinado em inglês e em tickets internos de TI; não há validação para português nem para suporte B2C.
- O F1 do classificador não prova que o domínio está correto.
- Os limiares de categoria foram definidos como metas técnicas propostas para validação de negócio; não são SLAs aprovados por uma operação real.
- Não habilitar roteamento automático nem ações em produção sem piloto em shadow mode, amostra real rotulada e revisão humana.
- A prioridade é estimada por regras, não aprendida de rótulos confiáveis.

## Reproduzir o componente ML

A partir de `solution/fase4/ml/`:

```bash
pip install -r requirements.txt
python inference.py "I cannot log into my account"
```

O treinamento completo está documentado no process log. Não é necessário retreinar para executar a aplicação: os modelos treinados estão em `model/`.
