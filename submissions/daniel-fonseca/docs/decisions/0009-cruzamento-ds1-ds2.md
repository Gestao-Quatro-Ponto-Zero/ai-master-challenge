# 0009 — Cruzamento DS1 × DS2 sem join

- **Status:** Aceita (validada pelo Daniel em 2026-11-09)
- **Data:** 2026-11-09
- **Origem:** Daniel (pergunta: dá para relacionar pelo id?) · IA (desenho)

## Contexto
O challenge diz que "o poder está no cruzamento" dos dois datasets. Mas eles não têm chave em comum e vêm de mundos diferentes:
- **DS1:** suporte ao **cliente final** de eletrônicos (cobrança, reembolso, cancelamento, problema técnico), 8.469 tickets sintéticos.
- **DS2:** service desk de **TI interno** (hardware, acessos, RH, compras), 47.837 tickets reais.

Ligar `ds1.ticket_id = ds2.id` criaria uma relação **inventada**: o ticket 1 do DS1 (um GoPro) não tem nada a ver com o documento 1 do DS2. Seria o mesmo erro do ranking de CSAT — um número que parece análise e é ruído.

## Proposta — cruzar por **papel**, não por linha
Cada dataset responde ao que o outro não consegue:

| | DS1 (métricas, texto falso) | DS2 (texto real, sem métricas) |
|---|---|---|
| Serve para | Volume, mix de tipo/canal/prioridade/status → **tamanho da operação** e modelo de custo | Treinar e medir o classificador → **quanto dá para automatizar, e com que precisão** |
| Não serve para | Medir a qualidade da IA (texto e rótulos aleatórios) | Calcular horas e custo (não tem tempo nem volume operacional) |

Três pontes concretas:
1. **ROI:** taxa de automação e precisão **medidas no DS2** (por nível de confiança) × volume e mix **do DS1** × premissas de tempo/custo editáveis → horas e R$ economizados. É a resposta ao "quanto estamos desperdiçando" do Diretor.
2. **Mesma política nos dois mundos:** o pipeline (embedding → classificação → política de 3 níveis) é o mesmo. No DS2 a política usa categoria + confiança; no DS1, tipo + prioridade (ex.: reembolso, cancelamento e Critical → humano). O console aceita tickets dos dois.
3. **Taxonomia de roteamento comum:** mapear tipos do DS1 e categorias do DS2 para filas e níveis de risco (ex.: Technical issue ↔ Hardware/Access/Storage → fila técnica; Refund/Cancellation → fila financeira, só humano). O mapeamento é **decisão humana**, explícita numa tabela.

## Alternativas descartadas
- **Join por id ou por posição:** relação falsa.
- **Similaridade textual entre DS1 e DS2:** o texto do DS1 é templatizado e de outro domínio; os vizinhos encontrados seriam arbitrários.

## Consequências
- O cruzamento fica defensável e explicável em uma frase: "o DS2 prova o quanto a IA acerta; o DS1 dimensiona quanto isso vale".
- As premissas do modelo de custo precisam estar visíveis e ajustáveis — senão o ROI vira chute.
