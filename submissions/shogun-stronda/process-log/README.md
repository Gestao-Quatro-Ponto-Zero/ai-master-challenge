# Process log

Ferramenta principal: **Claude Code** (CLI, modelo Claude Opus), no terminal, com acesso ao repositório, Python e navegador headless (`playwright-cli`).

Evidências nesta pasta, na ordem em que foram produzidas:

| Arquivo | O que é |
|---|---|
| `eda.py` → `eda-output-1.txt` | EDA 1: volumes, nulos, taxa de ganho por todo recorte, ciclo |
| `eda2.py` → `eda-output-2.txt` | EDA 2: curva de sobrevivência, idade dos abertos, vendedor x produto |
| `eda3_sinais.py` → `eda-output-3-sinais.txt` | Caça a sinais fora da amostra depois que a v1 falhou |
| `eda-output-4-regioes.txt` | Por que o Centro-Oeste não tinha nenhum deal quente |
| `critica.md` | Revisão do crítico independente e a resposta a cada finding |
| `screenshots/` | A ferramenta rodando (v3) |
| git log da branch | Histórico de commits |

Rodar as EDAs: `cd solution/data && python ../../process-log/eda.py` (idem `eda2.py`); `cd solution && python ../process-log/eda3_sinais.py`.

## Workflow

1. **Ler antes de abrir ferramenta.** Repo clonado; brief, CONTRIBUTING, guia e template lidos; dataset baixado do Kaggle. Pedido do Head de RevOps anotado: "o vendedor abre e sabe onde focar", "entender por quê", "precisa funcionar".
2. **EDA antes de modelar.** O Claude escreveu os scripts, eu li os números:
   - taxa de ganho ~63% **plana** em produto, setor, região, porte, manager;
   - nenhum deal fechou depois de **138 dias**, mas **1.291 de 1.589** em Engaging (81%) estão abertos há mais que isso;
   - 1.425 abertos **sem conta**;
   - `GTXPro` no pipeline vs `GTX Pro` no catálogo; setor `technolgy`.
3. **v1 = o que qualquer LLM faria.** Score ponderado: taxa vendedor x produto + taxa da conta (log-odds com shrinkage bayesiano) + valor + momento. Já com backtest temporal embutido.
4. **v1 falhou.** AUC 0,504 fora da amostra; calibração plana (o quintil "74%" fechou 64%).
5. **Caça a sinais** (`eda3_sinais.py`): mais 8 hipóteses. Só o tempo mostrou algo: deals que passam de 14 dias fecham +5 p.p., estável entre treino e teste.
6. **v2.** Chance pela curva de sobrevivência + gate de AUC para atributos + urgência. App HTML + JS puro. Testado no navegador (desktop, gaveta, abas, filtro, mobile 390px sem scroll horizontal).
7. **Achado regional** (`eda-output-4-regioes.txt`): **todos os 500 Prospecting são do Centro-Oeste** e só 5 Engaging dele estão vivos. Virou recomendação.
8. **Crítico independente.** Sub-agente sem acesso ao meu raciocínio, instruído a reprovar. Reproduziu todos os números a partir dos CSVs crus e deu **6/10**. Achado principal: a chance temporal, testada como ordenador por snapshot (deals abertos no corte, com a idade daquele dia), também fica em AUC 0,50 a 0,55, ou seja, não passaria no meu próprio gate. Mais 13 findings ([`critica.md`](critica.md)).
9. **v3.** Probabilidade saiu do score. `Score = Valor (60) + Momento (40)`. Ação depende só do momento (resolve "ticket baixo nunca é prioridade"). Novo estado "reta final" (90 a 138 dias). Prospecting e zumbis com chance "desconhecida". Backtest por snapshot em 3 cortes com IC por bootstrap. Correções de CSV, persistência, acessibilidade.
10. **Reais e redesign** (pedido do usuário depois da v3). Conversão US$ → R$ pela PTAX de venda do Banco Central de 05/11/2026, buscada na API oficial (`olinda.bcb.gov.br`) e fixada no código; só trocar o símbolo deixaria os números errados. Nomes de setor traduzidos. Interface refeita com a skill `design-taste-frontend`: o índigo antigo lia como "roxo de IA" e virou cobalto como acento único; fonte Geist; abertura em uma frase; fila dos 5 primeiros; métricas sem caixa; gaveta com fundo escurecido e foco preso. Teste de navegador pegou dois problemas: o texto "faltam 0 dias" no dia 138 (virou "hoje é o último dia") e o destaque permanente num KPI sem filtro.
11. **Nomes e regiões brasileiros** (pedido do usuário). Os 35 vendedores, 6 managers e 3 regiões ganharam nomes brasileiros por um mapa 1:1 em `solution/data/nomes_br.csv` (Central → Centro-Oeste, East → Sudeste, West → Sul). Os CSVs originais não foram tocados: a troca acontece no `load()` e um teste garante que o mapa é 1:1, cobre todo o time e não deixa primeiro nome repetido (os motivos usam o primeiro nome). As contagens por região antes e depois são idênticas. Os arquivos `eda-output-*.txt` mantêm os nomes originais porque são o registro bruto da análise.
12. **Animações e seletores customizados** (pedido do usuário). Skill `motion-design`: personalidade Corporate (140/240/400 ms, curva `cubic-bezier(.2,0,0,1)`, entrada desacelerada, saída acelerada, cascatas abaixo de 500 ms). Cada movimento tem função: entrada em cascata mostra a hierarquia; contadores mostram que o número mudou ao filtrar; indicador de aba desliza; gaveta, barras e score se montam em sequência; um único movimento contínuo, o pulso no chip "Contato urgente". Tudo desligado sob `prefers-reduced-motion` (testado: valores finais corretos, sem animação). Os `<select>` nativos viraram um componente próprio (`CustomSelect`) com padrão ARIA listbox: setas, Home/End, PageUp/PageDown, digitar para pular ("ca" → Camila), Enter, Esc, Tab, clique fora, abre para a esquerda se faltar espaço. O teste no navegador pegou dois bugs antes do commit: fonte de 11 px herdada pelo texto do botão e, no mobile, a lista aberta ficando atrás das métricas (o `backdrop-filter` do topo prendia o z-index).
13. **Rolagem e hover** (pedidos do usuário). A lista do seletor ganhou trilho de rolagem próprio (pílula cobalto, arrastável, sincronizado com teclado, sombra de "tem mais" nas bordas), porque a barra nativa é ignorada no macOS e invisível em vários navegadores; o resto do app usa barras nativas estilizadas com as mesmas cores. Hover em todo elemento clicável: botões sobem 1 px, cards sobem 3 px com score e produto em cobalto, linha da tabela ganha barra cobalto à esquerda, seletores, abas, métricas, ícone de tema, link com seta. "Como o score funciona" abre com cascata item a item. Um bug achado no teste: a animação de entrada com `fill-mode: both` travava o `transform` e anulava o hover dos cards; trocado para `backwards`.
14. **Terceiro crítico (motion + seletores): 7/10.** Os 10 achados foram corrigidos e verificados no navegador: indicador de aba com `ResizeObserver`; foco mantido após clicar em métrica e em "Mostrar mais" (vai para a primeira linha nova); só 12 linhas novas animam; crossfade de tema restrito às superfícies; seletor de ação anuncia o valor ao leitor de tela; busca não repete a cascata; repetir a letra percorre os nomes e digitar no botão fechado abre a lista; opções sem cascata; pulso do chip para após 3 ciclos; clicar fora devolve o foco ao seletor.
15. **Verificação final.** 17 testes; navegador de novo; cada número dos docs conferido com a saída do código (`docs/validacao.md` é gerado, não escrito à mão).

