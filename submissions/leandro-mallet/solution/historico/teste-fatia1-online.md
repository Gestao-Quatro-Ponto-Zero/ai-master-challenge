# Teste no ar — fatia 1 do app

**Veredito: leitura aprovada, escrita reprovada.** Os números de Painel, Pipeline e filtros batem com o banco nos três perfis, as telas não mostram erro cru e a segurança testada se comporta como pedido. Mas duas escritas centrais não funcionam no ar: marcar ✓/✗ nas Prioridades do dia (404) e mudar o estágio do deal (409 falso). Sem elas, a "segunda-feira de manhã" não fecha o ciclo.

- **Endereço:** https://g4-sight.vercel.app, versão do commit `a468ed4`. Escritas em memória nesta fatia.
- **Quando:** 10/11/2026.
- **Como:** Chrome no computador (1.920 px) e navegador embutido emulando celular (375 × 812, com toque). Perfis testados: vendedora Anna Snelling, manager Dustin Brinkmann e admin. Nada no app foi alterado.
- **Números de referência:** consultados no banco com o dataset (somente leitura), com data de referência 31/12/2017 e janela de 30 dias = 02/12 a 31/12/2017 contra 02/11 a 01/12/2017.

Durante o teste apareceu no menu um item novo, "Leads": houve uma publicação nova no meio. Os dois bugs de escrita foram repetidos depois disso e continuam.

Prints em [prints-fatia1/](prints-fatia1/) (numerados na ordem abaixo).

## 1. Números do Painel × dados

| Cartão | Anna (vendedora) | Time Dustin (manager) | Todos (admin) | Confere |
|---|---|---|---|---|
| Leads novos (abertos em 30 dias) | 7, −12% (antes 8) | 18, −40% (antes 30) | 117, −57% (antes 275) | ✅ |
| Em negociação | 57 · US$ 95.414 | 193 · US$ 283 mil (282.707) | 1.589 · US$ 3,89 mi | ✅ |
| Fechamentos hoje / 30 dias | 2 (US$ 3.354) / 26, +18% | 6 (US$ 10.953) / 91, +36% | 19 (US$ 41.764) / 498, +23% | ✅ |
| Conversão em 30 dias | 86,7% (26 × 4), +33 p.p. | 86,7% (91 × 14), +33,9 p.p. | 78,7% (498 × 135), +25 p.p. | ✅ |
| Receita ganha em 30 dias | US$ 36.454, +74% | US$ 142 mil, +49% | US$ 1,1 mi, +17% | ✅ |
| Pipeline aberto (preço de tabela) | US$ 173 mil (173.259) | US$ 586 mil (585.616) | US$ 4,97 mi | ✅ |
| Total de leads | 448 | 1.583 | 8.800 | ✅ |
| Em risco (107–138 dias) / esfriaram (> 138) | 1 / 56 | 3 / 190 | 141 / 1.291 | ✅ |
| Funil (Prospecção / Negociação / Ganho / Perdido) | 55 / 57 / 208 / 128 | 204 / 193 / 747 / 439 | 500 / 1.589 / 4.238 / 2.473 | ✅ |

Outros conferidos:
- Tabela "Por vendedor" do manager: abertos 112 + 43 + 80 + 65 + 97 = 397 (= 204 + 193); em risco e esfriados somam 3 e 190.
- Pipeline: cabeçalhos das colunas iguais ao funil (Anna: 55 · US$ 77.845 e 57 · US$ 95.414; Dustin: 204 · US$ 303 mil e 193 · US$ 283 mil).
- Escolha de perfil: contagem de abertos por vendedor confere (ex.: Anna 112, Darcel 194, Wilburn 31). Os 8 vendedores com 0 abertos estão corretos: 5 não têm nenhum deal, e Donn Cantrell, Reed Clapper e Garret Kinder só têm deals fechados.
- **Bug conhecido (abas 66/67 × 55/57): não reproduzido** no celular para a Anna. As abas mostraram "Prospecção (55)" e "Em negociação (57)" (print 22). Pode depender de outro perfil ou de outra versão.

## 2. Funções

