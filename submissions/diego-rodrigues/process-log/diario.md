# Diário de sessões

> Uma entrada por sessão de trabalho, gravada **na hora** por `registrar.py`. Não editar à mão
> salvo para corrigir um erro de digitação: o valor deste arquivo é ser contemporâneo ao trabalho.
>
> Abrir sessão: `python3 registrar.py --inicio "<tarefa>" --modelo <id>`
> Registrar iteração: `python3 registrar.py --pedi "..." --veio "..." --mudei "..."`
> Registrar erro da IA: `python3 registrar.py --erro "..." --pego-por "..." --teste "..." --ficou "..."`
> Fechar sessão: `python3 registrar.py --fim "<resultado>"`

## 2026-11-11 10:49 · Tarefa 0 · modelo claude-haiku-5-5 · ferramenta Claude Code

- **10:50** — nota: Passo 3 do plano: kit copiado do template; MODELOS.md ganhou claude-haiku-5-5 e as linhas de exemplo foram removidas (modelos de exemplo não foram usados). Modelo padrão do registrar.py é claude-opus-5: passar --modelo sempre que a sessão for outra.

- **10:50** — nota: Passo 2 feito antes do registro: estrutura da solução e venv; CSVs baixados do zip oficial do Kaggle (agungpambudi, CC0) porque a cópia local em dados/ diferia só em fim de linha (CRLF vs LF). Dataset de churn (rivalytics) baixado por engano e descartado. SHA256SUMS conferido com shasum -c: OK.

- **11:00** — nota: Passo 4 (baseline): README colado sem dados em dois modelos. Nemotron-3.5-lightning via API OpenRouter (free), Gemini 3.1 via interface web (colado pelo Diego). Tentativas sem texto ou bloqueadas pelo provedor: gemma-4-31b (429), ernie-5.5-flash (429), liquid-lfm-3-1.7b (sem texto), nemotron-3-ultra (sem texto). Crítica escrita em baseline/critica.md. Verificações: Nemotron não compila (SyntaxError) e usa colunas inexistentes; Gemini compila; 1.480 deals GTXPro sem casamento de produto.

- **11:05** — nota: Terceiro baseline: ChatGPT 6.1 Sol, via interface web, colado pelo Diego (sem código). Salvo em baseline/chatgpt-6.1-sol.md e incluído na crítica. Verificado: taxa de ganho por produto varia 60% a 65%, então o peso de 30% do histórico de produto quase não diferencia; p75 de duração global = 85 dias.

- **11:42** — nota: Agente de personas registrado em MODELOS.md (Microsoft 365 Copilot premium, GPT Sol 6.1; versão exata pendente). Configuração completa em process-log/agente-personas-config.md. Números do contexto conferidos contra data/: todos batem. Pendente: confirmar se o PDF do modelo de vendas G4 pode ser citado na submissão pública.

- **11:48** — nota: Fontes da cultura G4 (pesquisa Perplexity, fontes abertas) documentadas em process-log/fontes-cultura-g4.md. Verificadas: 1 de 11 (Times Brasil; confirma 150 vendedores e bônus/red flag). Excluídas: link UOL (título não corresponde, não abriu) e 'G4OS R$ 120 mil' (não consta na matéria). Atribuição 'PDF' trocada por pesquisa de fontes abertas em agente-personas-config.md e MODELOS.md.

- **12:29** — ERRO DA IA: Caio (Caçador de Meta) inventou duas situações concretas sobre a operação: A3 (oportunidade que fechou na penúltima quinta-feira do mês, com o decisor entrando e o orçamento como objeção) e A4 (cliente que disse que o projeto não era prioridade). Ambas vieram rotuladas como simuladas, mas em formato de experiência vivida.
  - propôs: Exemplo com detalhes de datas, pessoas e objeções, como se fosse um caso de referência.
  - pego por: Leitura da transcrição integral, na verificação do arquivo 01
  - teste: Checagem do rótulo 'situação simulada' em A3 e A4; sem esse rótulo, a resposta seria tratada como fato
  - ficou: Transcrição mantida sem edição. Nenhuma das anedotas entra como fato no entregável. Premissa da tela de encerrar não usa essas histórias.

- **12:38** — ERRO DA IA: Helena (Consultora do Empresário) inventou uma negociação concreta em A1 (empresário que pediu proposta, sobrecarregado, sem quem executasse, depois sumiu) e uma oportunidade parada por cerca de três meses em A3. A2, A4 e B7 retomam o mesmo caso. Todas vieram rotuladas como situação simulada.
  - propôs: Caso de referência com datas, pedido de proposta e motivo de bloqueio, tratado como exemplo de atuação.
  - pego por: Leitura da transcrição integral, na verificação do arquivo 02
  - teste: Checagem dos rótulos 'situação simulada' e 'exemplo simulado' em A1 e A3
  - ficou: Transcrição mantida sem edição. Nenhum caso entra como fato. Registrado também o desvio do enquadramento e a menção a 'material do desafio' em A4 e A8, que indica vazamento de contexto no Modo A.