## Onde a IA errou e como corrigi

| Erro | Como percebi | Correção |
|---|---|---|
| v1: score por atributos que não preveem nada | Backtest temporal + calibração | Descartado |
| v2: "chance temporal" validada só em deals fechados, nunca como ordenador | Crítico independente (snapshot backtest) | Backtest por snapshot em 3 cortes no código; probabilidade fora do score |
| v2: "Fechar esta semana" impossível para 3 dos 7 produtos | Crítico: aritmética do limiar 70 | Ação vem só do momento + teste |
| v2: Prospecting com 63% de chance sem nenhum dado, inflando o forecast em R$ 3,7 mi | Crítico | Chance e valor esperado `None` + teste |
| Off-by-one na curva (aberto há `a` dias ⇒ ciclo ≥ `a+1`) | Crítico | `survival[age+1]` + teste |
| Join de produto quebrado (`GTXPro`) | EDA | `PRODUCT_FIX` + `load()` falha alto se aparecer produto desconhecido |
| "Medical. receita" (troca de `,` por `.` na frase toda) | Screenshot | Formatar só o número + teste com regex |
| Um exemplo no `logica.md` afirmava que um MG Special urgente ficava acima de deals caros. Falso (40 vs ~70) | Conta conferida por script antes do commit | Trocado por exemplo verdadeiro (GTX Pro 83 vs 68, igual à tela) |
| `submissions/` ignorado pelo `.gitignore` do repo | Crítico | `git add -f` só da pasta, `.gitignore` local para artefatos |

## O que eu adicionei que a IA sozinha não faria

- **Desconfiar do número bonito duas vezes.** A v1 e a v2 davam motivos convincentes. As duas caíram em teste. Mandar ao vendedor um "78% de chance" que não se sustenta é pior que não ter número.
- **Crítico adversarial na própria entrega**, com instrução de reprovar, e refazer o modelo quando ele achou o furo, em vez de defender a v2.
- **Ação separada de ordem.** Ação pelo momento (o que fazer hoje), score pelo valor (por onde começar).
- **Linguagem calibrada.** "Verificar no CRM", não "encerrar". Os dados não distinguem deal morto de registro desatualizado.
- **Stack pelo usuário final.** Streamlit exigiria Python na máquina do vendedor. HTML estático abre em qualquer lugar.

## Iterações

- Modelo: 3 versões (v1 e v2 descartadas por evidência).
- App: 3 rodadas (build, screenshot, crítico).
- Testes: 12 → 17 → 18 (reais) → 19 (nomes brasileiros).
