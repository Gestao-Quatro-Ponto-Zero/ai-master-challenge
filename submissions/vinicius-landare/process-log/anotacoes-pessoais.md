# Anotações Pessoais — Vinicius Landare
## Challenge 004 — Estratégia Social Media (v2)

> Estas anotações documentam meu processo de pensamento, pesquisas externas, decisões estratégicas e intervenções durante o desenvolvimento com IA. Cada item mostra onde EU dirigi o processo e onde a IA executou sob minha orientação.

---

## PARTE 1 — Estrutura de Pensamento (antes de codar)

**1. Pensamento orientado à demanda real**

Para o ajuste, estruturei o pensamento de "atender a demanda" com relevância para o gestor ter números e insights que realmente são acionáveis e não apenas números na tela. O dashboard v1 tinha dados bonitos mas o gestor não sabia o que fazer com eles na segunda-feira.

**2. IA como amplificador, não como líder**

Eu tenho a minha própria capacidade de estruturar o ajuste, porém utilizo a IA como suporte para ampliar os horizontes em 2 frentes: A primeira é imputando o contexto da tarefa e recebendo um output da LLM, a segunda é imputando o meu pensamento estruturado para uma análise crítica da IA (Claude Code). A decisão final é sempre minha.

**3. Por que Claude Code com Opus 4.6?**

Porque julgo ser a melhor ferramenta para o desenvolvimento de sistemas, com subagentes para tarefas específicas. Durante o desenvolvimento observo cada parâmetro de execução que os agentes estão realizando, se eles estão seguindo um caminho alucinógeno, eu interrompo imediatamente a execução para inserir informações mais deterministas. Em alguns momentos utilizei o "Plan mode" para criar um novo plano convergente com minhas ideias iniciais + pesquisas realizadas nos chats anteriores. Não me limitei a uma ferramenta — validei abordagens com ChatGPT Codex e Antigravity também.

**4. Releitura do desafio — o que o gestor REALMENTE quer**

Ao ler novamente o desafio entendi que o gestor não quer apenas a análise dos dados para tomada de decisão, mas acompanhar no dia a dia os dados em tempo real. Comparar o que mudou do passado para o presente, e onde o insight passado se perde, identificando tendências atuais e não apenas ações baseadas no passado. Isso mudou toda a arquitetura.

**5. Pesquisa sobre prompt engineering — Draft → Critique → Output**

Recentemente li um artigo da Anthropic sobre o melhor setup para textos de marketing é o "Fluxo encadeado de prompts" e combinei essa pesquisa com um vídeo que assisti do Don Woodlock onde ele explica o sistema agêntico de Rascunho → Crítica → Output. Com isso criei uma sequência de chamadas na LLM em 3 steps para gerar as melhores ideias, recomendações e roteiros de conteúdos para o gestor. Para isso acontecer utilizei a OpenRouter para o encadeamento de diferentes modelos (Gemini Flash para criatividade, Claude Sonnet 4.5 para crítica analítica).

**6. Divergência → Convergência**

Descobri que a minha cadeia de pensamento se chama na literatura de divergência → convergência e isso pode ser uma base sólida na arquitetura do sistema G4. Expande possibilidades, filtra o que presta. Apliquei isso tanto no meu processo de trabalho quanto na arquitetura do pipeline de conteúdo.

---

## PARTE 2 — Pontos-chave extraídos do briefing

- Faz parcerias com influenciadores — integrei Z-API para reavaliar parcerias via WhatsApp direto do dashboard
- O foco principal é O QUE REALMENTE FUNCIONA — cada seção responde isso com dados
- 3 Pontos principais: O que gera engajamento de verdade, se vale a pena patrocinar influenciadores, qual deveria ser a estratégia de conteúdo
- Estratégia baseada em dados e não uma opinião — não quer inferência, quer determinação. Por isso adicionei testes estatísticos e badges de significância
- Ferramenta para acompanhar no dia a dia — criei calendário de conteúdo, cron job diário, e análise de perfil via Apify
- Mesmo conteúdo performando por plataforma? — explorador interativo permite cruzar plataforma × formato × tier
- Modelo preditivo: Característica do post / Engajamento estimado — o pipeline de 3 steps funciona como preditor qualitativo

---

## PARTE 3 — Decisões de arquitetura

