# Submissão — Leandro Ruel — Challenge 003

## Sobre mim

- **Nome:** Leandro Ribeiro Ruel
- **LinkedIn:** https://www.linkedin.com/in/leandro-ribeiro-ruel/
- **Challenge escolhido:** Challenge 003 — Lead Scorer

---

## Executive Summary

Para este projeto desenvolvi um dashboard react usando llms que mostra o score de um deal para o agente de vendas com analytics e filtros avançados. nas minhas buscas encontrei busquei ferramentas, a melhor forma de abordá-las. recomendo rodar o `start.sh` em seu terminal para iniciar a aplicação.



---

## Solução

Realizei primeiro uma análise de como realizar o cálculo do score, com ajuda da llm, que é baseado no seguinte:
```
Fase do Negócio (0-25) + Tamanho da Conta (0-20) + Desempenho do Vendedor (0-20) + Desempenho do Produto (0-20) + Tempo no Pipeline (0-15) = Pontuação Total (0-100)
```
depois, pesquisei a melhor abordagem de desenvolvimento, como tinha incertezas se ferramentas prontas me dariam a liberdade de customização, optei por pedir a llm que construisse tudo usando react + sqlite. em questão de design, realizei diversas mudanças pontuais até alcançar um resultado satisfatório, de modo que mostre um datatable com filtros e uma aba de analytics que podem dar insights para o vendedor.

### Abordagem

Utilizei chatGPT para uma pesquisa rápida, pesquisei como funcionam algumas ferramentas, depois usei o claude code Haiku 4.5 integrado ao chat do vscode, para desenvolver boa parte inicial, após os tokens acabarem, continuei o desenvolvimento com opencode, uma ferramenta de llm que é executada no terminal, priorizei a formula e depois o desenvolvimento da UI. ao longo do tempo fui atacando coisas menores do visual.


### Resultados / Findings

_O que você encontrou/construiu. Mostre dados, screenshots, links._
chatgpt: https://chatgpt.com/share/6a2c5293-25b0-83e9-baa3-7c4d41d32262, chat que usei pra pesquisar rápido sobre metabase, pesquisei como são realizados dashboards de kpi e como se parecem para que pudesse fazer algo proximo e que atende o desafio: https://www.tableau.com/dashboard/sales-dashboard-examples-and-templates



### Recomendações
1. Usar o score 0–100 como priorização principal — o modelo de scoring (fase + porte da conta + desempenho do vendedor + produto + tempo no pipeline) já está calculado e funcional. Agentes devem focar nos deals com score > 70, que têm maior probabilidade de sucesso.
2. Adotar o dashboard no dia a dia dos times de vendas — com filtros por região, gerente, produto e estágio, gestores conseguem identificar gargalos no pipeline e realocar recursos. A aba de Forecast (receita ponderada vs fechada por mês) já dá visibilidade de curto prazo.
3. Corrigir a qualidade dos dados de origem — os CSVs vieram com line endings DOS (\r\n), o que corrompeu campos como regional_office com carriage return. A empresa deve padronizar para Unix e validar imports automaticamente.
4. Internacionalizar também os labels do score — "Excellent/Good/Fair/Poor" e formatação de moeda/data estão hardcoded em inglês. Para operações multilíngue, precisam seguir o mesmo padrão i18n do restante.
5. Deploy com dados reais via API — o conceito está funcional com SQLite local. Para produção, conectar a um banco centralizado (PostgreSQL) com autenticação e dados em tempo real é o próximo passo.


### Limitações

_O que você não conseguiu resolver, verificar, ou que precisaria de mais tempo/dados._
Gostaria de entender mais de KPIS (rs) mas como tenho pouca experiência com KPI fui com o que tinha em mãos, checando diversas vezes os dados da planilha, e batendo com o que temos, mas se tivesse mais tempo com certeza me dedicaria mais adicionando mais indicadores.



---

## Process Log — Como usei IA

> Usei claude code haiku no chat do vscode + opencode. (ver logs)

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| ChatGPT | Dúvidas rápidas sobre ferramentas para uso no projeto |
|ClaudeCode Haiku on VSCode | Desenvolvimento de código. Construçao de boa parte da aplicação |
| OpenCode | Finalização dos toques finais do projeto, desenvolvimento final do código |

### Workflow

_Descreva passo a passo como você trabalhou. Onde a IA entrou em cada etapa?_

1. ChatGPT para pesquisar sobre metabase
2. desenvolvimento inicial do projeto com claude code no vscode
3. opencode para finalizar o desenvolvimento do projeto e melhoria da UI

### Onde a IA errou e como corrigi

Ao longo do desenvolvimento a IA deixou alguns erros no desenvolvimento mas que foram rapidamente resolvidos. apenas copiei e colei o erro e ela soube como resolver.



### O que eu adicionei que a IA sozinha não faria

foi necessário adicionar contexto, precisei passar os campos do filtro, caso contrário ela nao saberia que teria que adicionar, além de detalhes como linguagem.



---

## Evidências

_Anexe ou linke as evidências do processo:_

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [x] Chat exports
- [ ] Git history (se construiu código)
- [ ] Outro: _____________

---

_Submissão enviada em: 12/06/2026