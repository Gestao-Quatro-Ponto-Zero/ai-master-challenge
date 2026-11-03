# Investigação pelos cinco princípios — 03/11/2026

O candidato pediu uma investigação antes da etapa final: compreensão da entrega
e dos papéis humano/IA, reprodução, insights de negócio, incrementos úteis agora
e evoluções futuras. A P01 não foi iniciada.

## Trabalho da IA e conclusões

Lidos briefing, plano, documentação de entrada, contratos, resultados agregados,
setup e código da interface. A [revisão](../docs/pre-submission-review.md) registra
forças, lacunas, decisões acionáveis, critérios de aceite e dependências.

A principal lacuna é de conexão entre diagnóstico e uso: a aplicação mostra
triagem/revisão, enquanto achados operacionais e resultados finais ficam em
documentos. Recomendou-se uma rodada limitada a entrada executiva/demo, visão
de gestão com agregados e clareza de reprodução/status. Exportação e simulador
são opcionais; IA analista, planilhas, comunicação e helpdesk ficam no futuro.

As propostas não foram implementadas. A revisão identifica corretamente o modelo
local como TF-IDF/logística e atribui à IA a análise e implementação. O humano
definiu direção, requisitos, critérios desta investigação e contestou falhas de
uso nos passos anteriores; não se inventou programação ou revisão de rótulos feita
pelo candidato.

## Verificação

- Fundação e apresentação passaram no estado de entrada.
- Reagregação dos 7.175 resultados salvos conciliou matrizes, decisões e hashes,
  com zero cargas de modelo, novas previsões ou ajustes.
- Setup já preparado passou em 0,288 s e manteve hashes/mtimes dos 23 arquivos
  de dados/modelos monitorados. Não é tempo de instalação limpa.
- O setup imprimiu a frase obsoleta de teste reservado: ficou registrada como
  correção proposta, sem alteração no código congelado ou nas métricas.
- Consulta a fontes primárias confirmou os caminhos de download no Streamlit,
  append no Sheets, mensagens/rascunhos no Gmail e webhook no Discord. Nenhum
  acesso a contas, configuração, envio ou integração foi realizado.

Os resultados estão em [evidência da investigação](../docs/review-evidence/pre-submission-review-checks.json).
Mudanças desta sessão se limitam à documentação e sua evidência. Os recibos
afetados exigem revalidação documental, preservando fontes/cálculos/resultados.
Os 11 testes existentes da fundação passaram; 465 destinos de links locais
foram conferidos, sem lacunas. O inventário atualizado passou com 22 capturas,
162 ocorrências de mensagens e 120 IDs explícitos distintos.

## Conversas e limite

A [captura 21](chat-exports/21-codetour-completion-chat.md) adiciona quatro
mensagens ainda não preservadas do chat anterior, incluindo a conclusão da
correção e a troca sobre nome do commit; quatro turnos retornados, hasMore=true.
A [captura 22](chat-exports/22-pre-submission-review-chat.md) preserva cinco
mensagens deste chat: o pedido original e quatro atualizações, distribuídas em
quatro registros de turno retornados, hasMore=false. IDs já existentes foram
excluídos. Ferramentas, instruções internas e contexto de ambiente não foram
arquivados. Resposta final e mensagens posteriores ao corte continuam pendentes.

Plano, status e backlog registram R02 concluída e propostas ainda pendentes.
Sem treino, nova inferência, alteração de política/modelo, commit, push ou PR.
