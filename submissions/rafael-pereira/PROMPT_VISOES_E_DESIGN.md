Leia CLAUDE.md, docs/SCOPE.md, docs/SCORING.md e process-log/07_correcao-curva.md. Execute de ponta a ponta sem me perguntar, registre tudo no process-log e publique no git ao final.

OBJETIVO: (1) separar a visão do vendedor da do manager, mantendo a página estática (opção A); (2) documentar a arquitetura de produção com segregação real (opção B); (3) aplicar uma direção visual inspirada na identidade do G4 e elevar a interatividade com um loop de verificação visual.

PARTE 1 — Visões por perfil (opção A, página estática)
1. Tela de entrada "Quem é você?": Vendedor (escolhe o nome) ou Manager (escolhe o nome). O perfil vai no hash da URL (#perfil=vendedor&nome=...). Use localStorage só para lembrar o último perfil, sempre com try/catch.
2. Visão Vendedor, "Minha semana":
   - mostra SOMENTE os deals do vendedor, sem seletor de outros vendedores. Trocar de perfil volta à tela de entrada;
   - resumo no topo com o progresso da semana;
   - abas Foque, Reative, Limpe e Qualifique com cards;
   - ações por deal ("contatei", "agendei", "encerrar no CRM") salvas no localStorage, com o aviso "salvo só neste navegador";
   - simulador "e se eu fechar este?", mostrando o impacto no valor da semana;
   - estados vazios úteis (ex.: vendedor sem deals abertos).
3. Visão Manager, "Meu time":
   - mapa do time: uma linha por vendedor, com vivos, esfriando e zumbis e o valor de cada grupo;
   - clicar num vendedor abre a carteira dele em modo leitura;
   - "Pauta do 1:1" gerada por vendedor: 3 deals para empurrar, 3 para resgatar e quantos limpar;
   - indicador de higiene do CRM (zumbis por vendedor), rotulado como higiene de carteira e NUNCA como desempenho, coerente com a decisão 4 do CLAUDE.md;
   - nenhum ranking de win rate por vendedor.
4. Transparência obrigatória: no "Como funciona" e no README, deixe explícito que nesta versão a separação é de experiência, não de segurança. O data.js contém todos os deals. A segregação real está em docs/ARQUITETURA_PRODUCAO.md.
5. Links diretos no README para o avaliador: "Entrar como vendedor (ex.: Rosalina Dieter)" e "Entrar como manager (ex.: Celia Rouche)".

PARTE 2 — Arquitetura de produção (opção B, só documentação)
Crie docs/ARQUITETURA_PRODUCAO.md (máx. 3 páginas):
- Requisito de controle: "vendedor vê só a própria carteira; manager vê só o time; RevOps vê tudo", e por que a página estática não atende (os dados estão no cliente).
- Arquitetura alvo: front estático + Supabase (Auth com SSO corporativo + Postgres com Row-Level Security). O job de scoring roda no servidor (agendado) e grava os scores; o front nunca recebe linhas fora do escopo do usuário. Inclua um diagrama Mermaid.
- Modelo de dados: tabelas deals, sales_teams, scores e user_profiles (user_id → papel, sales_agent, manager).
- Políticas RLS em SQL para os 3 papéis. Se houver Postgres ou Docker disponível, teste as políticas com dados de exemplo e registre o resultado. Se não houver, marque "SQL não executado — validar".
- Governança: trilha de auditoria de acesso, minimização de dados (LGPD), revisão periódica de acessos e o que acontece quando um vendedor muda de time.
- Caminho de migração de A para B, com esforço estimado.
Atualize DECISIONS.md (A escolhida por fricção zero para o avaliador, B mapeada), MODEL_CARD.md (limitação de acesso) e a seção de limitações do README.

PARTE 3 — Estética: direção visual inspirada no G4
1. Se a skill frontend-design estiver disponível, carregue-a. Escreva docs/DESIGN.md ANTES de mexer no CSS.

2. Identidade de referência. Valores extraídos dos estilos computados de https://g4business.com em 25/10/2026:
   - Azul-marinho principal #001F35 (variação mais escura #031A26);
   - Dourado de destaque #B9915B;
   - Off-white #F5F4F3;
   - Texto de interface em Manrope;
   - Destaques editoriais em Libre Baskerville itálica (ex.: uma palavra-chave da frase de resumo);
   - Botões primários com fundo dourado, texto marinho, raio de 10px e peso 800;
   - Tom sóbrio e premium, com frases curtas e diretas.
   REGRA: a ferramenta é INSPIRADA na identidade, não uma cópia. Não use o logotipo nem o nome "G4" na interface. O nome da ferramenta continua "Lead Scorer". Registre essa decisão em DECISIONS.md.

3. Tokens (CSS custom properties em style.css, documentados em DESIGN.md):
   - Marca:
     --navy-900: #001F35; --navy-950: #031A26; --gold-500: #B9915B; --offwhite: #F5F4F3;
     derive de 2 a 3 tons de cada cor (hover, bordas, fundos suaves).
   - Semântica das listas: o dourado é reservado para ação primária e marca e NÃO pode ser cor de status. Proponha cores de status que harmonizem com marinho e off-white. Ponto de partida:
     Foque = verde-sálvia; Reative = cobre/laranja queimado; Limpe = cinza-azulado; Qualifique = azul-aço.
     Cada status sempre leva cor + ícone + rótulo; nunca só a cor.
   - Contraste: valide AA (4,5:1 para texto, 3:1 para elementos gráficos) para todas as combinações nos dois temas e registre a tabela em DESIGN.md. Ajuste os tons até passar.
   - Tipografia:
     --font-ui: 'Manrope', system-ui, sans-serif;
     --font-accent: 'Libre Baskerville', Georgia, serif (só itálico, só em destaques; nunca em números ou tabelas).
     Use números tabulares (font-variant-numeric: tabular-nums) em valores e scores.
   - Fontes auto-hospedadas: baixe os .woff2 de Manrope e Libre Baskerville (ambas sob licença OFL) para solution/app/fonts/, inclua o arquivo de licença e use @font-face. Isso mantém tudo funcionando em file:// e sem depender de CDN.
   - Espaçamento em múltiplos de 8px, raio de 10px em botões e 14 a 16px em cards, sombras suaves.
   - Temas:
     claro = fundo off-white, texto marinho, cabeçalho marinho;
     escuro = fundo marinho-950, superfícies marinho-900, texto off-white.
     Siga prefers-color-scheme e ofereça um botão de alternância.
   - Movimento: transições de 150 a 200ms, respeitando prefers-reduced-motion. Foco visível em dourado.
   - Layout: mobile first na visão do vendedor, desktop first na visão do manager.

4. Referências de layout no Figma Community. Use APENAS como inspiração de estrutura (organização de cards, pipeline, tabelas de time); a paleta é sempre a dos tokens acima:
   - Sales Pipeline CRM UI Kit: https://www.figma.com/community/file/1655963876379347889/sales-pipeline-crm-ui-kit-modern-saas-dashboard-for-figma
   - Lead & Sales Dashboard Design: https://www.figma.com/community/file/1386640726702426181/lead-sales-dashboard-design
   - CosaFin Elite (estética premium): https://www.figma.com/community/file/1426624463292496929/cosafin-elite-financial-insights-wealth-management-dashboard
   - Dark CRM SaaS Dashboard UI Kit: https://www.figma.com/community/file/1658081005734427644/dark-crm-saas-dashboard-ui-kit-inventory-orders-shipping-customer-management
   Arquivos da Comunidade só ficam legíveis pelo conector depois de duplicados para a minha conta. Se o conector Figma estiver ativo nesta sessão E houver em docs/DESIGN.md um link de arquivo meu (duplicado ou criado), crie a sessão do Figma, carregue a skill figma-design-to-code e use get_design_context e get_screenshot como referência de layout. Caso contrário, use as descrições acima e registre "Figma: referências usadas só como inspiração, arquivo não lido".

5. Interatividade com propósito:
   - o card do deal expande com um clique e mostra o "porquê";
   - as ações (contatei, agendei, encerrar) dão feedback imediato e atualizam o resumo;
   - o simulador "e se eu fechar este?" anima o número da semana;
   - no manager, o mapa do time é ordenável e clicável, e a pauta do 1:1 tem um botão "copiar";
   - navegação por teclado completa.
   Nada de animação decorativa sem função.

6. Loop visual com Playwright, em no máximo 3 rodadas:
   a) Capture a matriz {vendedor, manager} × {tela de entrada, abas principais, pauta do 1:1} × {390px, 1280px} × {claro, escuro}. Salve em process-log/screenshots/design-rN/.
   b) Critique cada tela contra este checklist:
      - hierarquia clara em 3 segundos;
      - ação principal óbvia;
      - dourado usado só para ação ou marca;
      - status legível sem depender da cor;
      - nada cortado ou sobreposto;
      - contraste AA;
      - estados vazios úteis;
      - consistência com os tokens;
      - "parece uma ferramenta premium e sóbria, não um template genérico".
   c) Corrija e repita. Registre em process-log/08_visoes-e-design.md o que mudou em cada rodada, com antes/depois.

