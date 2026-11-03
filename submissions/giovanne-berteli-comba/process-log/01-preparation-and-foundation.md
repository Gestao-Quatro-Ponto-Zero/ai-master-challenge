# Preparação, decisões e criação da base

Data deste registro: 02/11/2026. Parte da preparação ocorreu antes desta data;
os horários originais disponíveis estão nos arquivos das conversas.

## Contexto e evolução

Na [conversa inicial](chat-exports/01-preparation-chatgpt.md), o usuário propôs
preparar o ambiente, organizar conhecimento compartilhado e usar diferentes
IAs para análise, implementação e crítica. Também discutiu evidências e sugeriu
um CodeTour para explicar a aplicação. A IA propôs uma estrutura ampla e depois
recomendou começar com o mínimo e expandir conforme necessário.

Neste [chat de planejamento](chat-exports/03-planning-chat.md), o usuário
questionou o orçamento de preparação de 8%, para reduzir repetição de contexto
e consumo de tokens; pediu checks em Markdown; propôs testes unitários e de
integração, dashboard interno e catálogo de componentes quando úteis; e discutiu
idioma da entrega. O percentual passou a ser uma referência flexível. Não há
medição de economia de tokens nesta etapa.

## Comparação dos desafios e decisão humana

O usuário informou contagens de PRs por desafio: 001: 45; 002: 42; 003: 95;
004: 21. São contagens informadas pelo usuário, sem auditoria de candidatos
únicos ou qualidade das submissões. Uma recomendação anterior favoreceu o 004
pela menor quantidade de submissões. Uma [segunda análise](chat-exports/02-challenge-comparison.md)
favoreceu o 002 pela aderência à experiência declarada com agentes, automações,
integrações e arquitetura. Depois, o usuário escolheu explicitamente o **002**.

Esta sequência preserva uma mudança real de direção: a recomendação inicial
da IA pelo 004 não foi tratada como decisão final. A justificativa pessoal
completa da escolha pode ser acrescentada pelo usuário, sem ser inventada pela IA.

## Ajustes e limitações identificados

- Respostas anteriores chamaram contagens de PRs de participantes. Esses
  números não demonstram pessoas únicas nem chances de aprovação.
- Uma resposta inicial disse não haver acesso a outros chats. Na criação da
  base, ferramentas do aplicativo disponíveis permitiram recuperar os três
  chats relevantes identificados; isso não equivale a acesso irrestrito a
  todas as conversas do usuário.
- O briefing lista o protótipo como diferencial; incluí-lo é uma escolha do
  projeto, enquanto diagnóstico, proposta e process log são obrigatórios.
- A estrutura sugerida inicialmente precisa respeitar o limite do G4:
  somente arquivos da pasta da submissão podem ser alterados no PR.
- Volumes, qualidade e propriedades dos datasets permanecem não verificados.
  Os conjuntos não devem ser conectados sem justificativa após a auditoria.

## Autorização desta etapa

O usuário autorizou montar a base e deixou a decisão sobre uso conjunto dos
datasets para a próxima etapa. Também solicitou preservar as conversas passadas
e futuras no process log. A implementação criou instruções compartilhadas,
contexto mínimo em OKF, plano, backlog, estratégia de validação e os registros
das conversas disponíveis.

## Estado resultante

- Conhecimento em OKF v0.2, consultado por índice e documentos selecionados.
- Código, Git e documentação técnica interna em inglês; narrativa ao avaliador
  em português; conversas preservadas no idioma original.
- Plano com critérios de aceite e checkboxes que dependem de evidência.
- Estratégia de testes preparada, com execução futura conforme implementação.
- Dataset audit, arquitetura, métricas e protótipo continuam pendentes.
- Dashboard e catálogo de componentes ficam no backlog; CodeTour virá após
  estabilizar a implementação.

Os resultados dos checks documentais desta etapa serão registrados em
[activity-log.md](../execution/activity-log.md). Não há testes de aplicação ou
resultados analíticos para relatar, pois nenhum código funcional foi criado.
