# CodeTour — roteiro da implementação

Na raiz do repositório, execute:

```bash
bash submissions/giovanne-berteli-comba/review.sh
```

Dentro desta submissão, basta `bash review.sh`. O comando confere/instala o
CodeTour no perfil atual e abre uma nova janela de revisão, preservando a anterior.
Clique **Start CodeTour** na notificação da primeira visita; o tour também aparece
na seção CodeTour do Explorer. Não é necessário procurar diretórios ou configurar
a extensão manualmente. Se a instalação for necessária, ela requer rede/Marketplace.

O [inicializador](../review.sh) abre [review.code-workspace](../review.code-workspace):
a submissão passa a ser a raiz dos caminhos do tour. A extensão não procura
automaticamente todos os `.tours` aninhados no workspace do repositório. O
[arquivo do tour](../.tours/assisted-triage.tour) usa padrões únicos, não executa
comandos e não abre dados locais do teste. Não é necessário usar VS Code para
ler o roteiro abaixo.

O formato foi conferido na [documentação/schema primário](https://github.com/microsoft/codetour).
Os checks locais validam a estrutura usada, workspace, arquivos e uma âncora
única por parada. O [teste real de descoberta/navegação](review-evidence/codetour-discovery.json)
usou VS Code e CodeTour em perfis isolados: a raiz não descobriu o tour, o workspace
correto descobriu e navegou às 13 âncoras. A verificação usa APIs do editor, sem
alegar inspeção visual humana ou screenshots. Nenhuma configuração global foi alterada.

## Roteiro sem extensão

### 1. Problema, resultado e principal limite

[README.md:37](../README.md#L37)

Comece pelo resumo. O diagnóstico de atendimento e o benchmark IT têm populações distintas. Observe cobertura junto da concordância e os 50 erros de classes especializadas: a proposta continua assistida. Os resultados são conferíveis nos JSONs vinculados, sem confundir cenário de horas com economia medida.

### 2. Dois datasets, dois papéis

[knowledge/dataset-usage.md:36](../knowledge/dataset-usage.md#L36)

A ausência de chave e mapeamento validado impediu misturar rótulos ou transferir acurácia entre domínios. O arquivo de clientes descreve operação/satisfação; Document/Topic_group forma o benchmark IT. A indisponibilidade de esforço ativo impede medir desperdício real em horas.

### 3. Inicialização depois do feedback real

[run.sh:31](../run.sh#L31)

O candidato encontrou erro de pasta, dependência de venv e traceback ao repetir treino. O inicializador resolve sua pasta, fornece runtime local com checksum, verifica dependências/dados e reutiliza artefatos válidos. A reprodução limpa/offline está em docs/review-evidence/setup-reproduction.json; o tour apenas mostra o código.

### 4. Critérios antes de treinar

[data/evaluation-protocol.json:19](../data/evaluation-protocol.json#L19)

Quatro candidatos/ajustes, vocabulário só no treino e seleção na validação. Metas, custos ilustrativos, gates e referências foram fixados antes dos resultados; não são política empresarial aprovada. A V01 não refaz seleção usando o teste consumido.

### 5. Ajuste e reuso sem treino duplicado

[solution/train_triage.py:43](../solution/train_triage.py#L43)

A entrada verifica tentativa concluída antes de ajustar. O loader usa apenas treino/validação; nenhum exemplo final participa da seleção. Estimadores e referência ficam locais, com hashes. A correção do preflight conservou a proveniência original e não reajustou os modelos do workspace.

### 6. Decisão compartilhada e anomalias

[solution/triage/core.py:68](../solution/triage/core.py#L68)

Score baixo, possível anomalia e referência insuficiente têm precedência sobre a categoria especializada. Quantis são comparados sem arredondamento; os limites são inclusivos. Categoria prevista não garante a verdadeira categoria: preserve os motivos e a confirmação humana. O mesmo núcleo serve avaliação e app.

### 7. Falha visível e worker sem banco

[solution/triage/runtime.py:27](../solution/triage/runtime.py#L27)

O coordenador valida entrada/contexto, limita a inferência por subprocesso e é o único escritor. Timeout, saída inválida, termos desconhecidos e falha de persistência têm estados distintos; uma escrita falha não pode aparecer como sucesso salvo. Identificador repetido não cria uma nova execução.

### 8. Valores originais e revisão durável

[solution/triage/repository.py:72](../solution/triage/repository.py#L72)

Caso, execução e duas avaliações são gravados atomicamente. Revisões posteriores são eventos com identificação/tipo/motivo; não sobrescrevem predição ou valor nem viram treino. filter_metrics combina filtros e projeta o estado mais recente. Duas métricas não equivalem a dois tickets.

### 9. Gestão, capacidade e continuidade

[solution/management_ui.py:88](../solution/management_ui.py#L88)

A aplicação abre em diagnóstico e ações de negócio. Agregados de clientes e benchmark IT ficam separados da atividade local, sem carregar casos finais na demonstração. render_capacity reutiliza a fórmula existente com premissas e perdas visíveis; render_future mostra ideias fora do escopo. A triagem e as exportações de casos, avaliações e eventos estão em solution/app.py e solution/management.py. Nenhuma dessas telas modifica modelo ou referências.

### 10. Evidência final e risco residual

[docs/final-evaluation.md:57](../docs/final-evaluation.md#L57)

Leia erros com seus denominadores: 1.951 sugestões padrão, 67 divergências, 50 com rótulos especializados. O teste de 7.175 casos foi consumido sem ajuste posterior; as 64 medições reais e nove falhas provocadas são populações separadas. A latência local não prova SLA e seus tempos individuais externos não foram persistidos.

### 11. Quem decidiu e o que está preservado

[process-log/README.md:13](../process-log/README.md#L13)

As narrativas preservam decisões, alternativas, correções e falas acessíveis. A cobertura distingue extrações textuais, lacunas e mensagens sem IDs; não afirma histórico completo. As escolhas humanas documentadas não são confundidas com escolhas técnicas do agente. P01 ainda precisa confirmar identificação e preparar o envio.

### 12. Aprendizado que mudou o fluxo

[docs/operational-learning.md:1](../docs/operational-learning.md#L1)

O candidato questionou a ligação entre acurácia e economia. A objeção levou ao lote e a um ensaio com participação humana. Veja o que foi implementado, o que falta medir e por que tempos de testes automatizados não comprovam ganho humano.

### 13. Comparação local sem fabricar ROI

[solution/batch_workflow.py:382](../solution/batch_workflow.py#L382)

O plano é fixado antes das etapas, só usa treino e separa grupos/casos. Rótulos não aparecem durante a tarefa manual/assistida; a comparação exige ambas as conclusões. O relatório retém falhas, tipo de participante e diferenças negativas. Não altera o modelo congelado nem apresenta o ensaio como teste final ou economia de produção.