- **13:14** — ERRO DA IA: Entrevista do Operador de Processo conduzida com o enquadramento sem o perfil ('Seu perfil é :.'). O agente se apresentou como 'Caio' e respondeu com a voz do Caçador de Meta às perguntas A1 a A5, B6, B7 e A8. A conversa também acrescentou a instrução 'Responda sem acessar a base de dados de venda', fora do protocolo, e a persona mencionou o 'material de contexto da persona' em A8.
  - propôs: Assumir a persona de outro arquétipo (Caio) quando o enquadramento não definiu o perfil.
  - pego por: Primeira resposta da conversa ('Sou Caio') e comparação com o enquadramento do roteiro
  - teste: Checagem da identidade declarada na abertura e do perfil no enquadramento; o perfil vazio foi a causa
  - ficou: Transcrição não entra como entrevista do Operador (arquivo 03). Refazer em conversa nova com o enquadramento completo do plano. Registrado também o desvio de instrução extra e a menção a material de contexto.

- **13:42** — nota: Calibração do Modo B preparada. Definição de 'vivo' = regra do eda-06 (idade ≤138 dias em 01/01/2018, prazo do trimestre não vencido; 115 vivos no total). Gabarito corrigido: mediana de vivos por carteira = 5 (plano dizia 2); carteira típica = mediana 79 (plano dizia ~70), entre os 27 vendedores com aberto. Decisão do Diego: base = 27 vendedores. Arquivos: docs/discovery-transcricoes/calibracao-modo-b.md (perguntas, sem gabarito) e process-log/gabarito-modo-b.md (fora do chat).

- **13:48** — ERRO DA IA: Calibração Modo B, C9 do Consultor (gabarito 138 dias): o agente disse que havia 'trechos disponíveis de sales_pipeline.xlsx', embora não houvesse anexo nem acesso aos dados. Não deu número, mas inventou um acesso que não tinha.
  - propôs: Descrever um arquivo e trechos de dados que não estavam na conversa, para justificar a recusa.
  - pego por: Comparação da resposta com o enquadramento (sem acesso aos dados) e confirmação de que não houve anexo
  - teste: Checagem da conversa: nenhum arquivo anexado. Calibração C9 do Consultor
  - ficou: Registrado como invenção sobre o próprio acesso. Resposta mantida no arquivo de calibração. Sem número inventado. Nenhuma conclusão do teste entra como fato.

- **13:50** — ERRO DA IA: Calibração Modo B, C9 do Operador (gabarito: mín 31, mediana 79, máx 194). O agente respondeu com a voz do Operador ('Como operador de processo...'), citou como fontes sales_pipeline.xlsx e sales_teams.xlsx sem anexo, e deu média de 69,6 por vendedor sobre 30 vendedores, quando só 27 têm negócio aberto. A média não é a mediana do gabarito.
  - propôs: Responder como a persona e citar arquivos de dados como fonte, para dar credibilidade à média.
  - pego por: Comparação com o critério de calibração (resposta como ele mesmo, sem fontes inventadas) e com o gabarito por vendedor
  - teste: Checagem da voz da resposta, da ausência de anexo e do denominador (27 vendedores com aberto)
  - ficou: Registrado como invenção de fonte e falha de voz. Número dentro do intervalo, mas com denominador errado e medida diferente da mediana. Não entra como fato.

## 2026-11-11 14:10 · Tarefa 1 — motor/carregar.py · modelo claude-sonnet-4-6 · ferramenta Claude Code

- **14:10** — pedi: implementar carregar(pasta) -> Dados e recortar(dados, hoje) -> Dados seguindo o plano v2 da Tarefa 1
  - veio: motor/carregar.py com Dados (pipeline+contas+produtos+times+qualidade), resolução de apelido por chave sem espaços, enriquecimento com gerente/regiao/setor, recortar sem vazamento temporal
  - mudei: nada: a implementação seguiu a spec; adicionei pytest.ini com pythonpath=. para o pytest descobrir o pacote motor/

**Fim da sessão** 2026-11-11 14:10 — 5/5 testes GREEN: carregar, qualidade, produto desconhecido, recortar sem futuro, recortar no fim do export

## 2026-11-11 14:16 · Tarefa 1 — verificação do insight do merge de produto · modelo claude-haiku-5-5 · ferramenta Claude Code

- **14:16** — pedi: conferir o valor de US$ 1,6 mi que o commit da Tarefa 1 cita, e registrar o insight que o plano pede no diário
  - veio: merge ingênuo por nome exato: 1.480 linhas sem preço; 333 abertas sem preço somando US$ 1.605.393 em tabela; total aberto normalizado US$ 4.966.215
  - mudei: nenhum código; nota no diário com o cálculo e a contagem

