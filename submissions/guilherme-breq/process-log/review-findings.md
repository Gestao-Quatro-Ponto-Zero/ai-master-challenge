# Revisão independente: achados e o que foi feito

A revisão foi delegada a agentes do meu time no Maestri, rodando em paralelo enquanto eu escrevia a documentação. Os dois revisores eram **só leitura**: apontam, não editam. A triagem e as correções ficaram com o agente principal, e parte da UI foi implementada por um terceiro agente (Torno), com escopo de arquivos isolado.

## Esquadro: código, estatística e segurança

| # | Sev. | Achado | Ação |
|---|---|---|---|
| 1 | Alta | **Viés de seleção no backtest do momento:** o teste usava só deals que acabaram fechando, ou seja, escolhia a amostra com informação do futuro. Com todos os abertos, a AUC cai de 0,66/0,70/0,87 para ~0,60/0,54/0,71 | **Corrigido** (`analysis/06`). O alvo "decidiu em 30 dias" é conhecido para todo aberto, então o teste agora usa todos. Os números novos foram para a doc, inclusive o fato de que caíram |
| 2 | Alta | **A curva ignora censura:** foi estimada só com fechados, e os deals ainda abertos (em risco, sem decisão) ficavam de fora. Em jul/2017, previa 40,6% contra 9,7% observados | **Corrigido com Kaplan-Meier** no Python e no TypeScript, com teste que cruza as duas implementações. Calibração média: previsto 25%, real 26%. Efeito colateral valioso: a curva corrigida mostra que deals **esfriam** depois de ~100 dias, e isso virou o estado "esfriando" no app |
| 3 | Média | "589 zumbis" eram observações repetidas de 411 deals; "nenhum fechou" não prova chance zero | **Corrigido:** deduplicado, e o corte de 138 dias passou a ser descrito como heurístico |
| 4 | Média | Preço vazio ou inválido no catálogo vira 0 ou NaN e contamina a escala log | **Corrigido:** só preços finitos e positivos entram; produto sem preço é sinalizado ao vendedor; score sempre finito. Com teste |
| 5 | Média | Engajamento no futuro gera idade negativa; data inválida gera NaN | **Corrigido:** idade negativa vira 0 com aviso; data inválida vai para prospecção com aviso. Com teste |
| 6 | Média | Histórico vazio gera ciclo −∞ e taxa NaN; com poucos fechados, a curva vira 0% | **Corrigido:** o motor recusa histórico insuficiente com erro explícito. Com teste |
| 7 | Baixa | Horizonte inconsistente (`<=` na curva, `<` no alvo) | **Corrigido:** `<=` nos dois |
| — | — | Segurança: sem segredo ou `.env`; filtros, desempates e `use cache` sem achados | — |

## Retina: QA de interface (3 rodadas)

Feita com Edge via CDP (emulação de dispositivo), desktop a 1440px e mobile a 390px.

### Rodada 1: 11 achados

| # | Sev. | Achado | Status final |
|---|---|---|---|
| 1 | Média | Vendedor sem deal vivo (ex.: Darcel) caía num beco sem saída | Resolvido: estado vazio com botões "Limpar N zumbis" e "Engajar N em prospecção" |
| 2 | Média | Abas sem navegação por setas (WAI-ARIA) | Resolvido: roving tabindex com setas, Home e End |
| 3 | Média | Muito texto de 10–11px; cinza com contraste baixo | Resolvido: piso de 11px só para metadado e cinza clareado para ~5:1 |
| 4 | Média | Mobile: o 1º deal só aparecia depois de ~1000px de rolagem | Resolvido: filtros recolhidos e KPIs em faixa rolável. O 1º deal aparece a 677px |
| 5 | Média | Tabela do Time ilegível no mobile | Resolvido (Torno): cartões por vendedor |
| 6 | Baixa–média | Alvos de toque menores que 44px | Resolvido |
| 7 | Baixa | Jargão ("win rate", "AUC", "backtest") | Resolvido: "taxa de ganho", "deal prioritário" e nota explicada como "0,5 = cara ou coroa" |
| 8 | Baixa | Gráfico bonito, mas sem ajudar a decidir | Resolvido: faixas "cedo / decisão / esfriando" e linha do limite |
| 9 | Baixa | Empates repetitivos sem critério visível | Resolvido: critério explicado na aba e na doc |
| 10 | Baixa | "Conta não vinculada" em itálico como título | Resolvido (Torno): produto como título + selo "sem conta" |
| 11 | Baixa | Layout pulava quando a barra de rolagem sumia | Resolvido: `scrollbar-gutter: stable` |

### Rodada 2: 6 pontos novos

| # | Achado | Status |
|---|---|---|
| N1, N2 | Rótulos do gráfico colidindo (desktop) e ilegíveis (mobile) | Resolvido: versão compacta para o mobile e limite no topo da linha |
| N3 | Ações contraditórias em idades vizinhas ("reengajar" × "pedir decisão") | Resolvido: progressão explícita "reengajar antes que esfrie" → "forçar o sim ou o não", explicada na aba Janela |
| N4 | Cartões do Time sem a taxa de ganho | Resolvido |
| N5 | Busca não encontrava por ação | Resolvido |
| N6 | Mobile: 1º deal ainda a 795px | Resolvido (677px) |

### Rodada 3: confirmação

- **Overflow a 390px: nenhum.** O "texto cortado" de uma captura minha era artefato do Edge headless com `--window-size`.
- **3 detalhes resolvidos:** o 1º card de KPI colado na borda (`scroll-padding`), a barra de rolagem visível na faixa de KPIs e o selo "sem conta" truncando o produto no mobile.

## O que essa revisão mudou

O achado mais importante não foi de UI. Foi o **viés no meu próprio backtest**. A versão original reportava uma AUC de até 0,87 para o momento, e o número honesto é 0,65 em média. Um número inflado desse tipo é exatamente o que a submissão critica no baseline das IAs. A correção também revelou o achado de negócio mais útil para a Head de RevOps: **deals esfriam depois de ~100 dias**.
