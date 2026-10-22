# 02 · Da tese ao sistema

> **Data:** 22/10/2026
> **Ferramenta:** Claude Code (Opus 5.5)
> **Decisões desta etapa:** [D02 a D09](decisoes.md) · **Erros:** [erros-da-ia.md](erros-da-ia.md)

Depois de saber o que já existia ([01](01-o-que-ja-se-sabe.md)), faltava decidir onde construir. Esta etapa foi da minha experiência até um sistema rodando e medido.

---

## 1. A direção

A IA mostrou onde ninguém tinha ido: a resposta ao cliente. Concordei, e o motivo é meu. Trabalho com IA de atendimento e já vi de perto a IA prometendo o que não podia, e o cliente pedindo pra falar com uma pessoa. Contei por áudio os três problemas que vejo ([D02](decisoes.md#d02--construir-a-ia-de-atendimento-com-trava-no-que-ela-pode-dizer)), e a IA cruzou com casos públicos que confirmam cada um: Air Canada, Cursor, Gartner e Klarna.

O ponto fraco, a IA disse na hora: era experiência, não dado. A vaga pede dados pra validar hipóteses.

## 2. Transformar experiência em teste

Pra virar número, a gente montou um teste:
- **80 tickets difíceis**, escritos pela IA pra não serem fáceis: o advogado que exige confirmação por escrito, o cliente que diz que "o Carlos já aprovou", a bateria estufada, o "ignore as instruções anteriores".
- **O gabarito ficou comigo.** Respondi 33 por áudio. Desses, a IA tirou 8 regras e eu aprovei. As regras preencheram mais 37, e eu aprovei. Em 8 casos que as regras não cobriam, a IA sugeriu e eu decidi.
- **No gabarito, cada resposta diz de onde veio:** minha, regra minha aplicada pela IA, ou sugestão da IA aprovada por mim.

Depois comparei meu gabarito com o que a IA tinha pensado em cada armadilha. Bateram 65 de 80. Das 15 diferenças saíram as regras R9 (segurança), R10 (urgência) e R11 (apurar responsabilidade). Uma delas foi um erro meu: a bateria estufada.

**O resultado dessa parte:**
- a [política](../solution/05-politica.md), com 11 regras
- a [base de processos](../solution/06-base-de-processos.md), com 26 processos ligados à lei do consumidor

O princípio que saiu disso: **processo escrito vem antes da IA.**

## 3. A tela

Sou muito visual, preciso ver. A primeira versão, editorial, ficou horrível. A segunda acertou o visual. A estrutura de conversas veio do inbox do sistema de gestão que eu construí. Resultado: [`solution/interface/`](../solution/interface/), com Fila, Conversas e Painel.

## 4. O motor

O motor é Python puro, sem chave de API ([`solution/motor/`](../solution/motor/)):
- **um leitor** que procura sinais no texto
- **um decisor** que aplica as regras na ordem da política
- **um redator** que monta o resumo e o rascunho só com frases que a base permite
- **uma trava** que barra promessa de prazo, aprovação, garantia, desconto, culpa e "pode continuar usando"

## 5. A medição que importa

| Teste | Resultado |
|---|---|
| 80 tickets usados pra escrever as regras | 80 de 80 |
| 30 tickets novos, com outras palavras (teste cego) | **16 de 30, 7 erros perigosos** |
| Os mesmos 30, depois de aplicar "na dúvida, pessoa" | **21 de 30, 1 erro perigoso** (já não é cego) |
| Trava, 24 frases | 24 de 24 |

O 80 de 80 não prova nada, e a IA avisou antes de eu me empolgar. Os 30 novos mostraram a verdade: **as regras e a trava aguentam, e a leitura do texto por palavra-chave não.** Isso mudou a proposta final. Um modelo lê o texto, as regras decidem e a trava confere ([proposta](../solution/04-proposta.md)).

## 6. A conta

O diretor pediu quanto se desperdiça. O dado não mede tempo, então a conta virou fórmula, com cada premissa na mesa ([diagnóstico](../solution/03-diagnostico.md)): de 1.932 a 5.094 horas por ano, ou 1,1 a 2,9 pessoas. Isso só vale depois do modo sombra.

---

## Quem fez o quê nesta etapa

| Parte | Eu | Claude Code |
|---|---|---|
| **Direção** | Escolhi a resposta ao cliente. Trouxe, por áudio, os três problemas que vejo na prática | Apontou a resposta como o lugar onde ninguém foi. Achou os casos públicos que confirmam a tese (Air Canada, Cursor, Gartner, Klarna) e disse que, sem dado, era só experiência |
| **Teste** | Respondi 33 tickets. Aprovei as regras uma por uma. Decidi os 8 casos que elas não cobriam. Percebi que os tickets fugiam do Dataset 1 | Escreveu os 80 tickets, as armadilhas, a planilha e a página do gabarito. Tirou as regras das minhas respostas. Comparou meu gabarito com as armadilhas |
| **Política e processos** | Defini o princípio: a IA nunca determina, processo vem antes, e a lei não se contraria. Corrigi o T04. Resolvi os conflitos com a base | Escreveu as 11 regras e os 26 processos, ligou cada um ao CDC e marcou o que precisa de validação jurídica |
| **Tela** | Defini a direção (neutra, sem barra lateral, sem emoji, sem fonte padrão). Reprovei a primeira versão. Trouxe a estrutura do inbox que eu construí | Construiu as três versões e testou cada uma no navegador |
| **Motor** | Aprovei o plano. Recusei dar o gabarito caso a caso dos 30 novos, porque a política já estava escrita | Escreveu o leitor, o decisor, o redator, a trava e os testes. Avisou que o 80 de 80 não provava nada e propôs os 30 tickets novos |
| **Conta e documentos** | Pedi a conta, o fluxo escrito e a ordem de leitura. Revisei | Escreveu a fórmula, os documentos e este registro |

## Sobre o tempo

Passei das 4 a 6 horas sugeridas. A maior parte foi em três lugares:
- montar o gabarito
- refazer a tela duas vezes
- descobrir que o primeiro resultado do motor era bom demais pra ser verdade

Os três mudaram o resultado final. Não incluí horas que não mudaram nada.
