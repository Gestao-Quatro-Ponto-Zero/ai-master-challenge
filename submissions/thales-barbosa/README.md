# Submissão — Thales Barbosa — Challenge 002

## Sobre mim

- **Nome:** Thales Barbosa
- **LinkedIn:** [linkedin.com/in/thalessapuppo](https://www.linkedin.com/in/thalessapuppo/)
- **Challenge escolhido:** 002 — Redesign de Suporte (Operações / CX)

---

## Executive Summary

Comecei validando os dois datasets e descobri que os campos de tempo do dataset operacional não podem ser usados como duração: em 49,3% dos tickets fechados, a resolução aparece antes da primeira resposta. Com os sinais válidos, encontrei um problema distribuído pela operação: 33,3% dos tickets estão abertos sem primeira resposta, 34,0% aguardam o cliente e não há um canal, tipo ou prioridade que explique sozinho o resultado. A solução combina triagem, automação com limites de risco, assistência ao agente e um protótipo funcional com portal do cliente, Copilot, dashboards e simulador de ROI. No cenário-base, a automação libera 4.404 horas por ano e gera R$ 84,5 mil líquidos no primeiro ano; recomendo validar as premissas em um piloto de 4–6 semanas antes de ampliar.

---

## Solução

### Como executar

Requer Python 3.13.

```bash
cd solution
pip install -r requirements.txt   # ~8 min
python bootstrap.py               # ~25-30 min (uma vez; baixa modelos e gera embeddings)
python app.py                     # abre na hora
```

Abra [http://localhost:8502](http://localhost:8502). Perfis de demonstração:

- Cliente: `cliente123`
- Administrador: `admin123`

**Tempos** (medidos num ambiente limpo, Windows + Python 3.13, CPU): instalação ~8 min, preparação ~25–30 min só na primeira vez (roda quase sozinha — baixa dois modelos da HuggingFace e gera os embeddings dos 47.823 tickets), e o app sobe instantaneamente. O bootstrap é retomável: se interromper, continua de onde parou (`python bootstrap.py` de novo). Para só verificar os artefatos: `python bootstrap.py --check`. Testes: `pytest tests/ -q` (51 testes).

Quem não quiser rodar encontra a jornada completa do app em [`process-log/screenshots/`](process-log/screenshots/).

### Abordagem

1. Validei estrutura, qualidade e significado dos campos antes de calcular indicadores.
2. Separei dado observado de premissa. Como o dataset não mede duração de atendimento, horas e custos usam premissas declaradas com faixas de sensibilidade.
3. Usei o Dataset 1 para diagnóstico operacional e ROI, e o Dataset 2 para classificação e busca semântica.
4. Transformei a proposta em um fluxo funcionando: cliente tenta autoatendimento; casos incertos ou de risco vão para humano com contexto; o administrador acompanha operação e resolve a fila.

Detalhes técnicos:

- [Auditoria dos dados](solution/docs/data_audit.md) — a prova de que os timestamps são sintéticos
- [Diagnóstico e ROI](solution/docs/diagnostic_report.md)
- [Estratégia de automação](solution/docs/automation_strategy.md)
- [Modelos de ML](solution/docs/ml_models.md)
- [Notebooks executados](solution/notebooks/)

### Resultados / Findings

| Pergunta | Resultado |
|---|---|
| Onde o fluxo trava? | 33,3% Open sem primeira resposta e 34,0% Pending. Os testes por canal, tipo e prioridade não apontam um segmento responsável; o problema é sistêmico. |
| O que impacta satisfação? | Nos 2.769 tickets avaliados, nenhum efeito medido foi relevante. A satisfação média é 2,99/5 e 39,8% são detratores. Isso descreve o dataset recebido, não prova que drivers não existam em produção. |
| Quanto desperdiçamos? | Carga estimada de 9.207 h/ano, equivalente a 5,5 FTE e R$ 368 mil. Deflexão e assistência podem liberar 4.404 h/ano, ou 2,6 FTE. |
| Qual o retorno? | Com implantação interna e custo incremental de implantação igual a R$ 0, o cenário-base gera R$ 84,5 mil líquidos no ano 1, ROI de 282% e payback imediato. Em regime, gera R$ 146,2 mil líquidos/ano. |

O protótipo “PAUTA” oferece:

- portal em pt-BR com autoatendimento e abertura de chamado qualificado;
- login separado para cliente e administrador;
- dashboard executivo e visão operacional;
- Copilot com categoria, confiança, prioridade, equipe, vetos e tickets semelhantes;
- fila de chamados e reaproveitamento de resoluções humanas;
- simulador de ROI com premissas ajustáveis.

No experimento em inglês, TF-IDF+Regressão Logística atingiu macro-F1 de 0,865. O portal serve um modelo multilíngue com macro-F1 de 0,784, threshold 0,70, cobertura de 64,1% e 91,7% de acerto nos casos cobertos. A escolha reduz desempenho no teste inglês, mas permite comparar perguntas em português com tickets históricos em inglês.

### Recomendações

1. Rodar um piloto de 4–6 semanas com autoatendimento em Product inquiry e assistência em Technical issue.
2. Medir `created_at`, `first_response_at`, `resolved_at`, reabertura e CSAT para substituir premissas por tempos reais.
3. Direcionar a capacidade liberada para os tickets sem primeira resposta, em vez de assumir redução imediata de equipe.
4. Automatizar follow-up de Pending e manter humano obrigatório em disputas, risco legal, fraude, prioridade Critical e exceções de política.

### Limitações

1. Os timestamps do Dataset 1 são sintéticos; horas e custos são estimativas com sensibilidade, não medição direta.
2. As distribuições do dataset são muito uniformes. Os resultados de satisfação precisam ser repetidos com dados reais de produção.
3. O classificador foi treinado em tickets de TI. Para uma operação B2C, os pesos precisam ser treinados na taxonomia real da empresa.
4. Uma sonda curta em pt-BR acertou 3 de 5 intenções. O protótipo mantém gate de confiança, piso de evidência e escalonamento humano por esse motivo.
5. As taxas de deflexão são hipóteses para o piloto. O cenário conservador continua negativo quando desempenho é baixo e custo recorrente é alto.

---

## Process Log — Como usei IA

Os registros completos estão em [`process-log/`](process-log/).

### Ferramentas usadas

| Ferramenta | Uso |
|---|---|
| Claude Code | Exploração inicial, análise dos dados, código, notebooks e primeira versão da documentação. |
| Codex | Revisão pré-submissão, correção do ROI, criação do bootstrap e validação final do pacote. |
| Python e pytest | Recalcular resultados, treinar modelos e testar as regras da solução. |
| Navegador local | Conferir login, permissões, dashboards, Copilot, portal e ROI em funcionamento. |

### Workflow

Primeiro dividi o problema em diagnóstico, automação, ML e protótipo. A auditoria dos timestamps mudou o plano: em vez de publicar tempos médios inválidos, usei status, volume e satisfação como sinais observados e tratei AHT como premissa. Depois implementei as regras de automação e o modelo econômico em código, comparei abordagens de classificação e montei o fluxo cliente/admin. Por fim, executei testes, notebooks e o aplicativo antes de preparar a submissão.

### Onde a IA errou e como corrigi

- Uma versão do relatório informou AHT médio de 14,8 minutos; o recálculo mostrou 18,4. Corrigi o documento e mantive o valor vindo do código.
- A primeira regra de SLA usava valor absoluto do delta entre timestamps. Descartei a regra porque uma duração real não funciona assim e os campos de origem eram sintéticos.
- O modelo multilíngue classificava texto vago como Hardware com confiança muito alta. Adicionei um segundo bloqueio baseado na similaridade com casos reais.
- A primeira versão do ROI incluía implantação externa. Ajustei para a decisão de negócio informada: construção interna pelo AI Master, com custo incremental de implantação igual a R$ 0.

### O que eu adicionei que a IA sozinha não faria

Eu defini os limites da solução: não transformar timestamps inválidos em métricas, não automatizar casos de risco, manter o cenário conservador negativo e tratar capacidade liberada como decisão de gestão, não como demissão automática. Também determinei que cada correção final fosse revisada separadamente antes de entrar na entrega.

---

## Evidências

- [x] Narrativa escrita em [`process-log/`](process-log/)
- [x] Notebooks comentados e executados
- [x] Código funcional com 51 testes automatizados
- [x] Screenshots do protótipo em [`process-log/screenshots/`](process-log/screenshots/)
- [ ] Screenshots de conversas com IA
- [ ] Screen recording
- [ ] Chat exports
- [ ] Git history evolutivo — não utilizado como evidência principal

_Submissão enviada em: 2026-07-19_
