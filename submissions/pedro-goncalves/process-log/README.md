# Process log: como usei IA

## Ferramentas

| Ferramenta | Papel |
|---|---|
| Codex | Coordenação, pesquisa, auditoria, implementação, testes e integração |
| Maestri | Orquestração visual da equipe e isolamento de papéis |
| Lume, Antigravity | Primeiro rascunho de diagnóstico operacional |
| Nexo, Antigravity | Primeiro rascunho de fronteira humano-IA |
| Crivo, Codex independente | Rubrica adversarial e gates de qualidade |
| Context7 | Documentação atual do Streamlit e AppTest |

## Decomposição antes do build

O problema foi separado em sete gates:

1. contexto, rubrica e matriz de decisão;
2. auditoria dos dois datasets;
3. diagnóstico operacional e ROI;
4. fronteira humano-IA;
5. protótipo;
6. documentação e process log;
7. revisão adversarial.

Três agentes foram criados no Maestri. Lume e Nexo podiam propor; Crivo não podia editar nem avaliar sem evidência. O Codex permaneceu como quarto papel, responsável por integração e decisão.

## Linha do tempo

| Momento | Ação | Resultado |
|---|---|---|
| 23/07 | Leitura do challenge, guia, template e CONTRIBUTING | Critérios formais e time budget consolidados |
| 23/07 | Crivo criou rubrica antes de ver a solução | Bloqueadores definidos sem viés de confirmação |
| 23/07 | Lume e Nexo produziram rascunhos paralelos | Hipóteses úteis, mas também números e regras sem evidência |
| 24/07 | Download, hash e auditoria física dos arquivos | Dataset 1 divergiu do brief e teve campos temporais inválidos |
| 24/07 | Matriz ponderada com veto crítico | Shadow mode venceu com 4,6 de 5 |
| 24/07 | Treino e calibração do classificador | Macro-F1 0,868 no teste final do Dataset 2 |
| 24/07 | Construção do protótipo e testes | 16 testes aprovados no primeiro gate final |
| 24/07 | Revisão de claims e documentação | ROI observado e automação produtiva foram vetados |
| 24/07 | Gate final independente | FAIL inicial por precedência, seleção de threshold e fingerprint |
| 24/07 | Correção adversarial | Política reordenada, split 70/15/15 e log sem fingerprint |
| 24/07 | Revisão pela lente pública de Bruno Nardon | Decisão executiva, demo pronta e piloto de 30 dias incorporados |
| 24/07 | Validação pós-revisão executiva | 18 testes aprovados e duas telas inspecionadas |
| 24/07 | Gate Final 3 | FAIL por comandos, premissa econômica oculta e links |
| 24/07 | Correção executiva final | Premissas completas, caminhos corrigidos e teste determinístico |
| 24/07 | Reavaliação do Gate Final 3 | PASS, 18 testes e nenhum bloqueador material |
| 24/07 | Revisão pelos critérios canônicos | Entrada CSV e teste cruzado dos 8.469 textos incorporados |
| 24/07 | Correção do enquadramento do case | Empresa fictícia tratada como cliente e 460 reincidências priorizadas |
| 24/07 | Gate Final 4B | PASS no snapshot staged, 35 testes e nenhum bloqueador |

## Onde a IA errou

O primeiro rascunho de diagnóstico assumiu:

- 30 mil tickets como volume medido;
- touch time de 10 e 30 minutos;
- custo de R$ 25 por hora;
- 40% de elegibilidade;
- custos anuais de implantação;
- hipóteses causais sobre TTR e CSAT.

O primeiro rascunho de automação também sugeriu prioridade automática, respostas diretas, categorias equivalentes entre os datasets e confiança fictícia.

Esses elementos foram rejeitados porque não existiam no arquivo, no brief ou em fonte operacional aprovada.

## Como corrigi

1. Recontagem por parser CSV, não por linhas físicas do arquivo.
2. Hash SHA-256 e relatório de qualidade reproduzível.
3. Inspeção semântica dos campos temporais.
4. Separação explícita dos papéis dos datasets.
5. Classificador treinado apenas no Dataset 2.
6. Split 70/15/15, baseline, threshold na validação, teste final, calibração e abstenção.
7. Claim ledger separando medido, hipótese e não provado.
8. Calculadora paramétrica sem defaults financeiros inventados.
9. Política determinística com human-only, kill switch e log sem texto bruto.

