# Submissão — Felipe Calgaro — Challenge 003

## Sobre mim

- **Nome:** Felipe Calgaro
- **LinkedIn:** https://www.linkedin.com/in/felipe-calgaro-81031a388/
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Construímos uma aplicação funcional em Next.js para priorizar negócios abertos com base nos CSVs reais do desafio, usando uma lógica de score explícita, determinística e auditável. Organizamos o fluxo em duas etapas centrais: seleção do vendedor e visualização do pipeline ranqueado, com explicação dos fatores positivos e negativos que compõem cada score. Também implementamos uma funcionalidade de dica da IA para transformar o breakdown técnico em orientação prática para o vendedor. A principal recomendação é evoluir esta base como ferramenta operacional de uso diário, preservando a transparência da pontuação e melhorando desempenho, segurança e persistência das respostas geradas.

---

## Solução

Entregamos um protótipo web funcional com leitura dos CSVs reais, página de entrada com seleção de vendedor, pipeline ranqueado por prioridade e explicação detalhada do score por negócio. A solução foi estruturada para privilegiar (1) clareza de uso para o time comercial e (2) clareza de manutenção para outros desenvolvedores.

### Abordagem

Começamos pela leitura integral do desafio e pela definição de restrições: usar os dados reais, evitar qualquer opacidade no score e manter o produto útil já no primeiro uso. A partir disso, decompusemos o trabalho em ingestão de dados, modelagem da lógica de pontuação, fluxo de seleção de vendedor, interface do pipeline, explicabilidade e validação com testes. Priorizamos sempre aquilo que aumentava valor de uso imediato na segunda-feira de manhã: ranking claro, justificativa visível e ação sugerida.

### Resultados / Findings

Construímos uma aplicação que carrega vendedores a partir do CSV da equipe comercial, persiste a seleção do agente e mostra seus negócios abertos em Engajamento e Prospecção ordenados por score. A pontuação é calculada por critérios explícitos e exibida na interface com chips resumidos, score final, ranking e painel de explicação expandível. Adicionamos ainda uma rota para geração de resumo e próxima ação com IA, além de testes unitários para validar a estabilidade e a coerência da lógica de score.

Lógica que pensamos para o cálculo do score:

![critérios](/process-log/screenshots/criteria.png)

### Recomendações

Recomendamos manter a lógica heurística como núcleo do produto, porque ela já entrega valor com alta transparência e baixo custo de interpretação, e considerar a utilização da análise da IA para a abordagem das oportunidades. Se aplicável, vale evoluir a experiência operacional com cache das respostas da IA, melhoria do tempo de resposta e aprofundamento do filtro de vendedor na etapa inicial. Por fim, seria prudente tratar segurança e governança como trabalho prioritário antes de qualquer exposição mais ampla da aplicação.

### Limitações

A página de login permanece simples e com lógica de filtro incompleta, embora funcional para o fluxo principal de seleção do vendedor. A segurança do projeto é inexistente neste estágio, o que é aceitável apenas como protótipo local de challenge. A resposta da IA poderia ser cacheada ou armazenada para evitar repetição de chamadas equivalentes, e o tempo de resposta atual está muito lento; resolver isso exigiria mais tempo para analisar causas, otimizar o processo e possivelmente implementar streaming, persistência ou outra estratégia de entrega progressiva.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta                        | Para que usou                                                                                                                                                  |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub Copilot (GPT-5.4 e outros) | Vibe Coding: entendimento do desafio, planejamento, implementação do protótipo em Next.js, refino da lógica de score, documentação do processo e revisão final |
| OpenAI API (gpt-5-nano)           | Geração da explicação textual e da próxima ação dentro do próprio produto, a partir dos fatores de score calculados pela aplicação                             |

### Workflow

1. Começamos entendendo o enunciado, os arquivos CSV e as exigências não negociáveis do challenge antes de sair implementando qualquer tela.
2. Em seguida, usamos a IA para estruturar um plano de execução, criar um arquivo de instruções do projeto e transformar o problema em partes menores: login, leitura dos dados, score, pipeline, explicação e testes.
3. Implementamos a lógica de pontuação de forma determinística e isolada em utilitários, validando o comportamento com testes unitários e cenários de borda.
4. Depois conectamos a lógica ao App Router do Next.js, construindo a página de login, a página de pipeline e a camada de explicabilidade na interface.
5. Por fim, refinamos a funcionalidade de dica da IA, ajustamos detalhes de UX, revisamos o código com foco em manutenção e documentamos o processo e as limitações da solução.

### Onde a IA errou e como corrigi

A IA precisou de correção principalmente em decisões de boas práticas específicas de Next.js. Houve momentos em que foi necessário reforçar separação entre lógica de negócio e camada de interface, manter o que era determinístico fora de componentes React e evitar soluções apressadas que misturassem responsabilidade demais em uma única página. Também corrigi escolhas de acabamento textual na tradução final da interface, porque algumas palavras ficaram sem acentos ou com padronização inconsistente em português, algo que precisava ser revisto manualmente para manter qualidade de produto.

### O que eu adicionei que a IA sozinha não faria

O principal acréscimo humano foi definir instruções específicas de desenvolvimento em Next.js com base em intuição técnica e gosto pessoal de implementação, especialmente na forma de organizar o App Router, preservar clareza arquitetural e manter a experiência enxuta e direta para uso comercial. Também insisti em uma solução limpa para buscar a resposta da IA na interface, usando uma biblioteca específica para isso, o TanStack React Query em vez de recorrer a uma gambiarra com fetch espalhado e gerenciamento manual excessivo. Além disso, houve julgamento humano na escolha de manter a heurística explicável como centro do produto.

---

## Evidências

- [x] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [ ] Git history (se construiu código)
- [x] Outro: narrativa escrita em Lead Scorer.pdf e gravação do histórico de conversa

---

_Submissão enviada em: 12/03/2026_
