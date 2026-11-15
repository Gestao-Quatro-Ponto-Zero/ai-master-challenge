# docs

| Arquivo | O que é |
|---|---|
| `contribuicao-do-rodrigo.md` | O que o Rodrigo acrescentou que a IA sozinha não faria: cada contribuição com a frase ou decisão dele, onde ela aparece no app e o que teria acontecido sem ela. Inclui as ideias dele que foram testadas e não entraram, e o que foi da IA. |
| `ux/` | Estudo de UX feito no Paper, antes do código: 12 pranchas em PNG e o PDF único `ux/estudo-de-ux.pdf`. |
| `app/` | Capturas do app rodando (10 telas, na data simulada de 4 dez 2017), tiradas no Chrome a partir do servidor local. |

## Estudo de UX

O estudo foi desenhado antes do código, para discutir as telas antes de construí-las. Passou por três revisões de usabilidade feitas por IA e por uma auditoria contra as regras do desafio. Depois, o app passou a calcular cada frase a partir do dado, e os textos foram alinhados com esse cálculo. Isso corrigiu, por exemplo, a frase "deal aberto quase nunca tem cliente" (no fim da base, um em cada três tem) e números de duas datas misturadas (31 dez e 4 dez 2017). As pranchas foram exportadas de novo depois desse alinhamento. Elas são referência de desenho; onde ainda divergirem do app, vale o app (`app/`).

| Prancha | O que mostra |
|---|---|
| `00-fundamentos.png` | De onde veio cada decisão de desenho (as quatro ideias da prática do Rodrigo), cores, tipografia e as peças que se repetem: linha do deal, barra das duas leituras, cartão da Gabi. |
| `01-acesso-simulado.png` | Entrada sem senha: escolher perfil (vendedor ou gestor) e pessoa, com três sugestões. Ao lado, o pipeline declarado contra o vivo da empresa. |
| `02-vendedor-foco-da-semana.png` | Foco da semana do vendedor: deals por score em abas Quentes, Mornos, Frios e Sem desfecho, filtro com e sem cliente, o porquê de cada score e os Insights da Gabi. |
| `03-gestor-meu-time.png` | Visão do gestor: declarado e vivo por vendedor, taxa oficial e taxa contando os sem desfecho, pauta da Gabi e mensagem pronta para quem não abre o sistema. |
| `04-maquina-do-tempo.png` | A prova: em qualquer segunda simulada, a lista do score ao lado da lista só por valor, com o desfecho revelado. Abaixo, o resultado das 22 segundas e os limites da prova. |
| `05-pipeline-por-fase.png` | Pipeline do vendedor em colunas por fase (kanban): Prospecção, Em negociação, Sem desfecho (separada), Ganhos e Perdidos dos últimos 30 dias, com filtro com e sem cliente. |
| `06-clientes.png` | Clientes da regional, ordenados por valor ganho, com o painel lateral aberto na aba Dados: histórico fechado, o que mais compra e cadastro. |
| `06b-painel-do-cliente-abas.png` | As outras duas abas do painel do cliente, Em aberto e Fechadas, com o aviso de que o cliente dos deals abertos não é confiável. |
| `07-fontes-de-dados.png` | Configurações: a base do desafio em uso, a lista de CRMs de referência com o alerta escrito pelo Rodrigo, e o que uma integração real precisa trazer. |
| `08-como-o-score-funciona.png` | O cálculo passo a passo de um deal, a tabela de chance por faixa de idade e os sinais testados que ficaram fora. |
| `09-como-chegamos-aqui.png` | Transparência: o que veio da prática do Rodrigo, o que a IA fez e onde a IA errou. |
| `10-qualidade-dos-dados.png` | O que a base tem e o que falta, e as cinco particularidades que mudaram o desenho do score. |
