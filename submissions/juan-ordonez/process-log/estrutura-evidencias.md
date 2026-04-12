# Estrutura do PDF de Evidências

Guia de montagem para o `evidencias-processo.pdf`.
Cada bloco abaixo é uma seção do PDF. Coloque os screenshots relevantes
e complete o texto de contexto indicado.

---

## 1. Capa

- Nome: Juan Ordoñez
- Challenge: build-003-lead-scorer
- Ferramentas: Claude Code (Opus 4.6), Lovable, Almond Voice, Codex
- Data: abril 2026

---

## 2. Exploração dos dados (3-4 páginas)

**Contexto:** antes de construir qualquer coisa, explorei os dados pra
entender o que realmente importa.

**Screenshots sugeridos:**
- [ ] Print da análise de taxas de conversão por recorte (vendedor, setor, região)
- [ ] Print mostrando a descoberta de que setor/região não discriminam
- [ ] Print do insight "deals perdidos morrem rápido, deals ganhos demoram"
- [ ] Print da validação de interação entre variáveis (tabela de deltas)

**Texto entre os prints:** o que perguntei, o que descobri, e por que
isso mudou minha abordagem.

---

## 3. Decisões de arquitetura (2-3 páginas)

**Contexto:** escolhi o caminho do score e a stack da ferramenta com
base nos dados, não em preferência técnica.

**Screenshots sugeridos:**
- [ ] Print da comparação dos 3 caminhos (heurística, lookup empírico, regressão)
- [ ] Print da escolha de HTML estático sobre Streamlit (com argumentos)
- [ ] Print da decisão de ranking por vendedor em vez de limites de corte fixos

**Texto entre os prints:** por que cada decisão foi tomada e qual era
a alternativa rejeitada.

---

## 4. Taxonomia e categorias (2-3 páginas)

**Contexto:** iteramos 3 versões dos nomes das categorias até chegar
em Prioridade 1-4 com ações claras.

**Screenshots sugeridos:**
- [ ] Print da primeira versão (6 categorias, nomes genéricos)
- [ ] Print do problema: 56% dos deals caindo em "Acompanhar"
- [ ] Print da versão final: Prioridade 1-4 + Atribuir conta
- [ ] Print da mudança de "Já vendeu / 1º Contato" pra "Cliente / Prospect"

**Texto entre os prints:** o que estava errado em cada versão e por que mudei.

---

## 5. Construção da interface (3-4 páginas)

**Contexto:** a interface passou por várias iterações visuais, de
smoke test até o layout final inspirado em CRM profissional.

**Screenshots sugeridos:**
- [ ] Print do smoke test inicial (versão mínima funcionando)
- [ ] Print da referência do Lovable (versão React)
- [ ] Print da referência visual (Twenty CRM ou similar)
- [ ] Print da versão final com tabela, dropdown custom, cards expandíveis
- [ ] Print mostrando visão de time/regional no dropdown

**Texto entre os prints:** o que mudei em cada iteração e por que
(cores, contrastes, colunas, badges, expand/collapse).

---

## 6. Correções e bugs (1-2 páginas)

**Contexto:** durante o desenvolvimento, encontrei bugs e informações
incorretas que precisaram ser corrigidos.

**Screenshots sugeridos:**
- [ ] Print do bug dos deals expandidos ao trocar de vendedor
- [ ] Print do bug do dropdown mostrando número errado de deals
- [ ] Print da validação dos dados oficiais do Kaggle (MD5 idênticos)

**Texto entre os prints:** o que estava errado, como descobri, e
como corrigi.

---

## 7. Auditoria final (1-2 páginas)

**Contexto:** antes de submeter, fiz uma auditoria completa pra
garantir que o motor, os dados e a interface estão consistentes.

**Screenshots sugeridos:**
- [ ] Print do resultado da auditoria (6/6 buckets OK, 10/10 deals idênticos)
- [ ] Print do ranking do Darcel validado (top 15 por retorno esperado)

**Texto entre os prints:** o que verifiquei e qual foi o resultado.

---

## 8. Revisão com Codex (1 página)

**Contexto:** usei o Codex pra fazer uma revisão geral final antes
de submeter.

**Screenshots sugeridos:**
- [ ] Print da revisão do Codex confirmando integridade

**Texto:** o que o Codex validou e se encontrou algum problema.

---

## Dicas de montagem

- **15-20 screenshots** no total (não precisa dos 100 — selecione os que mostram julgamento e iteração)
- Cada screenshot com **1-2 frases de contexto acima** (o que estava fazendo) e **1 frase abaixo** (o que decidiu)
- O avaliador quer ver que você **pensou**, não que trabalhou muito
- Formato: PDF de ~15-20 páginas