**A arquitetura precisa mudar de ETL batch → dashboard estático para pipeline contínuo → motor de detecção + gerador de ações.**

Isso guiou toda a reestruturação:
- De 9 tabs técnicas (por hipótese) para 6 tabs orientadas ao negócio
- De recomendações hardcoded para geração automática via IA com dados do dataset
- De snapshot único para calendário com aprovação e histórico de aprendizado
- De dados estáticos para análise de perfil em tempo real via Apify

**Nota sobre credenciais:** OpenRouter, Apify, Z-API foram usadas credenciais com limite de uso, descartáveis e sem risco para a integridade da conta.

---

## PARTE 4 — Plano de implementação (meu, antes da IA executar)

1. Integrar com o Apify para fazer análise de dados de engajamento dos posts em todas as redes sociais (5 plataformas: Instagram, TikTok, YouTube, RedNote, Bilibili)
2. Opção de dados do dataset para mostrar como ficaria o frontend usando os dados históricos como benchmark
3. Utilizar o processo de 3 steps para criar recomendações, insights e roteiros de conteúdo — não para analisar dados, mas para gerar ação
4. Sistema de recomendações em loop: gera → critica → refina → gestor aprova/descarta → descartados alimentam próximo ciclo

---

## PARTE 5 — Mudanças durante a visualização do frontend (23 intervenções)

Cada item abaixo é uma decisão minha ao ver o frontend funcionando — a IA não teria feito essas correções sozinha.

**1.** Ainda mantendo dados com percentual de pontos percentuais, ainda não tenho clareza do que fazer com cada um dos pontos, então pedi uma troca de pontos percentuais para porcentagem, assim conseguimos definir com clareza (mesmo que mínima) a porcentagem do quanto um conteúdo foi bem.

**2.** Melhorei a distribuição das tabs deixando os dados mais claros para um gestor não técnico fazer uma leitura rápida.

**3.** O gráfico de campanhas de tráfego pago estava confuso com barras horizontais e uma barra cinza gigante de "electronics" que não fazia sentido visual. Pedi pra trocar por uma tabela visual mais limpa com barras inline e cores claras (verde = positivo, vermelho = negativo).

**4.** A geração de conteúdo travava no "Gerando..." e ao trocar de tab perdia o estado. Pedi pra travar a tela com um overlay durante a geração, assim o gestor não perde o contexto.

**5.** Identifiquei que todos os textos do frontend estavam sem acentos (Patrocinio, Calendario, Analise, aprovacao). Pedi uma busca completa e correção em todos os componentes.

**6.** A Z-API dava erro 400 de "client-token not configured". Identifiquei que faltava o token de segurança e pedi pra adicionar a variável ZAPI_CLIENT_TOKEN no .env e em todas as chamadas da API.

**7.** O modal da Z-API tinha botões brancos com fundo branco — não dava pra ler. Pedi pra corrigir o contraste e remover a mensagem técnica "Credenciais armazenadas no servidor (.env). Nunca expostas no frontend." que não serve pro gestor.

**8.** Ao clicar em "Enviar via ZAPI" aparecia "Enviado!" mesmo sem estar conectado. Pedi verificação de status antes de enviar com mensagens de erro claras (WhatsApp desconectado, número inválido, etc).

**9.** Pedi pra colocar paginação na página de influenciadores porque a lista era enorme e travava a rolagem.

**10.** O detalhe do influenciador abria embaixo da tabela e o gestor não via. Pedi pra trocar por popup/modal que abre na frente da tela.

**11.** No calendário, o descarte de conteúdo salvava com status "descartado" — mas descartou, não precisa ficar no calendário. Pedi pra remover do calendário e salvar no histórico de aprendizado.

**12.** A nota/score dos conteúdos estava exposta pro gestor (Score: 8.2/10). Pedi pra remover — o gestor não precisa ver nota, só precisa ver o conteúdo pronto pra aprovar.

**13.** A geração de conteúdo era aleatória (plataforma e nicho sorteados com Math.random). Pedi pra usar os dados do dataset pra definir o mix semanal baseado nas melhores combinações reais.

**14.** O pipeline de conteúdo exigia nota 8 mínima e falhava sem mostrar resultado. Baixei pra 7 e pedi auto-retry de até 3 tentativas. Se mesmo assim não atingir, mostra as melhores disponíveis — o gestor sempre recebe resultado.

