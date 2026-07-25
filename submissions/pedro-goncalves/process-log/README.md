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
| 24/07 | Correção do enquadramento do case | Empresa fictícia tratada como cliente e 460 mensagens reincidentes priorizadas |
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

### Iteração 14

A avaliação humana do primeiro uso revelou quatro falhas de produto: a planilha não estava clara,
a memória aparecia vazia, a barra lateral não tinha função e as evidências exigiam navegação fora
do protótipo. Pedro também questionou a exclusão precoce de duplicatas e pediu justificativa
explícita para não usar retropropagação ou RAG.

A base foi reauditada. O Dataset 1 possui zero linhas exatamente duplicadas e zero IDs repetidos.
Descrições semelhantes pertencem a registros distintos, portanto podem representar reincidência.
A regra passou a preservar a fonte, limpar apenas em camada derivada e consolidar somente
duplicata técnica comprovada.

O aplicativo foi redesenhado como `AI Master OS`, sem barra lateral. A direção visual usa
Manrope, azul-marinho, papel claro e dourado como referência ao ecossistema G4, sem copiar marca
ou transformar identidade em evidência. A jornada agora contém `Comece aqui`, `Triagem`,
`Aprendizado`, `Entregáveis` e `Ajuda`.

Foi criada uma matriz sem dados pessoais com 16 cenários representativos. Ela cobre voz do
cliente, reincidência, cobrança, cancelamento, escalonamento, privacidade, baixa confiança,
categorias sensíveis e um erro conhecido do classificador. Os 16 casos passam.

A memória SQLite ganhou seis lições operacionais aprovadas e uma correção reproduzida: uma compra
de monitores classificada como `Hardware`. A memória não substitui a previsão silenciosamente.
Ela reconhece o precedente e força revisão humana.

Retropropagação foi adiada porque faltam volume de correções aprovadas, autorização e teste final
independente. RAG foi rejeitado nesta fase porque as lições são poucas, estruturadas e críticas.
Adicionar recuperação vetorial e geração aumentaria complexidade sem resolver um gargalo
demonstrado. Essas recusas materializam o critério do challenge: saber onde a IA ajuda e onde deve
parar.

A suíte final passou em **41 de 41 testes**. A versão permanece candidata até duas aprovações
humanas independentes pelo protocolo em `docs/gate-3/protocolo-aprovacao.md`.

### Iteração 15

Pedro reprovou a direção visual clara inspirada no site de carreiras. A interface parecia um
template de IA e ficou menos profissional que a versão anterior. A estética voltou para um dark
mode sóbrio, próximo da ferramenta original: fundo neutro, painéis discretos, tipografia nativa e
vermelho apenas como cor de ação. A barra lateral continuou removida porque não possuía função.

A Demanda 2 ampliou o objetivo do protótipo. A entrega passou a demonstrar o case e também o
processo reutilizável em outra empresa. O novo fluxo recebe duas planilhas CSV/XLSX, perfila as
colunas, sugere papéis e exige que o humano confirme uso, ordem, papel, contexto e relação. A
fonte não é alterada e nenhuma junção é feita apenas por semelhança de nome.

O painel gerencial do case usa os dois datasets completos e mostra volume, contatos repetidos,
inconsistência temporal e desempenho do classificador. O painel universal é gerado somente após
validação da estrutura e não inventa NPS, FRT, TTR ou ROI quando esses campos não existem.

Também foi documentada a escolha do case. Pedro atuou no suporte da Cheers, criou documentação e
procedimentos, trabalhou com automações e consolidou planilhas em Power BI para apoiar decisões
dos sócios. Esse histórico explica a escolha sem transformar experiência pessoal em claim
quantitativo não comprovado.

A suíte passou para **47 de 47 testes**, incluindo CSV, XLSX, validação de ordem, preservação de
eventos repetidos, painel do case, dez entregáveis e entrada universal de duas planilhas.

### Iteração 16

