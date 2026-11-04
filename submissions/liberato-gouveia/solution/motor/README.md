# Motor do Lead Scorer

Calcula a priorização de todos os deals abertos e grava o resultado que a tela mostra.

## Como rodar

Requisitos: Python 3.10 ou mais recente, com `pandas` e `numpy`. Os testes usam também `pytest`.

```bash
cd solution/motor
pip install pandas numpy pytest
python gerar_scores.py          # lê ../data e config.json e grava saida/
python -m pytest -v tests/      # 12 testes automáticos
```

Saída:
- `saida/deals_priorizados.json`: tudo o que a tela usa (deals, listas, notas, explicações, curva de chance, equipe e validação)
- `saida/deals_priorizados.csv`: os mesmos deals, para abrir numa planilha

## O que ele faz

1. **Reconstrói o CRM na data de referência** (`visao_na_data`). Tudo o que aconteceu depois dessa data é apagado antes de qualquer cálculo, e é isso que impede o vazamento de futuro.
2. **Calcula o limite de ciclo**, que é o maior ciclo entre os deals já fechados (hoje, 138 dias), e a **curva de chance pela idade**.
3. **Classifica cada deal aberto** em uma das 4 listas: Foco, Requalificar ou encerrar, Iniciar contato e Automatizar.
4. **Calcula a nota e escreve, em português, a ação e o "porquê"** de cada deal.
5. **Refaz o teste de volta no tempo** (30/09 → 31/12/2017) para conferir que a lógica continua funcionando.

As regras estão em `docs/ficha-da-logica.md`. Os limites ficam em `config.json`, e o código não tem nenhum valor nem nome de produto escrito diretamente.

## Testes automáticos (`tests/test_motor.py`)

| Teste | O que garante |
|---|---|
| Todo deal aberto recebe exatamente uma lista | Os 2.089 deals abertos estão classificados, sem repetição |
| Todo deal tem ação, "porquê" e texto da nota | Nenhuma explicação vazia ou com "nan" |
| Aviso de empresa nas 4 listas | Deal sem empresa sempre mostra o aviso |
| Regras das 4 listas | Idade, preço e ação de cada lista seguem a ficha aprovada |
| Nota só no Foco e na ordem do valor esperado | A nota vai de 0 a 100 e respeita a ordem |
| Valor esperado = chance × preço | A conta mostrada é a conta feita |
| Números batem com a ficha aprovada | 236 / 1.291 / 500 / 62 deals; 350 "ligar" e 941 "encerrar"; limite de 138 dias |
| Volta no tempo reproduz a Fase 2 | Top 20% captura entre 66% e 70% da receita |
| **Sem vazamento de futuro** | Embaralhar tudo o que aconteceu depois de 30/09 não muda a priorização de 30/09 |
| Configuração muda o resultado | Os limites vêm do `config.json`, não do código |
| Nenhum nome de produto no código | Nomes próprios ficam na configuração |
| Saída válida para a tela | O JSON abre e a equipe completa (35 vendedores) está nele |

O teste de vazamento foi conferido com uma sabotagem: numa cópia do motor, a linha que apaga o futuro foi desligada, e o teste reprovou (`process-log/analises/resultados/fase3a_testes.txt`).
