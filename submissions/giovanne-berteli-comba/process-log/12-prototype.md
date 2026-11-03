# Protótipo local — 02/11/2026

## Contexto e execução

O usuário pediu a próxima etapa após o commit `9178e20`. O estado inicial estava
limpo e o recibo da fundação passou. Codex implementou I01 sob os contratos S01 e
V00, sem alterar candidatos, conjuntos, metas, custos ou critérios após resultados.
O [setup](../docs/prototype.md) e o [registro técnico](../knowledge/prototype.md)
explicam a aplicação; a seleção está no [relatório agregado](../data/triage-development.json).

Foram criados núcleo compartilhado de decisão/anomalias, carregamento de artefatos
locais com hashes, worker sem acesso ao banco, coordenador com prazo de 5s,
repositório SQLite, CLI e interface Streamlit com Triagem/Revisão. A inferência
usa subprocesso por solicitação, encerrado no timeout; o coordenador é o único
escritor. Foi preferido a callbacks de tarefas tardias ou um serviço/API adicional.
Pickles só são carregados do diretório local fixo após validação; não há upload.

Caso/execução e duas avaliações são gravados atomicamente. Reenvios iguais devolvem
a execução original, inclusive sob concorrência; identificador conflitante não
sobrescreve registros. Revisões são eventos, com estado mais recente por sequência,
sem alterar rótulos de benchmark, valor/predição original, referências ou treino.
Os filtros combinam situação/direção/motivo/revisão/categoria/métrica/versão.
Identificação de operador é declarada; fixtures usam tipo automated_test.

## Seleção congelada e resultado de desenvolvimento

Somente quatro modelos foram ajustados no treino, sem refit com validação:
majoritária, Naive Bayes e regressões C=0,5/C=2. Nenhum warning de ajuste foi capturado.
Macro F1 na validação: 0,055396 / 0,652147 / 0,824600 / 0,852554. C=2 venceu sob a regra
prévia. As 42 combinações de gate produziram limiar 0,80/cauda 0,01; suporte mínimo 100.

Nos 7.177 casos de validação, houve 2.053 sugestões padrão (1.977 corretas, 76 erradas),
1.935 destinos especializados e 3.189 triagens. Cobertura padrão 28,61%, acerto 96,30%
nesse subconjunto e limite inferior Wilson 95% de 95,39%. Houve 291 casos com possível
anomalia e um com métricas não avaliadas por nenhum termo conhecido. Não são
resultados finais: seleção e referência reutilizam validação. Não se alegou acerto
de anomalia sem adjudicação humana, transferência para clientes ou economia medida.
Custos 0,946092/0,983015 são proxies adimensionais, não dinheiro ou minutos.

O registro local de tentativa usa criação exclusiva para impedir repetição
acidental do orçamento. Os quatro estimadores, vetores de validação, referência,
configuração e exemplos de treino ficam ignorados; o relatório público registra
hashes e agregados. A UI só oferece exemplos de treino. Zero previsões do teste final.

## Revisões e checagens

Antes de treinar, os testes do núcleo e da UI passaram. Foram reforçadas a
validação de identidade do modelo/membership/referência e a tipagem de revisores.
O formulário passou a oferecer estados compatíveis com seu alvo, evitando uma
combinação inválida por padrão. Conexões SQLite passaram a ter fechamento explícito;
os testes da fundação deixam de copiar modelos e bancos locais para fixtures.
Esses ajustes ocorreram antes do treinamento; não mudaram o protocolo numérico.

Os 57 testes passaram sem skips no ambiente fixado. Incluem entrada
vazia/grande/expansão Unicode, contexto fora de IT,
saídas inválidas/não finitas, vocabulário desconhecido, referências altas/baixas/
iguais/constantes/insuficientes, stale hashes, falha e timeout real de subprocesso,
rollback de escrita, entregas repetidas/concorrentes, filtros parametrizados e
eventos de revisão. AppTest cobriu exemplo real de treino, análise, recarga e revisão
em base temporária. É simulação de widgets, não inspeção visual em navegador.

O [smoke real](../docs/review-evidence/triage-smoke.json) usou três exemplos de treino
e entradas sintéticas de falha/contexto: sete solicitações únicas mais um reenvio,
sete execuções e 14 métricas salvas. Falha de escrita provocada não deixou registro
parcial e mostrou resultado não salvo. Sua pequena amostra de latência não prova
SLA. Um [servidor local real](../docs/review-evidence/triage-server.json) respondeu
HTTP 200 em 127.0.0.1 e foi encerrado, sem deploy. A execução local foi autorizada
pelo mecanismo automático de permissões.

Fontes primárias consultadas: documentação de AppTest, persistência scikit-learn e
processos Python. A implementação escolheu subprocess.run para o prazo/encerramento;
nenhuma API externa, nova dependência ou autenticação empresarial foi adicionada.

## Evidências e handoff

[Testes](../docs/review-evidence/triage-tests.txt) e
[recibo](../docs/review-evidence/triage-current.json) identificam a versão.
Status/plano/donos operacionais e execução F02/F03 foram atualizados. Saídas D01/A01
e preparação V00 foram regeneradas antes de atualizar recibos; modelos não foram
reajustados. O próximo passo é V01, com driver congelado e teste reservado.
Sem commit/push, integração de helpdesk ou ação em outros sistemas.

A [captura 16](chat-exports/16-prototype-chat.md) preserva nove mensagens novas de
quatro turnos, após deduplicação; inclui final V00 e troca de nome do commit.
`hasMore=true` indica histórico anterior fora da página. Mensagens posteriores e
final I01 ficam para a próxima captura; não se reconstruiu texto ausente.
