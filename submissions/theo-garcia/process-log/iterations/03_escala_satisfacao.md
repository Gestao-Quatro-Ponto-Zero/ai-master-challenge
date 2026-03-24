# Iteracao: Pesquisa de Satisfacao com Escala Quebrada

**Fase:** 3 — Analise de Causa Raiz
**Ferramenta:** Claude Code (Opus 4.6)

---

**Eu:** "Investigue o non-response bias nos satisfaction scores. 41% sao null — quem nao responde?"

**IA:** Analisou correlacao entre nulls e churn_flag. Mostrou que churned tem mais nulls que retidos. Conclusao: "possivel non-response bias — insatisfeitos podem nao responder."

**Eu:** "Mostre a distribuicao dos scores que EXISTEM."

**IA:**
```
3.0    396 respostas
4.0    405 respostas
5.0    374 respostas
Nulls: 825
Total: 2.000
```

**Meu julgamento:** Espera. Zero respostas com nota 1 ou 2? Em 2.000 tickets?

Isso nao é non-response bias — é um instrumento quebrado. A pesquisa simplesmente nao permite (ou nao incentiva) notas baixas. A escala efetiva é 3-5, nao 1-5.

Implicacoes:
1. A media de 4.0 nao significa "satisfacao boa" — significa "unica opcao disponivel"
2. O CS esta tecnicamente correto ao dizer "satisfacao esta ok" — mas esta medindo com regua de borracha
3. A metrica de satisfacao nao detecta insatisfacao — detecta ausencia de resposta
4. Combinar 41% de nulls com escala truncada = a empresa NAO TEM dado de satisfacao confiavel

**O que fiz:** Documentei como finding separado e adicionei ao dashboard na secao "Validacao dos Claims do CEO". O avaliador precisa ver que eu nao so analisei os dados — questionei se os dados sao confiaveis.

**Evidencia:** `notebooks/03_root_cause_analysis.py` (Finding 6), `app.py` (secao CEO Claims)
