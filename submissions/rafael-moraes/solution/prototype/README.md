# Protótipo — Triagem de suporte com IA

**Para usar:** abra `index.html` no navegador. Não precisa instalar nada nem de internet (só as fontes vêm do Google Fonts; sem elas, usa a fonte do sistema).

## Três abas
- **Triagem (atendente):** fila com prioridade por cor, rótulo de quem age, tag de atraso e filtros; teste com qualquer texto em português ou inglês.
- **Limiar e ROI (diretor):** controle do limiar de confiança e premissas editáveis; números calculados sobre 9.568 previsões reais de teste.
- **Saúde dos dados (gestão):** verificação de uma exportação de tickets; aceita outro CSV, lido só no navegador.

Botão PT | EN no canto superior.

## Estrutura
| Arquivo | Papel |
|---|---|
| `src/engine.js` | Classificador (TF-IDF + regressão logística) e regras de quem age e prioridade (cada regra cita a decisão que a originou) |
| `src/glossary_pt.js` | Camada de português (glossário PT → vocabulário do modelo) |
| `src/health.js` | Verificações de qualidade de dados |
| `src/template.html` | Interface |
| `model.json`, `eval.json`, `queue_sample.json`, `health_ds1.json` | Gerados pelas análises |
| `build.py` | Junta tudo em `index.html` |

## Reconstruir e testar
```bash
python ../analysis/05_exportar_modelo.py caminho/all_tickets_processed_improved_v3.csv . 20000
node -e 'const fs=require("fs");const {parseCSV,runChecks}=require("./src/health.js");fs.writeFileSync("health_ds1.json",JSON.stringify(runChecks(parseCSV(fs.readFileSync(process.argv[1],"utf8")))))' caminho/customer_support_tickets.csv
python build.py
node src/parity_test.js model.json parity_check.json   # Python × JavaScript: 200/200
node src/regression_test.js                             # 43 casos (testes do Rafael e da auditoria)
node src/pt_eval.js model.json ../analysis/pt_teste_original_en.json ../analysis/pt_teste_traduzido.json
node src/coverage_with_rules.js model.json textos_teste.json   # efeito das regras (textos de teste gerados por ../analysis/06)
node src/cross_ds1.js model.json caminho/customer_support_tickets.csv   # classificador nos textos do Dataset 1
```
Requer Node 18+ para os testes.
