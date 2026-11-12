# Como usar a demo

**Endereço:** https://lead-scorer-diego.vercel.app

A demo é um site estático. Não tem login, não chama servidor e não depende de chave de API. Os dados são o CRM público do desafio (licença CC0), calculados em 01/01/2018, primeira semana do trimestre, porque o export termina em 31/12/2017. O topo da tela mostra "Dados de 01/01/2018".

Uma diferença importa: na demo, os botões **Feito**, **Adiar** e **Não está vivo** guardam a marcação só no seu navegador. Rodando local com `solution/run.py`, as ações são gravadas num arquivo.

Tempo total do roteiro: cerca de 60 segundos.

## Passo 1 — Escolher o vendedor

Abra a demo. A tela inicial é a aba **Segunda-feira**. No seletor **Vendedor**, escolha **Boris Faz**. É o vendedor com um negócio na fila de fechar, o melhor para ver o fluxo inteiro. O seletor mostra o resumo ao lado de cada nome, por exemplo "Boris Faz (1 para fechar, 5 vivos)".

![Segunda-feira, desktop](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/01-segunda-desktop.png?raw=true)

**O que observar:** a frase do topo diz quantos negócios vivos o vendedor tem. Abaixo vem o **Foco da semana**, com até cinco negócios, cada um com um verbo de ação ("Ligar e propor data de fechamento") em vez de uma nota. Mais abaixo, **Todas as filas** reúne as quatro filas recolhidas — Fechar, Preparar, Iniciar e Encerrar —, com a contagem e o valor de tabela de cada uma.

No celular a mesma tela cabe em 390 px:

![Segunda-feira, mobile](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/02-segunda-mobile.png?raw=true)

## Passo 2 — Entender por que o negócio está ali

Em qualquer negócio, clique em **Por que este deal**. Aparecem três cartões e uma lista do que a ferramenta não sabe:

![Por que este deal](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/03-por-que.png?raw=true)

- **Valor:** o preço de tabela e a posição do negócio na fila do vendedor.
- **Momento:** nas viradas de trimestre anteriores, quantos de cada 100 negócios dessa duração decidiram nas quatro semanas seguintes.
- **Prazo:** quantos dias faltam até o limite do fim do trimestre.
- **Não sei:** o registro de atividade, o desconto e a quantidade negociados, o motivo de perda de negócios parecidos e, quando falta, a conta no CRM.

A explicação é uma frase que o vendedor consegue checar, e a ferramenta diz o que ela não sabe. O índice de 0 a 100 que aparece junto é a posição relativa entre os vivos da carteira, não a chance de ganhar.

## Passo 3 — Ver o estado vazio

Troque o vendedor para **Anna Snelling**. Ela não tem negócio vivo, e a tela não fica em branco: explica que não há nada vivo nesta semana, mostra quantos negócios os vendedores tinham abertos nesta altura em trimestres anteriores e orienta por onde começar (os 55 negócios em Iniciar). Vendedores do cadastro sem nenhum negócio no export aparecem como "sem deal no export".

![Estado vazio](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/04-vazio.png?raw=true)

## Passo 4 — A visão do gestor

Clique na aba **O time**. Use os filtros **Região**, **Gerente** e **Vendedor**. A frase do topo diz quantos vendedores têm ao menos um negócio vivo e quanto do valor aberto já passou da janela de decisão. A tabela abaixo traz, por vendedor, quantos negócios há em cada fila, o valor vivo, o valor vencido e a carga de referência.

![Visão do time](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/05-time.png?raw=true)

## Passo 5 — Auditar a lógica

Clique na aba **Como decide**. É a tela para quem quer conferir a conta:

- a **tabela de destino por faixa de duração**: quantos negócios foram observados, quantos decidem em 28 dias e quantos ganham até o fim do trimestre;
- o **backtest** por data de corte e somado, com valor ganho, taxa de acerto e fração do teto para cada política;
- a **permutação de atributos**, com o p-valor de cada um. Nenhum fica abaixo de 0,05, e é por isso que a ferramenta não tenta dizer quem ganha.

![Como decide](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/06-como-decide.png?raw=true)

## Atalho

A aba e o vendedor ficam no endereço. Para abrir direto num vendedor, acrescente o nome depois de `#segunda=`, por exemplo `https://lead-scorer-diego.vercel.app/#segunda=Boris Faz`.

## O que a demo não faz

Não grava nada em servidor, não escreve no CRM e não usa IA: os textos de cada vendedor vêm de modelo fixo e dizem isso na própria tela ("Texto gerado por modelo fixo, sem IA."). Limites completos em [limitacoes.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/limitacoes.md); a lógica em [logica.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/logica.md).
