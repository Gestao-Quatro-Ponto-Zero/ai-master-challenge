# Trechos da conversa com a IA

Ferramenta: Claude Code (Claude Opus 5.5), em 26/10/2026, horário de Brasília.

Seleção de mensagens minhas que mudaram o rumo do trabalho, com o que a IA fez em seguida. As mensagens foram escritas em português informal; aqui a ortografia está corrigida, sem mudar o conteúdo.

| Hora | O que eu escrevi | O que a IA fez | O que mudou na entrega |
|---|---|---|---|
| 18:44 | "E a arquitetura desse sistema?" | Explicou as partes: dados → motor em Python → tela no navegador → testes | A arquitetura foi definida antes de qualquer código |
| 18:45 | "A arquitetura deve estar na documentação, você não acha?" | Criou o documento de arquitetura, com o desenho do sistema | [`docs/arquitetura.md`](../docs/arquitetura.md) existe desde o primeiro commit |
| 18:48 | "Veja os dados: são esses os dados?" | Conferiu os 4 arquivos contra a descrição do desafio | Confirmado: 85 clientes, 7 produtos, 35 vendedores, 8.800 vendas |
| 19:18 | "Faz um checklist de tudo que é solicitado no desafio do G4." | Montou o checklist com os 4 documentos do G4 (desafio, guia, modelo e regras de envio) | Cada exigência conferida contra a entrega |
| 19:19 | "E, sendo honesto, o que você acha do projeto?" | Apontou os pontos fracos: chance otimista, uma venda de US$ 16 entre as 5 da semana e a previsão da chefe sem explicação | Base das três correções abaixo |
| 19:20 | "Você está falando que tem coisas estranhas." | Corrigiu os dois pontos que confundiriam quem usa | A semana ignora vendas de valor muito baixo; a tela da chefe explica a diferença entre o CRM e a previsão |
| 19:32 | "E onde está a IA aqui?" | Explicou: a nota é estatística; a IA foi usada para construir, testar e corrigir | Decisão de não pôr IA dentro do produto, porque o desafio não pede |
| 19:33 | "Não quero fazer nada que o G4 não solicitou. Este projeto pode melhorar ou já está no nível máximo de entrega?" | Respondeu que havia 2 pontos dentro do pedido do G4: a chance otimista e a prova da conversa | — |
| 19:35 | "Melhorar os dois pontos antes." | Achou a causa da chance otimista (a chance caiu ao longo de 2017) e criou o ajuste pelo último trimestre | Erro da previsão passou de +12% a +35% para −4% a +25%; este arquivo |

O passo a passo completo de cada etapa está nos outros arquivos desta pasta, e o histórico de commits mostra a evolução do código.
