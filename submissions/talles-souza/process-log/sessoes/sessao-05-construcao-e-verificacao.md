# Sessão 05 — Desenho final, construção e verificação (E3, E4 e E5)

**Data:** 2026-10-22 e 2026-10-23 · **Ferramentas:** Claude Code (Claude Opus 5.5) como coordenador; workers do Orca para a construção; subagentes para revisão de código, segurança e documentação · **Etapas:** E3 construir, E4 verificar, E5 documentar

## Problema

O enunciado pede "uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar", que "precisa funcionar", com lógica de priorização que "não é só ordenar por valor" e em que "o vendedor precisa entender por que um deal tem score alto ou baixo". O que foi medido da sessão 02 à 04 mostrou que, neste dado, só a idade do negócio separa o desfecho.

**Critério de aceite:** a ferramenta roda num comando com os dados reais; cada número da tela vem de uma regra testada contra o `deals.json`; o vendedor vê grupo, motivo e próxima ação de cada negócio; a verificação é rodada pelo coordenador, não aceita pelo relatório de quem construiu; cada número do README é reproduzível a partir do repositório.

## O desenho final e o porquê

| Decisão | Por quê (enunciado e dado) |
|---|---|
| **A tela inicial é do vendedor:** "Quem é você?" e depois "Onde focar hoje", com os negócios abertos dele | "o vendedor abre isso na segunda-feira de manhã. O que ele precisa ver?" |
| **Grupos pela idade:** Foque agora 41–60 d, Siga no ritmo ≤ 40 d, Ainda não começou (sem data), Nutrição > 60 d | É o único atributo que separa: no replay de 30/09/2017, 50,2% (≤ 40 d), 26,6% (41–60 d), 2,6% (> 60 d) ganharam até 31/12 (`evidencias/curva-fina.txt`). O Foque é a faixa que ainda fecha mas está esfriando: "deixam oportunidades boas esfriar" |
| **Ordem Foque → Siga → Ainda não começou → Nutrição** | O Foque acima do Siga é suposição declarada: o efeito de agir não foi medido, porque o dataset não registra ações |
| **Indicador "{chance} em 10" com uma frase do motivo** | "Explainability ganha." Um número e o porquê em linguagem de vendedor, em vez de uma nota sem contexto |
| **Receita esperada** (chance da faixa × preço de tabela) ordena dentro do grupo e soma no topo | "não é só ordenar por valor": o valor ordena só dentro do grupo, e a idade decide o grupo. Nos ganhos, `close_value` ≈ preço de tabela (razão média 0,996) |
| **Comissão opcional, digitada pelo vendedor** | O vendedor quer saber quanto deve coletar; o dataset não tem comissão, então nenhum percentual é sugerido |
| **BANT ancorado no dado:** T = idade, B = preço como contexto, A/N/próximo passo = perguntas de sim ou não | O dataset não tem coluna de decisor, dor nem próximo passo. Perguntar ao vendedor é o único jeito honesto de cobrir essas letras |
| **"Não" muda só a ação, nunca o grupo** | Mover por resposta tiraria da fila um negócio que ainda fecha (Siga, 5 em 10). O motor recusa um método que tente mover |
| **Nutrição recolhida, com "Encaminhar os {n}"** | É a maioria dos abertos (1.532 de 2.089); aberta, esconderia o Foque. Encaminhar exige confirmação e grava uma decisão por negócio |
| **Acompanhar a equipe:** painel só leitura, filtros por vendedor, manager e região, sem ranking e sem botão de ação | "Bonus: filtro por vendedor/manager/região". Sem ranking porque o vendedor não prevê ganho fora da amostra (AUC 0,522); sem ação porque quem age é o vendedor |
| **Os 35 vendedores sempre visíveis**, inclusive os 8 com zero abertos | O time do enunciado tem 35; esconder quem não tem negócio aberto daria uma equipe que não existe |
| **API fina + modo local no navegador** | "API que recebe dados de um deal e retorna score + explicação" é um formato válido do enunciado, e o modo local garante que a fila continue se a API cair |
| **Banco compartilhado opcional, com papel restrito** | Sem banco, as respostas ficam no navegador. Com banco, chegam ao painel e a outros aparelhos; o papel só lê os negócios e só acrescenta respostas e decisões |
| **"Hoje" = 31/12/2017** | Último fechamento do dataset; o enunciado não fixa data, e contar até a data real daria anos para todos |

## A construção

