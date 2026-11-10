# Teste no ar — correções N1 a N4

**Veredito: aprovado.** As quatro correções funcionam no ar e a regressão passou. Fica uma observação leve (R1).

- **Endereço:** https://g4-sight.vercel.app, commit `1e3a86b`.
- **Quando:** 10/11/2026, 06:43–06:50 UTC.
- **Perfis:** vendedora Anna Snelling (3), manager Dustin Brinkmann (40), admin (2). Para conferir quem vê os lotes, também Cecily Lampkin (9, vendedora do mesmo time) e o usuário 41 (manager de outro time).
- **`/api/health` no início e no fim:** banco "ok", fonte "banco", somente leitura falso.

Prints em [prints-n1-n4/](prints-n1-n4/).

## N1 — filtro livre

| Texto digitado | Etiqueta | Resultado |
|---|---|---|
| Teste de persistência | Contém "teste persistencia" | ✅ 1 lead: "Teste de persistência (pode encerrar)" (88UBTBQ8) |
| PERSISTENCIA teste | Contém "persistencia teste" | ✅ o mesmo lead: ordem, acento e maiúsculas não importam |

## N2 — Lotes recentes

| Teste | Resultado |
|---|---|
| Botão "Lotes recentes" na tela Leads | ✅ abre "Lotes das últimas 24 horas" com tipo, quantidade, autor, hora (de Brasília) e o prazo para desfazer; lotes já desfeitos mostram quem desfez e quando |
| Quem vê (`/api/lotes`) | ✅ Anna (autora): os 4 lotes. Dustin (manager do time): os 4. Admin: os 4. Cecily (vendedora do mesmo time, não é autora): nenhum. Manager de outro time: nenhum |
| "Desfazer este lote" pela vendedora (lote 2) | ✅ pede confirmação na própria janela ("Confirmar / Cancelar"); aviso "Lote desfeito: 1 mudança desfeita."; o comentário do lote foi removido |
| "Desfazer este lote" pelo manager (lote 1), com o lead alterado depois do lote | ✅ aviso "Lote desfeito: 0 mudanças desfeitas; 1 ficou como está, porque o lead mudou depois."; a lista passa a mostrar "Desfeito por Dustin Brinkmann" |

## N3 — contador das Prioridades

| Teste | Resultado |
|---|---|
| ✗ em um item da Anna | ✅ "2 de 10 feitas" não muda; aparece "1 pulada" ao lado |
| Desfazer o ✗ | ✅ volta a "2 de 10 feitas", sem "pulada" |
| ✓ em um item (regressão) | ✅ 2 → 3 de 10; Desfazer volta a 2 |

## N4 — erro de campo na API

Cada pedido levou uma marca no valor digitado; nenhuma resposta a devolveu.

| Campo inválido | Resposta |
|---|---|
| E-mail do contato | ✅ 400 "E-mail inválido. Confira o endereço (exemplo: nome@empresa.com)." |
| Telefone do contato | ✅ 400 "Telefone inválido. Use de 6 a 25 caracteres: números, espaço, +, parênteses, ponto ou traço." |
| Nome vazio | ✅ 400 "Preencha o nome." |
| Nome com mais de 120 caracteres / cargo com mais de 80 | ✅ 400 com o limite de cada campo |
| Comentário com mais de 1.000 caracteres | ✅ 400 "O comentário pode ter no máximo 1000 caracteres." |
| Pedido sem um campo obrigatório que a tela sempre manda (ex.: `versao`) | 400 genérico "Não entendi o pedido…" (adequado: não é erro de digitação do usuário) |

## Regressão rápida

| Teste | Resultado |
|---|---|
| ✓ com tipo e comentário + Desfazer | ✅ 200 / 200 |
| Estágio Perdido + Desfazer (B08R55ET) | ✅ Perdido → Em negociação |
| Comentário + Apagar (B08R55ET) | ✅ publicado e apagado com confirmação na tela |
| `/api/health` | ✅ ok |

## Escritas feitas (auditoria 9112–9125)

| Hora (UTC) | Usuário | O quê | Estado final |
|---|---|---|---|
| 06:45:52 | Anna | Desfez o lote 2 (o comentário "Teste QA banco: lote" no 88UBTBQ8 foi removido) | lote desfeito |
| 06:46:10 | Anna | Removeu a tag "teste" do 88UBTBQ8 (para testar o caso "ficou como está") | tag removida |
| 06:46:39 | Dustin | Desfez o lote 1 (0 desfeitas, 1 ficou) | lote marcado como desfeito |
| 06:47:00 | Anna | ✗ no 1FEHFRKX (prioridade da Anna) | desfeito |
| 06:47:53 | Anna | ✓ no 1FEHFRKX, comentário "Teste QA regressao" | desfeito; o último contato do deal foi recalculado |
| 06:48:19 | Anna | B08R55ET → Perdido | desfeito (Em negociação) |
| 06:48:25 | Anna | Comentário "Teste QA regressao comentario" no B08R55ET | apagado (remoção lógica) |

Os pedidos com erro do N4 foram todos recusados e não gravaram nada. Os 4 lotes da Anna estão desfeitos.

## Observação

| # | Gravidade | Achado | Sugestão |
|---|---|---|---|
| R1 | Leve | Comentário só com espaços passa pela validação da rota e cai numa regra do banco: volta 422 com a frase genérica "Não foi possível salvar: os dados não são aceitos." | Aparar os espaços no schema da rota (`trim().min(1)`) para responder "Escreva o comentário." |
