# 0015 — Navegação de um nível, Tickets em formato de conversa e Slack simulado no navegador

- **Status:** Proposta (decisões do Daniel na revisão de 10/11; aguarda o OK final depois da construção)
- **Data:** 2026-11-10
- **Origem:** Daniel (pente fino do app em produção) · IA (opções de navegação, desenho da conversa e da camada de dados)
- **Substitui em parte:** [0007](0007-notificacoes-slack-e-inbox.md) (caixa no painel), [0008](0008-console-como-validador.md) (console em abas), [0014](0014-arquitetura-do-app.md) (toggles internos)

## Contexto
O app em produção tinha dois controles segmentados empilhados: as áreas na top bar e as visões de cada área abaixo do título. O Daniel avaliou a experiência como ruim. A triagem, a fila de revisão e a caixa de alertas ficavam em três abas separadas, e o mesmo ticket aparecia em lugares diferentes conforme o caminho.

## Decisão
1. **Navegação de um nível com submenus:** a top bar tem `Painel ▾ · Tickets · Como foi feito ▾`. O menu abre com um clique, e cada subitem traz uma linha de descrição. No mobile, a barra do rodapé abre uma folha. As visões passam a ter rotas reais (`/painel/roi`, `/tickets`, `/como-foi-feito/decisoes`), e as URLs antigas redirecionam.
2. **Tickets em formato de conversa:**
   - lista à esquerda, do mais recente ao mais antigo, com "Não lido" e a tag do caminho;
   - conversa à direita: a mensagem do cliente e depois, conforme o caminho:
     - **Resposta automática:** a resposta da IA;
     - **Revisão humana:** o rascunho para validar;
     - **Somente humano:** a nota interna em pt-BR.
   - Na Revisão humana e no Somente humano, o atendente pode escrever a própria resposta. Na Revisão humana, isso conta como rascunho recusado e **não** entra na base de conhecimento.
3. **Slack simulado no navegador:** quando um ticket do visitante cai em Somente humano, aparece uma notificação "Simulação de mensagem no Slack". O histórico fica numa bolinha no canto inferior direito, só deste navegador. O fluxo 1 do n8n deixa de gravar na tabela `notifications`. O nó Slack (desativado) continua no fluxo como documentação do envio real.
4. **Privacidade entre visitantes:** a lista mostra os tickets de demonstração, compartilhados, mais os criados neste navegador. Cada triagem do visitante recebe um `client_token` aleatório, e só quem tem o token busca o ticket.
5. **Alertas do sistema fora da interface:** heartbeat e monitor de uso continuam gravando em `notifications`, e quem acompanha são as rotinas do Claude do Daniel.

## Alternativas consideradas
- Barra lateral fixa: ocupa largura que a conversa precisa.
- Página longa por área com âncoras: mistura análise estática com indicadores ao vivo.
- Manter os dois níveis com abas sublinhadas: continua com dois controles visíveis.
- Lista compartilhada entre todos os visitantes: um visitante veria o texto livre de outro.

## Consequências
- O avaliador vê o ciclo inteiro de um ticket numa tela só.
- O diagnóstico perde o forest plot do CSAT; o CSAT continua como métrica do gráfico principal.
- `notifications` deixa de ser lida pelo app; `/api/inbox` sai.