## Julgamento humano que mudou a solução

A pergunta central deixou de ser "onde colocar IA" e passou a ser **"qual decisão tem evidência suficiente para receber autonomia"**.

Foi adotada uma matriz ponderada:

- evidência verificável: 30%;
- impacto operacional: 25%;
- segurança e controle humano: 20%;
- viabilidade: 15%;
- diferenciação: 10%.

Um problema crítico de evidência, segurança ou conformidade aplica veto mesmo quando a média ponderada é alta. Essa regra impediu que o protótipo tecnicamente funcional virasse uma alegação de produção.

## Iterações principais

### Iteração 1

Proposta ampla de diagnóstico e automação. Reprovada por premissas não rastreáveis.

### Iteração 2

Auditoria de dados e redefinição do problema. A falta de telemetria tornou-se o achado principal.

### Iteração 3

Classificador com confiança calibrada e abstenção. Uso limitado ao Dataset 2.

### Iteração 4

Política de controle humano, PII, audit log, ROI paramétrico e testes da interface.

### Iteração 5

Revisão de claims, limites e conformidade da pasta de submissão.

### Iteração 6

O Crivo reprovou a primeira versão final por três achados altos:

1. shadow mode era avaliado antes de categoria sensível e baixa confiança;
2. o mesmo conjunto era usado para observar e escolher threshold;
3. o log guardava SHA-256 determinístico do texto mascarado.

A política foi reordenada, foram adicionados testes combinados, o experimento passou a usar treino 70%, validação de threshold 15% e teste final 15%, e todo fingerprint derivado do texto foi removido. A calculadora também passou a subtrair retrabalho no mesmo horizonte dos demais parâmetros.

### Iteração 7

A entrega tecnicamente aprovada foi relida pela lente pública de Bruno Nardon: eliminar o erro óbvio antes de otimizar, transformar plano em execução e entregar um MVP vertical funcional, valioso e utilizável. Nenhuma fala privada ou avaliação oficial do G4 foi presumida.

O principal defeito era gerencial: um diretor precisava atravessar diagnóstico, método e controles para descobrir qual decisão tomar. A versão foi reorganizada para responder em cerca de 60 segundos:

1. onde o tempo é perdido e o que ainda não pode ser medido;
2. qual tarefa merece IA primeiro;
3. o que já funciona e com qual evidência;
4. quem faz o quê nos primeiros 30 dias;
5. quais gates impedem autonomia prematura.

O protótipo passou a abrir com um cenário de demonstração preenchido, sem exigir preparação do avaliador. Foi adicionada uma sensibilidade econômica com todas as premissas visíveis, editáveis e sem converter cenário em resultado observado. Dois screenshots foram inspecionados em 1440 x 1100. Os testes de cenário de demonstração e dos três cálculos de referência elevaram a suíte para 18 testes.

### Iteração 8

O Gate Final 3 reprovou a primeira versão executiva por três inconsistências: os comandos do README não entravam em `solution/`, a sensibilidade econômica escondia a taxa segura usada no cálculo e dois links de figuras apontavam para o nível errado.

Os comandos e links foram corrigidos. A tabela passou a mostrar tickets no período, elegibilidade, adoção, taxa segura, minutos poupados, revisão, retrabalho e horas líquidas. Os três cenários foram centralizados no módulo de ROI e ganharam teste determinístico. A aba de cenários foi inspecionada em 1440 x 1100 antes do novo gate.

### Iteração 9

A solução foi revista pela tese do vídeo indicado por Pedro: ferramentas e automações tendem a
virar infraestrutura comum; o valor permanece no diagnóstico do problema, no redesenho do
processo e na medição do resultado. O pedido inicial era fazer a IA "aprender sempre com os
erros usando retropropagação". A revisão separou três mecanismos diferentes:

1. log registra o que aconteceu;
2. memória por recuperação consulta lições anteriores;
3. retropropagação altera pesos durante um retreinamento.

