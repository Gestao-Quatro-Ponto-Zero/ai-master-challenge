# Mensagens do Rodrigo

Estas são as mensagens de quem conduziu o projeto, Rodrigo Costa, copiadas da conversa com a IA, na ordem em que foram enviadas e com a grafia original. As respostas da IA não estão aqui; estão resumidas na narrativa (`README.md` desta pasta). Depois de cada mensagem, uma linha diz o que ela mudou no projeto.

---

### 13 nov

> estou participando de um processo seletivo, de uma olhada aqui https://github.com/rodrigopiffer/ai-master-challenge

O que isso mudou: a IA leu o repositório do desafio antes de propor qualquer coisa.

---

### 13 nov

> me explique cada desafio

O que isso mudou: a IA explicou cada desafio do repositório; a escolha veio depois.

---

### 13 nov

> 003 Lead Scorer

O que isso mudou: definiu o desafio da entrega.

---

### 13 nov

> Vamos pensar no projeto aqui
> quero passar na vaga, precisamos fazer algo surreal, algo que faça contratarem....

O que isso mudou: abriu a conversa de produto antes de qualquer código.

---

### 13 nov

> Esquece o que ja foi feito, vamos começar do zero aqui, apaguei tudo da pasta ja

O que isso mudou: a primeira tentativa (um app local e uma análise, feitos no mesmo dia em outra conversa) foi descartada; tudo nesta entrega foi feito a partir daqui.

---

### 13 nov, em resposta às três perguntas da IA sobre o uso de CRM

> 1. Depende do vendedor... isso de abrir na segunda feira é relativo.. Tem alguns que nao tao nem ai pra nada, depende 100% do cliente cobrar e chamar.. e outros que sao hunter, ficam em cima etc.. Esses vao olhar o sistema para saber qual focar
> 2. Sim, muitos vendedores abandonam por esquecimento, outros deixam em aberto para nao marcar que perdeu e contabilizar algo negativo... Esfriou é menos pior que Perdeu... tem varias formas de mascarar e burlar
> 3. Não quero algo que faça ser dificil de rodar, eu sei que é algo de desenvolvimento, uma vaga disso, mas queria que fosse facil e rapido de validar sabe?

O que isso mudou: virou a espinha do produto. A faixa "Sem desfecho" e a taxa de ganho que conta esses deals vêm do item 2; a mensagem pronta por vendedor para o gestor vem do item 1; a máquina do tempo, o acesso simulado e o app que roda com um comando, sem instalar nada, vêm do item 3.

---

### 13 nov

> quais infos temos dos clientes e oportunidades? quero saber antes de te responder essa analise

O que isso mudou: a primeira análise da IA não foi aceita de primeira; antes veio o inventário da base (`evidencias/analise/profile.py`), e a discussão passou a partir do que os dados de fato têm.

---

### 14 nov

> \* Pelo que vi na sua analise... olhando os que fecharam, o time to close é alto, levam meses para conquistar uma venda... Ai adicionando os sem desfecho quebra... Porem essa analise entendo que deveria ser por produto, por que varia... Vou dar um exemplo: Fechar um desenvolvimento de website e um de um software + app tem prazos diferentes, até por que tem valores diferentes
> \* Priorização seria por Score
> 1. Ficar atualizando a data de fechamento, registrar atividades na oportunidade etc..
> 2. Traria as duas opções.
> 3. Nao se preocupe com isso, só vamos fazendo.
> Temos que entregar tambem um score para os deals né...
> Nosso score tem que considerar o faturamento da empresa, pq se ela nao tem dinheiro pra comprar, nao vai fechar.
> Historico de compras
> Quero que a UX / UI seja incrivel, se quiser podemos desenhar no paper primeiro.. e ai exporta o arquivo e coloca na entrega junto para verem que teve estudo de UX/UI
> uma ideia: poderia ter um "Insights da Gabi" que seria a IA da G4...que poderia ter insight desse que falei de perda escondida e tal.. o que acha?
> uma das entregas quero que seja um doc que fale da minha contribuição, que foi essencial para o projeto e como contribui...

