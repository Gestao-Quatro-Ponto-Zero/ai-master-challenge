# Onde a IA errou e como foi corrigido

> O documento que mais pesa numa avaliação de uso de IA, porque é o único que não se consegue
> escrever sem ter verificado de verdade. Cada item precisa dos quatro campos. `registrar.py --erro`
> acrescenta a estrutura automaticamente.
>
> Regra: **erro sem mecanismo que o pegou não entra aqui.** "A IA errou e eu corrigi" é afirmação.
> "A IA propôs X, o teste Y falhou com este valor, virou Z" é prova.

## Modelo de item

<!-- exemplo: apague esta linha ao preencher -->

## A chance de decidir chegava a 100% nas idades altas

- **O que a IA propôs:** calcular a chance de um deal decidir nos próximos 30 dias como "entre os deals do histórico com ciclo ≥ idade, a fração que fechou até idade + 30".
- **Como foi pego:** script próprio recalculando com os deals ainda abertos no denominador. A fórmula proposta dava 100% aos 120 dias; com os abertos em risco e a janela censurada, o real é 15,6%.
- **Teste que fixa:** `test_nao_ha_vies_de_sobrevivencia`, que exige menos de 5% nas duas faixas mais velhas.
- **O que ficou:** tábua de vida com censura explícita, e o número errado documentado como regra rejeitada.

<!-- exemplo: apague esta linha ao preencher -->

---

## Itens
