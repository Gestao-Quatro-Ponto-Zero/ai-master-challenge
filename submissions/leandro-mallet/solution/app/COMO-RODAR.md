# Foco da Semana: como rodar

Uma página web estática (HTML, CSS e JavaScript puro). Não tem build, não tem `npm install` e não tem dependência além de um navegador e de um servidor de arquivos.

## Rodar em 1 minuto

Pré-requisito: Python 3 (qualquer versão recente; só para servir os arquivos).

```bash
cd submissions/leandro-mallet/solution
python -m http.server 8000
```

Abra **http://localhost:8000/app/** no navegador.

Sem Python, qualquer servidor estático na pasta `solution/` funciona, por exemplo `npx serve .`.

> Abrir o `index.html` com dois cliques não funciona: o navegador bloqueia a leitura do arquivo de dados quando a página vem direto do disco. Nesse caso a própria tela explica o que fazer e deixa escolher o JSON manualmente.

## De onde vêm os dados

O app lê, nesta ordem:

1. `?dados=<caminho>` na URL, se informado (útil para testar outro arquivo);
2. `../data/scored/deals_scored.json`: o score oficial, gerado em `solution/scoring/`;
3. `sample/deals_scored.sample.json`: um exemplo com os deals abertos reais e um score provisório. Quando ele é usado, aparece uma faixa amarela no topo avisando.

Para regenerar o exemplo (a partir de `solution/`): `python app/sample/gerar_sample.py`.

## O que tem na tela

| Tela | Para quem | O que mostra |
|---|---|---|
| **Meu dia** | Vendedor | Escolhe o nome e vê os 5 deals para focar hoje, cada um com 2–3 motivos em frase simples; a lista "Requalificar ou desistir"; atalho para a lista completa. |
| **Visão do manager** | Manager | Pipeline do time (deals, valor esperado, % esfriando), deals esfriando que ainda valem salvar e um quadro por vendedor. Tocar num nome abre o dia daquele vendedor. |
| **Todos os deals** | Ambos | Tabela com busca, filtro por ação e ordenação por score, valor, dias ou vendedor. |

- **Filtros** de região, manager e vendedor no topo valem para todas as telas e ficam no link (dá para mandar `.../app/#dia?vendedor=Anna+Snelling` para a pessoa).
- **Explicação do score:** tocar em qualquer deal abre o detalhe com os motivos, os pontos de cada componente (chance de fechar, valor em jogo, tempo no pipeline, histórico da conta) e os dados do deal. A barra colorida ao lado de cada score mostra a mesma divisão em miniatura.
- O app lembra o último vendedor escolhido neste navegador.

## Formato esperado do arquivo

```json
{
  "reference_date": "2017-12-31",
  "generated_at": "2026-11-09T21:00:00+00:00",
  "component_weights": { "chance": 40, "valor": 25, "tempo": 20, "conta": 15 },
  "deals": [
    {
      "opportunity_id": "FZWU2I30",
      "sales_agent": "Zane Levy", "manager": "Summer Sewald", "regional_office": "West",
      "product": "GTX Plus Pro", "account": "The New York Inquirer", "sector": "medical",
      "deal_stage": "Engaging", "engage_date": "2017-12-10", "days_in_pipeline": 21,
      "expected_value": 3525,
      "score": 70,
      "components": { "chance": 26, "valor": 14, "tempo": 20, "conta": 10 },
      "reasons": ["frase simples 1", "frase simples 2"],
      "flags": ["esfriando", "sem_conta"],
      "action": "focar"
    }
  ]
}
```

- `component_weights` é opcional: quando existe, o detalhe mostra "26 de 40 pontos". Sem ele, o app detecta sozinho se os componentes somam o score (pontos) ou se cada um vai de 0 a 100.
- Componentes com outros nomes também aparecem (com o nome do campo e uma cor neutra).
- `action` aceita `focar`, `requalificar` e `desistir`. `flags` conhecidas: `esfriando`, `sem_conta`, `sem_data`; outras aparecem com o próprio texto.

## Como o "Meu dia" escolhe os deals

- **Seus 5 deals para hoje:** os 5 de maior score com ação `focar`. Se houver menos de 5, completa com os de maior score marcados para `requalificar`.
- **Requalificar:** ordenados por valor esperado (o que mais vale salvar primeiro).
- **Desistir:** ordenados por tempo aberto (os mais parados primeiro).

## Arquivos

```
app/
  index.html       estrutura da página
  styles.css       visual (claro e escuro, celular e computador)
  app.js           leitura do arquivo, filtros, telas e detalhe do deal
  sample/          arquivo de exemplo e o script que o gera
  COMO-RODAR.md    este arquivo
```

## Limitações

- Só leitura: o app não grava nada no CRM. Para atualizar, gere um novo `deals_scored.json`.
- Sem login: qualquer pessoa com o link vê o pipeline de todos. Em produção, cada vendedor veria só o próprio (e o manager, o time).
- A fonte é carregada do Google Fonts; sem internet, o navegador usa a fonte do sistema e tudo continua funcionando.