7. Qualidade objetiva:
   - rode axe-core (@axe-core/playwright) nas telas principais, nos dois temas: zero violações "serious" ou "critical";
   - se disponível, rode o Lighthouse (acessibilidade e performance) e registre as notas;
   - crie testes Playwright que cobrem:
     - entrar como vendedor e não ver outros vendedores;
     - entrar como manager, abrir um vendedor e gerar a pauta;
     - totais da tela batendo com o data.js;
     - alternância de tema.

RESTRIÇÕES
- HTML, CSS e JS puros, sem build e sem CDN obrigatório. Precisa funcionar em file:// e no GitHub Pages.
- Não altere a lógica de scoring. Se algo na interface exigir mudança no motor, registre e pare essa parte.
- Nada fora de submissions/rafael-pereira/. Use git add -f.

VERIFICAÇÃO E PUBLICAÇÃO
1. pytest, `python -m scorer.build`, os testes Playwright e o axe passam.
2. Commits separados: "visões vendedor/manager", "arquitetura de produção (doc)" e "design: identidade inspirada no G4, tokens e loop visual".
3. Push para origin submission/rafael-pereira, sem --force. Espere o Pages republicar, abra a URL publicada com cache-buster e confirme as duas visões e os dois temas no ar.
4. Se houver PR aberto, comente com gh pr comment resumindo as mudanças.

ENTREGA
Responda com:
- os links diretos das duas visões;
- 4 screenshots finais (vendedor e manager, celular e desktop) e 1 do tema escuro;
- a tabela de contraste;
- o resultado do axe e do Lighthouse;
- o que mudou entre as rodadas de design;
- os hashes dos commits.
