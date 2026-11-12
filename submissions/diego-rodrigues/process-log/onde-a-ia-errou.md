# Onde a IA errou e como foi corrigido

> O documento que mais pesa numa avaliação de uso de IA, porque é o único que não se consegue
> escrever sem ter verificado de verdade. Cada item precisa dos quatro campos. `registrar.py --erro`
> acrescenta a estrutura automaticamente.
>
> Regra: **erro sem mecanismo que o pegou não entra aqui.** "A IA errou e eu corrigi" é afirmação.
> "A IA propôs X, o teste Y falhou com este valor, virou Z" é prova.

## Parte 1 — erros das personas sintéticas (Tarefa 0B, discovery)

## Caio (Caçador de Meta) inventou duas situações concretas sobre a operação: A3 (oportunidade que fechou na penúltima quinta-feira do mês, com o decisor entrando e o orçamento como objeção) e A4 (cliente que disse que o projeto não era prioridade). Ambas vieram rotuladas como simuladas, mas em formato de experiência vivida.

- **O que a IA propôs:** Exemplo com detalhes de datas, pessoas e objeções, como se fosse um caso de referência.
- **Como foi pego:** Leitura da transcrição integral, na verificação do arquivo 01
- **Teste que fixa:** Checagem do rótulo 'situação simulada' em A3 e A4; sem esse rótulo, a resposta seria tratada como fato
- **O que ficou:** Transcrição mantida sem edição. Nenhuma das anedotas entra como fato no entregável. Premissa da tela de encerrar não usa essas histórias.
- **Quando:** 2026-11-11 12:29

## Helena (Consultora do Empresário) inventou uma negociação concreta em A1 (empresário que pediu proposta, sobrecarregado, sem quem executasse, depois sumiu) e uma oportunidade parada por cerca de três meses em A3. A2, A4 e B7 retomam o mesmo caso. Todas vieram rotuladas como situação simulada.

- **O que a IA propôs:** Caso de referência com datas, pedido de proposta e motivo de bloqueio, tratado como exemplo de atuação.
- **Como foi pego:** Leitura da transcrição integral, na verificação do arquivo 02
- **Teste que fixa:** Checagem dos rótulos 'situação simulada' e 'exemplo simulado' em A1 e A3
- **O que ficou:** Transcrição mantida sem edição. Nenhum caso entra como fato. Registrado também o desvio do enquadramento e a menção a 'material do desafio' em A4 e A8, que indica vazamento de contexto no Modo A.
- **Quando:** 2026-11-11 12:38

## Entrevista do Operador de Processo conduzida com o enquadramento sem o perfil ('Seu perfil é :.'). O agente se apresentou como 'Caio' e respondeu com a voz do Caçador de Meta às perguntas A1 a A5, B6, B7 e A8. A conversa também acrescentou a instrução 'Responda sem acessar a base de dados de venda', fora do protocolo, e a persona mencionou o 'material de contexto da persona' em A8.

- **O que a IA propôs:** Assumir a persona de outro arquétipo (Caio) quando o enquadramento não definiu o perfil.
- **Como foi pego:** Primeira resposta da conversa ('Sou Caio') e comparação com o enquadramento do roteiro
- **Teste que fixa:** Checagem da identidade declarada na abertura e do perfil no enquadramento; o perfil vazio foi a causa
- **O que ficou:** Transcrição não entra como entrevista do Operador (arquivo 03). Refazer em conversa nova com o enquadramento completo do plano. Registrado também o desvio de instrução extra e a menção a material de contexto.
- **Quando:** 2026-11-11 13:14

## Calibração Modo B, C9 do Consultor (gabarito 138 dias): o agente disse que havia 'trechos disponíveis de sales_pipeline.xlsx', embora não houvesse anexo nem acesso aos dados. Não deu número, mas inventou um acesso que não tinha.

- **O que a IA propôs:** Descrever um arquivo e trechos de dados que não estavam na conversa, para justificar a recusa.
- **Como foi pego:** Comparação da resposta com o enquadramento (sem acesso aos dados) e confirmação de que não houve anexo
- **Teste que fixa:** Checagem da conversa: nenhum arquivo anexado. Calibração C9 do Consultor
- **O que ficou:** Registrado como invenção sobre o próprio acesso. Resposta mantida no arquivo de calibração. Sem número inventado. Nenhuma conclusão do teste entra como fato.
- **Quando:** 2026-11-11 13:48

