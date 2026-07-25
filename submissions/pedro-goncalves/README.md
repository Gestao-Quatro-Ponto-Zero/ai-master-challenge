# OSS: Operating System for Support

> **Decisão recomendada:** corrigir os registros e testar a IA em modo de observação.
> **Decisão vetada:** resposta autônoma em produção.

## Glossário rápido

- **Solicitação (ticket):** pedido, dúvida ou problema enviado ao atendimento.
- **Modo de observação (shadow mode):** a IA sugere, mas não responde nem altera sistemas.
- **Registro de data e hora (timestamp):** marca quando cada etapa aconteceu.
- **Confiança mínima (threshold):** limite abaixo do qual a IA pede ajuda.
- **Tempo de trabalho ativo (touch time):** minutos realmente gastos pela equipe.

## Resumo executivo

O primeiro arquivo é a amostra operacional da empresa fictícia, com **8.469 solicitações**; as
aproximadamente 30 mil do brief representam o volume anual da operação. A voz do cliente revelou
um problema concreto: **460 mensagens** dizem que o suporte já foi procurado várias vezes e o
problema continua sem solução. Há 152 casos abertos, 156 pendentes e 152 marcados como encerrados.
Os registros de data e hora também exigem correção: em **49,3% dos 2.769 pares disponíveis**, a
conclusão aparece antes da primeira resposta.

O copiloto separa duas filas. No atendimento ao cliente, preserva o tipo informado e procura
sinais de reincidência, possível dano, cancelamento, escalonamento e insatisfação forte. Na fila
de TI, sugere uma das oito categorias, mostra confiança e pede revisão quando necessário. Em
ambas, registra decisões sem guardar a mensagem original. A memória SQLite recupera somente
lições aprovadas. Um segundo modo recebe duas planilhas, exige validação humana das colunas e
gera um painel gerencial sem alterar as fontes.

No segundo arquivo, a prova técnica equilibrou **86,8% de desempenho entre os diferentes
assuntos**. No teste final, a IA decidiu sobre 69,7% dos casos e acertou 96,6% deles. Esse
resultado pertence à fila de suporte interno de TI, não à fila de clientes.

O cruzamento revelou a fronteira: quando o modelo do Dataset 2 foi aplicado às 8.469 mensagens
do Dataset 1, **85,1% viraram “Hardware”**, embora 49,5% superassem o limite de confiança. Ou
seja, confiança alta não corrige uma taxonomia incompatível. Por isso o piloto aceita filas
reais em CSV ou XLSX, mas mantém toda decisão em observação.

## As três respostas do diretor

| Pergunta | Resposta executiva | Próxima decisão |
|---|---|---|
| Onde perdemos tempo? | 460 mensagens contêm sinal de contato repetido sem solução; 152 casos ainda estão abertos | Revisar reincidências e auditar os 152 encerramentos |
| O que automatizar? | Detecção de cuidado na fila de clientes e sugestão de assunto na fila de TI | Testar em observação, sem responder ao cliente |
| Funciona? | 58 testes, casos do case reproduzíveis, 47.837 textos no experimento e 8.469 mensagens no teste cruzado | Medir erros durante o piloto |

## A decisão em uma frase

**Medir o fluxo real, rodar a IA em paralelo ao humano e só ampliar autonomia depois que erro, risco e capacidade forem observados.**

## O diferencial

O resultado mais importante não é o modelo. É o **critério para decidir**. A primeira análise
chegou a inventar tempo de trabalho, custo por hora e parcela automatizável. Esse caminho foi
interrompido, os dados foram auditados e a proposta foi redesenhada. O protótipo demonstra onde
usar IA e, principalmente, onde ela ainda não merece autonomia.

### Saber onde parar

Não usamos retropropagação a cada correção. Alterar pesos com poucos exemplos, sem conjunto final
independente e sem revisão transforma um erro humano em comportamento recorrente. Também não
usamos RAG: as lições atuais são poucas, estruturadas e críticas. Uma tabela SQLite aprovada por
outra pessoa é mais simples de auditar e mais previsível que busca vetorial com geração.

A memória guarda seis aprendizados operacionais comprovados no case e uma correção reproduzida do
classificador. Quando encontra um erro parecido, ela não decide no lugar da equipe: bloqueia a
automação, mostra a evidência e solicita revisão humana. Retropropagação só entra quando houver
volume autorizado, dados rotulados e teste final separado. RAG só entra quando conhecimento
validado e não estruturado crescer a ponto de regras explícitas deixarem de ser suficientes.

## Plano de 30 dias

