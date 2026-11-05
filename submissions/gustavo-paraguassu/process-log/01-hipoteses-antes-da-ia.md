# 01 — Minhas hipóteses antes da estratégia da IA

**Escrito por:** Gustavo Paraguassu, em 04/11/2026, sem consultar a IA.

**Contexto, para ser honesto sobre a ordem dos fatos.** Antes deste texto, o Claude Code já tinha:

- baixado os dados;
- verificado que o Dataset 1 é sintético (`analysis-outputs/01_*` e `02_*`);
- levantado como as outras submissões do 002 e as avaliações do G4 abordaram o desafio.

Nenhuma proposta de solução tinha sido feita. Pedi para parar ali e escrevi a minha leitura do problema a partir da fala do Diretor e da minha experiência. Ela vem antes de qualquer estratégia sugerida pela IA. Daqui para frente, cada hipótese é testada contra os dados, e o que os dados não conseguirem testar fica registrado como tal.

---

## Texto original (sem edição)

> Minha hipótese é que o suporte perde tempo com dúvidas repetidas, busca de informações e registros manuais.
> Também há retrabalho quando faltam dados, o chamado vai para a equipe errada ou o cliente precisa repetir sua história.
> Separaria o tempo de trabalho do tempo esperando cliente, aprovação ou outra área, porque cada gargalo exige uma solução.
> Automatizaria resumos, classificação de tickets, preenchimento de campos e sugestões de resposta baseadas em conteúdo aprovado.
> Liberaria respostas automáticas para dúvidas simples e bem delimitadas, com acesso fácil a uma pessoa.
> Nunca daria autonomia irrestrita à IA para decisões críticas, ações irreversíveis ou compromissos fora das regras da empresa.
> Para mostrar funcionando, começaria com um assistente que prepara respostas para revisão do atendente.
> Testaria essas hipóteses medindo esforço por resolução, transferências, reaberturas e satisfação do cliente.

---

## Hipóteses numeradas, para rastrear até o resultado

| # | Hipótese | Dá para testar com os dados? | Onde |
|---|---|---|---|
| H1 | Tempo perdido com **dúvidas repetidas** | Sim. Medir quanto do volume são pedidos quase idênticos | Dataset 2 |
| H2 | Tempo perdido com **busca de informação e registro manual** | Não diretamente, porque nenhum dataset tem tempo de manuseio | Plano de medição |
| H3a | Retrabalho quando **faltam dados** no chamado | Parcialmente. Tickets curtos ou vagos têm mais erro de roteamento? | Dataset 2 |
| H3b | Retrabalho quando o chamado **vai para a equipe errada** | Sim. Quais filas se confundem, e se há texto igual com filas diferentes | Dataset 2 |
| H3c | Cliente **repete a história** | Não. Não há histórico de conversa por cliente | Plano de medição |
| H4 | Separar **tempo de trabalho** de **tempo esperando** (cliente, aprovação, outra área) | Não há duração confiável. Só o status "Pending Customer Response" (34%) indica espera | Dataset 1 e plano de medição |
| H5 | Automatizar **resumo, classificação, preenchimento de campos e resposta a partir de conteúdo aprovado** | Classificação: sim. Os outros itens dependem de uma base de respostas aprovadas que não existe nos dados | Dataset 2 e protótipo |
| H6 | Resposta automática **só para dúvida simples e bem delimitada**, com saída fácil para uma pessoa | Sim, via acerto por faixa de confiança | Dataset 2 |
| H7 | **Nunca** dar autonomia em decisão crítica, irreversível ou fora da regra | É uma regra de política, que vira lista explícita por categoria | Dataset 1 (tipos) e Dataset 2 (filas) |
| H8 | Protótipo = **assistente que prepara a resposta para revisão** do atendente | É o protótipo | — |
| H9 | Métricas de sucesso: **esforço por resolução, transferências, reaberturas, satisfação** | Nenhuma existe de forma confiável nos dados, então vira instrumentação do protótipo | Plano de medição |
