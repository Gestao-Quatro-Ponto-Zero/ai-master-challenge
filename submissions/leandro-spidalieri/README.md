# Submissão — Leandro Spidalieri — Challenge 002

## Sobre mim

- **Nome** — Leandro Spidalieri
- **LinkedIn** — pendente de fornecimento
- **Challenge escolhido** — 002, Redesign de Suporte

## Executive Summary

O SupportOps AI reúne diagnóstico de suporte, triagem assistida de TI e um simulador de capacidade. Dos 8.469 tickets de suporte, 5.700 estavam abertos ou aguardavam o cliente. A falta de abertura e de tempo ativo, somada a 1.365 inversões em 2.769 pares de timestamps, limita o diagnóstico de atraso, resolução e desperdício. Em 6.664 tickets reservados de TI, a política acertou o tema em 5.114 das 5.591 sugestões. Proponho testar a coleta em chamados técnicos nas redes sociais, comparar os quatro canais antes de intervir e avaliar sugestões em modo sombra antes de avançar para confirmação humana. [Diagnóstico e piloto](docs/analysis.md) · [Avaliação](solution/artifacts/evaluation.json).

## Solução

### Abordagem

Auditoria de esquema, semântica, qualidade e privacidade nos dois snapshots do Kaggle. Diagnóstico pelo Dataset 1 e prova de classificação pelo Dataset 2, cada qual com sua população e taxonomia. Em TI, textos equivalentes e quase duplicados ficaram na mesma partição. O pipeline treinou um TF-IDF com regressão logística e comparou com a maioria do treino no mesmo teste. O corte foi definido antes da avaliação reservada. [Método e reprodução](docs/technical.md).

### Resultados / Findings

- **Carga e satisfação.** Os canais têm entre 2.073 e 2.143 registros. O cruzamento com mais volume é Social media × Technical issue entre os cortes de canal e tipo, com 465 tickets. Há 2.769 notas, todas entre fechados, das quais 1.087 (39,3%) são 4 ou 5. A interface explicita o denominador e permite filtrar os quatro eixos. [Agregados do diagnóstico](solution/artifacts/diagnosis.json).
- **Triagem de TI.** Acurácia de 86,1% e macro-F1 de 85,9%, ante 29,1% e 5,6% da maioria. A política teve 83,9% de cobertura e 91,5% de acerto entre as sugestões. Em `Administrative rights`, 46 de 246 tickets rotulados receberam sugestões para outras classes, apesar das guardas. [Métricas e erros](solution/artifacts/evaluation.json).
- **Capacidade hipotética.** O cenário base estima 18 h/mês para 600 triagens assistidas sob as premissas iniciais. Com conversão de capacidade em caixa igual a zero, o cenário base tem caixa líquido de −R$ 150/mês antes da implantação. [Premissas e cenários](solution/artifacts/impact.json).

### Recomendações

Instrumentar abertura, primeira resposta, fechamento, troca de fila e minutos ativos por tarefa. Usar o volume e a cobertura para escolher um piloto e rotular tickets na chegada. Testar sugestões em paralelo, sem exibi-las ao atendente. Se a qualidade no domínio alvo atender aos critérios acordados, comparar triagem assistida com manual. Exigir confirmação da fila pelo atendente e manter estornos, cancelamentos, permissões e ações críticas sob responsabilidade humana. [Matriz de decisões](docs/analysis.md#fluxo-proposto-e-autoridade) · [Protocolo de piloto](docs/analysis.md#protocolo-de-piloto).

### Limitações

FRT, TTR, tendência, causalidade sobre CSAT e desperdício observado são indisponíveis com o arquivo de suporte. A avaliação de classificação vale para o corpus de TI e o score é não calibrado. Faltam avaliação de transferência ao suporte ao consumidor, avaliação em português e medição operacional de ganho. Recuperação de casos, geração de respostas e integração com atendimento ficaram fora do P0 entregue. [Limites por fonte](solution/artifacts/manifest.json) · [Análise](docs/analysis.md).

### Executar localmente

A partir da pasta desta submissão, com **Python 3.13** e Bash:

```bash
cd solution
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/pipeline.py acquire
.venv/bin/python scripts/pipeline.py audit
.venv/bin/python scripts/pipeline.py train
.venv/bin/python scripts/pipeline.py evaluate
bash scripts/validate.sh
.venv/bin/python -m streamlit run app.py
```

Abra [SupportOps AI local](http://127.0.0.1:8501). Os agregados publicados podem ser vistos sem treinar, e o simulador funciona sem dados brutos. A triagem de TI usa o modelo gerado pelo comando acima. Para dados baixados manualmente ou falha de aquisição, siga o [guia de dados](solution/data/README.md).

Para conferir a triagem, abra **Teste reservado (local)** na área **Triagem**, escolha um ticket em **Amostra aleatória** e clique em **Avaliar ticket**. Compare a categoria prevista com o rótulo de referência. Ao marcar a prioridade como **Crítica** e avaliar novamente, a decisão passa a revisão humana.

## Process Log — Como usei IA

### Ferramentas usadas

Codex no desktop para decompor, implementar e revisar o P0. Terminal e navegador para testar as hipóteses e registrar saídas. A aplicação usa NLP supervisionado local para classificar tema. [Registro do processo](process-log/README.md).

### Workflow

1. Leitura do briefing, inspeção Git e conferência do commit oficial.
2. Aquisição e auditoria dos CSVs para definir o que o diagnóstico poderia sustentar.
3. Particionamento por grupos, treino, congelamento do corte, avaliação e implementação da interface.
4. Recontagem independente, testes de aplicação e navegador, reprodução limpa e revisão do escopo Git.

### Onde a IA errou e como corrigi

O Codex corrigiu um seletor posicional que atingia o controle de navegação no AppTest. A reprodução limpa expôs um HTTP 404 no downloader em Python. A comparação com a aquisição inicial levou ao endpoint público e a cabeçalhos explícitos do cliente. O Chrome também revelou formatação matemática indevida em valores em reais, corrigida antes das capturas finais. [Registro de iterações](process-log/README.md#do-briefing-à-evidência).

### O que eu adicionei que a IA sozinha não faria

A solicitação de Leandro delimitou escopo, verificabilidade, necessidade de revisão e restrições de publicação.

**Minha decisão principal foi testar a coleta em um recorte e comparar os quatro canais antes de intervir.** Escolhi os chamados técnicos em redes sociais para testar a medição. Em seguida, usaria o mesmo protocolo em uma amostra dos quatro canais para decidir onde agir com base no tempo ativo e na espera.

Na automação, Leandro escolheu avaliar sugestões em modo sombra e só então avançar para assistência com confirmação humana se o teste no domínio alvo sustentar a mudança. Para o impacto, manteve 18 h/mês como hipótese base, 3,15 h/mês como cenário conservador e 0% de conversão em caixa. O Codex executou o ensaio técnico registrado. [Decisões confirmadas durante a revisão](process-log/README.md#decisões-confirmadas-por-leandro).

## Evidências

- [x] Narrativa do uso de IA, iterações e decisões. [Process log](process-log/README.md).
- [x] Saídas da verificação e capturas do app local. [Checks](process-log/checks.txt) · [Capturas](process-log/screenshots).

_Rascunho para revisão do candidato. Envio pendente._
