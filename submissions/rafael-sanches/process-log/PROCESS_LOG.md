# Process Log — Como usei IA neste desafio

> **Modelo de trabalho, sem enfeite:** eu usei o **Claude Code** como copiloto e **dirigi** o processo — escolhi o desafio, defini a estratégia, impus um protocolo de trabalho fase-a-fase (parar e discutir antes de cada etapa), aprovei ou rejeitei cada escolha, e fiz o controle de qualidade. A IA executou análise e código sob essa direção. Este log mostra *como* dirigi — incluindo os pontos em que a IA (ou eu) errou e o processo de verificação corrigiu.

## Ferramentas usadas

| Ferramenta | Para quê |
|---|---|
| **Claude Code (Sonnet)** | Copiloto do início ao fim — análise exploratória, escrita dos scripts, protótipo, e como interlocutor pra pressionar hipóteses |
| **Python** (pandas, scikit-learn, matplotlib) | Auditoria dos dados, diagnóstico estatístico, treino do classificador |
| **Streamlit** | Protótipo funcional (a interface do agente) |
| **API Anthropic** (Haiku, Sonnet, Opus) | Benchmark honesto: supervisionado vs. LLM zero-shot |

## Como decompus o problema antes de promptar

Antes de qualquer análise, defini a espinha dorsal: os **dois datasets não se cruzam** (domínios e taxonomias diferentes, sem chave comum), então o "cruzamento" que o desafio pede é **complementaridade funcional** — Dataset 1 para o diagnóstico, Dataset 2 para o classificador. A partir disso, um plano de 4 fases com um portão de revisão entre cada uma: **(0)** auditoria de integridade dos dados, **(1)** diagnóstico, **(2)** protótipo + benchmark, **(3)** síntese e submissão. Eu não deixei a IA "sair executando" — cada fase começava com uma discussão do *porquê*.

## Onde a IA (ou eu) errou — e como o processo corrigiu

Esta é a parte que mais importa. Exigi verificação em vez de aceitar o que a IA (ou o próprio brief) afirmava:

1. **O brief mentia sobre o volume dos dados.** Antes de analisar, pedi ao Claude para validar os dados contra os arquivos reais em vez de confiar no enunciado — e ele pegou: o brief diz "~30.000 registros" no Dataset 1, mas o arquivo tem **8.469 linhas.** Uma IA rodando o desafio no automático repetiria "30k" como verdade. Meu papel foi **exigir a verificação contra a fonte**, não aceitar o número do enunciado.
2. **Os dados operacionais são sintéticos — e quase caí numa armadilha.** A ideia inicial era "recuperar tickets similares e sugerir a resolução real como resposta". Ao validar o dataset **antes** de construir, descobrimos que o campo `Resolution` é texto sintético incoerente (Faker), e que 49% das "durações" de atendimento são **negativas** (resolução antes da primeira resposta — impossível). Isso matou a ideia da sugestão de resposta e reescreveu o diagnóstico inteiro. Se eu tivesse construído primeiro, teria demonstrado uma feature sugerindo texto sem sentido.
3. **Minha própria hipótese foi corrigida pelo dado.** Ao comparar o classificador com um LLM, previmos que o LLM erraria só nas categorias "de convenção" (Miscellaneous, Administrative rights). O teste mostrou que o pior fracasso foi em **Hardware** — a maior classe, que eu não esperava. Revisei a explicação em vez de forçar a hipótese: o texto degradado + a convenção larga do dataset derrotam o raciocínio semântico do LLM de forma mais ampla do que eu previa. Deixei a evidência mandar.
4. **Uma revisão crítica pegou um número enganoso.** Pedi ao Claude um "pente fino" no protótipo antes de fechar; ele mesmo sinalizou que o app exibia "96% de acurácia" numa amostra pequena e balanceada — enganoso, já que a referência honesta é 86,5%. Exigi que virasse uma ressalva explícita na interface, porque o desafio pune exatamente vender um número sem contexto.
5. **Corrigi o tom, não só o conteúdo.** O diagnóstico primeiro dizia "os dados são cegos" — arrogante, culpando o time. Reescrevi para "o sistema foi feito para operar, não para diagnosticar; faltam capturar 4 campos". Mesma verdade, sem atacar quem construiu.
6. **Forcei um teste justo antes de concluir.** Quando a IA sugeriu comparar o classificador só com o modelo de LLM mais barato, questionei: a acurácia depende do modelo, então isso seria escolher o adversário fraco. Testamos os três (Haiku, Sonnet, Opus) para a conclusão ficar à prova de objeção.

## O que meu julgamento acrescentou (que a IA sozinha não faria)

- **Ceticismo como método.** A IA, sozinha, teria analisado dados sintéticos como se fossem reais e "descoberto" gargalos que são ruído. O valor não foi promptar — foi desconfiar, verificar contra a fonte, e testar significância antes de chamar qualquer coisa de insight.
- **O enquadramento estratégico.** Reconhecer que os datasets não se juntam e transformar isso num diferencial; decidir que o diagnóstico honesto (dado cego → recomendação de instrumentação) vale mais que um gargalo inventado.
- **Saber onde parar.** O gate de confiança e a lista do "que não automatizar" saíram de uma decisão de negócio — automatizar tudo é red flag — não de uma capacidade técnica.

## Iterações

Muitas, e por design. O protocolo fase-a-fase gerou dezenas de ciclos de discussão→execução→revisão: cada gráfico do diagnóstico (cortados de 4 para 2 por decisão minha), cada escolha do classificador, os três modelos de LLM, e dois passes de refino no protótipo depois de eu pedir um "pente fino". Nada foi um prompt único.

---

*Evidência complementar: histórico de commits (evolução fase-a-fase do código), scripts comentados em `solution/analysis/`, e as figuras da análise em `solution/figures/`. O protótipo roda localmente (`solution/prototype/`) para inspeção ao vivo.*
