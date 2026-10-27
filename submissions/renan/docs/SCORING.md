# Lógica de scoring

> Todo número aqui é reproduzível com `npm run analyze`, que também gera [FINDINGS.md](./FINDINGS.md) (tabelas completas).

## 1. A conclusão em uma frase

**Neste CRM, ninguém consegue prever quais deals vão ser ganhos e quais vão ser perdidos — nem um modelo, nem o "feeling" do vendedor. O que dá para saber é quanto vale cada deal e quais estão mortos.** A ferramenta foi desenhada a partir dessa evidência, e não de pesos inventados.

## 2. O que a exploração mostrou

### H1 — As features "óbvias" não separam ganho de perda · **confirmada**

| Fator | Taxa de vitória bruta (mín–máx) | Após descontar o ruído estatístico |
|---|---|---|
| Produto (7) | 60,0% – 64,8% | 63,2% (sem diferença) |
| Setor (10) | 61,2% – 64,8% | 63,2% (sem diferença) |
| Porte da conta (3) | 62,5% – 64,2% | 63,2% (sem diferença) |
| Escritório (3) / Manager (6) | 62,6% – 63,9% / 62,1% – 64,4% | — |

Com milhares de deals por grupo, diferenças de 3 a 4 pontos estão dentro do que o acaso produz.

### H3 — O vendedor é um sinal relevante · **rejeitada**

A taxa bruta varia de 55% (Lajuana Vencill) a 70% (Hayden Neloms). Parece um sinal forte, e é exatamente o que um ranking de vendedores mostraria. Três testes dizem que é ruído:

- **Qui-quadrado:** 33,3 com 29 graus de liberdade, que é o esperado se todos tivessem a mesma taxa real.
- **Estabilidade:** a correlação entre a taxa do vendedor no 1º e no 2º semestre é de apenas 0,32, uma relação fraca. Para vendedor × produto, é de −0,08: quem "vai bem" num produto num semestre não repete no outro.
- **Bayes empírico:** depois de descontar o ruído, a faixa encolhe para 62,1% – 63,9%.

**Implicação de produto:** não exibimos um ranking de "melhores vendedores" nem sugerimos realocar deals por taxa de vitória. Isso puniria pessoas por sorte.

### H2 — O tempo no pipeline é o sinal mais forte · **confirmada, com nuance**

- **Perdas acontecem cedo:** a mediana do ciclo dos perdidos é de 14 dias; a dos ganhos, 57. Um deal que sobrevive às 2 primeiras semanas passa de 63% para ~69% de chance, e de 120 dias em diante, para ~76%.
- **Existe um limite duro:** nenhum dos 6.711 deals fechados levou mais de **138 dias**. Na data de referência, **81% dos deals em Engaging (1.291) já passaram disso**. Eles somam **64% do valor de tabela do pipeline aberto** (US$ 3,2 mi de US$ 5,0 mi).

### H4 — Problemas de qualidade dos dados · **confirmada**

| Problema | Afetados | Tratamento |
|---|---|---|
| "GTXPro" no pipeline vs. "GTX Pro" no catálogo | 1.480 deals | Unificado; sem isso, 17% dos deals ficariam sem preço |
| Setor "technolgy" | 12 contas | Corrigido |
| **Deals abertos sem conta** | **1.425 de 2.089 (68%)** | Conta vira fator opcional; a UI pede o cadastro |
| Prospecting sem data de engajamento | 500 (todos) | Sem relógio; usa a taxa geral |
| Vendedores sem nenhum deal | 5 | Fora dos rankings |

### Achado extra — fim de trimestre

Deals fechados no último mês do trimestre têm **80,7%** de vitória; nos outros meses, **52,3%**. Pode ser um padrão comercial real (vitórias puxadas para o fechamento do trimestre, perdas baixadas no início do seguinte) ou um artefato do dataset sintético. Como não sabemos em que mês um deal aberto vai fechar, esse efeito **não entra no score**: ele aparece como insight para o manager, com essa ressalva.

