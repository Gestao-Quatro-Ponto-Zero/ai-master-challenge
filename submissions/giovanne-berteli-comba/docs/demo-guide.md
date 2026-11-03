# Roteiro de demonstração — aproximadamente cinco minutos

Tempo sugerido, ainda não medido com entrevistadores. Para o fluxo completo, em
Linux x86_64/glibc, execute na raiz:

```bash
bash submissions/giovanne-berteli-comba/run.sh
```

Ao abrir a aplicação, selecione **Instrutor** no campo **Perfil de visualização**.
A visão inicial **Empresa** mostra resultados e capacidade, sem o material descritivo
da seleção. O Guia do instrutor orienta o percurso e apresenta o comando do CodeTour.

Primeira execução: preparar ambiente → verificar/baixar dados → separar os grupos
congelados → ajustar os quatro candidatos apenas se ainda não existir treino
concluído válido → iniciar a interface. A preparação não executa o teste final.
O resultado publicado já consumiu esse teste. Não existe duração medida de setup
frio para prometer ao revisor; fases e logs mostram o progresso.

| Tempo sugerido | O que mostrar | O que concluir |
| --- | --- | --- |
| 0–1 min | **Diagnóstico e resultados:** composição por canal, prioridade e tipo; notas e ações | A operação precisa validar status/prioridade e capturar datas/esforço para medir gargalo e desperdício. |
| 1–2 min | Benchmark IT, três filas, cobertura junto da concordância e erros | O modelo auxilia; confirmação e revisão especializada continuam necessárias. As métricas IT não descrevem a operação de clientes. |
| 2–3 min | **Triagem:** clique em **Carregar exemplo** e depois **Analisar e salvar** | O texto é da partição de treino, em inglês; contexto IT é declarado. Confira categoria/destino e motivo. Exemplos demonstram o fluxo, não substituem a avaliação de 7.175 casos. |
| 3–4 min | **Revisão e anomalias:** confira original; aceite, corrija ou adie com identificação e motivo | Uma revisão acrescenta evento. Recarregar preserva o histórico. Em contexto desconhecido/cliente o sistema encaminha para humano. |
| 4–5 min | Filtre avaliações, baixe CSVs; abra **Capacidade** e mude para Desfavorável | Exportação distingue execuções, métricas e eventos. A economia depende de premissas e pode ser negativa. Encerre em **Evoluções planejadas**. |

Na primeira visita não há histórico local. Uma análise de demonstração cria registros
somente no SQLite local, ignorado pelo Git. Identificação do operador é declarada,
sem autenticação de papéis. Testes automatizados usam o tipo próprio e não são
aprovação humana. Para um caso real, confira o conteúdo antes de decidir.

## Três arquivos para continuar o trabalho

- **Casos por execução:** uma linha por execução selecionada, IDs, versão, fila,
  resultado e estado mais recente da revisão de triagem. Um caso pode ter mais de uma execução.
- **Avaliações filtradas:** apenas as linhas que atendem aos filtros combinados.
  Duas métricas da mesma execução não são dois tickets.
- **Histórico de revisões:** todos os eventos das execuções selecionadas, com IDs,
  datas, decisão e tipo declarado de revisor; inclui eventos anteriores ao estado atual.

CSVs v1 em UTF-8 com BOM; textos originais, nomes e motivos livres não integram o
esquema. Campos iniciados por fórmula recebem apóstrofo para leitura como texto
em planilhas. O horário de exportação identifica o recorte. Exportar não altera
histórico/modelo nem envia dados para serviços externos.

Para só conhecer os resultados/simulador, `bash run.sh --overview` na submissão
dispensa dados brutos e treino. O [CodeTour](code-tour.md) permite aprofundar a
implementação; o [resumo de uma página](start-here.md) explica direção humana e IA.

## Novo fluxo e experimento

**Triagem em lote** está disponível na aplicação completa em Empresa e Instrutor.
Use o [roteiro do aprendizado operacional](operational-learning.md): inicie o lote,
importe o CSV, gere sugestões, confira/corrija as linhas, registre-as e conclua o
arquivo. A revisão individual continua disponível como demonstração técnica.

Para medir uso, abra **Instrutor → Experimento**. O protocolo prepara duas etapas
com oito casos de treino distintos em cada uma, referências ocultas e ordem fixada.
A execução pessoal exige marcar **Operador (declarado)** e completar ambas; é uma
atividade separada da demonstração de cinco minutos. Nenhum tempo de conclusão
humana foi medido pelo agente para prometer uma duração. Os testes automatizados
verificam o software e são identificados pelo seu tipo, sem provar economia humana.
