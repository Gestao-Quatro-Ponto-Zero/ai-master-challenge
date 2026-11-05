# Process log: Challenge 002

Registro do que aconteceu, na ordem em que aconteceu. Ferramenta usada: Claude Code (modelo Claude Opus 5.5), no VS Code.

## Como o trabalho evoluiu

1. **Escolha.** Depois de enviar o Challenge 003, Vinicius decidiu seguir para outro desafio. Um diagnóstico rápido dos outros três datasets indicou o 002 como a melhor opção, e ele aceitou seguir.
2. **Auditoria do dataset de suporte** (`exploration/audit_support.py`). Cada padrão foi comparado com dados embaralhados. O arquivo tem 8.469 tickets, não ~30.000, e as métricas se comportam como ruído.
3. **Teste do classificador** (`exploration/classifier_benchmark.py`). Com divisão aleatória, a acurácia foi de 85%. Nos tickets de clientes, o modelo classificou 76% como Hardware, seja qual for o tipo do ticket.
4. **Teste de deriva e de ticket desconhecido** (`exploration/drift_and_guard.py`). A queda de acurácia no último bloco, vista na validação cruzada, levou a um teste em ordem de linhas: 80,5% de acurácia nos 20% finais. Uma trava por vocabulário conhecido bloqueou 98,3% dos tickets de clientes e 4,9% dos tickets de TI.

## Onde a IA errou e como foi corrigido

| Erro | Como apareceu | Correção |
|---|---|---|
| Afirmei que 16% dos tempos de resolução eram negativos | Na auditoria: o cálculo incluía tickets sem data. Entre os encerrados, são 49,3% | Número corrigido |
| Citei 99,4% de acerto em 36% dos tickets como evidência do sinal | Divisão aleatória, em um diagnóstico rápido. Em ordem de linhas, com um modelo mais simples, são cerca de 93% em 58% | Só valem números com separação em ordem de linhas |
