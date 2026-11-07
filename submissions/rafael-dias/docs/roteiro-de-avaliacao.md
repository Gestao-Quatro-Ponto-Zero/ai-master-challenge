# Roteiro de avaliação — cerca de 10 minutos

## Iniciar

Siga o setup do [README da submissão](../README.md). Não é preciso configurar Supabase. Para começar sem registros de QA, use um perfil de navegador novo ou janela privativa, sem apagar seus registros existentes. A mesma origem (host e porta) precisa ser mantida para conferir persistência.

## Fluxo sugerido

1. Em **Meu dia**, selecione um vendedor com oportunidades abertas. Confira as prioridades e seus motivos. Observe que 8.800 inclui encerradas: a aplicação trabalha 2.089 abertas.
2. Abra uma oportunidade identificada. Confira conta, produto, referência histórica, saúde e lacunas. Em uma sessão nova, “Em validação” é esperado: o dataset não contém respostas do comprador.
3. Registre um contato fictício identificado como teste. Não acione telefone/e-mail de pessoas reais. Escolha resposta e próximo passo conforme o cenário simulado, com data futura quando exigida.
4. Confira o registro e o compromisso na agenda. Recarregue a página na mesma origem: o histórico deve continuar.
5. Para experimentar SQL, preencha necessidade, decisor e prazo com conteúdo explicitamente fictício. Confirme a resposta do comprador e o aceite somente como simulação. Veja a mudança na cobertura e nos fatores da saúde.
6. Registre proposta com valor total em USD e bloqueio financeiro fictício. Confira o risco e a orientação para revisar as condições. Uma soma alta não deve remover o risco.
7. No **Meu pipeline**, arraste uma oportunidade para outra etapa. Cancelar o formulário deve preservar a etapa; salvar exige os critérios da transição. Há alternativa pelo formulário do card.
8. Confira **Resultados** da carteira e da empresa; diferencie atividades desta sessão dos resultados históricos de 2017. Experimente os filtros por gestor/região.
9. Confira **Entenda as prioridades**, tema claro/escuro e menu recolhido. Uma carteira vazia deve mostrar estado vazio, não oportunidades inventadas.

## Ler e verificar

- Regras atuais: [saúde v2](../solution/docs/health-v2-implementation.md).
- Código das regras: `solution/lib/health.mjs`, `priority.mjs` e `evidence.mjs`.
- Testes: `solution/tests/`; execute `npm run check` com o servidor parado.
- Continuidade: [manutenção](../solution/docs/maintenance.md).
- Histórico de decisões: [process log](../process-log/workflow.md).

Os cenários de QA não demonstram aumento de conversão. A participação real de vendedores e um piloto comparativo continuam pendentes.