## 3. O score

```
Chance de fechar  = taxa geral 63,2%
                    → ajustada pelo tempo no pipeline (curva de sobrevivência)
                    → ajustada por vendedor, produto, setor e porte (Bayes empírico)
Valor esperado    = chance × preço de tabela do produto
Score (0–100)     = percentil do valor esperado entre os deals ativos
```

- **Pesos aprendidos, não inventados.** O Bayes empírico estima quanto da variação de cada fator é real. Hoje produto, setor e porte recebem peso zero, e o vendedor, quase zero. Se o CRM passar a ter sinal (por exemplo, com dados de atividades), os pesos sobem sozinhos.
- **Explicação que fecha a conta.** A chance é decomposta em pontos percentuais por fator, e os passos somam exatamente o resultado (há teste automatizado para isso).
- **Momento do deal**, com limites derivados do histórico:

| Momento | Regra | Próxima ação |
|---|---|---|
| Prospecção | sem data de engajamento | Agendar o primeiro contato |
| Início | até 14 dias (mediana das perdas) | Qualificar já: é quando metade das perdas acontece |
| Em andamento | de 15 a 88 dias | Avançar a proposta |
| Reta final | de 89 a 138 dias (p75 dos ganhos → maior ciclo) | Empurrar o fechamento |
| **Parado** | **mais de 138 dias** | **Revisar ou desqualificar.** Sai do ranking de foco e vai para a fila de revisão |

## 4. Backtest: o score funciona?

Simulamos a ferramenta em 3 datas passadas. Em cada uma, ela aprende só com o que tinha fechado até o corte e é avaliada nos deals que estavam abertos naquele dia (cerca de 900 a 970 por corte), cujo resultado hoje é conhecido.

| Estratégia | AUC da chance (jun / ago / set) | % da receita capturada no top 20% (jun / ago / set) |
|---|---|---|
| **Score (valor esperado)** | 0,505 / 0,557 / 0,500 | **50,7% / 50,7% / 46,9%** |
| Ordenar por preço do produto | — | 50,5% / 50,0% / 45,9% |
| Só tempo no pipeline | 0,504 / 0,557 / 0,500 | 20,2% / 20,7% / 16,9% |
| Taxa bruta do vendedor | 0,508 / 0,531 / 0,493 | 17,9% / 20,0% / 21,1% |
| Ordem aleatória | ≈ 0,50 | 18,5% / 19,0% / 19,8% |

Leitura honesta:

1. **A chance de fechar não discrimina** (AUC ≈ 0,5, igual a uma moeda). Nenhuma estratégia discrimina; a "taxa do vendedor", que é o que um score ingênuo usaria, também não.
2. **O que captura receita é o valor:** o top 20% pelo score traz cerca de metade da receita, contra ~19% do acaso. Isso é 2,5× mais receita por hora de trabalho.
3. **Contra "ordenar por preço", o ganho no backtest é pequeno** (+0,2 a +1,0 ponto), porque nos cortes testados não havia deals parados. **Hoje é diferente:** se o vendedor ordenasse o pipeline atual por preço, **47% do top 20% seriam deals parados** há mais de 138 dias. É aí que o score muda a decisão.

**Limitação:** a regra de "parado" não pode ser validada no backtest, porque nos cortes nenhum deal tinha passado do ciclo máximo conhecido. Ela se apoia no fato de que, em 6.711 deals fechados, nenhum levou mais de 138 dias.

## 5. Limitações

- Dataset sintético: os padrões (ou a ausência deles) podem não refletir um CRM real.
- Sem dados de atividade (e-mails, reuniões, próximos passos), que no mundo real costumam ser o sinal mais forte de fechamento. É a primeira coisa a adicionar.
- Deals abertos não têm valor negociado; usamos o preço de tabela. Nos ganhos, o valor fechado fica entre 87% e 112% da tabela (p10–p90).
- A curva de sobrevivência trata o histórico como estável no tempo.
