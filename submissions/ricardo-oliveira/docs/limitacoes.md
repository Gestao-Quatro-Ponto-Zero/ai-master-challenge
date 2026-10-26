# Limitações: o que a solução não faz e o que precisaria pra escalar

- **Dataset gerado.** Ganhos e perdidos param nos mesmos 138 dias e a taxa de ganho é igual em todo corte. Os cortes são percentis deste arquivo, em células editáveis. Num CRM real, recalcular todo mês, e esperar sinal de probabilidade que aqui não existe.
- **"Outro vendedor fechou depois" não prova o mesmo pedido.** Pode ser outro departamento, outra quantidade, compra recorrente. No backtest esses deals fecharam ganhos em 58% contra 62% dos limpos: o sinal não separa quem fecha. Por isso o bloco é de confirmação, não de encerramento, e a regra é de operação comercial (conta sem dono), não achado estatístico.
- **O backtest é exploratório.** Um snapshot, sem relação de causa; os cortes de 57 e 138 dias vêm do arquivo inteiro, inclusive do que fechou depois do snapshot. Serve pra escolher entre ordens, não pra prometer resultado. A ordem em uso ganha mais deals que o acaso pareado (270 contra 215) e menos receita (US$ 624 mil contra 650 mil).
- **Sem data de último contato.** A lista diz "aberto há X dias". A partir do app, `Atividades` cria esse dado.
- **Recompra é estimativa.** Última compra mais intervalo médio daquela conta naquele produto, com o número de compras que sustenta a estimativa. Não é contrato. Quando o atraso passa do dobro do ritmo, o card avisa que a conta pode ter parado de comprar ou comprado em outro lugar, e manda confirmar antes de contar com a recompra.
- **Comissão preservada é meta, não prova.** A carteira preserva o potencial histórico (-4% a +7%); o efeito real é checado no piloto junto com a carga de trabalho.
- **Prospecting sem data** fica fora do backtest e entra na lista pelo valor do produto até o vendedor engajar.
- **Redistribuição de carteiras depende da RevOps.** O app roda sem ela (modo "como está hoje").
- **Relógio simulado.** Um CRM congelado em 31/12/2017 e um job que anda um dia por vez. Durante a avaliação o job fica desligado, pra que o "hoje" do app bata com o README. Com um CRM vivo, o job leria o export do dia e o `Atividades` viraria o CRM.
- **Demo compartilhada.** Todo mundo que abre o app olha a mesma planilha. Marcar Feito, Ganho ou Perdido grava pra todo mundo (é o comportamento esperado de um CRM). Avançar o dia, zerar e ligar o job mudam o relógio de todos, por isso pedem a senha de administração (no README).
- **Escala.** A planilha aguenta este volume (8.800 linhas) com folga; com dezenas de milhares de deals a lógica migra pra um banco, mantendo as mesmas regras (a aba `Hoje` vira a tabela de configuração). O Apps Script tem cota diária de execução; um volume maior pede uma API própria.
- **Sem login na demo.** Os e-mails dos vendedores não existem no dataset; a primeira tela escolhe quem está olhando. Com a aprovação da RevOps: SSO da empresa e permissão por papel (vendedor vê o seu, manager vê o time).
- **Mensagens por e-mail** no job diário. Slack com um webhook, sem mudar o resto.
- **Fora de escopo:** regra pra conta nova (new logo), crédito de passagem de deal, especialização de GTXPro.
