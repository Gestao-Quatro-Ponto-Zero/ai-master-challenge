# Protocolo: teste com colegas (com vs. sem assistente)

## Pergunta
O assistente reduz o tempo de atendimento **sem piorar o acerto de fila**? E o atendente corrige a IA quando ela erra (viés de automação)?

## Desenho
- **Participantes:** 3 a 5 colegas, no papel de atendente. Ninguém precisa conhecer o Dataset 2.
- **Material:** 16 chamados reais do conjunto de *teste* do Dataset 2 (2 por fila), reescritos em português de chat pelo Claude Opus 5.5, que não recebeu a fila ([cenarios.json](cenarios.json), gerado por `analysis/05_pt_eval.py`). A fila verdadeira é a do dataset.
- **Duas condições, no mesmo participante (pareado):**
  - **COM assistente:** o card mostra fila sugerida, confiança, campos extraídos, resumo e resposta pronta (conteúdo aprovado). Botões: Enviar / Editar / Outra fila.
  - **SEM assistente:** o card mostra só a mensagem do cliente. O atendente escolhe a fila entre as 8 e digita a resposta.
- **Contrabalanceamento:** os 16 cenários se dividem em dois blocos, A e B. Participantes ímpares fazem A com assistente e B sem; pares fazem o contrário. Assim, cada cenário é atendido nas duas condições. COM e SEM se alternam chamado a chamado, e a ordem inverte entre ímpares e pares, para diluir aprendizado e cansaço.
- **Triagem fixa:** a triagem dos cenários está em cache, então todos os participantes veem exatamente a mesma sugestão. O teste não depende da API nem varia entre pessoas.

## Como rodar (≈15 min por pessoa)
1. O participante entra no grupo de atendentes.
2. Alguém manda no grupo `/rodada P1` (P2, P3... para os próximos). O bot cria o tópico "🧪 Experimento P1" e posta um chamado por vez.
3. Instrução ao participante, que é a única que ele recebe: *"Atenda cada chamado como se fosse real: confira a fila e mande uma resposta adequada ao cliente. Trabalhe no seu ritmo normal."* Não diga que a IA pode errar nem qual condição é "a melhor".
4. Ao terminar os 16, o bot posta "Rodada concluída".

## O que é medido (tudo vem de `runtime/eventos.jsonl`, com horário de cada clique)
| Métrica | Definição |
|---|---|
| Tempo por chamado | do card postado até a resposta final (inclui trocar de fila e editar) |
| Acerto de fila | fila final = fila do Dataset 2 |
| Aceitação sem edição | % de respostas COM assistente enviadas como sugeridas |
| Correção da IA | quando a sugestão estava errada: % em que o atendente trocou para a fila certa |
| Dano à IA | quando a sugestão estava certa: % em que o atendente manteve |

`python experiment/analisar.py --salvar` gera `outputs/metricas_eventos.json`.

## Como ler o resultado (definido antes de rodar)
- **Sucesso:** tempo mediano COM ≥ 30% menor que SEM, na maioria dos participantes, e acerto de fila COM não inferior ao SEM em mais de 5 pontos.
- **Alerta de viés de automação:** se, entre as sugestões erradas, menos da metade for corrigida, o card precisa destacar mais a incerteza (ex.: esconder a resposta pronta quando a confiança estiver abaixo do limiar).
- Os tempos medidos substituem as premissas `min_triagem_manual` e `min_triagem_com_sugestao` em `analysis/04_cost_of_error.py`.

## Limites honestos
- 3 a 5 pessoas e 16 chamados dão **tamanho de efeito e direção**, não significância estatística.
- Colegas não são atendentes de TI; o tempo SEM assistente tende a ser maior do que o de um especialista.
- O texto em português foi gerado por IA a partir do inglês pré-processado. Mensagens reais de clientes serão mais variadas.
