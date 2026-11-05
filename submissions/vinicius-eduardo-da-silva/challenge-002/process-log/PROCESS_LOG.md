# Process log: Challenge 002

Registro do que aconteceu, na ordem em que aconteceu. Ferramenta usada: Claude Code (modelo Claude Opus 5.5), no VS Code.

## Decisões tomadas por Vinicius

Em cada caso, o Claude apresentou as opções e uma recomendação, e Vinicius decidiu.

| Decisão | Escolha | Alternativas descartadas |
|---|---|---|
| Fazer outro desafio depois do 003 | Sim, o 002 | 001 e 004 |
| Como responder ao Diretor | Mostrar a resposta pedida e provar que é ruído | Só o que os dados sustentam; tratar como dados reais |
| Quanto automatizar | Rotear só o seguro, começando em modo sombra | Só sugerir; rotear mais |

## Decisões de julgamento do Claude

Estas regras não vêm dos dados e foram informadas a Vinicius: a lista de palavras sensíveis, enviar "Administrative rights" apenas como sugestão, e o mínimo de 50% de confiança para sugerir.

## Como o trabalho evoluiu

1. **Escolha** (`exploration/probe_challenges.py`). Depois de enviar o Challenge 003, Vinicius decidiu seguir para outro desafio. Um diagnóstico rápido dos outros três datasets indicou o 002 como a melhor opção, e ele aceitou seguir.
2. **Auditoria do dataset de suporte** (`exploration/audit_support.py`). Cada padrão foi comparado com dados embaralhados. O arquivo tem 8.469 tickets, não ~30.000, e as métricas se comportam como ruído.
3. **Teste do classificador** (`exploration/classifier_benchmark.py`). Com divisão aleatória, a acurácia foi de 85%. Nos tickets de clientes, o modelo classificou a maioria como Hardware, seja qual for o tipo.
4. **Teste de deriva e de ticket desconhecido** (`exploration/drift_and_guard.py`). A queda de acurácia no último bloco, vista na validação cruzada, levou a um teste em ordem de linhas. A trava de vocabulário nasceu aqui.
5. **Protótipo** (`solution/`). O modelo roda no navegador, e o teste confirma que ele dá os mesmos resultados do Python em 381 tickets.
6. **Documentação.** Relatório para o Diretor, README e registro do processo.

## Onde a IA errou e como foi corrigido

Os itens abaixo foram detectados pelo próprio Claude Code, nos testes e nas revisões que ele fez.

| Erro | Como apareceu | Correção |
|---|---|---|
| Afirmei que 16% dos tempos de resolução eram negativos | Na auditoria: o cálculo incluía tickets sem data. Entre os encerrados, são 49,3% | Número corrigido |
| Citei 99,4% de acerto em 36% dos tickets como evidência do sinal | Divisão aleatória, em um diagnóstico rápido. Nas últimas linhas, com um modelo mais simples e a política completa, são 92,7% em 51,7% | Só valem números com separação em ordem de linhas |
| Recomendei o 004 antes de olhar os dados | O diagnóstico mostrou que views, likes e seguidores não têm relação entre si | Recomendação retirada |
| Um teste prometia verificar os rótulos do teste, mas só treinava o modelo duas vezes | Revisão do próprio teste | Removido; a separação dos dados tem um teste próprio |
| O protótipo não trazia exemplos dos dados para justificar o que não automatizar, como o enunciado pede | Revisão contra o enunciado | Exemplos reais incluídos na aba Fluxo proposto |

## O que eu adicionei

> **Vinicius: esta seção precisa das suas palavras antes do envio.** Conte o que você avaliou, estranhou ou mudaria ao usar o protótipo.