## Calibração Modo B, C9 do Operador (gabarito: mín 31, mediana 79, máx 194). O agente respondeu com a voz do Operador ('Como operador de processo...'), citou como fontes sales_pipeline.xlsx e sales_teams.xlsx sem anexo, e deu média de 69,6 por vendedor sobre 30 vendedores, quando só 27 têm negócio aberto. A média não é a mediana do gabarito.

- **O que a IA propôs:** Responder como a persona e citar arquivos de dados como fonte, para dar credibilidade à média.
- **Como foi pego:** Comparação com o critério de calibração (resposta como ele mesmo, sem fontes inventadas) e com o gabarito por vendedor
- **Teste que fixa:** Checagem da voz da resposta, da ausência de anexo e do denominador (27 vendedores com aberto)
- **O que ficou:** Registrado como invenção de fonte e falha de voz. Número dentro do intervalo, mas com denominador errado e medida diferente da mediana. Não entra como fato.
- **Quando:** 2026-11-11 13:50

## Parte 2 — erros meus nas tarefas 1 a 13, pegos por verificação

## Permutação de atributos dava sinal ao vendedor por causa de deals sem conta

- **O que a IA propôs:** Incluir todos os deals na permutação. O vendedor saiu com p = 0,012 e porte com p = 0,001.
- **Como foi pego:** Investigação do sinal: o grupo sem conta tinha 838 deals e nenhuma vitória (0 de 838). Com esses deals fora, vendedor vai a 0,141 e porte a 0,983.
- **Teste que fixa:** `test_atributos_nao_predizem_o_ganho` (conta, vendedor e porte com p > 0,05, com 1.000 repetições).
- **O que ficou:** `historico` exclui deals sem conta, com a causa documentada em `docs/logica.md`. O campo de conta só é preenchido após o desfecho (0 de 6.711 fechados sem conta), então presença ou ausência de conta nunca entra como sinal.

## A tese de "três semanas de pipeline" foi repetida do plano sem cálculo

- **O que a IA propôs:** Escrever no experimento "cerca de três semanas de pipeline do time inteiro", frase do plano que eu não tinha medido.
- **Como foi pego:** Medição do fluxo de entrada de deals no export: 8.300 deals com data de engajamento em 62 semanas, ou 134 por semana. Com isso, 1.100 deals por braço são cerca de 8 semanas.
- **Teste que fixa:** Cálculo reproduzível em `docs/experimento.md`, com a fonte do fluxo.
- **O que ficou:** Frase trocada por medição, marcada como limite inferior, já que supõe que todo deal que entra é elegível.

## A base de 22% do experimento era a taxa de acerto do relógio, não a taxa de decisão

- **O que a IA propôs:** Usar 22% (taxa de acerto do relógio, que conta só ganhos) como base da métrica primária, que é a taxa de decisão (ganhou ou perdeu em 28 dias).
- **Como foi pego:** Recálculo da taxa de decisão com um registro por deal: 17,3% (3.839 deals distintos). Pelo cálculo de amostra sem ajuste de cluster, +5 pontos sobre 17,3% pedem 996 deals por braço, não 1.100.
- **Teste que fixa:** Mesmo cálculo reproduzível em `docs/experimento.md`.
- **O que ficou:** Base corrigida para 17,3%. O 1.100 do guia fica como número de planejamento, por ser mais conservador.

## Afirmei que a diferença entre as ordens era consistente nos seis cortes

- **O que a IA propôs:** "é consistente nos seis cortes do backtest" em `design.md`.
- **Como foi pego:** Comparação dos valores por corte: o relógio ganha em 5 de 6. No corte de 23/10/2017, preço e prazo ganha (US$ 150.104 contra US$ 133.640).
- **Teste que fixa:** A própria tabela de backtest, que `test_relogio_bate_a_melhor_alternativa_honesta` cobre pelo intervalo de confiança.
- **O que ficou:** Frase reescrita: a afirmação se sustenta pelo IC, não pela consistência corte a corte.

## A frase do CFO dizia que os vivos cabem em listas de cinco por vendedor

- **O que a IA propôs:** "O que sobra vivo cabe numa lista de cinco deals por vendedor", frase que o plano mandava usar.
- **Como foi pego:** Distribuição de vivos por vendedor: 11 dos 17 vendedores com negócio vivo têm mais de cinco. Só 77 dos 115 vivos caberiam.
- **Teste que fixa:** Contagem sobre `scored.json` (`vendedores[].vivos`), reproduzível.
- **O que ficou:** Trocada por "115 negócios em 17 dos 35 vendedores", com a contagem no resumo executivo.

