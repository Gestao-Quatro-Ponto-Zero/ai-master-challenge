# Modelo de score — receita esperada em 30 dias

## O que o score mede
`score` = percentil (0–100) de `p30 × preço de tabela` entre os deals abertos que não são zumbis. `p30` é a chance de o deal
**ser ganho em até 30 dias a partir de hoje**; `expected_value` é, portanto, a receita esperada no próximo mês.
Antes o modelo previa "o deal termina Won?" treinado só com deals já fechados, o que fazia deal velho parecer bom
(viés de sobrevivência) e o score acompanhar quase só o preço.

## Treino (`lead_trainer/training.py`)
- Fotos semanais do pipeline até **T − 30 dias**; entram **todos** os deals abertos na foto.
- Rótulo `won_30d` = fechou Won em até 30 dias da foto. Perdido **ou ainda parado** = 0. Só olha até Tk + 30 ≤ T: sem vazamento.
- Features point-in-time (`lead_core/features.py`), mais `age_vs_cycle` = idade / P99 do ciclo dos deals fechados.
- LightGBM com parada antecipada por AUC (paciência 100, mínimo 50 árvores).

## Calibração (`lead_trainer/calibration.py`)
Só um **deslocamento de nível** em log-odds (`method: level_shift`), sem mexer na inclinação. Um Platt completo chegou a esticar
o logit 12x entre datas e piorou a receita capturada. Se o shift não bate uma probabilidade constante fora da amostra
(`calibration.useful = false`), a probabilidade não deve ser exibida; o modelo vale pelo ranking. Isso é esperado: a taxa de
ganho em 30 dias varia muito entre janelas. Artefatos antigos (`shrink_to_base`) continuam carregando.

## Faixas (`lead_core/bands.py`)
| Faixa | Regra |
|---|---|
| prospecting | sem `engage_date`; sem score, `expected_value` = predição como se engajasse hoje |
| review (zumbi) | idade > **P99** do ciclo fechado; sem score |
| stale_risk ("Decidir") | idade > **P90**; mantém score só para ordenar, **limitado a 79** (nunca prioridade Alta) |
| focus / follow_up / low | score ≥ 80 / 40–79 / < 40 |
Os limiares são quantis, não o máximo histórico, então fechamentos tardios isolados (limpeza de carteira) não os movem.

## Portão de qualidade (`lead_trainer/evaluation.py`)
Backtest com **datas móveis**: as 4 últimas fotos, 14 dias entre elas, com desfecho de 30 dias conhecido (`rolling_snapshots`).
Promove somente se (1) o IC95% inferior do AUC > 0,5; (2) a receita capturada no top 20% supera ordenar só pelo preço;
(3) o AUC não cai mais que 0,01 vs. a versão ativa — comparado apenas se ambas usam o protocolo `won_30d.v1`.

## Resultados nos dados reais (universo vivo, idade ≤ 127, 13 datas de 2017)
Receita capturada no top 20%: 0,47 (modelo antigo) → ~0,55. Acerto do top-5 de cada vendedor: 0,17 → ~0,22–0,26.
AUC de conversão entre deals vivos: o antigo ficava em ~0,50. O ganho vem de tirar o viés de sobrevivência e de descontar
deals parados; o dataset não tem atividades (contatos, reuniões), principal próximo salto.
