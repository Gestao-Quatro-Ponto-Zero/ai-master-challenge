# Decisões

Cada decisão importante do projeto, com o que a IA sugeriu, o que eu decidi e por quê.

---

## D01 · Partir do que já foi descoberto, não refazer

**Data:** 22/10/2026 · **Etapa:** leitura dos dados

**Contexto.** Abri os dois datasets no Kaggle. No primeiro, vi que todas as colunas se dividem em partes quase iguais. Tipo de ticket, canal, prioridade, até gênero do cliente com "outro" em 32%. Numa operação real isso não acontece. É dado sorteado. Quando fui conferir, outras entregas já tinham chegado na mesma conclusão.

**O que a IA sugeriu.** Seguir o roteiro clássico: eu formar minha leitura dos dados do zero, etapa por etapa, e auditar o dataset.

**O que eu decidi.** Não refazer o que já foi descoberto. Se alguém já construiu o carro, eu não preciso construir outro do zero. Eu preciso melhorar o carro. Então:

1. Levantar tudo que as entregas públicas já descobriram, com o porquê, em tabela, com os dados. Quero ver com os meus olhos.
2. Dar o crédito de cada achado pro PR que encontrou.
3. Gastar meu tempo na parte que ninguém resolveu.

A IA completou com uma sugestão que eu aceitei: conferir cada achado nos dados com script próprio, em vez de copiar o número de quem escreveu.

**Por quê.** O desafio tem 4 a 6 horas. Gastar metade delas redescobrindo que o Dataset 1 é sintético é desperdício. O próprio desafio pede "inteligência no uso do tempo, não quantidade de horas". E é isso que eu faria numa empresa: antes de começar um projeto, ver o que o time já sabe.

---

## D02 · Construir a IA de atendimento, com trava no que ela pode dizer

**Data:** 22/10/2026 · **Etapa:** escolha da direção

**Contexto.** Quase todas as 48 entregas pararam na triagem: classificar o ticket e mandar pra fila certa.

**O que a IA sugeriu.** Atacar a resposta ao cliente, que ninguém mediu. A IA rascunha, um verificador barra o que ela não pode dizer, e o atendente aprova.

**O que eu decidi.** Concordei, pelos meus motivos. É onde a IA erra de verdade, e eu sei disso por dois lados. Trabalho com IA de atendimento e sei o que ela pode e o que não pode atender. E acompanhei de perto a operação de atendimento de um grande marketplace, com a IA respondendo errado e o cliente pedindo pra pular direto pra uma pessoa.

**Por quê.** IA no atendimento é uma boa ideia. Mas, mal implementada, causa mais problema do que resolve. Pra mim são três problemas:
1. **Processo mal documentado.** Não é problema de IA, vem antes. A IA prevê o próximo passo. Se o processo é confuso, ela prevê errado, ou não sabe e tenta contornar.
2. **A IA quer agradar.** Se puder prometer o reembolso e deixar a conta pro atendente depois, ela promete.
3. **O estado do cliente.** O cliente irritado não é só o reembolso, às vezes a vida dele tá uma merda. E ele não separa IA de pessoa. Se a IA irritou, ele dá zero pros dois.

## D03 · Sem chave de API

**Data:** 22/10/2026 · **Etapa:** escolha da direção

**O que eu decidi.** O sistema roda sem chave de API, em qualquer máquina. Hoje eu não tenho uma, e quem avalia também precisa conseguir rodar sem pagar nada.

**O que a IA sugeriu.** Que o sistema funcione 100% sem modelo, e que um modelo local fique como extra opcional.

**Consequência.** O leitor de texto ficou baseado em palavras. Foi exatamente aí que o teste com tickets novos mostrou a fraqueza (D09).

## D04 · A IA nunca determina

**Data:** 22/10/2026 · **Etapa:** política

