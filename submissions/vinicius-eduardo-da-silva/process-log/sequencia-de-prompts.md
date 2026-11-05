# Sequência de prompts aprimorada

> **Escrita depois do trabalho.** Estes não são os prompts usados. Durante o projeto, os pedidos foram mais curtos e informais, e a conversa original não está incluída nesta entrega. O que aconteceu de fato está em [`PROCESS_LOG.md`](PROCESS_LOG.md) e no histórico de commits.

Cada etapa mostra o que aconteceu e como eu faria o pedido hoje, com o que aprendi. A versão em um único pedido está em [`prompt-consolidado.md`](prompt-consolidado.md).

## O que aprendi sobre pedir

1. **Definir o que é "pronto".** Um pedido sem critério de saída termina quando a IA acha que terminou.
2. **Pedir a tentativa de derrubar o resultado.** A pergunta "isso vai dar resultado?" foi a que mais mudou a entrega.
3. **Separar fato, hipótese e premissa.** Sem isso, um chute aparece com a mesma confiança de um dado.
4. **Dizer o que não sei.** Não conheço o negócio de vendas, então peço opções e explicação, e deixo claro o que precisa de validação.
5. **Reagir ao uso real.** Boa parte das melhorias veio de abrir a ferramenta e dizer o que estava ruim.

---

## 1. Escolher o desafio

**O que aconteceu:** enviei as regras e pedi ajuda com o desenvolvimento e os passos. O Claude leu os desafios e recomendou o 003, e eu aceitei.

**Como eu pediria hoje:**

```text
Leia os 4 desafios, as regras de submissão e os critérios de avaliação do repositório.
Recomende um desafio considerando:
- onde uma resposta só de IA seria mais fácil de superar;
- o que dá para provar com os dados, e não só afirmar;
- quantos candidatos já enviaram cada desafio.
Baixe uma amostra dos dados antes de recomendar. Se os dados não tiverem sinal, diga.
Termine com a recomendação, os riscos e a decisão que depende de mim.
```

## 2. Entender os dados antes de construir

**O que aconteceu:** o Claude auditou os dados por iniciativa própria e encontrou os deals acima de 138 dias e as contas em branco.

**Como eu pediria hoje:**

```text
Antes de propor qualquer solução, descubra onde estes dados enganam: nomes que não
batem, nulos por estágio, histórico cortado, campos que vazam o resultado e deals
abertos fora do padrão. Quero cada problema com números e o que ele muda na solução.
Não desenhe o score ainda.
```

## 3. Descobrir o que realmente prevê o resultado

**O que aconteceu:** o teste temporal mostrou que vendedor, produto e porte quase não preveem o fechamento, e o plano mudou.

**Como eu pediria hoje:**

```text
Teste quais sinais preveem o fechamento, com validação temporal e usando só o passado
de cada deal. Depois, simule segundas-feiras passadas: monte o top 10 de cada vendedor
com o que se sabia naquele dia e meça a receita dos 30 dias seguintes.
Defina o critério de escolha antes de ver o resultado. Um sinal só entra no score se
melhorar essa simulação. Prove com um teste que mudar o futuro não altera o aprendizado.
```

## 4. Tomar as decisões de produto

**O que aconteceu:** o Claude trouxe opções, e eu escolhi a fila separada, o teste do efeito de trimestre e o formato sem deploy.

**Como eu pediria hoje:**

```text
Liste as decisões de produto que dependem de mim. Para cada uma, traga as opções, o
impacto de cada uma para o vendedor e sua recomendação. Como não conheço o negócio de
vendas, explique em termos simples e indique o que deveria ser validado com alguém da área.
```

## 5. Construir e revisar

**O que aconteceu:** o Claude construiu a ferramenta, testou no navegador e encontrou erros, como uma chance de 14% que deveria estar perto de 0–2,6%.

**Como eu pediria hoje:**

```text
Construa uma página que abra com dois cliques, sem servidor. Para cada vendedor, ela
deve responder: o que faço na segunda, e por quê? Inclua quem não tem nenhum deal vivo.
Teste em um navegador real. Depois, olhe as telas e confira se cada número contradiz
algo que já descobrimos, porque os testes automáticos não pegam isso.
```

## 6. Ir além do enunciado

**O que aconteceu:** perguntei se estávamos atendendo ao enunciado e se dava para ir além. Escolhi a Máquina do tempo, o plano de piloto e a calculadora.

**Como eu pediria hoje:**

```text
Confira requisito por requisito se o enunciado está atendido. Depois, aponte as maiores
fraquezas da entrega do ponto de vista da Head de RevOps. Proponha só extras que resolvam
uma dessas fraquezas, com esforço estimado, e diga também o que você não faria e por quê.
```

## 7. Melhorar a experiência

**O que aconteceu:** ao usar a página, achei que estava simples demais. Depois, notei a data fixa e pedi mais detalhes para o vendedor ver valor no deal. Cada retorno virou uma melhoria.

**Como eu pediria hoje:**

```text
Usei a ferramenta como vendedor. O que senti: [o que estranhei, com a tela e o momento].
Quero que ela seja mais fácil de entender, de agir e de revisar. Redesenhe em torno das
ações do vendedor, não dos dados. O score não deve mudar.

Para cada deal, mostre o que ajuda a preparar a conversa, como o valor típico, o que a
conta já comprou e o histórico com ela. Use só o passado e deixe claro que é contexto.
```

## 8. Atacar o próprio resultado

**O que aconteceu:** perguntei se tudo funcionava e se teríamos resultado. A auditoria mostrou que o "+42%" vinha em boa parte de tirar os deals parados: contra um rival mais forte, o ganho era de +21%, e de +8% em out–nov.

**Como eu pediria hoje:**

```text
Tente derrubar o resultado principal. De onde vem o ganho? Qual é o rival mais forte que
alguém com bom senso usaria? O ganho depende de poucos deals ou de um período? Vale para
a maioria dos vendedores? Isso prova aumento de vendas ou só boa identificação? Calcule o
que um piloto real conseguiria detectar. Se a mensagem principal mudar, atualize tudo.
```

## 9. Preparar a entrega

**O que aconteceu:** organizamos os arquivos, conferimos tudo em um clone limpo e completamos a documentação.

**Como eu pediria hoje:**

```text
Faça o caminho de quem vai avaliar: clone limpo, siga o README e rode tudo. Confira os
números e links dos documentos e as regras do PR. Mostre o que falta e o que só eu posso
escrever. Não publique nada sem o meu ok.
```