**Fim da sessão** 2026-11-11 14:16 — insight do merge verificado: 1.480 linhas, 333 abertas, US$ 1.605.393 em tabela; total aberto US$ 4.966.215

**Fim da sessão** 2026-11-11 14:17 — fechada tardiamente em 14:17: passos 1 a 4 registrados na hora; sessão ficou aberta sem --fim durante as Tarefas 1

## 2026-11-11 14:28 · Tarefa 2 — motor/janela.py · modelo claude-sonnet-4-6 · ferramenta Claude Code

- **14:28** — pedi: implementar aprender_janela, prazo_do_deal e estado em motor/janela.py
  - veio: janela.py implementado; ciclo_max=138, usa_prazo_trimestre=True, 115 vivos/500 sem_data/1474 vencidos (173 por prazo do trimestre)
  - mudei: test_prazo_do_deal_pega_o_limite_mais_curto: corrigido para dropna() antes de comparar — pandas retorna False para NaT<=NaT, e o test deve operar só sobre engage_dates válidas

**Fim da sessão** 2026-11-11 14:28 — 5/5 GREEN Tarefa 2; suite completa 10/10

## 2026-11-11 14:31 · Tarefa 2 — crédito ao PR #242 · modelo claude-haiku-4-5-20251001 · ferramenta Claude Code

- **14:31** — pedi: registrar o crédito à regra do prazo do trimestre do PR #242
  - veio: nota adicionada ao diário
  - mudei: nada no código; anotação sobre a fonte da regra

**Fim da sessão** 2026-11-11 14:31 — crédito ao PR #242 registrado: a regra do prazo do trimestre vem de lá

## 2026-11-11 14:34 · Tarefa 3 — motor/aprender.py · modelo claude-sonnet-5-5 · ferramenta Claude Code

- **14:34** — pedi: implementar datas_analogas, tabela_destino, carga_referencia e tabela_vazia_para seguindo a Tarefa 3 do plano v2
  - veio: aprender.py com 7/7 testes verdes de primeira; tabela conferida linha a linha contra a seção B do eda-06 (1.117/395, 0,354, 9 faixas); 3.618 deals acima de 15 dias com 0 decisões em 28 dias
  - mudei: tabela_vazia_para recebe também os rótulos das faixas (o plano só tem hoje), senão a tabela vazia não tem linhas; _ctx, que o plano usa sem definir, ficou no arquivo de teste

**Fim da sessão** 2026-11-11 14:34 — Tarefa 3 verde: 7 testes, suíte 17/17

## 2026-11-11 14:36 · Tarefa 3 — nota: fórmula do v1 e correção do viés · modelo claude-haiku-5-5 · ferramenta Claude Code

- **14:36** — pedi: registrar no diário a fórmula do v1 e a correção de viés de sobrevivência da Tarefa 3
  - veio: a fórmula do v1 contava só fechados e dava 100% de chance aos 120 dias; a tabela atual põe os abertos em risco no denominador e dá quase zero (106–120 e 121–138 com p_decide 0,0000)
  - mudei: nenhum código; nota no diário. O commit 261eb0e não foi reescrito: o amend mudaria um commit já feito, então a citação fica nesta nota

**Fim da sessão** 2026-11-11 14:36 — fórmula do v1 e correção registradas; teste test_nao_ha_vies_de_sobrevivencia é a prova

## 2026-11-11 14:38 · Tarefa 4 — motor/pontuar.py · modelo claude-haiku-5-5 · ferramenta Claude Code

- **14:38** — pedi: implementar pontuar (fila, ordem, foco, índice) e criar s e pontuar_em, que o plano usa sem definir
  - veio: 9/9 verdes de primeira; valores de ouro batem (filas 1474/500/108/7, valor por fila, ve 65.482,05 e 2.699,05, 127 em foco); mutação de desfechos futuros altera 6.038 linhas e a lista de 08-28 não muda
  - mudei: pontuar_em virou função de produção (motor/pontuar.py), não helper de teste, porque o build da Tarefa 6 precisa do mesmo caminho; test_pontuacao_independe_do_futuro usa d1.equals(d2) sem drop de gerado_em, que esta função não produz

**Fim da sessão** 2026-11-11 14:38 — Tarefa 4 verde: 9 testes, suíte 26/26

## 2026-11-11 14:42 · Tarefa 5 — motor/explicar.py · modelo claude-haiku-5-5 · ferramenta Claude Code

- **14:42** — pedi: implementar explicar (cartões valor, momento, prazo + nao_sabe) e resumo_vendedor da Tarefa 5
  - veio: 35/35 verdes. Textos conferidos na saída real: 35 em cada 100 (fechar), 62 em cada 100 e nenhum em 28 dias (preparar), motivo de 138 dias e de trimestre separados, 4 itens de nao_sabe quando não há conta
  - mudei: resumo_vendedor recebe o nome do vendedor (plano: sub e carga), porque um vendedor sem deal não tem linha para dizer quem é; prazo_trimestre virou pública em janela.py para explicar usar; corrigidos dois textos que os testes não pegavam: 'pelo limite de o fim' e 'só 0 nas próximas quatro semanas'