**15.** As mensagens geradas para influenciadores eram genéricas ("Sua performance está boa"). Pedi dados específicos do influenciador: engagement exato, comparação com benchmark do nicho, ações concretas e mensuráveis.

**16.** A mensagem do overlay de geração dizia "Pipeline IA: Rascunho → Crítica (nota mínima 7) → Roteiro final" — muito técnico pro gestor. Troquei por "Criando, avaliando e refinando conteúdos para a próxima semana".

**17.** Pedi pra dar opção de personalizar a mensagem gerada pela IA antes de enviar pro WhatsApp (textarea editável + campo de telefone + dois botões: wa.me e ZAPI).

**18.** O header mostrava "ZAPI" — troquei por "Conectar WhatsApp" que é mais claro pro gestor.

**19.** Pedi pra adicionar as recomendações baseadas no dataset na Visão Geral (onde investir, o que evitar, melhores dias e horários), além dos conteúdos pendentes de aprovação.

**20.** A análise de perfil via Apify tratava link de perfil como link de post (dava "Post does not exist"). Pedi normalização pra distinguir perfil vs post e fluxo de coleta dos últimos 5 posts do perfil.

**21.** A IA implementou a análise de perfil como assíncrona com polling, mas o Next.js matava o processo background antes de completar — a chamada nem chegava no Apify. Identifiquei o problema e mudei pra síncrono: a API aguarda o Apify terminar e retorna tudo de uma vez. O frontend mostra aviso "Não saia desta página durante a análise" enquanto coleta os dados.

**22.** Pra tornar a espera da análise mais agradável (que pode levar até 1 minuto), pedi um mini-game Double Jump com temática G4 (cores laranja/navy, troféu G4 no final) que o gestor pode ativar/desativar enquanto aguarda.

**23.** Adicionei disclaimer de honestidade em todas as seções que faziam recomendações absolutas: troquei "SIM para micro" por "Tendência positiva", "Parar de investir" por "Menor performance relativa — monitorar", e "Não é necessária estratégia localizada" por "Os dados não permitem concluir".

---

## PARTE 6 — O que a IA errou e eu corrigi

| Erro da IA | Minha correção |
|------------|----------------|
| Apresentou diferenças de 0.1% como insights acionáveis | Forcei disclaimers + badges de significância |
| Criou 9 tabs por hipótese técnica | Reorganizei para 6 tabs por pergunta do gestor |
| Geração de conteúdo 100% aleatória | Exigi mix baseado nos dados reais do dataset |
| Sugeria Google Sheets para tempo real | Questionei a fonte real — defini Apify |
| Score exposto na interface pro gestor | Removi — gestor vê conteúdo, não nota |
| Mensagens de influenciador genéricas | Refatorei prompt com dados específicos + benchmark |
| Gráfico de campanhas confuso | Troquei por explorador interativo com filtros |
| Botão ZAPI enviava "sucesso" sem verificar conexão | Forcei verificação de status antes do envio |
| Frontend todo sem acentos | Busca completa e correção manual |
| Substituição global de "pp" por "%" quebrou palavras | Identifiquei o erro (app→a%), corrigi |
| Link de perfil tratado como link de post no Apify | Pedi normalização e fluxo diferente por tipo |
| Análise de perfil assíncrona não funcionava (Next.js matava o processo) | Identifiquei o bug e mudei para síncrono com aviso para não sair da página |

---

## PARTE 7 — O que eu adicionei que a IA não faria sozinha

1. Análise crítica do próprio output — reli a v1 com olhar crítico
2. Pesquisa externa (artigo Anthropic + Don Woodlock) para fundamentar o pipeline
3. Validação multi-ferramenta (Claude Code + ChatGPT Codex + Antigravity)
4. Honestidade intelectual nos disclaimers
5. Histórico de aprendizado (descartados alimentam próximo ciclo)
6. Explorador interativo de patrocínio em vez de gráfico estático
7. Geração baseada no dataset, não aleatória
8. Mini-game para experiência do gestor durante espera
9. Sistema assíncrono com polling para análise de perfil
10. Normalização de input que aceita qualquer formato (@user, URL perfil, URL post)

---

**Documentado em:** 2026-03-21
**Autor:** Vinicius Landare