**O que eu decidi.** A IA não toma decisão que comprometa a empresa. Ela informa, qualifica, resume e encaminha. Ela só fecha um caso quando o critério é objetivo e está escrito. No caso ambíguo, ela monta um resumo e a pessoa decide. Exemplo: "Paulo Vinicius comprou um boné, não gostou, abriu, usou uma vez, comprou há 3 dias". Com isso o atendente chega com a resposta mastigada.

**Como virou regra.** Respondi 33 tickets do teste. A IA tirou das minhas respostas 8 regras, e eu aprovei uma por uma. Depois vieram mais 3 (D07). Estão em [`solution/05-politica.md`](../solution/05-politica.md).

## D05 · Processo escrito vem antes da IA, e a lei não se contraria

**Data:** 22/10/2026 · **Etapa:** base de processos

**O que eu decidi.** A IA só responde ou resolve sozinha quando existe um processo documentado que cobre o caso. Sem processo, vai pra pessoa. Os processos saem das minhas respostas e da lei do consumidor. Se a compra tem direito de 7 dias, é isso. Não vou contrariar a lei.

**O que a IA fez.** Escreveu a base com 26 processos, ligando cada um ao artigo do CDC ou à minha regra, e marcou o que precisa de validação jurídica. Achou 3 casos em que meu gabarito batia de frente com a base (T01, B01, R12). Eu decidi: vale a base.

## D06 · Os tickets de teste ficam presos à estrutura do Dataset 1

**Data:** 22/10/2026 · **Etapa:** teste

**Contexto.** A IA escreveu 80 tickets difíceis pra testar o sistema.

**O que eu percebi.** Perguntei se aquilo fazia sentido com os dados que a gente tinha. Não fazia. A IA tinha colocado geladeira, sofá, vestido e perfume, e um canal (WhatsApp) que não existe no Dataset 1.

**O que eu decidi.** Refazer os tickets usando só os tipos, assuntos, produtos e canais do Dataset 1. O script passou a conferir isso sozinho.

## D07 · Os erros que o teste mostrou viram regra

**Data:** 22/10/2026 · **Etapa:** comparação com as armadilhas

**Contexto.** Comparei meu gabarito com o que a IA pensou ao escrever cada ticket. Bateram 65 de 80.

**O que eu decidi.**
- **T04, bateria estufada com cheiro de queimado:** eu tinha posto "o robô responde". Errei. Virou a regra R9: risco físico vai pra pessoa na hora.
- **Urgência:** tudo que é urgente e não tem processo documentado vai pra pessoa (R10).
- **O tijolo (R01):** não é que o cliente não mereça o reembolso, ele merece. É que alguém precisa apurar quem causou, se foi o entregador ou o centro de distribuição. Virou a R11.

## D08 · Uma tela que o atendente entende, com o inbox que eu já uso

**Data:** 22/10/2026 · **Etapa:** interface

**Contexto.** Pedi uma identidade neutra, nada de coluna lateral grudada na esquerda, sem emoji e sem fonte padrão.

**O que aconteceu.** A primeira versão da IA foi editorial, com cara de jornal. Ficou horrível e confusa pra um atendente. Mandei refazer. A segunda ficou boa no visual, mas abria o ticket numa gaveta lateral. Mostrei o inbox do sistema de gestão que eu mesmo construí e pedi a mesma estrutura: quem está atendendo agora, lista com abas e a conversa ao lado. Copiei só o chat, com o visual da versão nova.

## D09 · Medir em tickets que o sistema nunca viu

**Data:** 22/10/2026 · **Etapa:** teste do motor

**Contexto.** O motor acertou 80 de 80, mas as regras foram escritas olhando esses mesmos tickets.

**O que a IA sugeriu.** Escrever 30 tickets novos, com outras palavras, e eu dar o gabarito às cegas.

**O que eu decidi.** Não dar o gabarito caso a caso. A política está escrita, então a resposta certa sai dela, e a IA aplica. O que interessa é o método, não a minha opinião sobre uma loja que não existe.

**Resultado.** 16 de 30 e 7 erros perigosos. As regras e a trava aguentaram. Quem quebrou foi a leitura do texto por palavra-chave.