1. **Fatias verticais.** Cinco contextos (`pipeline`, `organizacao`, `qualificacao`, `score`, `priorizacao`), cada um com domínio em TypeScript puro sem I/O, rotas na API, telas na web, testes e um documento em `solution/docs/contextos/`. Um script (`scripts/checar-fronteiras.mjs`) recusa um contexto que importe o interno de outro e um domínio que faça I/O. A política (limites, textos, ações) e o método (as perguntas) são arquivos de configuração: trocar um não toca no motor, e há teste disso.
2. **Ondas com workers em paralelo.** Primeiro o esqueleto e as interfaces públicas de cada contexto, escritos pelo orquestrador do build. Depois três workers do Orca em paralelo (domínio, API, web), cada um com spec em arquivo. Depois integração, revisão independente, E2E e documentação. Uma terceira onda acrescentou receita esperada, comissão, Nutrição em lote, os 35 vendedores, o painel da equipe, o banco e a saída para a Vercel. Uma última corrigiu os achados da verificação.
3. **Resiliência real, onde há dependência.** No cliente web: retry com backoff e jitter (3 tentativas), disjuntor (abre com 3 falhas, 15 s), timeout que cobre cabeçalho e corpo, e queda para o modo local, que calcula com o mesmo domínio sobre o mesmo `deals.json` conferido por SHA-256. Na API: validação de entrada, rate limit com 429 e `Retry-After`, limite de payload, timeout, cabeçalhos de segurança, checagem de `Host`. No banco: SQL só de leitura e inserção; se o metadado do banco não bate com o `deals.json`, a API usa o arquivo; se o banco cai, grava na memória. Cada proteção tem teste ([`solution/docs/resiliencia.md`](../../solution/docs/resiliencia.md)).
4. **Revisão independente** por dois subagentes só de leitura (TypeScript e segurança): 4 achados altos (corridas na tela do negócio, rejeição sem tratamento, timeout que não cobria o corpo, disjuntor sem geração) e vários médios. Todos os altos corrigidos com teste de regressão; os médios que ficaram estão nas Limitações.
5. **E2E com vídeo.** Playwright grava um vídeo por fluxo em `solution/e2e/videos/`: a segunda-feira do vendedor até a decisão guardada, a API derrubada com a fila continuando no modo local, o painel com o filtro por região mudando os números, a receita esperada e a comissão, a Nutrição recolhida e o encaminhamento, o vendedor sem negócio, a Central sem foco, as datas no formato brasileiro, "Como a nota funciona" e "Novo negócio", e 390 px sem rolagem horizontal, no desktop e no celular.

## A verificação feita pelo coordenador (E4)

Rodado por mim depois do "terminei" dos workers, entre 02:05 e 02:35 UTC de 23/10:

| Item | Resultado |
|---|---|
| `npm test` (fronteiras, typecheck, lint, domínio, API, web, dados) | verde: domínio 88, API 65 (+3 que só rodam com banco), web 86, dados 11. Rodado de novo na E5 com o mesmo resultado |
| Integração com o banco real (`apps/api/test/banco.test.ts`) | 10 de 10, gravando dentro de uma transação desfeita; o banco ficou com 0 respostas e 0 decisões |
| `npm run test:e2e` | 11 de 11, com vídeo |
| Credenciais no repositório (`git grep` por strings de conexão e chaves) | 0 |
| Saída de build da Vercel versionada | não |
| Seletor "Quem é você?" | 35 vendedores, por escritório e manager |
| Telas olhadas no `npm start` (um vendedor da Central, um do West e o painel) | fila, receita, grupos e painel com filtros conferidos |
| Números de referência | Foque 30 · Siga 27 · Ainda não começou 500 · Nutrição 1.532; receita esperada US$ 46.487; backtest US$ 1.284.794 previstos × US$ 1.251.928 realizados |

Os achados da E4 viraram uma rodada de ajustes de interface, cada uma num commit: card de "Ainda não começou" mais enxuto; "quase nada" quando a receita arredonda abaixo de US$ 1; a ordem dos grupos; datas em dd/mm/aaaa; o rodapé e o painel dizendo onde ficam as respostas (banco da equipe ou só neste navegador).

**E5, evidência reprodutível.** Os números da Lógica que vinham de scripts da esteira estão agora em `process-log/scripts/`, com os caminhos por argumento, e foram rodados de novo a partir do repositório. Todos bateram com os números citados:

| Número | Script → saída | Reexecução |
|---|---|---|
| curva por faixa; 50,2% · 26,6% · 2,6%; 27 · 30 · 1.532 · 500 | `curva_fina.py` → `curva-fina.txt` | bateu (saída idêntica à original) |
| AUC 0,759 (3 grupos), 0,767 (8 faixas), 0,483 (ingênuo), 0,488 (preço); 4,7% nos 61–138 d | `auc_faixas.py` → `auc-faixas.txt` | bateu (idêntica) |
| pontos do perfil 0,95–1,04, vendedor 0,87–1,11, idade 0,00–2,23; 6.711 fechados com conta | `metodo_hubspot.py` → `metodo-hubspot.txt` | bateu (o eixo da idade foi acrescentado ao script; as linhas de perfil são idênticas) |
| US$ 46.487; backtest US$ 1.284.794 × US$ 1.251.928; 637 de 1.196 | `receita_esperada.mjs` → `receita-esperada.txt` | bateu (idêntica) |
| 0,691 em outro corte; 0,495 só entre os que fecharam; 0 de 647 sem conta fecharam | `idade_robustez.py` → `idade-robustez.txt` | bateu (idêntica) |