Foi implementada uma memória SQLite local com eventos de feedback, lições e evidências. Uma
correção humana pode criar uma lição candidata; somente uma aprovação explícita permite que ela
participe de análises futuras. Quando uma lição aprovada encontra um padrão parecido, o sistema
força revisão humana e mostra a recomendação, sem executar ação externa.

O banco não guarda o texto bruto da solicitação. Lições repetidas aumentam a contagem de
evidências em vez de criar duplicatas. Aprendizados podem ser aprovados ou desativados sem apagar
o histórico. A documentação proíbe chamar esse mecanismo de retropropagação contínua. O eventual
retreinamento permanece como fase posterior, com dados autorizados, teste final separado,
comparação com a versão anterior e rollback.

Três revisores independentes contribuíram em leitura: Lume analisou o problema operacional, Nexo
propôs a estrutura auditável e Crivo definiu riscos de feedback ruim, envenenamento, privacidade
e regressão. O primeiro gate da memória foi FAIL porque campos livres aceitavam dados pessoais e
o mesmo operador podia criar e aprovar uma lição. A implementação passou a gerar a instrução
automaticamente, rejeitar padrões pessoais e credenciais, limitar termos, exigir autor e revisor
diferentes e registrar autoria, data e justificativa. Eventos de feedback ganharam proteção
contra alteração e exclusão comum. A suíte passou de 18 para 26 testes.

No segundo gate independente, o Crivo executou os 26 testes em cópia temporária e retornou
**PASS**, sem bloqueador. Permaneceram como riscos pré-produção: identidades autodeclaradas,
cobertura limitada dos filtros de dados sensíveis, política de retenção e comprovação do ganho
com memória ligada versus desligada nas filas do piloto.

### Iteração 10

Pedro identificou um risco que as métricas de classificação não capturavam: `Ticket Description`
contém a voz do cliente e uma reclamação não pode receber o mesmo tratamento de um pedido comum.
A hipótese foi testada contra o Dataset 1 antes da implementação. Todas as 8.469 descrições têm
placeholder de template, e a associação entre `Ticket Subject` e `Ticket Type` é praticamente
nula. Portanto, o arquivo não sustenta treinar um detector semântico nem tratar os rótulos como
verdade operacional.

Foi criado um gate conservador de foco no cliente, anterior ao classificador. Regras explícitas
procuram reincidência, dano financeiro, intenção de cancelamento, risco legal, segurança,
privacidade e forte insatisfação. Qualquer sinal força revisão humana. O audit log guarda apenas
os códigos dos sinais, sem o texto da solicitação. O mecanismo não atribui prioridade final nem
responde ao cliente.

O aplicativo também foi separado dos artefatos de avaliação. O protótipo agora contém somente
`Triagem`, `Aprendizado` e `Ajuda`, como uma ferramenta para uso comum numa tarde de trabalho.
Diagnóstico, evidências, matriz de decisão, cenários econômicos e plano de implantação permanecem
nos documentos obrigatórios. A suíte passou de 26 para 30 testes, incluindo reclamação com alta
confiança que ainda assim deve ser encaminhada a uma pessoa.

### Iteração 11

Os critérios literais do challenge foram relidos para testar uma falha de enquadramento: “usar
ambos os datasets” não poderia significar apenas citar um no diagnóstico e treinar no outro. O
modelo do Dataset 2 foi então aplicado às 8.469 mensagens do Dataset 1. Embora 49,5% das previsões
superassem o threshold de 0,75, 85,1% foram concentradas em `Hardware`. Sem rótulos compatíveis,
não há acurácia cruzada calculável.

Esse resultado virou evidência, não inconveniente escondido. Ele demonstra que confiança alta
não compensa incompatibilidade de taxonomia e impede roteamento automático entre domínios. O
aplicativo passou a aceitar uma fila CSV com até 5.000 linhas, aplicar o mesmo fluxo de proteção e
exportar somente ID e resultados. Assim, o avaliador pode usar os arquivos públicos ou outro lote
autorizado, sem depender dos exemplos de demonstração. A suíte passou para 32 testes, incluindo
consistência entre previsão individual e em lote e integridade da auditoria cruzada.

### Iteração 12

Pedro corrigiu uma premissa do integrador: o G4 é o avaliador do trabalho do AI Master, não a
empresa cujo atendimento seria posteriormente validado. Os dois arquivos representam a operação
da empresa fictícia dentro do exercício e precisam ser usados como o cotidiano disponível, mesmo
quando apresentam ruído.

