# Memo: triagem de tickets com IA

**Decisão pedida:** aprovar um piloto de 4 semanas com três frentes:

- instrumentar 5 eventos;
- colocar a triagem em modo sombra e depois ativar "IA decide" só em Access e Purchase, com "IA sugere" em outras 4;
- escrever com o time a definição das 8 filas.

E **não** contratar LLM para classificar.

## Por quê

- Os dados de tempo e satisfação não mostram gargalo: 49,3% dos tickets fechados registram resolução antes da 1ª resposta, e o CSAT não difere do acaso [1].
- O obstáculo é a medição, não o volume: por prioridade, já haveria amostra (332 tickets por grupo contra 123 necessários) [2].
- A seleção fora da dobra indicou 5 categorias (33,4% do volume); a confirmação no teste sustentou 2 (≈ 13,4%); só essas são ativadas, com precisão de 98,8% [3].
- A taxonomia não se explica sozinha:
  - um revisor externo concorda 46,7% com o rótulo histórico [4];
  - na mesma faixa de dúvida, o modelo acerta 69,5% e um LLM 26,5% [5].

  O modelo treinado nos rótulos históricos acerta 85,1% no geral [6].

## Ganho

- **Com uma etapa separada de triagem:** ~R$ 7,0 mil/ano (faixa de R$ 3,3 mil a R$ 13,4 mil) [7].
- **Sem etapa separada:** zero.
- O ganho maior ("IA sugere" e reatribuições evitadas) será medido no piloto.

O roteamento foi medido em 47.837 tickets reais de TI [8]. O volume da operação (30 mil/ano) é premissa.

## Risco e controle

- **Injeção de instrução:** em 6.395 ataques simulados, nenhum mudou uma decisão automática (limite superior 0,06%). Mas 860 (13,4%) saíram de "IA decide" para humano: o ataque não engana a decisão automática, mas gera carga humana e reduz a cobertura [9].
- **Rollback em segundos:** o modo sombra manda tudo para humano e mantém o log [10].
- **Versão pior não entra:** um teste de qualidade barra modelo ou política piores [10].

## Próximas 4 semanas

- **S1:** eventos instrumentados + triagem em modo sombra.
- **S2–S3:** medir precisão pelas correções e tempo de confirmação em "IA sugere".
- **S4:** ativar "IA decide" em Access e Purchase se a meta se confirmar. O diagnóstico por canal × prioridade fica possível em ~3,6 semanas de eventos [2].

---
Fontes (`solution/outputs/`, salvo indicação):

1. `f1_ds1_auditoria.json`
2. `f2_mde.csv`
3. `f8_faixas.json`
4. `f3_h2.json`; `process-log/revisao_rotulos_adjudicada.csv`
5. `f3_llm.json`
6. `f3_classico.json`
7. `f8_economia.csv`
8. `f1_dados.json`
9. `f5_injecao.json`
10. `docs/producao.md`