## Onde desconfiei e conferi

- **O Foque estava no lugar errado no primeiro rascunho.** A ideia intuitiva era pôr no topo o que está "perto do limite" (61 a 138 dias), prestes a esfriar. No backtest, essa faixa ganhou 4,7% (31 de 655), contra 50,2% dos de até 40 dias: perto do limite, já esfriou. A curva fina, por faixas de 10 dias, mostrou que a chance fica plana até 40 dias e cai a partir daí. O Foque ficou em 41 a 60 dias.
- **O número de benefício era de outro corte.** O revisor da fase de arquitetura apontou que o AUC citado como benefício (0,753) era de 4 faixas de uma medição anterior, não dos grupos em uso, e que o texto não dizia o que ele mede. Rodei com os grupos e as 8 faixas da ferramenta, com previsão gravada antes: 0,759 e 0,767 nos 1.879 abertos em 30/09 com até 138 dias, alvo "ganhou até 31/12", rotulado como dentro da amostra.
- **A receita esperada não é a receita do trimestre.** Medido antes de escrever o texto da tela: dos 1.196 ganhos do 4º trimestre de 2017, 637 vieram de negócios que entraram depois de 30/09. O topo da tela diz "Dos seus negócios abertos hoje" e "Não conta negócios novos que vão entrar".
- **Valor = preço de tabela, mas não exatamente.** A previsão era que `close_value` fosse igual ao preço em todos os ganhos. Errou: 4.021 de 4.238 diferem em mais de US$ 1, com razão média 0,996. O preço de tabela continua como valor, com a mediana 1,0 citada, e a tela o chama de "Preço de tabela".
- **O "Não" de uma pergunta não muda o grupo, e agora isso é garantido.** Uma frase de ação dizia "Sem data, o negócio vai para nutrição", o que o motor não fazia; e só a configuração impedia uma resposta de mover o negócio. Mover tiraria da fila um negócio que ainda fecha. O motor passou a recusar esse efeito, um teste responde "Não" e "Sim" às 3 perguntas dos 2.089 abertos e confere que nenhum muda de grupo, e a frase virou "Proponha uma data agora. Sem data marcada, a chance continua caindo."
- **Arredondamento contra a frase.** Na faixa de 61 a 90 dias, 6,7% arredondava para "1 em 10", ao lado de "menos de 1 em cada 10 fechou". Agora a tela e a tabela de "Como a nota funciona" mostram "menos de 1 em 10", com teste.
- **Arquivos novos fora dos commits.** O `.gitignore` do repositório ignora `submissions/`, então um `git add -A` não pega arquivo novo e não avisa. Dois commits saíram sem 3 arquivos. Corrigido nos commits seguintes; dali em diante, `git add -f` em todo arquivo novo e conferência da lista de ignorados.
- **E2E 8 de 9 na primeira rodada.** Isolado, o teste passava. Contei 6 respostas 429 no log do servidor: todos os fluxos saem do mesmo IP e passam do limite de taxa. O limite foi relaxado só no servidor do E2E, com comentário, e continua testado nos testes de proteção da API.
- **O E2E e os testes não podem sujar o banco.** O servidor do E2E sobe sem `DATABASE_URL`, mesmo que a variável exista no ambiente, e a integração com o banco grava dentro de uma transação desfeita. Conferido no banco depois: 0 respostas e 0 decisões.
- **Tempo reproduzível.** O revisor do portão final só conseguiu reproduzir os números cortando as transcrições no instante da medição, porque elas continuam crescendo. O script ganhou `--ate <ISO>`, e a evidência traz o comando com o corte e os 4 arquivos da sessão principal.
- **Tempo ativo com os workers.** Uma medição anterior dizia não incluir os workers, que teriam gravado em outra pasta de projeto. Conferi pelo campo `cwd` de todas as transcrições modificadas no período: nenhuma fora da pasta deste projeto trabalhava nele, e as dos workers estão na mesma pasta. A medição final inclui todas.

## Horas

O tempo declarado é o tempo ativo da sessão principal, medido no fim do trabalho: ver a seção "Tempo" do README da submissão.

## Próximo passo

O motor de pontos, o score e o painel do manager ([sessão 06](sessao-06-motor-score-e-verificacao.md)).