| # | Teste | Resultado | Print |
|---|---|---|---|
| F1 | ✓ Feito sem tipo de atividade | ✅ recusado: "Escolha o tipo de atividade." | 03 |
| F2 | ✓ Feito com tipo e sem comentário | ✅ recusado: "Escreva o que foi feito." | 04 |
| F3 | ✓ Feito com tipo e comentário | ❌ **"Este deal não está na sua lista de hoje."** (`POST /api/prioridades` → 404), embora o deal esteja na lista da tela | 05 |
| F4 | ✗ Pular hoje | ❌ mesmo erro (404), também depois da nova publicação | 06 |
| F5 | Desfazer das Prioridades | não testável (F3 e F4 não gravam) | — |
| F6 | Seletor de estágio → Ganho | ✅ abre "Encerrar como ganho" pedindo o valor, sugerindo o preço de tabela | 09 |
| F7 | Ganho com valor 0 | ✅ recusado (mensagem imprecisa, ver M3) | 10 |
| F8 | Ganho com valor válido; Perdido | ❌ **"Este deal foi alterado por outra pessoa"** (`POST /api/deals/{id}/estagio` → 409) sem ninguém ter mexido. Repetido em 3 deals, depois de recarregar e depois da nova publicação | 11, 12 |
| F9 | Arrastar card entre colunas | inconclusivo: o arraste da ferramenta não dispara o arrastar-e-soltar do navegador (nenhuma chamada saiu). Testar à mão; a rota é a mesma do F8 | — |
| F10 | Modal do deal: linha do tempo, nota, comentários, contato | ✅ abre com empresa, vendedor, time, estágio, valor, data e dias, linha do tempo e botões Liguei/Requalifiquei/Desisti | 13 |
| F11 | Postar comentário | ✅ 200; aparece com autor e data; continua depois de recarregar | — |
| F12 | Apagar comentário + Desfazer | ✅ pede confirmação, some da tela e da linha do tempo, "Desfazer" devolve (`/api/desfazer` 200) | 14 |
| F13 | Liguei | ✅ 200; entra na linha do tempo. O "Desfazer" não foi acionado a tempo no teste | — |
| F14 | Adicionar contato | ✅ 200; o nome aparece no modal. Só pede nome e cargo (ver M4) | 15 |
| F15 | Filtro livre "esfriou sem empresa GTX Pro" | ✅ entendeu as 3 etiquetas; vazio correto (a Anna não tem GTX Pro aberto) e a tela de vazio diz o que fazer | 16 |
| F16 | Filtro livre "esfriou sem empresa" | ✅ 37 deals, igual ao banco | 17 |
| F17 | Filtro com texto sem sentido | ✅ vira "Contém …", sem erro | — |
| F18 | Deal inexistente (`?deal=NAOEXISTE`) | ✅ "Não foi possível abrir este deal / Este deal não foi encontrado", com "Tentar de novo", "Fechar" e código para suporte | 23 |
| F19 | Tela inexistente | ✅ "Esta tela não existe", com "Ir para o Painel" | 24 |
| F20 | Celular 375 px | ✅ sem rolagem lateral; no Painel as Prioridades vêm primeiro; no Pipeline as colunas viram abas | 21, 22 |
| F21 | Console do navegador | ✅ nenhum erro | — |

## 3. Segurança

| Teste | Resultado |
|---|---|
| Escolher o usuário "sistema" (`POST /api/perfil {usuarioId: 1}`) | ✅ recusado (400, "Não entendi o pedido. Recarregue a página e tente de novo.") |
| `usuarioId` 0, texto e inexistente | ✅ 400, 400 e 404 ("Este usuário não existe. Escolha outro na lista.") |
| `?voltar=https://example.com/roubo` | ✅ depois de escolher o perfil, foi para `/painel` |
| `?voltar=//example.com` | ✅ foi para `/painel` |
| `?voltar=/pipeline?deal=B08R55ET` (interno) | ✅ abriu o deal pedido |
| Limite de pedidos: 65 escritas seguidas | ✅ 60 aceitas pelo limite, **61ª → 429** com "Muitas mudanças seguidas. Espere alguns segundos e tente de novo." |

## 4. Achados

| # | Gravidade | Achado | Sugestão |
|---|---|---|---|
| B1 | **Bloqueador** | ✓ e ✗ das Prioridades sempre respondem 404 ("não está na sua lista de hoje"), com o deal visível na lista | Comentário, ação e contato gravam e continuam depois de recarregar, então a memória não está se perdendo entre pedidos. A suspeita é a chave do dia da lista: a lista é montada com uma data e a marcação procura com outra (dia real × data do negócio, ou fuso) |
| B2 | **Bloqueador** | Mudar estágio (Ganho, Perdido) sempre responde 409 "alterado por outra pessoa" | Só a rota de estágio compara a versão. A suspeita é a versão enviada pela tela não bater com a do servidor (formato ou precisão do `atualizado_em`) |
| M1 | Média | O formulário do ✓ abre no item seguinte já preenchido com o tipo e o comentário do item anterior | Limpar o formulário ao trocar de item; senão, o comentário vai para o deal errado |
| M2 | Média | Depois de salvar um contato no modal, o card do Pipeline continua "Sem contato cadastrado" até recarregar | Atualizar o card junto com o modal |
| M3 | Leve | Ganho com valor 0 diz "Informe o valor de fechamento em dólares, sem centavos." | Para 0 ou negativo: "O valor precisa ser maior que zero." |
| M4 | Leve | "Adicionar contato" só tem nome e cargo; a especificação prevê também e-mail e telefone (opcionais) | Incluir os dois campos ou registrar a mudança na especificação |
| M5 | Leve | A explicação da nota mostra ao vendedor os termos internos "FIT" e "HEAT" (FE-02: sem jargão) | Trocar por "encaixe com você" e "tempo de atendimento" |
| M6 | Leve | Ao abrir "Encerrar como ganho", a página rola sozinha para outro ponto do Pipeline | Manter a posição da lista |
| M7 | Leve | "Apagar comentário" usa a confirmação nativa do navegador | Usar a mesma janela de confirmação do resto do app (FE-02/FE-03) |
| M8 | Observação | O limite por endereço de rede fica na memória de cada instância do servidor. Com várias instâncias, a soma pode passar de 60 por minuto | Quando a escrita for para o banco, o teto global da 0026/0027 cobre isso; nesta fatia, aceitar e documentar |
| M9 | Observação | "Sem nota ainda" em todos os deals | Esperado enquanto as notas do score não forem carregadas; conferir de novo na próxima fatia |

## 5. Dados de teste deixados (em memória, somem na próxima publicação)

No deal `B08R55ET` (Anna, "Sem empresa · MG Special"): 1 contato "Contato QA", 1 ação "Liguei" e 2 comentários de teste já apagados (remoção lógica). Nenhuma escrita foi feita no banco.
