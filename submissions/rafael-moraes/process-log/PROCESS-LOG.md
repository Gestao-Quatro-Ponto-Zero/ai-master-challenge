# Process Log — como usei IA

**Início oficial:** 06/11/2026, 14:45 (quando os dados chegaram). Registro de tempo em `ACTIVITY-LOG.csv`; decisões em `DECISIONS.md` (25 decisões, com data, opções e motivo).

## Ferramentas

| Ferramenta | Para quê |
|---|---|
| ChatGPT | Leitura inicial do desafio e primeiro plano de trabalho (antes do início oficial) — `chat-exports/chatgpt-planejamento-inicial.txt` |
| Claude (chat de execução, num projeto com instruções "seja crítico, não invente números") | Revisão do plano do ChatGPT, análise de dados em Python, construção e testes do protótipo, documentação |
| Claude (chat separado, fora do projeto) | **Teste de baseline:** o que uma IA entrega sozinha com o pedido simples — `baseline/` |
| Claude (chat auditor, sem acesso ao raciocínio do chat de execução) | **Auditoria adversarial:** tentar derrubar a entrega, 48 tickets difíceis, conferência de fontes — `auditoria/` |
| Python (pandas, scipy, scikit-learn) | Inspeção, testes estatísticos, classificador |
| Node.js + Playwright | Teste de paridade Python × JavaScript, testes de regressão e capturas de tela do protótipo |

## Como dividi o trabalho

Eu decidi; a IA executou e propôs opções. Cada decisão minha está no `DECISIONS.md`. As que partiram de mim, e não de uma sugestão da IA: lista vermelha para risco de cancelamento (10), suporte a português (12), perguntas simples ao cliente sem perguntar urgência (14), pergunta de impacto em falhas (16), tag de atraso para chamado esquecido (18), fluxo de cancelamento que entende se o cliente já decidiu (19) e "todo mundo pode pedir prioridade, mas o que define é o caso" (22).

## Linha do tempo

