# Auditoria do Dataset 2 - IT Service Ticket Classification Dataset

## Objetivo

Auditar o dataset usado para sustentar a parte de IA/classificacao da solucao.

Esse dataset nao sera usado para diagnosticar a operacao do Dataset 1. Ele sera usado para demonstrar que uma triagem automatizada de tickets e tecnicamente viavel.

Arquivo auditado:

```text
C:\Users\Jufer\Downloads\datasets g4\all_tickets_processed_improved_v3.csv
```

---

## Estrutura geral

| Item | Valor |
|---|---:|
| Linhas | 47.837 |
| Colunas | 2 |
| Tamanho aproximado | 13,89 MB |
| Linhas completamente duplicadas | 0 |
| Documentos duplicados | 0 |
| Campos nulos | 0 |

Conclusao inicial:

> O Dataset 2 e estruturalmente mais limpo que o Dataset 1. Ele tem textos e rotulos preenchidos para todos os registros.

---

## Colunas

| Coluna | Tipo | Nulos | Valores unicos | Uso |
|---|---:|---:|---:|---|
| Document | texto | 0 | 47.837 | Texto do ticket para treino/classificacao |
| Topic_group | texto | 0 | 8 | Categoria alvo do classificador |

---

## Distribuicao das categorias

| Categoria | Tickets | Percentual |
|---|---:|---:|
| Hardware | 13.617 | 28,47% |
| HR Support | 10.915 | 22,82% |
| Access | 7.125 | 14,89% |
| Miscellaneous | 7.060 | 14,76% |
| Storage | 2.777 | 5,81% |
| Purchase | 2.464 | 5,15% |
| Internal Project | 2.119 | 4,43% |
| Administrative rights | 1.760 | 3,68% |

Interpretacao:

- O dataset e grande o suficiente para treinar e validar um classificador.
- As classes sao desbalanceadas.
- `Hardware` e `HR Support` representam mais de 50% da base.
- `Administrative rights`, `Internal Project`, `Purchase` e `Storage` tem menor representatividade.

Implicacao:

> Nao devemos avaliar o modelo apenas por accuracy. Precisamos acompanhar macro F1 e desempenho por categoria, para nao esconder baixa performance nas classes menores.

---

## Qualidade dos textos

| Metrica | Valor |
|---|---:|
| Textos vazios | 0 |
| Tamanho medio | 291,9 caracteres |
| Mediana | 175 caracteres |
| P95 | 926 caracteres |
| Maximo | 7.015 caracteres |
| Media aproximada de palavras | 43,6 |
| Mediana aproximada de palavras | 26 |
| Textos com ate 3 palavras | 49 |
| Textos com ate 5 palavras | 287 |

Conclusao:

> A maioria dos textos tem tamanho suficiente para classificacao. Existe uma pequena fracao de textos muito curtos, mas isso nao compromete a utilidade geral do dataset.

---

## Exemplos de categorias

### Hardware

```text
connection with icon icon dear please setup icon per icon engineers please let other details needed thanks lead
```

### Access

```text
work experience user work experience user hi work experience student coming next his name much appreciate him duration thank
```

### Storage

```text
mailbox almost full mailbox almost hi mailbox almost kind thanks regards senior infrastructure engineer
```

### Purchase

```text
system hello movement has left available device please kind device denmark copenhagen...
```

### Administrative rights

```text
notification wireless devices upgrade cr medium wireless devices upgrade...
```

Observacao:

Os textos parecem pre-processados: pontuacao removida, caixa normalizada e algumas frases truncadas/ruidosas. Isso favorece modelos classicos de NLP, como TF-IDF, mas reduz interpretabilidade humana direta em alguns casos.

---

## Pontos fortes

- Sem nulos.
- Sem duplicados.
- Base grande.
- Rotulos prontos.
- Categorias suficientes para demonstrar roteamento.
- Bom dataset para treinar classificador local, sem depender de API externa.

---

## Pontos de atencao

- Classes desbalanceadas.
- Textos ja parecem pre-processados, entao nao representam exatamente mensagens naturais de clientes.
- E um dataset de tickets internos de TI, enquanto o Dataset 1 parece suporte ao cliente/produto.
- Nao ha chave para juntar os dois datasets linha a linha.

---

## Como usar na solucao

Uso recomendado:

1. Treinar um classificador de categoria de tickets.
2. Medir accuracy, macro F1 e desempenho por classe.
3. Usar o modelo para demonstrar triagem automatizada.
4. Aplicar o classificador nos textos do Dataset 1 como simulacao de roteamento.
5. Usar thresholds de confianca para decidir:
   - auto-rotear;
   - enviar para revisao rapida;
   - manter com triagem humana.

Uso nao recomendado:

- Nao tratar as categorias como a taxonomia real da operacao do Dataset 1.
- Nao afirmar que os dois datasets pertencem a mesma empresa.
- Nao usar apenas accuracy como prova de qualidade.
- Nao automatizar todos os tickets com base no modelo.

---

## Parecer de confiabilidade

| Criterio | Avaliacao | Comentario |
|---|---|---|
| Integridade estrutural | Alta | Sem nulos e sem duplicados |
| Volume para treino | Alta | 47.837 registros |
| Balanceamento | Medio | Algumas classes pequenas |
| Qualidade textual | Media | Textos pre-processados e ruidosos |
| Utilidade para classificador | Alta | Bom para demonstrar NLP local |
| Aderencia ao Dataset 1 | Media/baixa | Contextos diferentes |

Parecer final:

> O Dataset 2 e confiavel para treinar e validar um classificador de tickets, desde que a avaliacao considere desbalanceamento e que a entrega deixe claro que ele serve como base complementar para IA, nao como extensao direta do Dataset 1.

---

## Implicacoes para o produto

Com base na auditoria, o sistema deve:

1. Usar o Dataset 2 para treinar o motor de classificacao.
2. Mostrar confianca da IA sempre que classificar um ticket.
3. Ter uma camada de regras para evitar automacao indevida.
4. Medir macro F1 e desempenho por categoria.
5. Explicar que a classificacao e uma demonstracao tecnica, nao uma taxonomia definitiva da operacao.
