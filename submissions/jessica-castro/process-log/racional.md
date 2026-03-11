*Idéia Central* - lead scorer parecido com o rating bancário
*Plano Lógico*  - Discussão com o ChatGPT para descobrir os melhores modelos matematicos/algoritno, tecnicas para desenvolvimento do projeto. Ao final gerar um prompt para o Claude Code gerar um plano técnico.
*Problema técnico encontrado*
- Os dados históricos são antigos, o cálculo está sendo feito comparando com a data atual. Solução: Em vez de usar a data de hoje, usar a data do snapshot do deal, exemplo: days_since_engage = data_do_deal - ultimo_engajamento.
- O close_value foi removido como feature — um Lead Lost tem sempre close_value=0 e um Won tem valor positivo, o que causava leakage perfeito (AUC=0.98 artificial). Com a correção, o modelo usa sales_price (preço de lista) para todas as linhas, e o close_value real só é usado no cálculo de expected_revenue de saída.
*Melhorias/Bugs*
#  Crie filtros dependentes (cascata) em uma aplicação de dashboard.
Os filtros devem ser coordenados entre si. Quando o usuário selecionar um valor em um filtro, os outros filtros devem atualizar automaticamente para exibir apenas as opções válidas relacionadas.
Exemplo de comportamento esperado:
* Ao selecionar um **Vendedor**, o filtro de **Gerente** deve mostrar apenas os gerente(s) responsáveis por aquele vendedor.
* Ao selecionar um **Gerente**, o filtro de **Vendedor** deve mostrar apenas os vendedores vinculados a esse gerente.
* O mesmo comportamento deve ocorrer para os demais campos relacionados.
Requisitos:
* Os filtros devem funcionar de forma dinâmica.
* As opções disponíveis devem sempre refletir os dados filtrados pelas seleções anteriores.
* Caso nenhum filtro esteja selecionado, todos os valores devem aparecer normalmente.
* O código deve ser organizado e fácil de manter.
* Utilize boas práticas para manipulação de dados e atualização do estado da interface.

Objetivo: garantir que todos os filtros do dashboard sejam interdependentes e reflitam apenas combinações válidas de dados.


# Lógica: Criar, que critérios de scoring você usou e por quê
-----------------

*Dúvidas* 
- CLI tool ou script que gera relatório priorizados, onde está?
- Porque somente 6711 deals treinados? cade o resto?
- API que recebe dados de um deal e retorna score + explicação, onde está?
- Planilha inteligente com fórmulas de scoring, onde está?
- Bot que envia prioridades por Slack/email, onde está?


 