1. **Plano (ChatGPT → Claude).** Levei o plano do ChatGPT para o Claude e pedi uma revisão contra o repositório. Correções: a pasta `submissions/` é ignorada pelo `.gitignore` do G4 (precisa de `git add -f`); a branch e o título do PR têm formato obrigatório; o ChatGPT recomendava **não** cruzar os datasets, mas o briefing avalia justamente o cruzamento; 6 chats especializados era estrutura demais para 4–6 h. Fiquei com 2 chats: execução e auditor.
2. **Inspeção dos dados (14:45).** Antes de qualquer gráfico: Dataset 1 tem 8.469 linhas (não ~30 mil), textos com `{product_purchased}`, horários numa janela de 27 h, 49% de resoluções antes da primeira resposta, tudo uniforme. Decisão 4: responder ao Diretor provando o que os dados sustentam e o que não.
3. **Diagnóstico.** Testes estatísticos e de permutação. A IA propôs 5 achados; escolhi 3 e a IA apontou uma incoerência na minha escolha (eu queria priorização de tickets sem incluir o achado que a justifica). Reformulamos juntos (decisão 6).
4. **Premissas de custo.** Dei minhas estimativas (2–4 min de triagem, 2–5 min por reencaminhamento) e pedi fontes. A IA trouxe referências, descartou estatísticas de blogs de fornecedores e separou esforço do atendente (meus minutos) de tempo perdido por quem abriu o chamado (~40 min, HappySignals — estimado por usuários de TI interna, não clientes).
5. **Teste de baseline.** Abri um chat novo, colei o briefing e o CSV com um pedido simples. Resultado: a IA sozinha **também percebeu** os dados sintéticos — então isso não é diferencial. Lendo o código dela: calculou durações com o campo que ela mesma declarou inválido, considerou 100% da triagem automatizável e usou R$ 35–60/h sem fonte (chegou a R$ 201 mil/ano contra ~R$ 21,8 mil nosso). Ela teve duas ideias boas que eu incorporei com crédito (decisão 11): viés de sobrevivência na satisfação e coletar dados na abertura do ticket.
6. **Automação e limiar.** Escolhi 80% de confiança (90% para a categoria mais arriscada) e a lista do que nunca automatizar, acrescentando risco de cancelamento.
7. **Protótipo — 8 versões publicadas.** A maioria nasceu de um teste ou ideia minha (ver abaixo).
8. **Auditoria adversarial (16:50).** Mandei a entrega para um chat novo com o pedido de derrubá-la. Ele refez os números (bateram), confirmou que a fila de demonstração não foi escolhida a dedo e encontrou falhas reais em casos sensíveis, prioridade e premissas. A IA de execução triou cada crítica em corrigir, declarar ou discordar; eu decidi 4 pontos novos (21–24). Uma crítica estava errada: o auditor leu outro artigo da fonte dos 40 min.
9. **Auditoria fase 02 (17:16).** Exigi uma segunda fase antes de enviar. Resultado: "pronta com ressalvas", notas 5 a 7 por critério. Os números bateram em todos os documentos e o auditor reconheceu o próprio erro sobre a fonte dos 40 min. Mas, em 45 tickets inéditos, as regras novas erraram dos dois lados ("vazamento de memória" virou incidente de segurança P1; "quero desistir da assinatura" escapou) — elas tinham sido ajustadas às palavras dos testes da fase 01. Decidi **parar de ajustar regra por regra** (decisão 25): declarar o limite, medir o piso de erro (≥ 23% dos desvios), corrigir a seção do Diretor que vendia o número de TI como se fosse da operação de clientes, e medir quanto histórico rotulado a empresa precisa (curva de aprendizado).
10. **Auditoria fase 03 (17:29) — consolidação.** Sem tickets novos: o auditor verificou byte a byte que as regras não mudaram desde a fase 02 (a decisão 25 foi cumprida), conferiu que os quatro scripts produzem os números da entrega e subiu as notas (5–7 → 6–8). Restaram três ressalvas: preencher meus campos, corrigir três frases do README que prometiam mais do que foi medido ("acerta" em vez de "volume", "em qualquer cenário", histórico "já são os rótulos" sem auditar) e alinhar números antigos no Process Log e no protótipo — feito.
11. **Documentação e submissão.**

## Onde a IA errou e como corrigimos

| Erro | IA | Quem percebeu | Correção |
|---|---|---|---|
| Recomendou não cruzar os datasets; não viu o `.gitignore` | ChatGPT | Claude, lendo o repositório | Cruzamento por papéis; `git add -f` |
| Previu que a IA sozinha cairia no ruído | Claude | Meu teste de baseline | Diferencial redefinido: coerência, protótipo medido, julgamento |
| Calculou tempos com campo inválido; 100% de automação; custo sem fonte | Claude (baseline) | Claude (execução), lendo o código | Nossa análise usa status; 60,8% medidos com as regras; R$ 20/h com fonte |
| Regra "Administrative rights sempre vai para pessoa", pelo nome da categoria | Claude | **Meu teste** com 3 tickets em português (todos caíram no vermelho) | A categoria é suporte a software; regra passou a olhar pedido de privilégio |
| Glossário traduzia "problema" e "quero" para palavras que puxavam categorias | Claude | **Meus testes** | Palavras genéricas não são mais traduzidas |
| "Quero cancelar!" escapava da Retenção (regra fora de ordem) | Claude | **Meu teste independente** | Ordem fixa + testes de regressão |
| Cor misturava urgência e quem age | Claude | **Eu**, pensando no atendente | Cor = prioridade; rótulo = quem age |
| "Cancelar a reunião" iria para a Retenção | Claude | Claude, ao analisar meu print | Exclusão de reunião, agenda, convite |
| Assédio recebia questionário automático; phishing e vazamento iam com a IA | Claude | **Auditoria** | Filas de Ouvidoria e Segurança (decisão 21) |
| "URGENTE!!! trocar o papel de parede" virava P2; manutenção programada virava P1 | Claude | **Auditoria** | Só fatos sobem a prioridade (decisão 22) |
| Dois assuntos anulavam o cancelamento; "encerrar conta" ia para a TI | Claude | **Auditoria** | Checagem por ocorrência e termos novos |
| Cobertura de 64,4% ignorava os tickets desviados pelas regras | Claude | **Auditoria** | Recalculada com as regras: 60,8% |
| "Correção entra no próximo treino" era falso no protótipo | Claude | **Auditoria** | Texto corrigido |
| Disse que a fonte dos 40 min dizia 1h46 | Claude (auditor) | Claude (execução), conferindo o artigo citado | Mantido 40 min; corrigido que a fonte mede usuários de TI, não clientes |
| As correções da fase 01 eram ajuste às palavras dos testes: falham em casos inéditos | Claude | **Auditoria fase 02** | Parar de ajustar; declarar o limite; classificador próprio para casos sensíveis em produção (decisão 25) |
| "6 em cada 10" na seção do Diretor era o número de TI, não da operação de clientes (~12%) | Claude | **Auditoria fase 02** | Seção reescrita; retorno marcado como hipótese |
| "Horas de espera" exagerava: a fonte mede tempo perdido estimado pelos usuários | Claude | **Auditoria fase 02** | Renomeado para "tempo perdido evitado (estimado pelos usuários)" |
| Números ajustados no caminho (86,5% → 86,1% com modelo mais leve; "350" → ~330 termos) | Claude | Claude | Documentos usam os números finais |