Pedro forneceu duas referências visuais específicas depois de reprovar direções genéricas. O
arquivo local `g4-design-kit.html` passou a ser a fonte dos tokens: hero azul-marinho, superfície
branca, tinta `#051D29`, borda `#EDEEF0`, raio de 16 px e dourado proibido fora de um logo real.
O componente `Features 8`, do 21st.dev, passou a orientar somente a arquitetura bento da entrada,
sem importar seu tema escuro ou o conteúdo fictício.

A página `Visão geral` virou uma central de operação com cinco destinos funcionais:
`Demonstração`, `Analisar planilhas`, `Aprendizado`, `Entregáveis` e `Ajuda`. Cada card usa um
número já sustentado pela entrega e um comando explícito. A navegação horizontal continua
disponível para retorno direto, sem reintroduzir a barra lateral sem função.

Foi adicionado um teste que abre os cinco destinos a partir da home. A suíte passou para
**48 de 48 testes**. O QA visual continua bloqueado porque a captura headless do Streamlit
registrou apenas o esqueleto de carregamento e nenhum navegador interativo estava disponível.
Por isso, a implementação ainda não recebeu aprovação visual.

### Iteração 17

Pedro encontrou problemas materiais na primeira central de operação: botões sem leitura, números
quebrados, navegação duplicada, cards pouco nítidos e ausência de uma explicação executiva para
cada cálculo. Também reforçou que o produto precisa servir a um líder de suporte numa rotina
comum, com eficiência e produtividade comprováveis, não com promessas genéricas de IA.

A home foi reconstruída como central de acesso. A barra de abas foi removida da entrada; cinco
cards inteiros e clicáveis levam a `Demonstração`, `Analisar planilhas`, `Aprendizado`,
`Entregáveis` e `Ajuda`. Cada card recebeu uma imagem operacional própria, criada sob os tokens
visuais do projeto. Contraste, CTA, bordas, responsividade e legibilidade dos botões foram
reforçados.

O painel gerencial passou a trabalhar com quatro indicadores 80/20:

1. 460 relatos de contatos repetidos sem solução em 8.469 descrições;
2. 1.365 pares temporais incoerentes em 2.769 pares preenchidos;
3. 5.003 previsões cobertas em 7.176 mensagens do teste final;
4. 4.834 acertos entre as 5.003 previsões cobertas.

Cada número agora mostra fonte, numerador, denominador, fórmula, escopo e limite. O Pareto dos
quatro prioriza revisar reincidências, começando pelos 152 casos encerrados, e corrigir a base
temporal antes de publicar FRT, TTR, produtividade ou ROI observado.

A simulação de eficiência foi mantida, mas seus inputs foram rotulados como hipóteses. O volume
vem do arquivo; elegibilidade, adoção, tempos e sucesso seguro precisam ser medidos no piloto.
Foi criado `docs/gate-3/parecer-80-20.md` e um teste garante que seus quatro números continuam
sincronizados com os artefatos auditados. A suíte passou para **50 de 50 testes**. O QA visual
final continua dependente de nova captura renderizada da aplicação.

### Iteração 18

A primeira captura da nova home revelou um bloqueador P0: somente o primeiro card renderizava; os
demais apareciam como HTML literal. Lume diagnosticou que a string multilinha indentada era
interpretada pelo Markdown do Streamlit como bloco de código. Nexo isolou a montagem em
`build_home_cards_html()` e passou a concatenar as tags sem indentação ou quebras ambíguas.

Foram adicionados cinco testes para verificar os cinco links, seus destinos, ausência de tags
`pre` e `code`, ausência de indentação de bloco e ausência de HTML escapado. A suíte canônica
passou para **55 de 55 testes**.

Crivo revisou a correção sem editar arquivos, reproduziu os 55 testes e confirmou a causa e o
conserto técnico. A versão permanece bloqueada para liberação porque ainda falta uma captura
humana pós-correção com os cinco cards renderizados e navegáveis. Nenhum PASS visual foi
declarado sem essa evidência.

### Iteração 19

