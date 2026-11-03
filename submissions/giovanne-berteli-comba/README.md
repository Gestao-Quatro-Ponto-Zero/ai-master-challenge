# Challenge 002 — Redesign de Suporte

**Estado: E01 concluída; revisão final e identificação do candidato em P01. Entrega ainda não enviada.**

## Sobre mim

- **Nome:** a confirmar para a entrega final.
- **LinkedIn:** a preencher antes do envio.
- **Challenge escolhido:** 002 — Redesign de Suporte.

## Executive Summary

A análise encontrou 5.700 registros não encerrados em 8.469 (67,30%), mas os dados não permitem medir duração total ou esforço ativo do atendimento. A solução é uma triagem IT assistida, com categoria/destino sugeridos, confirmação humana e anomalias altas/baixas persistidas para revisão. No teste IT reservado, o macro F1 foi 0,844612 contra 0,646094 do baseline de texto; sugestões padrão cobriram 27,19% dos casos, com 96,57% de concordância com os rótulos nesse subconjunto. Dos 67 erros padrão, 50 tinham rótulos de classes especializadas, reforçando a confirmação humana. Os resultados sustentam o benchmark retrospectivo e o protótipo local, sem provar economia medida, transferência para clientes ou prontidão de produção.

## Revisar o código — CodeTour

**Para revisar o código no VS Code e encontrar o CodeTour sem configurar pastas:**

```bash
bash submissions/giovanne-berteli-comba/review.sh
```

O comando abre uma janela no workspace correto e confere/instala o CodeTour nesse
perfil. Na primeira visita, clique em **Start CodeTour** na notificação; o tour
também fica listado no Explorer. Dentro da submissão, use `bash review.sh`.
Não é preciso descobrir tours dentro da raiz do repositório. O
[roteiro em Markdown](docs/code-tour.md) também pode ser lido diretamente.

## Executar o protótipo

Na raiz do repositório:

```bash
bash submissions/giovanne-berteli-comba/run.sh
```

Ou, dentro desta submissão, `bash run.sh`. O inicializador fornece Python/ambiente,
verifica os dados e prepara o modelo quando necessário; um treino concluído válido
é reutilizado. Não exige `python3-venv` ou sudo. A primeira execução precisa de rede;
o setup foi testado em Linux x86_64/glibc. Veja [pré-requisitos e diagnóstico](docs/prototype.md).
O inicializador abre a interface local, sem executar a avaliação final automaticamente.

## Solução

### Abordagem

Usei os datasets de forma complementar: atendimento para diagnóstico descritivo e
cenários explícitos; IT para classificar suas oito categorias. Não há chave comum,
join ou mapeamento validado entre taxonomias, nem métricas de IA transferidas para
a operação de clientes. A [decisão D02](knowledge/dataset-usage.md) define esses limites.

A implementação usa Python, TF-IDF/regressão logística, Streamlit e SQLite.
Regras de score, anomalias, falta de referência, contexto e falha determinam o
encaminhamento humano. Dados de treino/validação/teste foram separados por grupos
antes da seleção; modelo, limiar e referência foram congelados antes do teste final.
O [fluxo proposto](docs/automation-proposal.md) e o [setup](docs/prototype.md) detalham a solução.

### Resultados / Findings

| Evidência | Resultado | Fonte e limite |
| --- | --- | --- |
| Diagnóstico operacional | 5.700/8.469 não encerrados; 1.403 Critical entre eles | [Diagnóstico](docs/operational-diagnosis.md); retrato da base, não duração do backlog |
| Satisfação | Média 2,99/5 em 2.769 encerrados; notas em 32,70% da base | [Populações e associações](docs/operational-diagnosis.md); sem inferência causal para não avaliados |
| Esforço hipotético | Referência 29,75 h/mês; desfavorável -26,67 h/mês | [Premissas e cenários](data/diagnosis-assumptions.json); não são economias medidas |
| Benchmark IT | Macro F1 0,844612; baseline de texto 0,646094 em 7.175 casos | [Avaliação final](docs/final-evaluation.md); teste consumido, sem refit ou ajuste posterior |
| Sugestões padrão | 1.951/7.175 (27,19%); 1.884 concordâncias e 67 divergências | [Erros e cobertura](docs/final-evaluation.md); 50 erros de classes especializadas, confirmação obrigatória |
| Anomalias | 338 casos distintos; 345 avaliações sinalizadas | [Contagens e limites](data/final-evaluation.json); raridade não equivale a erro confirmado |
| Software/runtime | 72 testes; 64/64 requisições reais salvas, p95 local 600,84 ms | [Relatório](docs/final-evaluation.md); amostra sequencial pequena, não SLA |

O arquivo operacional tem 8.469 registros, em vez dos ~30 mil do briefing, e não
contém abertura do ticket. Há 1.365 pares encerrados com resolução anterior à
primeira resposta. Os [dados auditados](docs/data-audit.md) não sustentam ranking
confiável de duração por canal nem desperdício ativo observado.

### Recomendações

1. Conferir não encerrados/prioridades com a operação e instrumentar abertura,
   eventos e esforço ativo antes de prometer SLA ou economia.
2. Usar a triagem como apoio com confirmação, preservando atenção a classes
   especializadas e revisão das anomalias, sem ação externa automática.