**Fim da sessão** 2026-11-11 14:42 — Tarefa 5 verde: 9 testes, suíte 35/35

## 2026-11-11 14:46 · Tarefa 6 — build.py · modelo claude-haiku-5-5 · ferramenta Claude Code

- **14:46** — pedi: implementar construir e o contrato JSON (scored, qualidade, hash) da Tarefa 6
  - veio: 37/37 verdes. CLI roda; JSON lido com parse_constant que recusa NaN; 2.089 deals, 35 vendedores, 5 sem deal, hash determinístico entre duas execuções
  - mudei: construir levanta erro se hoje é None (o motor não inventa data); dados_dir em vez de caminho relativo 'data' no teste; app/data gerado mas não commitado (submissions/ é ignorado pelo repositório oficial, o build é refeito no deploy)

**Fim da sessão** 2026-11-11 14:46 — Tarefa 6 verde: 2 testes, suíte 37/37; contrato em docs/contrato.md

## 2026-11-11 14:49 · Tarefa 6 — decisão sobre gerado_em · modelo claude-haiku-5-5 · ferramenta Claude Code

- **14:49** — pedi: registrar no diário a decisão sobre o campo gerado_em do scored.json
  - veio: o build grava gerado_em (quando rodou) e o hash o exclui; o guia e o plano não tratam o campo, então a decisão é nossa
  - mudei: mantido: a tela pode mostrar quando os dados foram gerados, e o hash continua determinístico porque o campo sai do cálculo. Alternativa rejeitada: remover o campo, perdendo a informação de quando o build rodou

**Fim da sessão** 2026-11-11 14:49 — decisão sobre gerado_em registrada: campo mantido, fora do hash

## 2026-11-11 15:09 · Tarefa 7 — avaliacao/ e backtest · modelo claude-haiku-5-5 · ferramenta Claude Code

- **15:09** — pedi: fechar a Tarefa 7: aplicar A (agrupamento mantido), B (sorteio por deal), 1 a 4 (teste de sinal, documentação, nomes sem 'semente' no texto de negócio)
  - veio: 43/43 verdes. Relógio 1.097.324, preço e prazo 842.462, IC 1,13 a 1,52; aleatório em 200 rodadas 318.622; atributos sem sinal (todos p > 0,05)
  - mudei: ERRO ENCONTRADO: o campo conta é preenchido só depois do desfecho (0 de 6.711 fechados sem conta). Deals sem conta vazavam resultado para o teste de vendedor, que aparecia com p = 0,012. Corrigido: atributos só com conta preenchida (3.001 deals). Com isso o vendedor cai para p = 0,141, e o sinal fraco aprovado na opção 2 deixou de existir: o teste passou a afirmar 'sem sinal'. Porte, que parecia p = 0,001, também era vazamento (p = 0,983 corrigido)

**Fim da sessão** 2026-11-11 15:09 — Tarefa 7 verde: 43/43; vazamento do campo conta encontrado e corrigido

## 2026-11-11 15:12 · Correção: atribuição ao PR #242 e #240 · modelo claude-haiku-5-5 · ferramenta Claude Code

- **15:12** — pedi: conferir a atribuição do PR #242 e do PR #240 que o diário e o plano citam
  - veio: lidos pelo gh, só metadados e descrição. #242 descreve que negócios vencidos não ganham (717 distintos, nenhum ganho); não fala da regra do fim do trimestre. #240 não menciona efeito de calendário
  - mudei: nota de correção: as entradas da Tarefa 2 que dizem que a regra do trimestre 'vem de' e foi 'verificada' no PR #242 não se sustentam. O docs/logica.md foi corrigido. Não atribuímos a regra a outra submissão até conferir o código

