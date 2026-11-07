# Metodologia e decisões

## Problema e público

Vendedores precisam decidir onde atuar, por que uma oportunidade aparece na fila e qual próximo passo considerar. Gestores precisam filtrar carteira sem confundir volume com qualidade.

## Score v1: hipótese explícita

`score = estágio + potencial + tempo`, entre 0 e 100, aplicado apenas a Engaging e Prospecting.

| Componente | Regra | Justificativa |
|---|---|---|
| Estágio | Engaging 40; Prospecting 20 | Uma negociação iniciada oferece mais evidência operacional de avanço. Não é uma estimativa de conversão. |
| Potencial | arredondar(30 × min(1, ln(1 + preço) / ln(1 + 26768))) | Preço unitário do catálogo é a única aproximação disponível. Escala logarítmica limita a dominância de produtos caros. 26768 é o maior preço deste catálogo, constante versionada. |
| Tempo | até 1 mediana: 30; até 2: 20; acima: 10; sem data: 0 | Favorecer negociação dentro do ciclo típico, sem descartar negócios longos. Acima de 2 ciclos também entra na fila de revisão. |

Mediana por produto dos encerramentos observados até a data de referência; com menos de 30 casos, usar mediana geral. O limiar 30 e os pesos são escolhas de projeto, não parâmetros estatisticamente comprovados. Empates são resolvidos por ID para manter a fila estável.

Oportunidades sem conta mantêm os pontos, mas recebem ação de identificar conta. Prospecção sem data tem componente temporal desconhecido (zero), explicitado na interface. Não recomendamos comparar o score entre estágios como probabilidade. Use a fila de qualificação para não abandonar a prospecção.

## Barreiras contra vazamento

- `close_value` não participa do cálculo e não é enviado ao navegador.
- `close_date` só participa das referências de negócios encerrados até o corte, não do cálculo individual das oportunidades abertas.
- Won/Lost não recebem score nem entram na fila operacional.
- A referência usa o fim do snapshot; não afirmamos ter realizado um backtest temporal reconstruído.
- Nenhuma taxa histórica baseada em vendedor, setor ou porte entra no score v1. Antes de incorporá-la, é necessário testar estabilidade, tamanho de amostra e disponibilidade temporal.
- Dimensões de contas e catálogo não têm histórico de versões; isso limita qualquer alegação point-in-time.

## Validação e próximos experimentos

Testes automatizados verificam isolamento do valor realizado, exclusão de encerrados e resultados futuros, fallback por amostra, soma dos componentes, limites, relações e reconciliação do snapshot. Esses testes verificam implementação; não comprovam impacto comercial.

Para avaliar utilidade: revisão de uma amostra por vendedores, comparar regras com ordenação por preço/idade, variar pesos e medir estabilidade do top 20. Após obter histórico de atividades e snapshots, realizar avaliação temporal com candidatos realmente abertos em cada corte e medir conversão, receita e esforço por contato. Nenhum lift ou ganho de receita foi medido nesta versão.

## Arquitetura

Next.js renderiza a aplicação. A preparação lê CSVs, normaliza produto, confere relações e produz snapshot reproduzível. O servidor pode ler esse snapshot local ou a tabela Supabase paginada. O cliente recebe oportunidades abertas enriquecidas e agregados históricos por vendedor para Resultados. Valores realizados não entram no score. A chave secreta fica no servidor. O modo Supabase é integração preparada para configuração, sem assumir conta provisionada.

## V2: execução comercial

Fluxo da demonstração: a trabalhar → contato → SQL confirmado → proposta → venda ou perda. O estágio operacional começa em “a trabalhar”, independentemente do Engaging original: ele representa o trabalho registrado nesta ferramenta, não uma substituição retroativa do CRM de 2017.

Qualificar exige conta, necessidade, decisor e prazo; proposta e venda exigem qualificação. Contato, qualificação, proposta e retorno exigem notas, próximo passo e data futura. Uma venda exige valor real positivo; perda exige motivo. Eventos encerrados não aceitam novas atividades nesta versão. Alterar perfil e registrar notas não promovem etapas.

Compromissos agendados aguardam o prazo; vencidos entram no foco inclusive fora das rodadas. Bloqueio financeiro pode entrar como revisão interna da proposta, sem antecipação do contato. A fila inicial prioriza contas conhecidas para abordagem e oferece contas ausentes em tarefa separada. Isso não altera pontos por falta de cadastro.

Saúde comercial v2: a política ativa está em [health-v2-implementation.md](health-v2-implementation.md). Substitui a antiga regra 80+20 por evidência de qualificação (40), participação/recência (25), próximo passo aceito/data (25) e viabilidade financeira (10), com cobertura e riscos explícitos. Eventos antigos permanecem sem resposta/aceite inferidos. Nota e tentativas não renovam conversa; vencimentos ultrapassam rodadas. A pontuação histórica não foi alterada e não representa probabilidade.


Atividades persistem em localStorage por navegador. A data de execução usa o relógio atual, separada do snapshot. Resultados da demo contam oportunidades únicas e eventos nesse armazenamento; histórico de 2017 usa agregados por vendedor. Não há evidência de causalidade entre priorização e vendas; não calcular SQL histórico sem registros.
