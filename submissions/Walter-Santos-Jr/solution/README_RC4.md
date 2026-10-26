# G4 RC4 — BIOS Demo Personas (incremento funcional)

## Execução

```bash
cd solution
python app.py
```

Abrir http://127.0.0.1:8050 e escolher **Head**, **Manager** ou **Seller**. O modo demonstração é o único habilitado nesta entrega. Não utilizar com dados reais ou exposição pública.

## Implementado neste incremento

- Capa de seleção de persona com três botões e troca rápida de perfil.
- Sessão demonstrativa por cookie HttpOnly / SameSite=Strict; RBAC e ABAC básicos no backend para endpoints de dados e operações.
- Escopo de Manager fixado em Melvin Marxen e Seller em Darcel Schlecht, para exploração reproduzível.
- Consulta de conversão Won/Lost histórica filtrada por vendedor, gerente e região, quando disponíveis no CSV.
- Reatribuição de deals dentro da mesma equipe com persistência SQLite e eventos de auditoria.
- Proteção contra leitura direta de deals e jobs fora do escopo demonstrativo.
- 66 testes automatizados aprovados.

## Limitações / não homologado

- A escolha de persona é intencionalmente livre para o avaliador; não é autenticação corporativa.
- Não há integração SSO/MFA, CSRF token, sessão persistida ou política IAM de produção. Servidor limitado a localhost e inicialização fora do Demo Mode bloqueada.
- Os três workspaces usam o cockpit existente, com escopo de dados por persona. Dashboards estratégicos/táticos exclusivos, KPIs Account 360 ampliados, testes E2E de navegador e simulação de fila até zero ainda não foram concluídos.
- Histórico da fila existente permanece sujeito à homologação visual. Mudança de owner não altera manager/regional.
- Dados históricos não possuem região/manager por registro: a consulta infere esses atributos pelo mapeamento do vendedor no snapshot ativo; essa limitação precisa ser apresentada ao avaliador.
- O score é heurístico, não uma probabilidade calibrada.

## Critérios de aprovação antes de submeter

1. Testar navegação e ações dos três perfis em navegador.
2. Validar autorização por endpoint, incluindo alteração de vendedor.
3. Verificar consistência da rosca sob filtros e diferenças entre histórico e pipeline ativo.
4. Validar o botão Histórico em Rework e atualização de filas.
5. Atualizar o caminho `submissions/Walter-Santos-Jr` para o identificador exigido pelo edital, se aplicável.

## RC4 — Workspace Navigation Fix (25/10/2026)

- Head: entrada em Executive Command Center; esconde filas e ações operacionais na interface, mantendo indicadores e hierarquia para investigação.
- Manager: entrada no panorama regional Central / East / West; seleciona região e gerente antes de operar a carteira autorizada.
- Seller: entrada em seleção Região → Manager → Vendedor; não assume Darcel Schlecht automaticamente.
- A troca de persona limpa filtros, breadcrumbs, seleção de deals, cache de jobs e estado de navegação.
- A identidade operacional escolhida é validada e vinculada à sessão no backend via `/api/demo/identity`; leituras e escritas de deals permanecem restritas ao escopo.
- Este ZIP é DEV, sem estrutura de submissão. Usuário GitHub de referência: `Walter-Santos-Jr`.
- Ainda exige UAT visual dos três fluxos e verificação de concorrência de requisições. Não é versão final.