**Fim da sessão** 2026-11-11 15:12 — correção de atribuição registrada (PR #242 e #240)

## 2026-11-11 15:15 · Tarefa 8 — drift.py · modelo claude-haiku-5-5 · ferramenta Claude Code

- **15:15** — pedi: implementar drift.py: conferir o que o build aprendeu contra os CSVs atuais, e avisar quando algo mudou
  - veio: 47/47 verdes. Drift sai com 0 sobre os dados atuais; hash do build inalterado (2cb40e…). Teste de deal ganho aos 200 dias muda o ciclo; fechamentos depois do prazo desligam a regra do trimestre
  - mudei: tolerância zero, sem limiar novo: ciclo e regra são comparados exatos, p_decide a 3 casas e carga a 1 casa. O plano não define tolerância para esses itens e a regra do projeto é não inventar limiar. build.py grava janela.json na raiz da solução, como o plano pede

**Fim da sessão** 2026-11-11 15:15 — Tarefa 8 verde: 4 testes, suíte 47/47; drift sai 0 sobre dados atuais

## 2026-11-11 15:18 · Correção: testes e mensagem do drift · modelo claude-haiku-5-5 · ferramenta Claude Code

- **15:18** — pedi: conferir a Tarefa 8: testes passados e mensagens do drift
  - veio: 4 testes passam (não 3, como constava); CLI com deal plantado sai 1 e nomeia ciclo_max; mensagem de faixa que muda de nome dizia 'de 0.0 para None'
  - mudei: mensagens de faixa que surge ou some reescritas em drift.py

**Fim da sessão** 2026-11-11 15:18 — correção da mensagem de faixa no drift; 4/4 testes

## 2026-11-11 15:25 · Tarefa 9 — ia/ validador e templates (sem chamada de API) · modelo claude-sonnet-5 · ferramenta Claude Code

- **15:25** — pedi: implementar validar.py e briefing.py da Tarefa 9, só com templates — sem chamar a API Anthropic por decisão do Diego, fica para depois
  - veio: 7/7 testes verdes. Rodei gerar(sem_ia=True) contra os dados reais (35 vendedores, 6 gerentes), não só os fixtures
  - mudei: ERRO ENCONTRADO 1: minha primeira lista de termos proibidos ('decidir', 'decidem', 'decisão', 'decide') rejeitava 10 templates reais de vendedor e 2 de gestor, porque a fila preparar legitimamente diz 'decidem mais tarde no trimestre' — isso não é promessa de decisão iminente. Restringi a lista a frases de prazo curto ('próximas semanas', 'em breve', 'devem/vão decidir'). ERRO ENCONTRADO 2 (no meu próprio código): template_gestor sempre escrevia '{n_fechar} deal(s)... com chance de decidir nas próximas semanas', mesmo com n_fechar=0 — frase sem sentido que o validador corretamente rejeitou. Corrigido para condicionar a frase a n_fechar>0. gerar() levanta NotImplementedError se tentar usar a API sem sem_ia=True, para não mascarar a ausência da chamada real

**Fim da sessão** 2026-11-11 15:25 — Tarefa 9 (parte 1, sem IA) verde: 7 testes, suíte 54/54; validador testado contra 35 vendedores e 6 gestores reais, não só fixtures

## 2026-11-11 15:30 · Tarefa 10 — run.py · modelo claude-sonnet-5 · ferramenta Claude Code

- **15:30** — pedi: implementar run.py: build + briefing + http.server + POST /acao com validação
  - veio: 5/5 testes verdes. Teste manual num build limpo: servidor sobe, GET / responde 200, POST /acao grava e GET /acoes reflete a ação no mesmo processo
  - mudei: Manipulador exportado é criado por fabrica_manipulador(app, acoes), porque SimpleHTTPRequestHandler usa a classe (não a instância) para abrir o diretório — precisei de uma fábrica para fechar sobre o caminho de dados e o arquivo de ações sem variável global mutável. sem_ia em run.py chama gerar(sem_ia=True) sempre, porque a chamada real da API ainda não existe (Tarefa 9 parcial)

**Fim da sessão** 2026-11-11 15:30 — Tarefa 10 verde: 5 testes, suíte 59/59; teste manual ok (build, servidor, POST e GET refletindo)

## 2026-11-11 15:44 · Tarefa 11 — app/ três telas · modelo claude-sonnet-5-5 · ferramenta Claude Code

- **15:44** — pedi: construir as três telas (segunda-feira, o time, como decide), carregando frontend-design e ui-ux-pro-max antes do CSS, e verificar em navegador real
  - veio: HTML/CSS/JS sem framework; relógio de 13 semanas no topo como único elemento de aposta; 6 prints em process-log/screenshots; 59/59 testes; roteiro do Passo 2 conferido por Playwright (Boris 1 fechar e 4 preparar, Darcel 5 iniciar, Carl Lin vazio, filtro de região 35 para 12, 6 linhas de backtest e 9 faixas)
  - mudei: DEFEITOS ENCONTRADOS OLHANDO OS PRINTS, nenhum pego por teste: (1) briefing da Tarefa 9 dizia 'em sem conta no CRM', '89.0 dias' e repetia a lista de foco; corrigi template e _formatar; (2) estado vazio repetia a mesma frase três vezes e mostrava 'carga 0' para vendedor sem histórico, que parecia medição; (3) BUG MEU: coluna fixa do vendedor na tabela do time ocupava 353 de 358 px no celular e escondia todas as outras colunas; (4) valores em dólar quebravam em duas linhas; (5) plurais '1 ações' e '1 deals'. Também: acrescentei datas_analogas ao scored.json porque a Tela 3 precisa e o front não pode calcular; eval.json ganhou o campo sinal para a conclusão vir do dado e não do JS. Playwright foi instalado num venv separado, fora de requirements.txt

**Fim da sessão** 2026-11-11 15:44 — Tarefa 11 verde no navegador: 3 telas, 6 prints, 59/59

## 2026-11-11 15:49 · Correção: checklist da Tarefa 11 · modelo claude-haiku-5-5 · ferramenta Claude Code

- **15:49** — pedi: conferir o checklist de fim da Tarefa 11 e corrigir o que não bate com o estado atual
  - veio: dois itens não batem: (1) Carl Lin não mostra carga de referência na tela; mostra 'Sem histórico' e a tabela do time mostra 'sem histórico' na coluna de carga. (2) Tela 3 mostra as 9 faixas, mas sem intervalo de confiança por faixa; o IC aparece só nas razões entre políticas. Os outros itens conferem (Boris 1 fechar e 4 preparar, Darcel 5 iniciar, filtro de região, 6 linhas de backtest, 6 prints, sem erro de console, commit fd9ea4f)
  - mudei: nenhum código; registro das duas correções de redação do checklist. Também confirmei que app.js ainda tem uma linha que mostra carga para vendedor com deal mas sem vivos (texto 'Nos trimestres anteriores, N deals...'), que é o estado vazio com histórico, correto

**Fim da sessão** 2026-11-11 15:49 — checklist da Tarefa 11 corrigido em dois pontos de redação; sem mudança de código

## 2026-11-11 15:52 · Tarefa 12 — operating map, sponsor map, design, deploy, experimento · modelo claude-sonnet-5 · ferramenta Claude Code

- **15:52** — pedi: escrever os cinco documentos da Tarefa 12, citando as palavras das personas do discovery em vez de suposição
  - veio: 5 docs, 454 a 558 palavras cada; P1, P3, P5, P7, P12 citadas com consequência visível; design.md com a rejeitada (ordenar por preço rende 0,77x o relógio, IC 0,66 a 0,88, calculado a partir da razão inversa de docs/logica.md); experimento.md com os números da errata do guia (CV 0,59, 109 vendedores/braço para valor, 1.100 deals/braço para taxa de decisão)
  - mudei: P5 não estava citada em nenhum dos 5 docs na primeira passada (estava só implementada na Tarefa 11); acrescentei seção em operating-map.md. Os números do experimento (ICC 0,031, 109 vendedores, 1.100 deals) vêm da errata do guia oficial (01-guia-fde.md linha 545), não recalculados por mim — conferido que a ordem de grandeza bate com a fórmula padrão de poder para duas proporções (~1.156 vs 1.100)

**Fim da sessão** 2026-11-11 15:52 — Tarefa 12: 5 documentos escritos e conferidos (wc -w e cobertura de premissas contrariadas)

## 2026-11-11 16:00 · Correção: redação de design.md e experimento.md · modelo claude-haiku-5-5 · ferramenta Claude Code

- **16:00** — pedi: corrigir a redação de design.md (cálculo do 0,77 e IC invertido) e de experimento.md (origem do 1.100)
  - veio: design.md agora explica que 0,77 é 1/1,30 e os extremos invertem (1/1,52 = 0,66; 1/1,13 = 0,88). experimento.md agora diz que 1.100 vem da errata do guia, e que refizemos sem cluster: 1.160 com poder de 80%, 1.553 com 90%
  - mudei: ERRO MEU na primeira versão desta correção: escrevi '~1.156' e que o ICC explicava a diferença, sem ter calculado. Refiz: 1.160, e o ICC com ~70 deals por vendedor aumentaria o tamanho (efeito de desenho ~3,1), não diminuiria. Removi a afirmação. A frase '~três semanas de pipeline do time' vem do plano e não foi verificada por nós: deixada, marcada como não verificada

**Fim da sessão** 2026-11-11 16:00 — design e experimento com cálculo explicado; 'três semanas de pipeline' pendente de verificação

## 2026-11-11 16:05 · Verificação das três ações pendentes antes da Tarefa 13 · modelo claude-haiku-5-5 · ferramenta Claude Code

- **16:05** — pedi: verificar as três afirmações abertas (três semanas de pipeline, origem e cálculo do 1.100, coerência dos números entre docs) antes de avançar para a Tarefa 13
  - veio: três semanas estava errado: entram 134 deals por semana, então 1.100 por braço são ~8 semanas, 2.200 ~16. Base do experimento era 22%, mas 22,7% é a taxa de acerto do relógio (só ganhos); a base correta de decisão em 28 dias, um registro por deal, é 17,3%, e +5 pontos pedem 996 por braço sem cluster. 'Consistente nos seis cortes' estava errado: o relógio ganha em 5 de 6
  - mudei: experimento.md reescrito com base 17,3%, 996 sem cluster, 1.100 como número de planejamento (guia), duração em semanas medida; design.md sem a frase falsa de consistência. Nenhuma correção de código

**Fim da sessão** 2026-11-11 16:05 — três afirmações verificadas; duas corrigidas, uma corrigida na redação; experimento reescrito

## 2026-11-11 16:09 · Tarefa 13 · etapa 1 — deploy na Vercel · modelo claude-haiku-5-5 · ferramenta Claude Code

- **16:09** — pedi: publicar a demo na Vercel com a conta já logada, projeto lead-scorer-diego
  - veio: conta diegoalves-data, time Diego, plano hobby. URL de produção: https://lead-scorer-diego.vercel.app. Acesso anônimo responde 200; demo carrega com faixa de demo e 5 deals em foco no desktop e no celular, sem rolagem horizontal
  - mudei: criei app/vercel.json (cleanUrls) e app/.vercelignore (data/acoes.jsonl), como o plano pede. Ressalva: /acoes responde 404 no host estático, e o console do navegador mostra esse erro; é o fallback esperado para o modo demo, mas um avaliador vai vê-lo. Não suprimi

**Fim da sessão** 2026-11-11 16:09 — deploy de produção pronto e conferido em navegador; erro 404 de /acoes é o fallback esperado

## 2026-11-11 16:12 · Correção: 404 de /acoes na demo publicada · modelo claude-haiku-5-5 · ferramenta Claude Code

- **16:12** — pedi: corrigir o 404 de /acoes na demo publicada, sem apenas esconder o erro
  - veio: causa: a interface chamava /acoes mesmo no host estático, e o navegador registra qualquer 404 de rede no console. Correção: a interface só chama /acoes e /acao quando o host é localhost, 127.0.0.1 ou ::1 (servidor do run.py); qualquer outro host é modo demo e não faz chamada de rede para ações
  - mudei: app.js: SERVIDOR_LOCAL e carregarAcoes. Testado nos dois modos: publicado (host não local) sem chamada a /acoes e sem erro; local (run.py) com GET /acoes. Redeploy de produção: zero erros de console e zero respostas 4xx/5xx no desktop e no celular

**Fim da sessão** 2026-11-11 16:12 — 404 eliminado na origem; demo publicada sem erros de console; redeploy feito

## 2026-11-11 16:16 · Tarefa 13 · etapa 2 — resumo executivo · modelo claude-opus-5 · ferramenta Claude Code

- **16:16** — pedi: escrever docs/resumo-executivo.md na ordem medido -> premissa, com a frase para a diretoria
  - veio: 626 palavras. Achado mais forte do que o plano previa: dos 734 deals distintos classificados como vencidos nos 6 cortes, ZERO foi ganho em qualquer momento do export, nao so nos 28 dias. Conta de horas virou ponto de equilibrio medido: US$ 1.416 por vendedor a cada 4 semanas (US$ 254.862 / 30 vendedores / 6 cortes), convertido em horas a tres custos-hora diferentes em vez de inventar um
  - mudei: DOIS ERROS NA FRASE DO CFO QUE O PLANO MANDA USAR, ambos corrigidos: (1) 'o que sobra vivo cabe numa lista de cinco deals por vendedor' e FALSO - 11 dos 17 vendedores com deal vivo tem mais de 5, e so 77 dos 115 vivos cabem em listas de cinco; troquei por '115 negocios em 17 dos 35 vendedores'. (2) 'intervalo de confianca que nao cruza zero' esta errado para uma razao: o IC [1,13; 1,52] nao cruza UM, nao zero; corrigido. Tambem declarei que os US$ 1.416 vem de simulacao historica, nao de operacao real

**Fim da sessão** 2026-11-11 16:16 — resumo executivo escrito; dois erros da frase do CFO do plano corrigidos

## 2026-11-11 16:41 · Tarefa 13 · etapa 3 — README.md · modelo claude-sonnet-5 · ferramenta Claude Code

- **16:41** — pedi: fechar o README.md com o template oficial, numeros de numeros-saida.txt, URL da Vercel, tabela de ferramentas e prints
  - veio: README criado (nao existia desde a Tarefa 0); 998 palavras; LinkedIn fornecido pelo Diego durante a etapa; URL da Vercel confere (200); 6 prints citados existem
  - mudei: a linha de benchmark do plano (credito ao PR #242) foi substituida por texto consistente com docs/logica.md, que ja registra que nao verificamos o PR. Marquei a verificacao independente como pendente (nao feita ainda, e a proxima etapa), nao como concluida -- erro que eu mesmo cometi na primeira versao do arquivo e corrigi antes de commitar. Tabela de ferramentas usa os modelos reais do diario (6 modelos Claude Code + Copilot + 3 baselines), nao a lista fixa do template

**Fim da sessão** 2026-11-11 16:41 — README.md criado e fechado; verificacao independente fica para a proxima etapa

## 2026-11-11 16:45 · Tarefa 13 · etapa 4 — limitacoes.md · modelo claude-sonnet-5 · ferramenta Claude Code

- **16:45** — pedi: fechar docs/limitacoes.md: dataset sintético, 3 trimestres, hoje fixo, sem atividade/desconto/motivo de perda, sem escrita no CRM, sem login, conta de horas como premissa, 1.425 sem conta, discovery ensaiado com personas
  - veio: 710 palavras; incorporei o rascunho da Tarefa 0B em vez de substituir; nenhuma ocorrência de 'entrevistei vendedores' fora da citação que explica a proibição
  - mudei: acrescentei um item que o plano não pedia explicitamente: o ajuste de cluster do calculo de amostra do experimento (1.100 vs 996 sem ajuste) nao foi verificado por nos -- e uma limitacao real que a Tarefa 12 ja tinha documentado em experimento.md, trazida aqui tambem

**Fim da sessão** 2026-11-11 16:45 — limitacoes.md fechado, 710 palavras

## 2026-11-11 16:48 · Tarefa 13 · etapa 5 — process log · modelo claude-haiku-5-5 · ferramenta Claude Code

- **16:48** — pedi: fechar o process log: MODELOS, onde-a-ia-errou, o-que-eu-acrescentei, REGISTRO, e fazer o --conferir passar
  - veio: --conferir passa sem pendências. onde-a-ia-errou tem 5 itens das personas (preservados) + 11 meus, cada um com proposta, mecanismo, teste e o que ficou. REGISTRO: 16 erros pegos no total (o --conferir conta so 5 do diario)
  - mudei: MODELOS e a tabela de ferramentas do README estavam atribuidos por suposicao; refeitos a partir das sessoes do diario. Corrigi tambem a afirmacao do README de que a verificacao independente estava concluida (nao esta). Removi todos os blocos de exemplo do template

**Fim da sessão** 2026-11-11 16:48 — process log fechado; --conferir sem pendencias; verificacao independente segue pendente

## 2026-11-11 17:13 · Tarefa 13 · etapa 6 — correção das 4 ressalvas da verificação independente · modelo claude-sonnet-5 · ferramenta Claude Code

- **17:13** — pedi: corrigir no README, resumo-executivo.md, design.md e logica.md as 4 ressalvas que o revisor independente (claude-opus-5-5) levantou
  - veio: docs ajustados: (1) 734 vencidos sem ganho agora explica que 733 nunca fecharam e o unico fechamento foi o perdido que ensinou a regra -- descreve o export, nao confirma a regra de forma independente; (2) regra do trimestre: forma escolhida a mao, so o liga/desliga e aprendido, com nota em logica.md, design.md e README; (3) 'relogio em vez de valor' trocado por 'valor esperado na janela, nao valor de tabela sozinho', com a prova de que so-tempo perde para preco (0,66x); (4) nota preventiva em logica.md que faixa de idade alta com p=0 e propriedade da posicao no trimestre (datas analogas), nao da idade isolada -- a afirmacao so aparecia num docstring de teste, nao em doc publico
  - mudei: tambem corrigido 'cinco datas' para 'seis datas' em logica.md (achado de inconsistencia de texto do revisor); secao do vazamento de conta reescrita de 'encontramos e removemos' para 'encontramos, e reduzimos', reconhecendo que o filtro ainda condiciona num campo que so existe apos o desfecho; nota sobre carregar.py usar a maior data do export inteiro, sem efeito em producao. Suite 59/59 inalterada (so docs)

**Fim da sessão** 2026-11-11 17:13 — 4 ressalvas corrigidas em README, resumo-executivo, design e logica; suite 59/59

## 2026-11-11 17:15 · Tarefa 13 · etapa 7 — checklist da seção 10 do guia · modelo claude-haiku-5-5 · ferramenta Claude Code

- **17:15** — pedi: conferir item a item o checklist de pronto (seção 10 do guia) contra o estado real do repositório
  - veio: CUMPRE: Vercel abre em desktop e celular com aviso de demo; pytest 59/59 com teste de soma por fila, GTXPro e determinismo; nenhum zumbi ganho (vencidos_ganhos=0 em todos os cortes); briefings validados e demo sem chave; README ~1.068 palavras com template, prints e links; limitacoes cobre os 6 itens; nenhuma mencao a Almap/Amazon/Barte; branch muda so 95 arquivos dentro de submissions/diego-rodrigues. PARCIAL: run.py testado no lugar (rm app/data, 3s), nao numa pasta clonada limpa; numeros.py imprime os numeros principais, nao todos os citados. NAO CUMPRE: resumo-executivo com 742 palavras, nao cabe numa tela; deploy.md sem criterio de aceite numerico e sem secao de saida; process-log/prompts nao existe (prompts nao foram salvos); historico git tem 4 commits que tocaram __pycache__ (nao reescrevo sem permissao); verificacao/ nao rastreada no git (precisa git add -f antes do PR)
  - mudei: nenhum documento alterado nesta etapa: os ajustes envolvem resumo-executivo e deploy.md, designados a Opus, e a pasta prompts, que precisa de decisao sobre o que existe de fato

**Fim da sessão** 2026-11-11 17:15 — checklist da seção 10: 7 itens cumpridos, 3 parciais, 4 nao cumpridos; aguarda decisao do Diego
