# Solução e Limitações

## Solução

A solução foi construída com dois serviços principais:

1. `API` (FastAPI)
2. `Front` (Streamlit)

### Arquitetura (2 serviços)

- `API`:
	- expõe endpoints para consulta de contas, produtos, equipes e oportunidades
	- calcula o score histórico de conta no endpoint `GET /account-scores`
	- serve como camada de dados para o front

- `Front`:
	- consome a API e exibe a priorização de deals
	- aplica filtros (vendedor, manager, região, estágio, produto, conta e faixas de score)
	- mostra cards com:
		- score do deal
		- score da conta
		- memória de cálculo do deal
		- memória de cálculo da conta
		- próxima ação recomendada

### Banco de dados

- usa SQLite (`data/sales.sqlite3`)
- inicializado automaticamente a partir dos CSVs

### Objetivo funcional

A solução ajuda o vendedor a responder rapidamente:

- quais deals priorizar
- por que priorizar
- qual próxima ação executar

## Limitações

### Segurança e autenticação

- não há autenticação/ autorização (`auth`) na API
- CORS está aberto para facilitar desenvolvimento local
- não há controle de perfis/roles (vendedor, manager, admin)

### Dados e modelagem

- parte dos dados de deals abertos não possui `close_value`
- score depende de regras heurísticas (não há modelo de ML treinado)
- não há versionamento formal de regras de score

### Operação

- não há observabilidade completa (logs estruturados, métricas, tracing)
- não há pipeline CI/CD configurado
- não há suite de testes automatizados cobrindo front e API ponta a ponta

### Produto

- sem integração com CRM externo em tempo real
- sem workflow de tarefas/notificações (ex.: Slack, e-mail)
- sem histórico de ações do usuário no front (auditoria de uso)

## Próximos passos sugeridos

1. Implementar autenticação (JWT/OAuth2) e autorização por perfil.
2. Adicionar testes de integração API + Front.
3. Criar versionamento de regras de score e monitoramento de impacto.
4. Integrar com CRM para atualização automática de pipeline.
