# 02 — Registro de decisões (quem decidiu o quê)

Ferramenta: Claude Code (Opus 5.5), em sessão única, trabalhando como par. A IA executa e eu tomo as decisões-chave. Este arquivo registra cada bifurcação: o que a IA propôs, o que eu decidi e por quê. As citações entre aspas são as minhas mensagens originais.

---

## D1 — Qual desafio (04/11/2026)

- **A IA propôs:** recomendou o 003 (Lead Scorer) com base no meu perfil de vendas.
- **Eu pedi antes:** *"Analise todos os Pull requests, veja quais o pessoal mais fez e quais menos fizeram"*.
- **O que os dados mostraram:** 226 PRs, sendo 224 submissões de 210 pessoas.
  - 003: 48%
  - 002: 23%
  - 001: 21%
  - 004: 8%
- **A IA então propôs:** o 003 só se eu tivesse um ângulo próprio; caso contrário, o 004, por ter menos concorrência.
- **Eu decidi:** *"Vamos com o 002"*.
- **Por quê:** é o desafio que pede diagnóstico, automação e algo rodando ao mesmo tempo, ou seja, o mais próximo do trabalho real de um AI Master. Não segui nenhuma das duas recomendações da IA.

## D2 — Modo de trabalho

- **Eu escolhi:** par de trabalho. A IA executa e para nas decisões-chave.

## D3 — Minhas hipóteses vêm antes da estratégia da IA

- **Contexto:** a IA tinha auditado o Dataset 1 (sintético) e encontrado as avaliações reais do G4 nos PRs. Nelas, a nota cai quando "a estratégia foi gerada pela IA antes da leitura do candidato".
- **A IA propôs:** parar e me pedir a minha leitura antes de propor qualquer solução.
- **Eu escrevi as hipóteses H1 a H9** sem consultar a IA ([01-hipoteses-antes-da-ia.md](01-hipoteses-antes-da-ia.md)).
- **Efeito:** o protótipo saiu da minha H8, *"um assistente que prepara respostas para revisão do atendente"*, e não de uma sugestão da IA.

## D4 — Diferenciação medida, não suposta

- **Eu pedi:** *"Me liste novamente todas as possíveis diferenciações do que o pessoal fez, me dê 5 opções."*
- **A IA fez:** contou nos 50 PRs do 002 quantos já fizeram cada ideia.
- **Correção no caminho:** a contagem por palavra-chave dizia que 10 PRs tinham "WhatsApp". Lendo o contexto, **nenhum** tinha integração construída; eram só menções como "próximo passo".
- **Resultado:**

| Diferencial | Quantos dos 50 fizeram |
|---|---|
| (1) Teste com pessoas reais | 0 |
| (2) Preenchimento de campos + pergunta do que falta | 0 |
| (3) Canal real | 0 construído |
| (4) Business case de comprador enterprise | 8 |
| (5) Curva de aprendizado + custo do erro | 8 a 9 |

## D5 — Canal: questionei o custo e o caminho até chegar ao Telegram

1. A IA sugeriu WhatsApp pelo LetsBot, que eu já tinha conectado.
2. Eu: *"Eu preciso desse plano aqui ou dá para fazer algo mais barato?"*, sobre um complemento de bot com IA de USD 54,99/mês.
   - **Achado:** o complemento era a IA do próprio LetsBot. Usá-la faria a IA da demo não ser a minha. Além disso, a conta não tinha o complemento de API, então nada funcionaria.
3. Eu: *"Para eu usar o WhatsApp a única opção é pela LetsBot?"*
   - A IA levantou 5 caminhos e descartou as bibliotecas não oficiais, porque violam os termos do WhatsApp e o número pode ser banido.
4. Eu: *"E agora WhatsApp pagando?"*
   - A IA levantou custos (Meta direto ≈ R$ 50 no 1º mês; intermediários ≈ US$ 49–59/mês).
5. Eu: *"E se ao invés do WhatsApp eu utilizasse o Telegram?"*
   - **A ideia foi minha.** A IA validou e acrescentou o grupo de atendentes com um tópico por fila, que funciona como tela do atendente sem custo de interface.

- **Decisão:** Telegram agora, com núcleo independente do canal. O WhatsApp fica documentado como próximo adaptador.

## D6 — Pacote final

- **Eu:** *"Podemos fechar esse pacote sim, mas queria ainda incluir o desenvolvimento dos outros diferenciais que você pontuou"*.
- **O pacote:**
  1. **Núcleo:** classificar, preencher campos e perguntar o que falta, validado no Dataset 2.
  2. **Canal:** bot no Telegram com a tela do atendente montada com tópicos.
  3. **Prova:** teste com 3 a 5 colegas como atendentes, com e sem o assistente.
  4. **Memo de 1 página** para o Diretor, com a minha visão de comprador enterprise.
  5. **Análise:** curva de aprendizado e custo do erro por fila.

## D7 — LLM no protótipo: qual modelo (04/11/2026)

- **A IA propôs:** um design híbrido. O LLM entende o português e extrai campos em JSON validado. O classificador validado decide a fila. A resposta sai de conteúdo aprovado (minha H5). Para o modelo, sugeriu o Haiku 5.5, com uma comparação contra o Opus 5.5 antes de fechar.
- **Eu:** *"Pode seguir"*, e salvei as duas chaves no `.env`. Aprovei a recomendação da IA, e a escolha ficou condicionada à medição.
- **Medição** (`analysis/05_pt_eval.py`, 160 chamados de teste reescritos em português):

