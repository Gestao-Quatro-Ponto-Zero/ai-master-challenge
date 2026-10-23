# Prompts-chave

Os pedidos do Tiago que mudaram a direção do trabalho. O texto está literal ou levemente resumido.

### 1. Planejar antes de executar
- **Prompt:** "Precisamos criar as skills necessárias desse projeto, mas antes de tudo precisamos planejar a execução desse projeto, onde criaremos um banco de dados no supabase, com ingestão de dados, criando um data lake, onde teremos os painéis e mcp para análise inteligente de churn, e precisamos documentar toda essa jornada…"
- **Por que:** entender e decompor o problema antes de abrir qualquer ferramenta. É o primeiro critério do G4.
- **O que mudou:** o plano único virou plano de projeto + plano técnico (`07f23bc`).

### 2. Skills por papel e produto completo
- **Prompt:** "…quero primeiramente que tenhamos o plano de projeto, depois qual o plano técnico, e as skills, tanto skill de cientista de dados para o datalake, quanto skill de business para especificar o que vão querer de indicadores… quanto skill de engenharia de software e especialista em python, e termos um painel em react para acompanhar a ingestão…, ver o catálogo de dados… views, dashboards e mcp para consultar a IA tomando decisões e trazendo os porquês com prompts pré-prontos, mas com possibilidade de editá-los"
- **Por que:** separar negócio, dados e engenharia, e exigir que a IA explique o "porquê".
- **O que mudou:** criação das skills, das tabelas `app.prompt_templates`, dos prompts editáveis e do contrato de resposta Resposta → Por quê → Confiança → Próxima ação.

### 3. Fonte real dos dados
- **Prompt:** "foi compartilhado esse dataset lá também, está usando como base?" e "consegue via MCP? … na nossa aplicação sincronizaremos o supabase via MCP do kaggle?"
- **Por que:** ir à fonte primária em vez de confiar no resumo do challenge.
- **O que mudou:** o schema real substituiu o schema suposto (`3c3d654`), e a ingestão passou a usar o Kaggle MCP com sincronização por versão (`03378b5`).

### 4. Experiência, outras IAs e RAG
- **Prompt:** "precisamos de skill de … react e ux para dar a melhor experiência ao usuário, conexão com claude pelo painel do frontend, mas também possibilidade de conexão de mcp no claude e em outras ias…, já deixar preparado para api token de outras llm também e aplicarmos uma rag inteligente nas análises"
- **O que mudou:** skill `react-ux-engineer`, camada multi-LLM, MCP documentado por cliente e RAG híbrido (`3701de5`).

### 5. Análise 360 por área
- **Prompt:** "criar skills e rags por perfil, para que possa-se ter uma análise 360, skills de análise de todas as áreas, e poder personalizar as skills default" e "painéis por persona do cliente e painéis por persona de quem está analisando e um painel geral"
- **O que mudou:** 8 perfis personalizáveis, endpoint 360 que destaca discordâncias entre áreas, 7 personas de cliente e painéis em 3 camadas (`f4557e8`).

### 6. Um ambiente só
- **Prompt:** "testes e demais itens sempre no supabase saas, não iremos rodar local via docker"
- **O que mudou:** testes com rollback ou run de teste com limpeza, e migration destrutiva só com confirmação (`d0defc4`).
