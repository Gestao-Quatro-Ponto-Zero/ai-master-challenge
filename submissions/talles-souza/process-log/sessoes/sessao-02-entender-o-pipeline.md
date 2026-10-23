# Sessão 02 — Entender o pipeline antes de definir o score (E2)

**Data:** 2026-10-22 · **Ferramenta:** Claude Code (Claude Opus 5.5) · **Etapa:** E2

## Problema

A Head de RevOps quer que o vendedor abra a ferramenta na segunda de manhã e saiba onde focar. Antes de desenhar qualquer score, a pergunta é: **o que nestes dados separa um deal que vai fechar de um que não vai?** Se a resposta for "nada", um score de pesos bonitos seria teatro.

**Critério de aceite da E2:** cada componente do score tem um número medido que o justifica, e o que não tem sinal fica fora (ou entra declarado como contexto, não como preditor).

## O que foi medido

Dois scripts, só leitura, com a saída bruta guardada:
- `scripts/explorar_pipeline.py` → `evidencias/explorar-pipeline.txt`: lacunas, ligações entre tabelas, win rate por atributo, tempo, valor, carga.
- `scripts/validar_sinal.py` → `evidencias/validar-sinal.txt`: os atributos predizem **fora da amostra**? (treino nos fechados até 30/09/2017, teste nos 1.985 fechados do 4º trimestre, taxas encolhidas para a média, AUC).

## O que os dados dizem

1. **Nenhum atributo do deal prediz ganho fora da amostra.** AUC no 4º trimestre: vendedor 0,522; conta 0,488; produto 0,500; setor 0,486; os quatro juntos 0,498. Moeda é 0,500. Dentro da amostra, os vendedores vão de 55% a 70% de win rate, e a diferença sobrevive controlando por produto (−8 a +9 p.p.), mas não se repete no trimestre seguinte. Produto, série, manager, escritório, setor e porte ficam todos a ±3 p.p. da média de 63,2%.
2. **Os abertos são, na maioria, deals mortos que ninguém fechou.** O ganho mais longo do histórico levou 138 dias; 95% dos ganhos fecham em até 116. **1.291 dos 1.589 deals em Engaging (81%) estão abertos há mais tempo que qualquer deal já fechado**, com idade contada até 31/12/2017, o último fechamento do dataset (não até hoje). Só ~298 estão dentro da janela em que deals de fato fecham.
3. **Perder é rápido; ganhar, não.** Mediana de 14 dias para os perdidos contra 57 para os ganhos. Entre os fechados, deals de 0–7 dias ganham 53,5%; de 15–30 dias, 72,8%. Isso só descreve deals que já fecharam: para um deal aberto, o tempo útil é a idade comparada à janela dos ganhos, não "quanto mais tempo, melhor".
4. **Valor é o preço de tabela.** A mediana do `close_value` dos ganhos é 1,00× o preço do produto em todos os 7 produtos. O valor esperado de um aberto é o preço do produto dele, e a faixa vai de US$ 55 (MG Special) a US$ 26.768 (GTK 500): 487 vezes.
5. **Lacunas e sujeira, declaradas:**
   - 1.088 dos 1.589 Engaging e 337 dos 500 Prospecting não têm conta.
   - Os 500 Prospecting não têm `engage_date`, então não têm idade.
   - O produto "GTXPro" do pipeline não existe no cadastro ("GTX Pro"); foi normalizado.
   - O setor "technolgy" tem erro de digitação, mantido.
   - 5 dos 35 vendedores não têm nenhum deal.
   - O 1º trimestre de 2017 tem 82% de win rate contra ~61% depois, provável artefato de recorte (o dataset começa em out/2016), por isso fica fora como sinal.
   - Carga de 31 a 194 deals abertos por vendedor.

## Onde desconfiei e conferi

- **A primeira leitura (vendedores de 55% a 70%) parecia sinal.** Só o teste fora da amostra mostrou que não é. Se o score usasse a taxa do vendedor como peso, ele ordenaria por ruído com cara de ciência.
- **A "idade no pipeline" a partir de hoje (2026) daria 9 anos para todo mundo.** A referência é o último fechamento do dataset, 31/12/2017.
- **AUC da duração (0,562)** aparece só como referência: ela só existe depois que o deal fecha, então não pode entrar no score de um aberto.

## Decisão que vai para o Talles

Com AUC de 0,50, prometer "probabilidade de fechar" seria inventar. O que os dados sustentam para a segunda de manhã:
- **Vivo ou morto:** a idade do deal contra a janela em que ganhos fecham (até ~116–138 dias). Quem está dentro é prioridade. Quem está muito fora vai para uma lista de "requalificar ou encerrar", que limpa o pipeline e o forecast.
- **Quanto vale:** o preço do produto, porque um GTK 500 vivo vale 487 MG Special.
- **Explicação em frase:** cada deal diz por que está onde está ("aberto há 40 dias, dentro da janela em que 9 de cada 10 ganhos fecham; produto de US$ 5.482").
- **O que não entra como preditor:** vendedor, conta, setor, porte e produto (exceto como valor). Aparecem como contexto e filtro, com o aviso de que não preveem resultado neste histórico.

## Como reproduzir

```bash
uv run --no-project --python 3.12 --with pandas==3.1.0 python -X utf8 process-log/scripts/explorar_pipeline.py <pasta crm-sales-predictive-analytics>
uv run --no-project --python 3.12 --with pandas==3.1.0 python -X utf8 process-log/scripts/validar_sinal.py <pasta crm-sales-predictive-analytics>
```

## Próximo passo

E3: com a tese aprovada, construir a ferramenta (fila do vendedor + lista de requalificação + filtro por vendedor, manager e escritório), com a explicação de cada deal.
