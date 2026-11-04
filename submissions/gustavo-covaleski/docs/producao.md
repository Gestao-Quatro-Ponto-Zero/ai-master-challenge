# Prontidão para produção

Núcleo: `solution/triagem.py`. Testes: `solution/tests/`, que também roda o golden set `solution/tests/golden/golden_v1.jsonl`. O clássico (TF-IDF + LR) é o único caminho de decisão; o LLM não decide.

## Matriz de falhas

| Falha | Como detecta | O que o sistema faz | Quem é avisado | Teste que prova | Já vi em produção |
|---|---|---|---|---|---|
| Evento duplicado | Chave = `event_id`, ou SHA-256 do texto normalizado + canal, já registrada em `runtime/idempotencia.sqlite` | Devolve o resultado anterior com `duplicado = True`; não grava uma nova decisão | Ninguém em tempo real; taxa de duplicados no monitoramento | `test_idempotencia`, `test_idempotencia_sem_event_id_usa_hash` | NPS em n8n (Pipedrive + WhatsApp + Supabase): o webhook disparava duas vezes e o cliente recebia o NPS em dobro; corrigi com deduplicação por ID do projeto + fase no Supabase. |
| Texto vazio ou curto | Menos de 3 palavras depois do mascaramento | `humano decide`, motivo "texto insuficiente" | Atendente da fila humana | `test_texto_insuficiente` | |
| Classificador falha ou modelo ausente | Exceção na classificação ou na faixa | `humano decide`, motivo "falha do classificador", erro no log; qualquer outra exceção → "falha interna"; `triar` nunca lança exceção | Responsável técnico (taxa de fallback) | `test_fallback_classificador`, `test_nunca_lanca_excecao` | Robô no Power Automate Desktop que exportava quantitativos de madrugada: o Revit travava com janela de erro; o robô passou a registrar a mensagem no log e tentar de novo em outro horário. |
| Injeção no texto | O clássico não executa instruções. Detector de padrões existe, mas está **desligado**: falso positivo de 4,75% do holdout, acima da regra de 1% (`f6_detector.json`) | Classifica normalmente. Em 100 pares de ataque, 9% trocam de rótulo e 3% atingem o alvo, mas **0 caem em "IA decide"** depois da política (`f5_injecao.json`, `dano_em_ia_decide`) | Ninguém; taxa de disparo do detector no monitoramento | `test_injecao_classico_nao_vai_para_alvo`, `test_detector_rebaixa_ataque`, `test_detector_nao_afeta_ticket_limpo_do_golden` | Triagem de briefings com LLM na BIM Brasil: documento do cliente separado das instruções, JSON de saída validado e ferramentas limitadas por agente. |
| Dado pessoal no texto | Regex de e-mail, telefone BR, CPF (11 dígitos só com dígito verificador válido), cartão (13–16 dígitos) e `nome_cliente` | Mascara antes de classificar e de gravar qualquer log ou correção | Ninguém (comportamento padrão) | `test_mascaramento_golden`, `test_mascaramento_20_clientes_ds1`, `test_cpf_valido_vira_cpf`, `test_celular_11_digitos_vira_telefone`, `test_separadores`, `test_registrar_correcao_grava_linha` | |
| Texto fora do idioma | Não há detector de idioma; o efeito aparece como `p_max` baixo | As 3 frases de teste em português caem em `humano decide` (p_max 0,32–0,55) | Ninguém | `test_portugues_nao_cai_em_ia_decide` | |
| Drift de categoria ou de vocabulário | Queda da cobertura de "IA decide"; mudança da distribuição de categorias previstas; alta da taxa de correção (ver Monitoramento) | Nada automático. A categoria afetada pode ser rebaixada no CSV da política (rollback de política) | Responsável pela operação de suporte | Nenhum teste automatizado (depende de dado de produção) | |
| Política ou modelo novo pior que o anterior | Portão de qualidade no holdout por grupo: acurácia ≥ 0,84 e precisão de "IA decide" ≥ 0,97 | O teste falha e barra a troca | Quem roda o `pytest` antes de publicar | `test_portao_de_qualidade` | |
| LLM indisponível | **Não se aplica ao caminho de decisão**: o LLM só aparece no teste de injeção, como comparação | Nada; a triagem não depende do LLM | Ninguém | — | |

## Monitoramento

Os limiares de alerta são **premissas editáveis**, a calibrar nas primeiras semanas.

| Métrica | Como calcular | Alerta (premissa) |
|---|---|---|
| Cobertura semanal de "IA decide" | Em `decisoes.jsonl`: linhas com `faixa == "IA decide"` ÷ total da semana (excluindo duplicados, que não geram linha) | Queda de mais de 3 p.p. contra a base de 12,98% do holdout (`f4_politica.json`) |
| Taxa de correção em "IA sugere" e precisão estimada | Juntar `correcoes.jsonl` e `decisoes.jsonl` por `chave`; correções ÷ decisões "IA sugere"; precisão estimada = 1 − taxa de correção | Precisão estimada abaixo de 0,9545 (meta de "IA sugere", `f3_faixas.json`) |
| Distribuição das categorias previstas | Proporção semanal de cada `categoria` em `decisoes.jsonl` contra a distribuição do treino (F1: Hardware 28,47%, HR Support 22,82% etc.; `f1_ds2_auditoria.json`) | Qualquer categoria com variação acima de 5 p.p. |
| Taxa de fallback | Linhas com `motivo` "falha do classificador" ou "falha interna" ÷ total | Acima de 0,5% num dia |
| Taxa de duplicados | Retornos com `duplicado = True` ÷ chamadas (contar na aplicação, porque o duplicado não grava linha) | Acima de 5% num dia |
| Taxa de disparo do detector de injeção | `detectar_injecao(texto_mascarado)` aplicado às linhas do log (o detector está desligado na decisão, mas pode ser medido) | Acima de 2× a base de 4,75% (`f6_detector.json`) |
| Latência p95 | Percentil 95 de `latencia_ms` no log | Acima de 50 ms (base 5,12 ms, `f5_latencia.json`) |

## Rollback em três níveis

| Nível | Como | Tempo |
|---|---|---|
| **Imediato** | `TRIAGEM_MODO=sombra`: tudo vai para `humano decide`, e o log continua registrando `faixa_sem_sombra`. `triar` lê a variável a cada chamada, então dentro do processo o efeito vale já na chamada seguinte; o app Streamlit precisa ser reiniciado com a variável | Imediato no processo; reinício do app em segundos (não medido) |
| **Política** | Restaurar a versão anterior de `solution/outputs/f4_politica_por_categoria.csv` (o hash `politica_versao` de cada decisão está no log) e reiniciar o processo, porque a política fica em memória | Segundos (cópia do arquivo + reinício; não medido) |
| **Modelo** | Apagar `modelo_cache/` e retreinar a versão anterior; a `modelo_versao` (hash dos ids de treino + parâmetros) está no log e se reproduz no retreino (`82d03ed9a103` nas duas medições) | Retreino medido: **21,5 s** (F5) e **78,2 s** (F6, mesma máquina; diferença não explicada, provavelmente carga da máquina). Planejar o pior caso de ~1,5 min |
