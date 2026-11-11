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
