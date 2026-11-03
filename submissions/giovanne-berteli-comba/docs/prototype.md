# I01 — Protótipo de triagem IT assistida

O protótipo local recebe um texto, sugere categoria/destino ou explica o
encaminhamento à revisão, salva duas avaliações numéricas e permite revisar sem
apagar o resultado original. **Toda sugestão exige confirmação humana.** Não há
envio ao cliente nem alteração em helpdesk, acesso, compra ou outro sistema.

## Executar

Na pasta da submissão, execute **um comando**:

```bash
bash run.sh
```

A partir da raiz do repositório, o mesmo inicializador pode ser chamado com:

```bash
bash submissions/giovanne-berteli-comba/run.sh
```

O script entra na pasta correta, prepara o ambiente, verifica/baixa os dados,
regenera a membership congelada quando ausente, treina somente na primeira
execução e abre a [interface local](http://127.0.0.1:8501). Depois de conferir
os hashes, execuções seguintes reutilizam os modelos sem novo ajuste. Ctrl+C
encerra a interface. Para apenas preparar/verificar, use `bash run.sh --prepare-only`.

Não é necessário instalar Python, pip ou `python3-venv` no sistema. Quando falta
um ambiente válido, uv 0.9.7 fornece Python 3.12.3 e sincroniza o lock em diretórios
locais, sem sudo e sem modificar o Python global. O download do uv tem URL/versão
fixas e SHA-256 verificado antes de executar. `.runtime/` guarda runtime/cache/log;
`.venv/` guarda apenas as dependências isoladas. Um venv anterior incompatível é
preservado em `.runtime/previous-venv-*`, sem apagar dados ou modelos.

**Escopo testado:** Linux x86_64 com glibc (como Ubuntu/Debian), Bash, tar,
sha256sum, flock e curl ou wget. Na primeira execução são necessários internet
para GitHub/PyPI/Kaggle, espaço em disco e permissão de escrita na submissão.
macOS, Windows e Alpine/musl não foram validados por este inicializador. O uv
oficial gerencia o Python sem usar ensurepip do sistema:
[documentação primária](https://docs.astral.sh/uv/guides/install-python/).

Duas preparações simultâneas são bloqueadas. Downloads interrompidos podem ser
retomados repetindo o comando. Dados alterados, membership incompatível, treino
interrompido ou artefatos sem origem válida são preservados e produzem orientação;
não há repetição silenciosa de ajuste nem remoção automática do registro de treino.
O detalhe da etapa fica em `.runtime/setup.log`. Um problema de conexão ou
privilégio do host ainda pode exigir correção local; não se promete execução em
qualquer máquina sem pré-requisitos.

A chamada direta de `solution/train_triage.py` também reconhece um treino
concluído válido e retorna sucesso com mensagem de reutilização, sem traceback.
Os comandos manuais da V00 ficam como referência técnica; o caminho recomendado
para quem vai experimentar a entrega é o inicializador acima. Uma nova reprodução
registra seus próprios tempos/hashes; recibos precisam de revalidação explícita
conforme os [controles](foundation-controls.md). Nenhum desses comandos avalia o
teste final.

Para executar uma análise pela CLI:

```bash
.venv/bin/python -I solution/triage_cli.py --example 0 --request-id demo-001
```

Repetir o mesmo identificador e entrada devolve a mesma execução; reutilizá-lo com
outra entrada resulta em conflito. Para texto próprio, use stdin com
`--context it_service_en`, `customer_support` ou `unknown`. Contexto é declarado
pelo operador; score alto não comprova domínio nem validade na abertura do ticket.
Não há demonstração com exemplos do teste reservado.

## Como usar a interface

1. Em **Triagem**, carregue um dos exemplos de treino ou informe texto/contexto.
   Clique **Analisar e salvar**. Veja a categoria, destino e motivos. Uma recarga
   da página não cria outra análise.
2. Em **Revisão e anomalias**, escolha uma execução e confira texto/resultado
   originais. Aceite, corrija uma categoria IT ou adie a decisão, com identificação
   e motivo. Para contexto desconhecido/cliente, aceite ou adie o encaminhamento.
3. Escolha a avaliação de score ou tamanho para registrar valor válido, problema
   confirmado ou adiamento. O julgamento é um evento separado; uma referência
   insuficiente não vira uma faixa estatística válida por revisão manual.
4. Combine filtros de situação, direção, motivo, estado da revisão, categoria,
   métrica e versão. Duas métricas do mesmo caso não contam como dois tickets.

As avaliações distinguem **possível anomalia alta/baixa**, **ordinária** e
**não avaliada**. As comparações usam apenas referências de validação compatíveis
por categoria prevista/domínio/modelo/normalização/métrica. Limites iguais são
ordinários; suporte abaixo de 100 é insuficiente. Alertas e score baixo levam à
triagem antes da política de especialista. Raridade não é erro confirmado.

Texto válido e histórico ficam somente no SQLite local ignorado pelo Git.
Entradas acima do limite não guardam texto ilimitado. Correções não alteram o
modelo, os valores originais, as referências ou os rótulos do benchmark. A
identificação do operador é declarada, sem autenticação empresarial. Testes
automatizados usam tipo próprio e não comprovam revisão humana real.

## Resultado de desenvolvimento — apenas validação

| Modelo | Macro F1 em 7.177 registros |
| --- | ---: |
| Classe majoritária | 0,055396 |
| TF-IDF + Naive Bayes | 0,652147 |
| Regressão logística C=0,5 | 0,824600 |
| Regressão logística C=2, selecionada | 0,852554 |

O critério prévio selecionou C=2, limiar de score 0,80 e cauda de referência 0,01,
sem reajuste com validação. Foram comparadas as 42 combinações previstas. A
fila padrão teve 2.053 casos (28,61%), com 1.977 acertos e 76 erros: 96,30% de
acerto nesse subconjunto, limite inferior Wilson 95% de 95,39%. Os demais foram
1.935 para especialista e 3.189 para triagem, todos ainda sujeitos à confirmação.

Houve 291 casos distintos com possível anomalia e um não avaliado por ausência de
termos conhecidos. Não houve adjudicação humana dos alertas: não são 291 erros ou
uma taxa de alarmes falsos. A mesma validação calibrou referências e selecionou
configurações; estas métricas não são estimativas independentes de generalização.
O custo ilustrativo médio foi 0,946092 (0,983015 dobrando a penalidade declarada de
erro especializado), em unidades adimensionais; não representa minutos ou economia.

O [relatório agregado](../data/triage-development.json) contém as quatro avaliações,
matrizes de confusão, métricas por classe, 42 combinações, seleção e hashes dos
artefatos. As fontes permanecem separadas: resultados IT não demonstram qualidade
na operação de atendimento ao cliente. A disponibilidade prospectiva de cada palavra
de Document não está comprovada. **Teste final e validação V01 continuam pendentes.**

## Verificações e limites

```bash
.venv/bin/python -I -m unittest discover -s tests -v
.venv/bin/python -I scripts/check_triage_prototype.py
python3 -I scripts/check_foundation.py --receipt docs/review-evidence/triage-current.json
```

Os **64 [testes de software](review-evidence/triage-tests.txt) passaram**, sem skips,
e verificam falhas de entrada,
saída não finita, referência, timeout, hashes, atomicidade, duplicidade inclusive
concorrente, filtros e histórico. AppTest verifica interação, recarga, exemplo de
treino com modelo real e revisão; não é uma inspeção visual em navegador.
O [smoke](review-evidence/triage-smoke.json) salva sete requisições únicas e 14
métricas numa base temporária, devolve a mesma execução no reenvio e mostra falha
não salva num erro de escrita provocado. Sua pequena amostra de latência inclui
commit SQLite; não é benchmark de produção. O
[servidor real](review-evidence/triage-server.json) respondeu HTTP 200 no loopback.

Falta V01: avaliar a versão congelada no teste reservado, medir erros/cobertura por
classe e comportamento de falhas/latência com os denominadores do protocolo.
Não há ganho operacional medido, integração real ou prontidão de produção.

O [check de setup](review-evidence/setup-reproduction.json) executou uma cópia
limpa sem venv, runtime, dados, membership ou modelos: quatro ajustes apenas
nessa reprodução isolada, mesmas métricas/seleção, zero previsões de teste final.
A repetição com rede bloqueada manteve hashes e mtimes dos dados/modelos; o
comando padrão abriu o servidor local e respondeu HTTP 200. O smoke de inferência
também passou no Python gerenciado. O treino original não foi repetido.

A [revalidação de compatibilidade](review-evidence/setup-binding.json) registra
que somente o preflight/diagnóstico do comando de treino mudou: a AST do corpo
de cálculo e os bytes dos estimadores/referência/política permaneceram iguais.
O relatório preserva os hashes originais de treino e separa os atuais bindings
de execução; cópias locais da proveniência anterior foram preservadas.
