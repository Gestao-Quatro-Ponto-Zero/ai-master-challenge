# Memo · Suporte com IA: proposta de piloto

**Para:** Diretor de Operações · **De:** Gustavo Paraguassu, AI Master · **Data:** 04/11/2026
**Decisão pedida:** aprovar um piloto de 4 semanas, com metas acordadas antes de começar.

## O que encontrei
- **Onde perdemos tempo:** no roteamento.
  - Hoje se gastam ~1.390 h/ano em triagem manual e em chamados que voltam por estarem na equipe errada.
  - "Hardware" recebe por engano 1 em cada 4 pedidos de permissão de admin e 9% dos de RH.
  - 56% das primeiras mensagens chegam sem o dado de que a equipe precisa.
- **O que a IA faz:**
  - roteia sozinha só onde o acerto medido passa de 95%;
  - pergunta ao cliente o que falta;
  - entrega ao atendente a resposta pronta, com texto aprovado.
- **O que não faz:** nenhuma resposta de mérito sai sem um atendente, e RH e permissão de admin nunca são roteados sozinhos.
- **Funciona:** está no ar no Telegram, num servidor de ~US$ 4/mês. No teste com mensagens em português, 97% de acerto no que foi roteado sozinho.

## Quem
- **Patrocinador:** Diretor de Operações, com orçamento e responsabilidade pelo resultado.
- **Condução do piloto:** liderança de Suporte.
- **Validação interna:** TI e Segurança avaliam integração, acesso aos dados e requisitos para contratação.

## Valor esperado
Liberar capacidade do time e melhorar a resolução, com benefício superior ao custo total de operação.

| Componente | Estimativa (premissas declaradas no repositório) |
|---|---|
| Triagem e retransferências evitadas | 510 a 920 h/ano (de 1.390 h hoje) |
| Resposta pronta em vez de digitada | ~160 h/ano (modelo KLM; a medir no piloto) |
| Custo de IA + servidor | ~US$ 70/ano (US$ 0,0005 por mensagem). O custo relevante é integração e revisão humana |

## Riscos e como o desenho trata cada um
| Risco | Proteção |
|---|---|
| Exposição de dados | Dados pessoais mascarados antes de qualquer envio ao modelo. RH e permissão de admin sempre com humano, mais uma trava que segura o que *parece* sensível. Em produção, grupos separados com acesso restrito |
| Respostas incorretas | O texto sai só do conteúdo aprovado e é sempre enviado por um atendente. O único autoatendimento é a troca de senha, com botão "falar com atendente" |
| Baixa adesão dos atendentes | O ganho para o atendente é não digitar (−38% de tempo, estimado). A adesão é medida: % de respostas enviadas sem edição |
| Custos de integração ou revisão que anulem o ganho | O piloto mede horas reais contra a meta. Sem benefício, o piloto para (abaixo) |

## Seguir, pausar ou parar
O piloto compara com 4 semanas da operação atual. Os números abaixo são propostos; os finais são acordados com o Suporte antes do início.
- **Seguir:** atingir as metas sem piorar satisfação, qualidade ou reaberturas.
  - Tempo mediano de atendimento −30%.
  - Acerto ≥ 95% no roteamento automático.
  - Transferências e reaberturas não acima de hoje.
  - CSAT não abaixo de hoje.
- **Pausar ou parar:** qualquer um destes.
  - Incidente grave: dado pessoal roteado sozinho para a equipe errada.
  - Erros críticos recorrentes.
  - Ausência de benefício econômico ao fim do período de avaliação.

## Condição para contratar ou escalar
| Condição | Como já está atendida |
|---|---|
| Evidências auditáveis | Cada mensagem e clique registrados com horário. Análises reproduzíveis no repositório |
| Responsável pelo serviço | Dono do conteúdo por fila e dono técnico nomeados no piloto |
| Possibilidade de intervenção humana | O atendente envia, edita ou troca a fila. O cliente pode pedir uma pessoa a qualquer momento |
| Saída contratual viável | O classificador é da empresa, treinado no próprio histórico. O núcleo independe do canal e do fornecedor do modelo, e os dados ficam com a empresa |

**Próximos passos:** (1) aprovação; (2) TI e Segurança validam acesso e integração; (3) metas assinadas; (4) 4 semanas de piloto na fila de Hardware, a de maior volume.
