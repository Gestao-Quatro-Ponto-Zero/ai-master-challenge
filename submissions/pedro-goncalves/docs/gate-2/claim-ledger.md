# Claim ledger

| Claim | Status | Evidência | População e limite |
|---|---|---|---|
| O Dataset 1 possui 8.469 tickets | Medido | `data_audit.json` e hash da fonte | Arquivo baixado em 23/07/2026 |
| 49,3% dos pares temporais têm resolução anterior à primeira resposta | Medido | 1.365 de 2.769 pares | Indica inconsistência, não causa |
| Todas as descrições do Dataset 1 contêm placeholder | Medido | 8.469 de 8.469 | Textos não representam linguagem natural íntegra |
| 460 mensagens relatam contatos repetidos sem solução | Medido | Busca literal reproduzível em `data_audit.json` | Não equivale a 460 pessoas únicas; 152 abertos, 156 pendentes e 152 encerrados |
| O Dataset 1 não possui duplicatas técnicas comprovadas | Medido | 0 linhas idênticas e 0 IDs repetidos em `data_audit.json` | Descrições repetidas permanecem como eventos distintos |
| `Ticket Subject` e `Ticket Type` quase não se associam | Medido | Cramér V 0,034, p 0,981 | Não tratar nenhum dos dois como verdade isolada |
| O modelo do Dataset 2 concentrou 85,1% das previsões do Dataset 1 em Hardware | Medido | `cross_dataset_audit.json`, 8.469 mensagens | Teste fora do domínio; acurácia desconhecida |
| 49,5% das mensagens do Dataset 1 ficaram acima de 0,75 | Medido | `cross_dataset_audit.json` | Confiança aparente não autoriza transferência de taxonomia |
| Canal, prioridade, tipo e assunto não apresentaram associação material com CSAT | Medido | Kruskal-Wallis nos 2.769 fechados | Não prova ausência de efeito real |
| O classificador atingiu macro-F1 0,868 | Medido | Teste final estratificado de 7.176 linhas, seed 42 | Apenas Dataset 2 |
| Threshold 0,75 cobre 69,7% com acurácia 96,6% nos cobertos | Medido | Threshold escolhido na validação e reportado uma vez no teste final | Referência de shadow mode |
| O modelo classifica a fila de clientes | Não provado | Taxonomia do Dataset 2 é de TI | Claim proibido |
| O sistema reduz TTR ou custo | Não provado | Sem touch time, implantação ou experimento | Usar apenas calculadora de cenários |
| Shadow mode reduz risco de implantação | Hipótese operacional | Política e protótipo demonstráveis | Deve ser validada em piloto |
| A memória evita repetir erros aprovados | Hipótese testável | SQLite, recuperação por termos e gate humano | Ainda sem piloto no domínio real |
| A memória contém seis lições operacionais aprovadas e uma correção reproduzida | Medido no protótipo | Semeadura idempotente e testes automatizados | Não equivale a retreinamento do modelo |
| A matriz demonstrativa passa em 16 de 16 casos | Medido no protótipo | `case_test_matrix.csv` e suíte automatizada | Cobre casos selecionados, não toda linguagem possível |
| O fluxo universal lê duas planilhas CSV ou XLSX | Medido no protótipo | Testes de leitura e dois uploaders | Não prova aderência semântica a qualquer empresa |
| O humano controla uso, papel e ordem das colunas | Medido no protótipo | `data_editor`, validação e testes de schema | A sugestão inicial pode estar errada |
| O painel universal representa desempenho do negócio | Não provado | Qualidade estrutural não equivale a resultado operacional | Indicadores dependem dos campos e definições validadas |
| A memória usa retropropagação contínua | Não provado | Não há retreinamento online | Claim proibido na versão atual |
| O protótipo precisa de RAG para aprender | Não provado | Lições atuais são pequenas, estruturadas e recuperadas deterministicamente | Reavaliar apenas quando a base validada crescer |
| O gate identifica todo cliente que precisa de cuidado | Hipótese testável | Regras explícitas aplicadas ao Dataset 1 | Medir falsos negativos e encaminhamentos desnecessários no piloto |

## Regra de comunicação

Resultados observados, estimativas e hipóteses nunca são misturados. Todo número financeiro depende de volume elegível, adoção, touch time, revisão, retrabalho, custo de pessoal e custo da solução aprovados pelo dono do processo.