A aba Entregáveis foi reformulada para transformar a lista de 11 documentos em uma leitura guiada estruturada para avaliação executiva. No topo, foi adicionado um resumo compacto dos 4 critérios formais do case (Números do Dataset 1, Uso material dos dois datasets, Protótipo funcional e Process log), cada um acompanhado por uma frase de prova objetiva de até 8 palavras.

Para reduzir a densidade visual e evitar o cansaço na navegação, foi adotado o padrão de revelação progressiva (progressive disclosure): as quatro etapas (Decisão, Evidência, Limites e Execução) passaram a ser expanders sanfonados, onde apenas a etapa '1. Decisão' fica aberta por padrão. A matriz de testes e o pacote bundle foram consolidados em um expander próprio 'Arquivos de submissão'.

Foram mantidos componentes discretos de anotação editorial dentro da etapa correspondente,
indicando pontos críticos como 'comece aqui', 'confira a prova' e 'aqui eu decidi não
automatizar'. O rabisco inicial virou orientação executiva estruturada.

O código morto de funções e ativos não utilizados (`HOME_ASSETS`, `base64`, `quote`, `image_data_uri`, `build_home_cards_html`) foi removido de `app.py` e `tests/test_app.py`. A suíte de testes foi atualizada para validar os 4 critérios do topo, os 5 expanders, os 11 botões de download de markdown e as anotações editoriais.

A referência do Opera Air foi traduzida como princípio de `calm technology`, não como cópia
visual. O protótipo deve apoiar sem interromper, mostrar orientação quando necessária e preservar
a decisão humana. A suíte canônica terminou com **53 de 53 testes**: cinco testes de um componente
de home removido deixaram de existir e três verificações relevantes da jornada simplificada foram
incorporadas.

### Iteração 20

O pacote foi testado na estrutura exata exigida para submissão, e não apenas na pasta de
desenvolvimento. Esse teste encontrou um erro de caminho: a aplicação procurava `docs/` dentro de
`solution/`, embora os documentos fiquem na pasta irmã da submissão. A resolução da raiz passou a
funcionar nos dois layouts e a suíte voltou a passar com **53 de 53 testes** no destino final.

O gate independente também encontrou ambiente virtual, caches, log de decisões e banco SQLite
gerados durante a validação. Esses artefatos de runtime foram removidos do pacote. Por precisão,
o texto final deixou de chamar 460 linhas de 460 clientes: o dado comprova **460 mensagens com
sinal de contato repetido**, não 460 pessoas únicas. Da mesma forma, 49,3% passou a ser descrito
como pares temporais incoerentes, que é exatamente o cálculo auditado.

Na revisão humana da aba `Entregáveis`, Pedro encontrou um desvio de autoria: sua própria
trajetória aparecia em terceira pessoa, como “vivência de Pedro”. A apresentação pessoal passou
para primeira pessoa e as anotações editoriais agora usam “Minha nota”. O ajuste é pequeno no
código, mas material na avaliação: o protótipo precisa comunicar uma decisão assumida pelo
candidato, não parecer um texto sobre ele produzido por terceiros.

### Iteração 21

O caminho universal exigia que o avaliador localizasse e enviasse manualmente as duas planilhas.
Foi incluído o botão `Usar dados do case`, que carrega o mesmo fluxo de validação com duas
amostras sistemáticas de 1.000 linhas. A seleção cobre uniformemente cada arquivo, não escolhe
casos favoráveis e remove Ticket ID, nome, e-mail, idade e gênero do Dataset 1. A interface declara que se
trata de amostra de avaliação e aponta a análise integral nos entregáveis. O upload de outras
planilhas permanece disponível como alternativa. Dois testes foram adicionados para provar o
carregamento sem upload, o limite de 1.000 linhas e a remoção dos identificadores diretos. A
suíte canônica passou para **55 de 55 testes**.

### Iteração 22

Uma banca simulada apontou que o atalho dos dados do case resolveu a entrada, mas ainda deixava
duas decisões escondidas: o que exatamente o líder aprovava antes da análise e qual fila deveria
abrir depois dela. A navegação por lista suspensa também exigia um clique desnecessário e não
mostrava a arquitetura do produto.