3. Validar disponibilidade dos textos na entrada, rótulos e fluxo em um piloto
   representativo com dados novos; medir carga humana, erros e esforço.
4. Preservar o resultado congelado: o teste já foi consumido e não deve orientar
   outro ajuste apresentado depois como avaliação inédita.

### Limitações

Textos IT já processados não provam disponibilidade na abertura; independência por
entidade e semântica dos rótulos não foram estabelecidas. A separação protege a
similaridade declarada, sem garantir independência semântica. Não houve adjudicação
humana dos alertas, autenticação empresarial, integração de helpdesk ou implantação.
A latência não inclui UI/tempo humano; suas observações individuais externas não
foram persistidas. O [relatório final](docs/final-evaluation.md) explicita esses limites.

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
| --- | --- |
| ChatGPT | Discussão inicial de organização, contexto e evidências; [captura inicial](process-log/chat-exports/01-preparation-chatgpt.md) |
| Codex | Comparação dos desafios, pesquisa, auditoria/cálculos, implementação, testes e documentação sob orientação do candidato; [narrativa e capturas](process-log/README.md) |
| Web e leitura de chats do aplicativo | Fontes primárias, amostra limitada de três PRs e extração das mensagens acessíveis; apoio às ferramentas de IA, sem nova IA atribuída |

Claude Code e Gemini foram discutidos como possibilidades; não há evidência de uso
efetivo nesta entrega. A geração técnica e os cálculos foram feitos com IA; as
intervenções humanas abaixo são as documentadas, sem inventar aprovação de negócio.

### Workflow

1. Organizar instruções, conhecimento seletivo e plano; confirmar a escolha humana do 002.
2. Auditar versões, schemas, qualidade e populações antes de interpretar os datasets.
3. Delimitar papéis dos arquivos e revisar três PRs do mesmo desafio, sem copiar execução.
4. Produzir diagnóstico e cenários; escolher um fluxo local com handoff/anomalias.
5. Congelar grupos, candidatos e critérios; treinar/selecionar só em treino/validação.
6. Implementar e testar; corrigir o setup após os erros de uso relatados pelo candidato.
7. Congelar e avaliar a versão no teste final; revisar resultados, evidências e tour.

Há registros separados por etapa e correção. Foram quatro ajustes de modelos na
execução principal e quatro na reprodução isolada do setup; a V01 não treinou.
Capturas/commits não são contagem de todos os prompts internos ou de todas as iterações.
A [trilha para o revisor](docs/review-guide.md) liga decisões, fontes e resultados.

### Onde a IA errou e como corrigi

- O setup exigia passos manuais e mostrava FileExistsError ao repetir o treino.
  O candidato relatou os problemas e cobrou um comando único; o agente corrigiu e
  testou instalação limpa/reuso offline. [Registro e fala original](process-log/13-setup-fix.md).
- A revisão reproduziu uma divergência de desafio que os checks iniciais não
  detectavam. Foram adicionados contratos e invalidação por hash, sem tratar a
  revisão como teste do futuro app. [Revisão e correção](docs/architecture-review.md).
- O tour tinha âncoras válidas, mas não era descoberto no workspace da raiz.
  Após o relato do candidato, foi criado um inicializador e testada a descoberta/
  navegação no VS Code real. [Correção e teste](process-log/16-codetour-discovery.md).
- Na consolidação, foi corrigida a formatação quebrada de uma métrica no README,
  conferindo o JSON original; não se mudou o resultado ou reavaliou o teste.
  [Registro E01](process-log/15-reviewer-evidence.md).

### O que eu adicionei que a IA sozinha não faria

As intervenções humanas registradas foram escolher o Challenge 002, exigir o
registro/filtro de anomalias altas e baixas, reservar o process log ao recrutamento
e confrontar o setup e a descoberta real do CodeTour até haver inicializadores
por um comando. Essas escolhas
estão nas [narrativas e mensagens originais](process-log/README.md). Stack, regras
numéricas e análises são decisões técnicas do agente dentro da orientação de
avançar; não há revisão humana de rótulos ou política empresarial implícita.

## Evidências

- [Guia de revisão e mapa de evidências](docs/review-guide.md)
- [CodeTour e roteiro sem extensão](docs/code-tour.md)
- [Process log e capturas com limites declarados](process-log/README.md)
- [Fontes/versões dos dados](data/manifest.json) e [resultados finais agregados](data/final-evaluation.json)
- [Testes de software](docs/review-evidence/final-evaluation-tests.txt) e [auditoria sem nova previsão](docs/review-evidence/final-evaluation-checks.json)
- Histórico Git: `git log --oneline -- submissions/giovanne-berteli-comba`

Não há screenshots ou gravação nativa para alegar como evidência. As capturas são
extrações textuais acessíveis, com origem/corte/omissões; não comprovam completude
de ramificações ou mensagens removidas. Nome, LinkedIn, revisão final e envio do PR
continuam em P01. Nenhuma data de submissão ou publicação é antecipada.

## Como retomar o trabalho

Na submissão, leia `AGENTS.md`, `PROJECT_STATUS.md`, `execution/plan.md` e
`knowledge/index.md`; depois apenas os conceitos necessários. Process logs/chats
são evidência para recrutamento, fora do contexto operacional padrão. Para conferir
contratos e hashes: `python3 -I scripts/check_foundation.py`.
