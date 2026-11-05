# Fase 3d: testes da tela publicada (04/11/2026, 21:30–21:37)

**O que foi testado:** o app publicado em https://lead-scorer-liberato.lovable.app, nas versões do commit Lovable `7316dc5` (mensagem 2) e `396c42e` (mensagem 3), lendo o arquivo do motor da branch no commit `620101a`.

**Como foi testado:** pelo navegador embutido do app Claude no computador do Liberato, com scripts que leem o texto da página e acionam filtros e abas. O ambiente do Claude não consegue acessar `lovable.app` diretamente. Os valores esperados foram calculados **a partir do arquivo do motor**, de forma independente da tela. O painel do navegador estava minimizado, então cliques reais com o mouse não funcionaram, e os filtros e abas foram acionados por eventos de script.

| # | Teste | Esperado (motor) | Resultado na tela |
|---|---|---|---|
| 1 | Faixa histórica | "Dados históricos de demonstração: pipeline como estava em 31/12/2017. Não são dados atuais." | ✅ Texto idêntico. Fica **fixa**: depois de rolar 4.000 px, continua no topo (`position: sticky`) |
| 2 | Nenhum "hoje" ou "agora" na página | 0 ocorrências | ✅ 0 |
| 3 | Subtítulo (visão "Todos") | "Situação em 31/12/2017 · 2.089 deals abertos naquela data" | ✅ |
| 4 | Cartões de resumo | Foco 228, Requalificar 1.301, Iniciar 500, Automatizar 60; US$ 128.722; 354 para ligar | ✅ Todos |
| 5 | Abas com contagem | Foco (228), Requalificar ou encerrar (1301), Iniciar contato (500), Automatizar (60), Como a nota funciona | ✅ |
| 6 | 3 primeiros do Foco | 1LY8CAXD (nota 100, 22%), RDHTQLNI (99, 45%), FZWU2I30 (99, 42%) | ✅ Depois da correção da nota (ver o problema 4 no Registro 10) |
| 7 | "Porquê" do 1º deal idêntico ao do motor | O texto completo do motor | ✅ Idêntico |
| 8 | Aviso de empresa não cadastrada | Presente no 2º deal (sem empresa) | ✅ |
| 9 | Filtro Vendedor = Zane Levy | Foco 27, Requalificar 58, Iniciar 0, Automatizar 3; US$ 9.155; 1º = FZWU2I30, 2º = 4D0K5T7T, 3º = 4R4QF0ZU; 88 deals | ✅ Todos. A posição aparece como "1º", e o nome do vendedor some dos cartões |
| 10 | Lista vazia (Zane Levy, Iniciar contato) | "Nenhum deal nesta lista para este filtro." | ✅ |
| 11 | Cascata: Região = East | Gerentes: Cara Losch e Rocco Neubert; 12 vendedores; 433 deals | ✅ |
| 12 | Requalificar (visão "Todos") | 1º = A04V2WB3, com "Ligar para requalificar"; "Mostrar mais (1276 restantes)" | ✅ |
| 13 | "Como a nota funciona" | 47% (0 dias), 26% (90 dias), 138 dias, US$ 100, US$ 4.000, o texto do teste de volta no tempo com 68% e 47%, e o gráfico | ✅ Todos |
| 14 | Nota final sem número de testes (mensagem 3) | "(testes automáticos, incluindo…)" | ✅ |
| 15 | Celular (375 × 812) | Sem rolagem horizontal; faixa visível | ✅ Nenhum elemento vaza para os lados (`tela_final_celular.jpg`) |
| 16 | Revisão do código (`src/routes/index.tsx`) | Sem recalcular nota, chance, valor esperado ou lista | ✅ O código só ordena pela `ordem_na_lista` do motor, filtra, conta, soma `valor_esperado_usd` e formata |
| 17 | Erros no console | — | ✅ Só um 404 da primeira tentativa de abrir o site, antes de a publicação terminar. Não é um erro do app |

**Limitações dos testes**
- Os cliques reais não foram testados com o mouse, porque o painel estava minimizado. Uma rodada com os seletores abertos ao mesmo tempo misturou as opções e foi **descartada e refeita** com a página recarregada.
- O fechamento visual dos seletores e a aparência geral devem ser conferidos pelo Liberato.
- O selo "Edit with Lovable" aparece sobre as abas no celular. É do plano do Lovable, não do código.
