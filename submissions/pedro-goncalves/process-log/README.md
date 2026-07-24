# Process log: como usei IA

## Ferramentas

| Ferramenta | Papel |
|---|---|
| Codex | Coordenação, pesquisa, auditoria, implementação, testes e integração |
| Maestri | Orquestração visual da equipe e isolamento de papéis |
| Lume, Antigravity | Primeiro rascunho de diagnóstico operacional |
| Nexo, Antigravity | Primeiro rascunho de fronteira humano-IA |
| Crivo, Codex independente | Rubrica adversarial e gates de qualidade |
| Context7 | Documentação atual do Streamlit e AppTest |

## Decomposição antes do build

O problema foi separado em sete gates:

1. contexto, rubrica e matriz de decisão;
2. auditoria dos dois datasets;
3. diagnóstico operacional e ROI;
4. fronteira humano-IA;
5. protótipo;
6. documentação e process log;
7. revisão adversarial.

Três agentes foram criados no Maestri. Lume e Nexo podiam propor; Crivo não podia editar nem avaliar sem evidência. O Codex permaneceu como quarto papel, responsável por integração e decisão.

## Linha do tempo

| Momento | Ação | Resultado |
|---|---|---|
| 23/07 | Leitura do challenge, guia, template e CONTRIBUTING | Critérios formais e time budget consolidados |
| 23/07 | Crivo criou rubrica antes de ver a solução | Bloqueadores definidos sem viés de confirmação |
| 23/07 | Lume e Nexo produziram rascunhos paralelos | Hipóteses úteis, mas também números e regras sem evidência |
| 24/07 | Download, hash e auditoria física dos arquivos | Dataset 1 divergiu do brief e teve campos temporais inválidos |
| 24/07 | Matriz ponderada com veto crítico | Shadow mode venceu com 4,6 de 5 |
| 24/07 | Treino e calibração do classificador | Macro-F1 0,868 no teste final do Dataset 2 |
| 24/07 | Construção do protótipo e testes | 16 testes aprovados |
| 24/07 | Revisão de claims e documentação | ROI observado e automação produtiva foram vetados |
| 24/07 | Gate final independente | FAIL inicial por precedência, seleção de threshold e fingerprint |
| 24/07 | Correção adversarial | Política reordenada, split 70/15/15 e log sem fingerprint |

## Onde a IA errou

O primeiro rascunho de diagnóstico assumiu:

- 30 mil tickets como volume medido;
- touch time de 10 e 30 minutos;
- custo de R$ 25 por hora;
- 40% de elegibilidade;
- custos anuais de implantação;
- hipóteses causais sobre TTR e CSAT.

O primeiro rascunho de automação também sugeriu prioridade automática, respostas diretas, categorias equivalentes entre os datasets e confiança fictícia.

Esses elementos foram rejeitados porque não existiam no arquivo, no brief ou em fonte operacional aprovada.

## Como corrigi

1. Recontagem por parser CSV, não por linhas físicas do arquivo.
2. Hash SHA-256 e relatório de qualidade reproduzível.
3. Inspeção semântica dos campos temporais.
4. Separação explícita dos papéis dos datasets.
5. Classificador treinado apenas no Dataset 2.
6. Split 70/15/15, baseline, threshold na validação, teste final, calibração e abstenção.
7. Claim ledger separando medido, hipótese e não provado.
8. Calculadora paramétrica sem defaults financeiros inventados.
9. Política determinística com human-only, kill switch e log sem texto bruto.

## Julgamento humano que mudou a solução

A pergunta central deixou de ser "onde colocar IA" e passou a ser **"qual decisão tem evidência suficiente para receber autonomia"**.

Foi adotada uma matriz ponderada:

- evidência verificável: 30%;
- impacto operacional: 25%;
- segurança e controle humano: 20%;
- viabilidade: 15%;
- diferenciação: 10%.

Um problema crítico de evidência, segurança ou conformidade aplica veto mesmo quando a média ponderada é alta. Essa regra impediu que o protótipo tecnicamente funcional virasse uma alegação de produção.

## Iterações principais

### Iteração 1

Proposta ampla de diagnóstico e automação. Reprovada por premissas não rastreáveis.

### Iteração 2

Auditoria de dados e redefinição do problema. A falta de telemetria tornou-se o achado principal.

### Iteração 3

Classificador com confiança calibrada e abstenção. Uso limitado ao Dataset 2.

### Iteração 4

Política de controle humano, PII, audit log, ROI paramétrico e testes da interface.

### Iteração 5

Revisão de claims, limites e conformidade da pasta de submissão.

### Iteração 6

O Crivo reprovou a primeira versão final por três achados altos:

1. shadow mode era avaliado antes de categoria sensível e baixa confiança;
2. o mesmo conjunto era usado para observar e escolher threshold;
3. o log guardava SHA-256 determinístico do texto mascarado.

A política foi reordenada, foram adicionados testes combinados, o experimento passou a usar treino 70%, validação de threshold 15% e teste final 15%, e todo fingerprint derivado do texto foi removido. A calculadora também passou a subtrair retrabalho no mesmo horizonte dos demais parâmetros.

### Gate final

O Crivo executou `uv sync --frozen` e os 16 testes em uma cópia temporária. O segundo veredito foi **PASS**, sem achado crítico ou alto. O risco residual de retenção do JSONL foi mantido como gate explícito antes de qualquer piloto real.

## Evidências

- `notebooks/challenge-002-analysis.ipynb`: análise executada
- `artifacts/data_audit.json`: auditoria estruturada
- `artifacts/classifier_metrics.json`: métricas da validação e do teste final
- `artifacts/tables/`: tabelas intermediárias
- `docs/gate-2/claim-ledger.md`: procedência dos claims
- `tests/`: comportamento da política e interface
- histórico git da branch de submissão

## Privacidade

Nenhum nome, email, telefone ou texto bruto de cliente foi copiado para a entrega. O log não guarda texto nem fingerprint derivado do texto. Registra somente decisão, versões, estado da política e contagens de padrões mascarados. A retenção precisa ser definida antes de produção.
