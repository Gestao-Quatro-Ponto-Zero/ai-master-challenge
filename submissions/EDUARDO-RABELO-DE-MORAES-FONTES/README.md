# Submissão — Eduardo Rabelo e Moraes Fontes — Challenge [003] — Lead Scorer

## Sobre mim

- **Nome: Eduardo Rabelo e Moraes Fontes**
- **LinkedIn:**
- **Challenge escolhido: Challenge [003] — Lead Scorer**

---

## Executive Summary

Desenvolvi uma solução funcional de priorização comercial com dois serviços integrados: uma API em FastAPI para dados e scoring, e um frontend em Streamlit para uso direto pelos vendedores. Estruturei os dados CSV em SQLite, implementei score de oportunidade e score histórico de conta, e adicionei filtros operacionais (vendedor, manager, região, conta, estágio e faixas de score). A principal descoberta foi que deals abertos não tinham close_value, então o cálculo foi ajustado para usar sales_price como valor potencial quando necessário. Também deixei a lógica transparente no front com memória de cálculo por card (deal e conta), facilitando confiança e adoção. A recomendação principal é evoluir para produção com autenticação/autorização, observabilidade e integração com CRM em tempo real.

---

## Solução

Foi um app usando SQLITE+FASTAPI+FRONTEND; o código está na pasta `solution`.

### Abordagem

_Como você atacou o problema. Por onde começou? Como decompôs? O que priorizou?_
Li a documentação para entender o foco do problema: "Fazer os vendedores não perderem tempo escolhendo os leads"

O que eu priorizei?
Conversei com IA para criar uma mini-infra para ter acesso facilitado aos dados (API com FastAPI);

O que priorizou?
Velocidade de entrega + entregar uma ferramenta útil e demonstrar capacidade técnica;

### Resultados / Findings

Olhe a pasta `process-log`

### Recomendações

Gerar mais dados e buscar soluções de inteligência comercial;

### Limitações

Segurança do app; gostaria de ter integrado com uma LLM para ela ajudar a dar um score mais refinado;

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

Usei somente o VSCode (tipo Cursor). Pago; aqui dentro tem uns 50 modelos que vou usando conforme a complexidade da tarefa;

### Workflow

Com o VSCode, essa parte se mistura muito, pois eu vou trabalhando e usando IA.

### Onde a IA errou e como corrigi

Várias coisas, principalmente no frontend; fui pedindo para ela ajustar (nos logs tem o histórico)

### O que eu adicionei que a IA sozinha não faria

Arquitetura da solução; ela foi muito boa para executar o que eu queria, mas, na minha cabeça, o projeto (ferramentas que iria usar etc.) estava pronto antes de eu iniciar;

---

## Evidências

_Anexe ou linke as evidências do processo:_

- [x] Screenshots das conversas com IA
- [x] Screen recording do workflow
- [x] Chat exports
- [x] Git history (se construiu código)
- [x] Outro: _____________

---

_Submissão enviada em: 09/03/2026 01:46_
