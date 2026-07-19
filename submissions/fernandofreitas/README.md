# Submissao - Fernando Freitas - Challenge 002

## Sobre mim

- **Nome:** Fernando Freitas
- **LinkedIn:** https://www.linkedin.com/in/fernando-freitas03/
- **Challenge escolhido:** 002 - Redesign de Suporte

---

## Executive Summary

Construí um protótipo funcional de **Support Copilot**: uma experiência de suporte assistida por IA que tenta resolver a dúvida do cliente antes de abrir ticket, abre tickets já classificados quando precisa de humano, e entrega ao admin um painel com gargalos, backlog, satisfação, oportunidades de automação e ROI. A análise encontrou 8.469 tickets no Dataset 1, com 5.700 abertos/pendentes, mediana corrigida de resolução de 11,6h e p90 de 21,7h. A automação proposta não tenta substituir o suporte inteiro: ela deflete dúvidas simples, qualifica tickets, sugere rota e mantém humano nos casos críticos, ambíguos, reembolso, cancelamento e baixa confiança.

---

## Solução

A entrega combina diagnóstico, automação e build:

- **App funcional:** `solution/flask_app.py`
- **Setup e deploy:** `solution/README.md`
- **Diagnóstico operacional:** `solution/docs/operational-diagnosis.md`
- **Blueprint de automação:** `solution/docs/automation-blueprint.md`
- **Auditoria dos dados:** `solution/docs/dataset-1-audit.md` e `solution/docs/dataset-2-audit.md`
- **Checklist de aderência:** `solution/docs/challenge-checklist.md`
- **Process log:** `process-log/ai-workflow.md`

### Como funciona o protótipo

1. Cliente entra no app autenticado.
2. Cliente descreve a dúvida em um input livre.
3. A IA consulta a base de conhecimento/RAG local e tenta responder.
4. Se resolver, o ticket é evitado.
5. Se não resolver, o cliente abre um ticket com o contexto já preenchido.
6. O sistema sugere categoria, prioridade e confiança.
7. Admin vê painel operacional e fila.
8. Humano resolve o ticket.
9. A resolução humana entra na base de conhecimento para casos futuros.

### Abordagem

1. Li o briefing e transformei os requisitos em perguntas de negócio.
2. Auditei os dois datasets antes de concluir qualquer coisa.
3. Identifiquei limitações reais: Dataset 1 tem 8.469 tickets, não ~30.000, e timestamps inconsistentes.
4. Calculei gargalos, backlog, CSAT, desperdício recuperável e combinações críticas.
5. Treinei um classificador com o Dataset 2 para demonstrar triagem automática.
6. Criei um app Flask com front customizado, autenticação simples, IA/RAG, abertura inteligente de ticket, painel admin e loop de aprendizado.

### Resultados / Findings

- Dataset 1: 8.469 tickets; 2.769 fechados com tempo/CSAT e 5.700 abertos ou pendentes.
- Mediana corrigida de resolução: 11,6h.
- P90 corrigido de resolução: 21,7h.
- Phone e Social media têm os piores tempos médios.
- `Phone + High + Refund request` tem o pior CSAT observado entre combinações relevantes: 2,29.
- Excesso acima da mediana nos tickets fechados: 8.733,5 horas.
- Classificador do Dataset 2: 86,5% accuracy e 86,6% macro F1.

### Recomendações

1. Implantar IA primeiro como camada de deflexão e qualificação, não como automação total.
2. Usar IA para responder dúvidas simples, recuperar casos similares, classificar e sugerir rota.
3. Escalar sempre para humano casos críticos, reembolso, cancelamento, perda de dados, baixa confiança e exceções de política.
4. Medir deflexão, taxa de escalonamento, tempo de primeira resposta, CSAT, reopen rate e taxa de override humano.
5. Corrigir instrumentação de timestamps antes de usar tempo de resolução como SLA oficial.

### Limitações

- O Dataset 1 público tem menos registros do que o briefing menciona.
- Os timestamps exigem tratamento; a métrica de resolução foi corrigida com regra de virada de dia.
- As categorias do Dataset 2 são complementares, não a taxonomia real do Dataset 1.
- O loop de aprendizado do protótipo salva resoluções em SQLite local; em produção, exigiria revisão humana, base vetorial, avaliação de qualidade e retreinamento controlado.

---

## Como rodar

```powershell
pip install -r submissions\fernandofreitas\solution\requirements.txt
python submissions\fernandofreitas\solution\flask_app.py
```

Abra:

```text
http://localhost:5000
```

Senhas demo:

```text
Cliente: cliente123
Admin: admin123
```

---

## Process Log - Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| Codex | Leitura do briefing, auditoria dos dados, análise exploratória, construção do protótipo, documentação e revisão crítica |
| OpenAI API | Opcional no app para resposta generativa do assistente, com fallback local |

### Workflow

1. Usei Codex para inspecionar o repositório e entender as regras de submissão.
2. Decompus o challenge em diagnóstico, automação, build e evidências.
3. Auditei os datasets localmente.
4. Identifiquei problemas de qualidade nos dados e documentei as limitações.
5. Calculei os gargalos e segmentos críticos.
6. Treinei e validei um classificador com o Dataset 2.
7. Construí uma primeira versão analítica e depois evoluí para um app Flask mais apresentável.
8. Ajustei o conceito para defletir tickets antes de abrir chamados.
9. Documentei decisões, erros, trade-offs e próximos passos.

### Onde a IA errou e como corrigi

A primeira leitura dos tempos gerou médias negativas de resolução, porque parte dos registros tinha `Time to Resolution` anterior a `First Response Time`. Em vez de aceitar o número, revisei a lógica, tratei esses casos como provável virada de dia e documentei a limitação. Também descartei a ideia de automação total, porque os dados mostram grupos sensíveis onde humano continua necessário.

### O que eu adicionei que a IA sozinha não faria

O principal julgamento foi reposicionar a solução: em vez de apenas classificar tickets, o produto tenta evitar tickets simples antes de virarem fila, abre tickets melhores quando precisa de humano e aprende com resoluções validadas. Isso conecta operação, produto, IA e mensuração de impacto.

---

## Evidências

- [x] Narrativa escrita em `process-log/ai-workflow.md`
- [x] Código funcional em `solution/flask_app.py`
- [x] Diagnóstico e auditorias em `solution/docs/`
- [x] Checklist de aderência em `solution/docs/challenge-checklist.md`
- [x] Screenshots do app em `process-log/screenshots/`
- [x] Git history com commits separados por módulo

---

_Submissão enviada em: 18/07/2026_