| Janela | DRI sugerido | Entrega | Gate |
|---|---|---|---|
| Dias 1 a 5 | Operações + Dados | Registrar entrada, primeira resposta, trabalho ativo e conclusão | Datas e tempos confiáveis |
| Dias 6 a 15 | AI Master | Modo de observação no atendimento real | Acertos e erros por assunto medidos |
| Dias 16 a 25 | Líder de Suporte | Assistência para pequena equipe | Override, retrabalho e reabertura estáveis |
| Dias 26 a 30 | Diretor de Operações | Decisão de canário ou interrupção | Qualidade preservada e capacidade comprovada |

## Potencial econômico, sem falsa precisão

Usando **30 mil tickets apenas como contexto narrativo do brief**, a sensibilidade abaixo mostra capacidade líquida anual. Não é resultado observado:

| Cenário | Tickets no período | Elegível | Adoção | Taxa segura | Min poupados | Revisão | Retrabalho | Horas líquidas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Conservador | 30.000 | 10% | 30% | 85% | 3,0 | 1,5 min | 0,5 min | 8,3 h |
| Base | 30.000 | 25% | 50% | 90% | 5,0 | 1,0 min | 0,5 min | 187,5 h |
| Expansão | 30.000 | 40% | 70% | 95% | 7,0 | 0,5 min | 0,25 min | 826,0 h |

Cada linha usa a mesma fórmula:

`horas líquidas = tickets × elegibilidade × adoção × minutos poupados × taxa segura ÷ 60 - tickets × elegibilidade × adoção × revisão ÷ 60 - tickets × elegibilidade × adoção × retrabalho ÷ 60`

Os percentuais e minutos da tabela são **hipóteses**, não medições dos datasets. O cenário
interativo do protótipo permite substituí-los pelos dados reais do piloto.

O valor financeiro só deve ser calculado depois de medir touch time e aprovar custo-hora, integração, plataforma e manutenção.

## Achados

| Achado | Evidência | Consequência |
|---|---:|---|
| Volume real do Dataset 1 | 8.469 tickets | Não usar 30 mil como denominador |
| Pares temporais inválidos | 1.365 de 2.769 | Vetar FRT, TTR e ROI observado |
| Texto templado | 8.469 descrições com placeholder e trechos ruidosos | Preferir regras auditáveis e revisão humana |
| Duplicidade técnica | 0 linhas idênticas e 0 IDs repetidos | Não apagar descrições repetidas, pois podem representar reincidência |
| Cliente sem solução | 460 relatos de contatos repetidos; 152 abertos e 152 encerrados | Subir para revisão humana e auditar encerramentos |
| Transferência entre datasets | 85,1% das previsões concentradas em “Hardware” | Não usar a taxonomia de TI para rotear clientes |
| Sinal de CSAT | Efeitos nulos ou desprezíveis | Não priorizar segmento por causalidade |
| Prova técnica | Macro-F1 0,868 | Classificação é tecnicamente viável no Dataset 2 |
| Abstenção | 69,7% de cobertura a 96,6% de acurácia no teste final | Expor a troca entre escala e erro |

![Ausência de dados por status](artifacts/figures/support-missingness-by-status.png)

![Cobertura e acurácia](artifacts/figures/coverage-vs-accuracy.png)

## Matriz de decisão

Escala de 1 a 5. A nota ponderada não supera veto crítico.

| Alternativa | Evidência 30% | Impacto 25% | Segurança 20% | Viabilidade 15% | Diferenciação 10% | Nota | Veto |
|---|---:|---:|---:|---:|---:|---:|---|
| Resposta autônoma | 1,0 | 4,0 | 1,0 | 2,0 | 3,0 | 2,1 | Sim |
| Roteamento automático | 4,0 | 4,0 | 3,0 | 4,0 | 4,0 | 3,8 | Produção |
| Copiloto em modo de observação | 5,0 | 3,5 | 5,0 | 5,0 | 4,5 | **4,6** | Não |
| Dashboard isolado | 3,0 | 2,0 | 5,0 | 5,0 | 2,0 | 3,4 | Não |

As notas são **julgamento gerencial explícito**, não métricas observadas. A conta é a soma de cada
nota multiplicada pelo peso da coluna. Exemplo do copiloto:
`5×30% + 3,5×25% + 5×20% + 5×15% + 4,5×10% = 4,575`, arredondado para `4,6`.

## O que funciona

O OSS funciona como ferramenta de operação e avaliação. Diagnóstico, evidências,
matriz de decisão, plano e cenários permanecem nos documentos, mas são acessíveis em
`Entregáveis`. A aplicação contém `Visão geral`, `Triagem diária`, `Análise da operação`,
`Aprendizado`, `Entregáveis` e `Ajuda`.

No piloto, o usuário consegue:

- receber a solicitação com ocultação de alguns padrões de dados pessoais;
- processar uma fila CSV com até 5.000 linhas por execução;
- receber duas planilhas em CSV ou XLSX, com limite explícito de até 5.000 linhas por base;
- mostrar estrutura, preenchimento, cardinalidade e papel sugerido de cada coluna;
- exigir confirmação humana para manter, remover, ordenar e interpretar colunas;
- impedir relação automática entre planilhas sem chave validada;
- abrir um painel gerencial centralizado após a análise;
- executar os casos reproduzíveis do case;
- exportar ID, sugestão, confiança, cuidado prioritário e próximo passo sem copiar mensagens;
- identificar sinais de cuidado prioritário com o cliente;
- classificar em oito categorias;
- ver confiança e alternativas;
- pedir ajuda quando não há confiança suficiente;
- exigir decisão humana em assuntos sensíveis;
- forçar todas as decisões para uma pessoa;
- registrar decisões sem guardar texto bruto;
- registrar correções numa memória SQLite;
- usar somente lições aprovadas e preservar seu histórico;
- consultar uma aba de ajuda sem sair do fluxo.
- abrir os documentos formatados na ordem recomendada dentro do próprio OSS.

## Rodar

Requer Python 3.11 ou superior e [uv](https://docs.astral.sh/uv/).

```bash
cd solution
uv sync
uv run streamlit run app.py
```

Abra `http://localhost:8501`.

## Testar

```bash
uv run python -m unittest discover -s tests -v
```

Resultado validado: **58 testes aprovados**.

## Reproduzir a análise

Baixe os dois arquivos CC0 indicados no challenge e posicione:

```text
data/raw/customer-support/customer_support_tickets.csv
data/raw/it-service/all_tickets_processed_improved_v3.csv
```

Depois:

```bash
uv run python scripts/data_audit.py
uv run python scripts/cross_dataset_audit.py
uv run python scripts/train_classifier.py
uv run python scripts/build_figures.py
uv run python scripts/build_notebook.py
uv run python scripts/build_demo_matrix.py
uv run python scripts/build_case_demo_data.py
```

O notebook executado está em `notebooks/challenge-002-analysis.ipynb`. Os dados brutos não são versionados.

## Recomendações

1. **Instrumentar antes de automatizar:** criação, primeira resposta, touch time, resolução, reabertura e override.
2. **Modo de observação:** comparar IA e humano nas filas do case sem impacto no cliente.
3. **Assistência controlada:** exibir sugestão, manter confirmação humana e medir retrabalho.
4. **Canário restrito:** somente ações reversíveis depois dos gates de segurança.

## Limitações

- O Dataset 1 não mede tempos operacionais de forma válida.
- O Dataset 2 representa suporte interno de TI e não compartilha a taxonomia da fila de clientes.
- O teste cruzado mostrou concentração de 85,1% em “Hardware”; confiança não valida transferência entre taxonomias.
- O exercício não inclui validação temporal nem experimento em produção.
- Regex não detecta todo tipo de PII.
- Threshold validado em dados públicos não autoriza produção.
- ROI permanece cenário até touch time, custos, adoção e retrabalho serem medidos.
- Autor e revisor da memória são identificados, mas ainda não autenticados.
- A memória precisa ser comparada ligada e desligada nas filas do piloto.
- A matriz 16/16 prova o comportamento dos casos escolhidos, não cobertura de toda linguagem possível.
- O fluxo universal organiza a análise, mas não conhece a semântica de qualquer empresa sem validação humana.
- O painel só mostra indicadores sustentados pelos campos recebidos.
- O score de qualidade mede estrutura, não desempenho da operação.
- Retenção e eliminação excepcional do SQLite precisam de regra antes de produção.
- O gate de cliente usa regras explícitas e pode não reconhecer toda forma de reclamação.

## Mapa da entrega

- `docs/gate-1/`: auditoria, diagnóstico e decisão
- `docs/gate-2/`: modelo, arquitetura, claims e medição
- `docs/gate-3/`: foco no cliente, trajetória profissional, memória e caminho seguro para retreinamento
- `artifacts/`: métricas, tabelas, figuras e modelo
- `artifacts/demo/`: matriz demonstrativa de 16 casos, sem dados pessoais
- `notebooks/`: análise executada
- `src/`: política, classificação, privacidade, auditoria, memória e cenários
- `tests/`: testes da política e da interface
- `process-log/`: uso de IA, erros e correções

## Process log

Leia [`process-log/README.md`](process-log/README.md).

## Sobre mim

- **Nome:** Pedro Gonçalves
- **LinkedIn:** [linkedin.com/in/pedrotg22](https://br.linkedin.com/in/pedrotg22)
- **Formação:** Engenharia de Produção, Unicamp
- **Challenge:** 002, Redesign de Suporte

Candidato de submissão preparado em 24/07/2026. A entrega só é liberada depois de duas rodadas
humanas aprovadas conforme `docs/gate-3/protocolo-aprovacao.md`.
