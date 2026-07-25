# Foco no cliente: cuidado antes da automação

## Decisão

`Ticket Description` é o campo mais importante para compreender o que o cliente viveu. No piloto,
ele passa por uma camada de cuidado antes da classificação técnica. Se houver reclamação,
possível dano ou risco na relação, a solicitação fica obrigatoriamente com uma pessoa.

Essa regra não depende da confiança do classificador. Uma previsão tecnicamente confiante não
autoriza automação quando a mensagem indica prejuízo, repetição de contato, cancelamento,
escalonamento jurídico, risco de segurança ou insatisfação forte.

## Limite do Dataset 1

O valor conceitual do campo não torna o arquivo público confiável para treinamento semântico:

- 8.469 de 8.469 descrições contêm placeholder de template;
- há 8.077 descrições distintas, mas muitas misturam trechos artificiais e contraditórios;
- 460 descrições relatam contatos repetidos sem solução; 152 estão abertas, 156 pendentes e 152 encerradas;
- foram encontrados padrões de email em 77 descrições e de telefone em 165;
- `Ticket Subject` e `Ticket Type` têm associação praticamente nula, com Cramér V de 0,034;
- `Ticket Priority` está quase uniformemente distribuída entre os tipos, sem evidência de regra operacional.

Portanto, o Dataset 1 ajuda a revelar campos necessários, problemas de qualidade e riscos de
privacidade. Ele continua sendo a base operacional do exercício, mas seus rótulos não ensinam de
forma confiável uma classificação automática de novos pedidos.

O grupo de 460 reincidências é acionável agora: deve subir para revisão humana, com auditoria
específica dos 152 casos que constam como encerrados apesar do relato de problema não resolvido.

## Gate de cuidado com o cliente

O piloto identifica seis grupos de sinais:

1. problema repetido ou ainda sem solução;
2. cobrança, reembolso ou possível prejuízo financeiro;
3. cancelamento ou risco de encerramento da relação;
4. escalonamento jurídico ou público;
5. segurança, privacidade, abuso ou discriminação;
6. insatisfação forte.

Ao encontrar qualquer grupo, o sistema:

- destaca o cuidado prioritário;
- explica os motivos encontrados;
- impede qualquer fluxo automático;
- encaminha a decisão para uma pessoa;
- registra apenas códigos gerais no log, sem copiar a mensagem.

O gate é uma proteção inicial baseada em regras explícitas. Ele não é análise emocional completa
e pode deixar passar formas de reclamação não previstas. Isso precisa ser medido com mensagens
reais, autorizadas e rotuladas pela operação.

## Outros campos que merecem tratamento especial

| Campo | Uso correto | Cuidado |
|---|---|---|
| `Ticket Subject` | Contexto complementar | Não usar como verdade isolada; no Dataset 1 quase não concorda com `Ticket Type` |
| `Ticket Type` | Organização inicial | Confirmar com o conteúdo real antes de encaminhar |
| `Ticket Priority` | Sinal informado pela operação | Não deixar prioridade baixa cancelar um alerta de cliente |
| `Ticket Status` | Etapa do processo | Detectar acúmulo e reabertura somente após instrumentação confiável |
| `Resolution` | Avaliar qualidade da solução | Existe apenas para casos fechados; não usar na triagem inicial |
| `Customer Satisfaction Rating` | Feedback após atendimento | Existe apenas em 2.769 casos fechados e não explica sozinho a causa |
| `Ticket Channel` | Adequar forma e velocidade da resposta | Não tratar canal como gravidade |
| `Product Purchased` e `Date of Purchase` | Contexto de produto e possível garantia | Não inferir valor ou importância do cliente |
| Nome, email, idade e gênero | Identificação estritamente necessária | Proteger privacidade e proibir priorização discriminatória |
| Tempos de resposta e resolução | Medir serviço | Os registros atuais são inconsistentes e não sustentam KPI ou ROI |

## Como validar no piloto

Montar um conjunto autorizado de reclamações e solicitações comuns, rotulado por pessoas da
operação. Comparar o gate ligado e desligado e medir:

- reclamações críticas não detectadas;
- solicitações comuns encaminhadas desnecessariamente;
- tempo adicional de revisão;
- correções humanas;
- reabertura e satisfação do cliente;
- incidentes de privacidade.

O piloto só avança quando reduz o risco de ignorar reclamações sem criar uma fila humana
impraticável.