A lista foi substituída por uma navegação horizontal persistente, com estado ativo e links
diretos por parâmetro de URL. Antes da análise, o líder agora recebe um recibo com bases,
linhas, colunas aceitas, problemas estruturais e confirmação de que nenhuma fonte será alterada.
Depois da análise, o painel abre pela decisão: casos de cuidado com cliente, revisões humanas e
próxima ação. A fila não exibe o texto original. O desenho prioriza a pergunta operacional:
“o que eu preciso fazer agora?”. A suíte passou para **56 de 56 testes**.

### Iteração 23

O protótipo ainda pressupunha que o avaliador conhecia a conversa de construção. A home passou
a oferecer um roteiro universal em três ações: executar os 16 casos, percorrer os dados do case
e ler as evidências. O caminho não exige login, upload próprio ou explicação verbal do candidato.

Na aba `Entregáveis`, baixar onze arquivos Markdown criava atrito e tirava o leitor do fluxo.
Cada documento agora abre formatado em um modal central dentro do OS. Downloads permanecem
apenas para artefatos de transferência, como a matriz CSV e o pacote da submissão.

### Iteração 24

O teste manual encontrou uma ambiguidade operacional: o campo aceitava 4.000 linhas, mas o recibo
continuava mostrando 2.000. A causa não era o controle, e sim as duas amostras limitadas a 1.000
linhas cada. As amostras sistemáticas passaram a ter 5.000 linhas por base. O recibo agora declara
que o limite vale por base, mostra linhas disponíveis, linhas analisadas e linhas fora da execução.
Assim, 4.000 por base em duas bases resulta explicitamente em 8.000 de 10.000 linhas.

A home deixou de antecipar resultados finais. Ela apresenta o problema, o volume de 56.306
registros e o que a avaliação precisa provar. O caminho principal passou a ser uma única jornada:
iniciar o dia com os dados do case, aprovar a estrutura, acompanhar o tratamento e abrir a fila
prioritária. Os nomes visíveis mudaram para `Triagem diária` e `Análise da operação`.

O fluxo também passou a atribuir contextos corretos às duas bases do case. A primeira inicia como
atendimento ao cliente e a segunda como suporte interno de TI. Sem isso, a análise cairia no modo
gerencial genérico e não produziria a decisão operacional esperada.

Por fim, a fronteira humano e IA foi explicitada em oito pontos do protótipo e detalhada no
entregável `Onde colocar IA`. Contagem e qualidade dos dados usam código determinístico.
Classificação textual de TI usa IA somente no domínio testado. Baixa confiança gera abstenção.
Cliente em risco, contexto, aprendizado e qualquer ação externa permanecem sob decisão humana.
Essa escolha evita chamar toda automação de IA e torna cada limite auditável.

O produto passou a se chamar **OSS: Operating System for Support**. A marca parte do conceito de
`Operating System`: uma camada que organiza recursos, regras e execução do trabalho diário. A
preposição `for` não entra na sigla.
A referência ao "oss" das artes marciais permanece discreta, sem virar explicação na interface.
O termo copiloto descreve apenas a autonomia limitada da IA dentro do OSS.

### Iteração 25

O teste do fluxo completo revelou que o botão do parecer desaparecia após o rerun do Streamlit.
A análise concluída e o estado do parecer passaram a persistir na sessão. O líder agora abre, na
mesma tela, um **Parecer técnico-gerencial** que começa pelo veredito e responde o que fazer agora.

O parecer usa apenas números da execução: linhas analisadas, revisão humana, cuidado com cliente
e sugestões em observação, todos com quantidade e percentual. O ROI permanece explicitamente
limitado a hipótese até existirem tempo manual, custos e retrabalho medidos no piloto. Três ações
foram validadas: abrir a fila prioritária, consultar evidências e baixar o parecer em Markdown.
A suíte canônica passou para **58 de 58 testes**.