## A frase do CFO dizia que o intervalo de confiança não cruza zero

- **O que a IA propôs:** "intervalo de confiança que não cruza zero", frase do plano, para uma razão entre políticas.
- **Como foi pego:** O IC de uma razão positiva cruza o valor nulo em 1, não em zero: [1,13; 1,52].
- **Teste que fixa:** `test_relogio_bate_a_melhor_alternativa_honesta` exige `lo > 1.0`.
- **O que ficou:** Frase corrigida no resumo executivo.

## A atribuição da regra do trimestre ao PR #242 não estava verificada

- **O que a IA propôs:** Creditar a regra do fim do trimestre seguinte ao PR #242, no diário e na mensagem de commit. Eu havia escrito "verificada em script próprio" sem ter feito a verificação.
- **Como foi pego:** Leitura da descrição pública do PR #242 via `gh`: ela fala de negócios vencidos que não ganham, não da regra do trimestre. O PR #240 não menciona efeito de calendário.
- **Teste que fixa:** Nenhum teste; a verificação é de fonte, não de código.
- **O que ficou:** Creditado como medição nossa. Nota de correção no diário e em `docs/logica.md`.

## O cálculo de amostra do experimento foi escrito sem ser calculado

- **O que a IA propôs:** "~1.156 por braço" e que o ICC explicava a diferença entre 1.100 e o cálculo.
- **Como foi pego:** Recálculo: 1.160 com poder de 80%, 1.553 com 90%. O ICC com cerca de 70 deals por vendedor aumenta o tamanho da amostra (efeito de desenho ~3,1), não diminui.
- **Teste que fixa:** Cálculo reproduzível no texto de `docs/experimento.md`.
- **O que ficou:** Explicação com o ICC removida. Ajuste de cluster declarado como não verificado.

## A demo publicada chamava /acoes, que não existe no host estático

- **O que a IA propôs:** Interface que tenta `GET /acoes` e `POST /acao` em qualquer host, inclusive na Vercel.
- **Como foi pego:** Log de requisições do navegador em produção: 404 em `/acoes`, que o navegador registra no console.
- **Teste que fixa:** Verificação no navegador em produção (zero respostas 4xx/5xx, zero erros de console).
- **O que ficou:** Interface decide o modo pelo host: `localhost`, `127.0.0.1` ou `::1` usam o servidor; qualquer outro host é modo demo, sem chamada de rede para ações.

## A tabela de modelos do README foi escrita por suposição

- **O que a IA propôs:** Atribuir modelos por tipo de tarefa (Opus para docs, Haiku para deploy, Sonnet para implementação), sem conferir.
- **Como foi pego:** Conferência com as sessões registradas no diário: as Tarefas 4 a 8 rodaram em Haiku, não em Sonnet.
- **Teste que fixa:** `registrar.py --conferir`, que lista os modelos do diário.
- **O que ficou:** `MODELOS.md` e a tabela do README refeitos a partir do diário.

## O README marcou a verificação independente como concluída

- **O que a IA propôs:** Marcar a verificação independente como feita no checklist de evidências.
- **Como foi pego:** Conferência da pasta `process-log/verificacao/`, que tinha só `LEIA.md`. A verificação é a etapa 6 e ainda não aconteceu.
- **Teste que fixa:** Checagem de existência do relatório antes de marcar.
- **O que ficou:** Marcada como pendente.

## A geração de briefings não tratava erro da API, e um saldo zero derrubava o build

- **O que a IA propôs:** chamar `messages.create` sem captura de erro. A suíte de testes usava cliente falso que sempre respondia, então nenhum teste cobria falha da API.
- **Como foi pego:** a primeira execução com a chave real. A API respondeu `400 credit balance is too low`, e o `run.py` terminou com traceback, sem gravar nada.
- **Teste que fixa:** `test_erro_da_api_nao_derruba_e_para_de_chamar`, com um cliente que levanta o erro da API.
- **O que ficou:** erro da API cai no template do item, para de chamar a API no restante da execução e registra o motivo em `recusas`. A IA continua não ligada nesta submissão, porque a conta não tem créditos. Registrado sem arredondar.