## O que eu adicionei que a IA sozinha não faria

A IA construiu rápido, mas pensava como quem analisa dados, não como quem vive a operação. Meu papel foi testar o sistema como atendente e como cliente, e mudar as regras quando algo não funcionaria no dia a dia.

- **Cancelamento nunca fica só com a máquina.** Perder um cliente custa mais do que qualquer ganho de velocidade. E, antes de tratar como perdido, o sistema pergunta: "a ideia é entender se ele realmente já decidiu ou se podemos resolver". Muitas vezes o cliente só está irritado.
- **Não se pergunta ao cliente se é urgente.** "Todo mundo pode pedir prioridade, mas o que define é o caso." Por isso as perguntas são sobre fatos: você consegue trabalhar? Quem mais foi afetado?
- **A cor precisa dizer o que resolver primeiro.** Na operação, o atendente olha a cor e age. Se vermelho significa "caso sensível" e não "urgente", ele se perde. Separei cor (prioridade) de rótulo (quem age), porque "não quero deixar o atendente perdido".
- **Chamado esquecido também é problema.** Criei a tag de atraso para "os atendentes filtrarem inclusive chamado relativamente simples, mas esquecido".
- **O cliente brasileiro escreve em português**, então o sistema tinha que aceitar.

Testando, encontrei erros que a IA não tinha visto: todos os meus chamados caíam no vermelho, e um "quero cancelar" passava direto pela máquina. Depois de duas auditorias, decidi parar de remendar regra por regra: corrigir cada frase que o auditor inventava seria decorar a prova. Preferi assumir o limite com honestidade e dizer o que resolve de verdade em produção.

_Este texto e o motivo da decisão 4 foram redigidos com ajuda da IA a partir das minhas decisões registradas no `DECISIONS.md`, e revisados por mim. Uso IA no meu trabalho todos os dias, minha evolução com ela tem sido constante, e nada me impede de me aperfeiçoar ainda mais — este desafio foi mais um passo._

## Evidências

- `DECISIONS.md` — 25 decisões com data, opções e motivo
- `ACTIVITY-LOG.csv` — tempo por fase
- `TESTE-INDEPENDENTE-PT.md` + `screenshots/` — meus testes do protótipo
- `baseline/` — pedido, resposta (PDF) e código da IA sozinha
- `auditoria/` — relatórios das fases da auditoria adversarial (PDFs)
- `chat-exports/` — planejamento no ChatGPT e o chat de execução no Claude
- Histórico de commits do repositório