O que isso mudou: três hipóteses para testar (ciclo por produto, faturamento do cliente, histórico de compras). Os testes mostraram que nenhuma muda o resultado, e investigar o sinal entre os deals abertos revelou que o campo cliente desses deals não é confiável. Também definiu: priorização por score, um score por deal, as duas leituras do gestor (declarado e real), as formas de mascarar deal parado (por isso o score usa só a data de entrada), o estudo de UX no Paper, o painel "Insights da Gabi" e o documento sobre a contribuição dele.

---

### 14 nov

> Sim comece, quero um app que possamos subir no railway.. que tenha um login simulado, entre gestor / vendedor e possa escolhar qual quero ver
> pode iniciar
> quero a identidade visual, similar à do G4OS [...]
> pode até ser como se fosse um modulo de analise de vendas do G4OS

O que isso mudou: definiu a forma da entrega (app web com acesso simulado de vendedor e gestor, preparado para o Railway) e a identidade visual. A IA desenhou as 5 primeiras telas no Paper e as submeteu a três revisores de usabilidade e a uma auditoria contra as regras do desafio.

---

### 14 nov

> \* seria bom ter uma tela de configurações que seria de onde vem os dados para o modulo de vendas funcionar. Uma lista de CRMs para integração, deixa com um alerta escrito "Tela apenas para referência, os dados vem da base fornecida para o desafio e não de alguma integração."
> \* Revisa no repositoria os termos de entrega, o que consideram ou nao etc.. e veja se nosso design atende..
> \* Acho quer seria legal ter uma visao kamban sabe? com as fases e as oportunidades nele..
> \* seria bom ter filtro de "Com Cliente" e "Sem Cliente"
> \* uma tela de clientes que abra um drawer com uma aba de dados do cliente e outra com oportunidades em aberto e outra com oportunidade fechadas.
> \* Seria bom em Transparencia ter a explicação que pedem de como chegamos a isso, o que cada um contribuiu etc.. explicar ideias etc..
> \* pode fazer a tela de transparencia e qualidade dos dados.

O que isso mudou: o estudo de UX passou de 5 para 12 pranchas (fontes de dados com o alerta dele, kanban, filtro com e sem cliente, clientes com painel de três abas, Transparência, qualidade dos dados). No redesenho, a IA achou que "ter cliente" adianta quem vai fechar numa data simulada, e o campo saiu do score e da prova; e a conferência independente da prova trocou a manchete de "+42%" para "+22%".

---

### 14 nov

> Pode iniciar o desenvolvimento

O que isso mudou: começou a construção do motor e da API por um fluxo de 13 agentes (núcleo, módulos, integração, quatro revisores independentes e correção dos achados), seguida da interface a partir das pranchas do Paper.

---

### 14 nov

> terminou?

O que isso mudou: nada no produto. A IA informou o andamento e seguiu até o teste final e a revisão da entrega.

---

### 15 nov

> \* precisa ajustar essa tabela em Meu time, ta cortando as laterais (print anexo)
> \* no menu lateral, deixaria os icones que sao funcionais com um pouco mais de destaque para que nao se confunda com os que nao funcionam
> \* o icone de configuração quero q seja o de rodinha, igula aqui o print .. ajusta o paper tambem
> \* no pipeline n funciona o drag n drop

O que isso mudou: a tabela de Meu time ganhou respiro nas laterais (o fundo da linha em destaque encostava no avatar e na taxa); os ícones do trilho que levam a algum lugar ficaram com cor cheia e contorno de botão, e os decorativos mais apagados; o ícone de Configurações virou engrenagem no app e nas pranchas do Paper (reexportadas); e o Pipeline passou a aceitar arrastar deal aberto para outra fase, com o movimento salvo só no navegador e botão de desfazer.
