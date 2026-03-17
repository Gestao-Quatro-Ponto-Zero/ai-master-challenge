# Process Log

Esse readme é o process log. 

## Análise Inicial

Inicialmente fizemos uma análise do problema, para entender o que precisamos resolver. Entendemos que precisamos descobrir o que automatizar, onde perdemos tempo e fazer algo que funcione. Vamos analisar os dados para achar as combinações com pior resultado e o custo desperdiçado. Aparentemente é necessário um direcionador de tickets com chatbot. 

## Análise de Dados

Para analisar os dados pedi ao Gemini que fizesse códigos de cálculos e gráficos para entender os dados, utilizei a IA apenas para criar códigos e me dar insights. Notei que o problema está nos canais, por conta da correlação da nota e os canais ser a maior de todas. Analisando um heatmap entre os canais e tipos de tickets foi possível notar que o melhor canal tem sido o chat. Precisamos explorar esse canal e utilizar menos os outros. 

## Proposta de Solução

Pensando nesse ponto podemos criar um direcionador dentro do chat que analisa o ticket e direciona para bot ou para humano. Nisso ao direcionar para humano ele precisa informar que o usuário pode enviar email ou ligar. (Somente irá avisar nesse caso pois é um caso sensível). É preciso lembrar que a empresa precisará repaginar o FAQ com isso e aumentar a visibilidade do chat e com ajuda da API do crm pode deixar o mesmo sistema nas redes sociais e até no whatsapp. 

## Preparação dos Dados

Antes de implementar o classificador notei que para problemas técnicos alguns precisam de humano, para isso juntei o csv "all_tickets_processed_improved_v3" no treinamento. Limpei os dados do "customer_support_tickets" para termos somente texto do ticket e tipo e juntei com o outro csv. Nesse caso o clasificador irá saber diferenciar quais categorias o bot irá resolver e quais o bot irá, mais especificamente. 

## Definição de Responsabilidades

O humano irá resolver categorias envolvendo trocas, pagamento e o que envolve dinheiro, pois é sensível. Já o chatbot conterá jsons com manuais de ajuda ao cliente envolvendo cada produto.

## Resultado Esperado

Realizando isso teremos uma economia de cerca de R$60k pois o bot irá resolver mais rapidamente do que o SLA de 11 horas e deixará tempo livre para consultores agirem mais rapidamente nos outros casos.