# Claim ledger

| Claim | Status | Evidência | População e limite |
|---|---|---|---|
| O Dataset 1 possui 8.469 tickets | Medido | `data_audit.json` e hash da fonte | Arquivo baixado em 23/07/2026 |
| 49,3% dos pares temporais têm resolução anterior à primeira resposta | Medido | 1.365 de 2.769 pares | Indica inconsistência, não causa |
| Todas as descrições do Dataset 1 contêm placeholder | Medido | 8.469 de 8.469 | Textos não representam linguagem natural íntegra |
| Canal, prioridade, tipo e assunto não apresentaram associação material com CSAT | Medido | Kruskal-Wallis nos 2.769 fechados | Não prova ausência de efeito real |
| O classificador atingiu macro-F1 0,868 | Medido | Teste final estratificado de 7.176 linhas, seed 42 | Apenas Dataset 2 |
| Threshold 0,75 cobre 69,7% com acurácia 96,6% nos cobertos | Medido | Threshold escolhido na validação e reportado uma vez no teste final | Referência de shadow mode |
| O modelo funciona para a G4 | Não provado | Sem dados G4 | Claim proibido |
| O sistema reduz TTR ou custo | Não provado | Sem touch time, implantação ou experimento | Usar apenas calculadora de cenários |
| Shadow mode reduz risco de implantação | Hipótese operacional | Política e protótipo demonstráveis | Deve ser validada em piloto |
| A memória evita repetir erros aprovados | Hipótese testável | SQLite, recuperação por termos e gate humano | Ainda sem piloto no domínio real |
| A memória usa retropropagação contínua | Não provado | Não há retreinamento online | Claim proibido na versão atual |

## Regra de comunicação

Resultados observados, estimativas e hipóteses nunca são misturados. Todo número financeiro depende de volume elegível, adoção, touch time, revisão, retrabalho, custo de pessoal e custo da solução aprovados pelo dono do processo.
