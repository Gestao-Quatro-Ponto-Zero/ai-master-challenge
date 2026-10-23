# ADR 0007: `deals.json` versionado, com checksum

**Status:** aceita

## Contexto

O vendedor precisa ver a fila calculada sobre os dados reais do desafio, e quem avalia precisa conseguir rodar seguindo as instruções. As 4 tabelas do CRM vêm do Kaggle (licença CC0); baixá-las no setup dependeria de acesso ao Kaggle na máquina de quem avalia. Juntar as tabelas pede pandas, e o avaliador pode não ter Python. Também é preciso saber que o arquivo calculado é o publicado.

## Decisão

- `data/preparar_dados.py` junta as 4 tabelas, normaliza os nomes que não casam (GTXPro → GTX Pro; erro de digitação no setor `technology`), calcula idade e duração, marca as lacunas e grava `data/deals.json` com `formato: 2`: os negócios e o time de vendas inteiro (os 35 de `sales_teams.csv`).
- No mesmo passo grava `data/deals.json.sha256`, no formato do `sha256sum`.
- Os dois arquivos ficam **versionados** no repositório (5.404.118 bytes, cerca de 5,4 MB).
- A API confere o SHA-256 e o schema antes de subir (`apps/api/src/carregador.ts`); o modo local da web confere de novo no navegador. Dado que não confere: a API não sobe (código 1); o modo local recusa.

## Consequências

- `npm install && npm start` funciona numa cópia limpa, sem Kaggle e sem Python.
- Arquivo adulterado ou truncado é recusado: teste "dado adulterado não carrega" em `apps/api/test/integracao.test.ts` e "recusa dado com checksum que não bate" em `apps/web/src/infra/clienteLocal.test.ts`.
- O resultado é reproduzível: regenerado a partir do CSV, deu o mesmo SHA-256 do arquivo versionado (`cd205caa…`). O banco compartilhado guarda esse SHA-256 em `lead_scorer.metadados`, e a API só usa os negócios do banco se ele bater ([ADR 0009](0009-banco-com-papel-restrito.md)).
- A junção tem 10 testes contra o CSV (`data/test_preparar_dados.py`), que rodam em `npm test` quando o uv e o CSV estão disponíveis.
- O formato versionado permite mudar o arquivo no futuro: o loader recusa formato diferente de 1 com uma mensagem clara.
- Cerca de 5,4 MB a mais no repositório.

## Alternativas consideradas

- **Baixar do Kaggle no setup:** depende de acesso ao Kaggle (e de credencial, se feito por API) na máquina de quem avalia; um passo a mais que pode falhar.
- **Gerar no `npm install`:** exige Python com pandas na máquina de quem avalia.
- **Ler os CSV direto no Node:** duplicaria a junção (que já tem testes em Python) e a normalização.