A releitura mudou o diagnóstico e o produto. As mensagens deixaram de ser descritas apenas como
limitação e passaram a orientar a fila: 460 solicitações dizem explicitamente que o cliente já
procurou o suporte várias vezes e continua sem solução. Dessas, 152 estão abertas, 156 pendentes
e 152 encerradas. O protótipo agora separa atendimento ao cliente e suporte interno de TI. Na
primeira fila, preserva o tipo informado e aplica o gate de cuidado; na segunda, usa o
classificador de oito categorias. Assim, nenhuma mensagem de cliente recebe a categoria
`Hardware` apenas porque o modelo de TI demonstrou confiança. Um teste adicional fixa o achado
dos 460 relatos e sua distribuição por status, elevando a suíte para 33 testes.

### Iteração 13

O Gate Final 4 retornou **FAIL** por dois bloqueadores. Primeiro, os novos arquivos ainda não
estavam rastreados pelo Git. Segundo, o fluxo CSV inferia “cliente” quando a coluna se chamava
`Ticket Description`; uma fila de clientes com outro nome de coluna poderia receber o modelo de
TI. O teste existente apenas confirmava a presença visual do uploader.

A lógica em lote foi movida para `batch.py`. Agora o contexto escolhido explicitamente é a única
fonte de verdade, independentemente do nome das colunas. Foram adicionados dois testes de fluxo:
um CSV de clientes chamado `body_text`, que proíbe qualquer chamada ao classificador de TI, e um
CSV de TI chamado `customer_words`, que exige a classificação. Ambos verificam IDs, decisões e
ausência do texto bruto na saída. A suíte passou para 35 testes.

Na reavaliação 4B, o Crivo criou um snapshot somente do conteúdo staged, reproduziu o ambiente
com Python 3.11 e executou os 35 testes. Confirmou que o diff contém apenas a pasta da submissão,
todos os arquivos materiais estão rastreados e nenhum cache, log ou banco runtime permanece. O
veredito foi **PASS**, sem bloqueador crítico, alto ou médio.

### Gate final

O Crivo executou `uv sync --frozen` e os 16 testes em uma cópia temporária. O segundo veredito foi **PASS**, sem achado crítico ou alto. O risco residual de retenção do JSONL foi mantido como gate explícito antes de qualquer piloto real.

Depois desse PASS, a Iteração 7 alterou apenas narrativa executiva, demonstração e teste de interface. Por isso, a suíte completa e um novo gate independente foram executados novamente antes do fechamento.

Na reavaliação do Gate Final 3, o Crivo reproduziu o ambiente a partir do lockfile, executou os 18 testes e confirmou o fechamento dos comandos, premissas econômicas e links. O veredito final foi **PASS**, sem novo bloqueador material.

## Evidências

- `notebooks/challenge-002-analysis.ipynb`: análise executada
- `artifacts/data_audit.json`: auditoria estruturada
- `artifacts/classifier_metrics.json`: métricas da validação e do teste final
- `artifacts/cross_dataset_audit.json`: aplicação exploratória do modelo nos 8.469 textos do Dataset 1
- `artifacts/tables/`: tabelas intermediárias
- `docs/gate-2/claim-ledger.md`: procedência dos claims
- `docs/gate-2/cross-dataset-validation.md`: interpretação e veto à transferência direta
- `docs/gate-3/memoria-de-aprendizado.md`: desenho e gates da memória SQLite
- `docs/gate-3/foco-no-cliente.md`: regras, limitações e validação do gate de reclamação
- `artifacts/figures/app-executive.png`: tela histórica da Iteração 7, não representa o protótipo final
- `artifacts/figures/app-triage.png`: tela histórica da Iteração 7, não representa o protótipo final
- `tests/`: comportamento da política e interface
- histórico git da branch de submissão

## Privacidade

Nenhum nome, email, telefone ou texto bruto de cliente foi copiado para a entrega. O log não guarda texto nem fingerprint derivado do texto. Registra somente decisão, versões, estado da política e contagens de padrões mascarados. A retenção precisa ser definida antes de produção.