| | Haiku 5.5 | Opus 5.5 (48 casos) |
|---|---|---|
| Acerto do pipeline em português | 72% | 71% |
| Custo por mensagem | US$ 0,0005 | US$ 0,019 |
| Latência mediana | 2,1 s | 4,1 s |

- **Decisão:** fica o Haiku. O Opus não melhora o acerto e custa 40 vezes mais.

## D8 — Achados que mudaram o desenho (decididos pelos dados, com regra definida antes)

- **O LLM sozinho acerta só 43% das filas** (o classificador acerta 72% no mesmo texto). Nesta empresa, "Outlook pedindo senha" é *permissão de admin* e "acesso a pasta" é *Armazenamento*. A fila é uma convenção interna, e só o histórico rotulado a conhece. **Regra: o LLM nunca decide a fila.**
- **Discordância LLM × classificador vai para humano?** Ficou definido antes de medir que só iria se o acerto dos automáticos com discordância fosse < 80%. **Resultado:** 12 de 12 certos, então a regra não entrou.
- **Com o português, cai a cobertura, não a qualidade:** o automático foi de 45% para 23% do volume, e o acerto se manteve em 97%. A política de limiar por fila protege contra mudança de entrada.
- **Só 44% das primeiras mensagens trazem os campos obrigatórios.** Isso é a minha H3a medida por campos, e justifica a pergunta automática antes de ocupar um atendente.

## D9 — Trava de filas sensíveis (PENDENTE: decisão minha de apetite a risco)

- **Achado da IA** (`analysis/04_cost_of_error.py`): mesmo com RH e permissão de admin sempre passando por humano, ~282 chamados sensíveis por ano caem sozinhos na fila errada, porque o modelo os confunde com Hardware com confiança alta.
- **Trava:** se P(RH) + P(admin) ≥ G, o chamado vai para humano.

| G | Automático | Acerto no automático | Sensíveis que escapam/ano |
|---|---|---|---|
| sem trava | 54,2% | 95,3% | 282 |
| 0,10 | 51,0% | 95,8% | 178 |
| 0,05 | 45,4% | 96,5% | 81 |
| 0,02 | 36,5% | 97,1% | 23 |

- **Valor provisório:** 0,05.
- **Nuance:** vários "vazamentos" parecem rótulo errado no dataset, como "erro de conexão no Exchange" rotulado como permissão de admin. Há uma amostra de 30 para revisão humana em `outputs/revisao_humana_vazamentos.csv`.

## D10 — Onde o bot roda

- **Eu perguntei:** *"Vai ser necessário colocar essa aplicação rodando em algum lugar?"*
- **Resposta:** sim, há um processo que precisa ficar ligado. No teste, roda no meu Mac. Na avaliação, um servidor pequeno (decisão adiada para perto do PR). Para reprodutibilidade, há um modo sem Telegram e sem chave (`app.simulate`, `tests/test_fluxo_bot.py`).

---

## Onde a IA errou até aqui (e como foi corrigido)

| # | Erro | Como apareceu | Correção |
|---|---|---|---|
| E1 | Teste KS de uniformidade aplicado a idade, que é número inteiro, gerou falso alarme (p=0,000) | Revisão do output | Trocado por qui-quadrado; o KS não serve para dado discreto |
| E2 | Supor que "o Dataset 1 é sintético" seria diferencial | Checagem dos concorrentes: 40 de 50 já diziam isso | O achado virou ponto de partida, não destaque |
| E3 | Contagem por palavra-chave inflou "WhatsApp" (10 PRs) | Leitura do contexto | 0 integrações reais |
| E4 | Modelo de boosting falhou com matriz esparsa | Erro de execução | Matriz densa no one-hot |
| E5 | A IA recomendou o 003 | Decisão minha (D1) | Escolhi o 002 |
| E6 | O prompt marcava troca da própria senha como "risco de segurança", e a resposta automática de senha nunca disparava | Teste de ponta a ponta com mensagens reais | Prompt v2 com exclusão explícita |
| E7 | Pedido de admin recebia a pergunta "qual sistema quer acessar?", que é a pergunta da fila errada | Mesmo teste | Só pergunta campo de fila quando a fila é conhecida |
| E8 | "Preciso de ajuda" ia para Acessos com 87% de confiança (texto vago engana o classificador) | Mesmo teste | Sem nenhum campo extraído, pede descrição genérica |
| E9 | `groupby.apply` mudou de comportamento no pandas e derrubou o script | Erro de execução | `groupby.sample` |
| E10 | Variável inexistente no teclado da triagem; o bot quebraria no primeiro chamado incerto | Pyright (analisador estático), não a IA | Corrigido antes do 1º uso |
| E11 | O cronômetro reiniciava depois de uma transferência e subestimaria o tempo de atendimento | Revisão do código de medição | Tempo conta do 1º card |
| E12 | A IA escreveu `reply_to_message_id`, que não existe mais na versão instalada da biblioteca | Conferência da assinatura antes de rodar | `reply_parameters` |
| E13 | O erro E9 ocorreu *depois* das chamadas de API: 135 gerações e 136 triagens foram feitas com uma amostra que não entrou em nenhum resultado (~US$ 0,60 desperdiçados) | Contagem do cache antes do commit (639 arquivos, esperados 368) | Cache órfão movido para fora do repositório. O 05 reproduz idêntico offline só com o cache commitado |
