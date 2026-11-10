# Teste no ar — versão ligada ao banco

**Veredito: aprovado.** As escritas que falhavam na fatia 1 agora funcionam no ar e persistem no banco: ✓/✗ das Prioridades (B1) e mudança de estágio (B2). Os itens médios corrigidos também conferem. Os números do Painel saem do banco e batem com ele. Entradas mal formadas não derrubam o app. Ficam três achados leves (seção 5).

- **Endereço:** https://g4-sight.vercel.app, versão dos commits `4ff100f` e `fdd15d0`.
- **Quando:** 10/11/2026, 06:20–06:35 UTC.
- **Como:** Chrome no computador. Perfis: vendedora Anna Snelling (usuário 3), manager Dustin Brinkmann (40) e admin (2). Cada escrita foi conferida na auditoria do banco (somente leitura).
- **`/api/health` antes e depois de tudo:** `{"app":"ok","banco":"ok","fonte":"banco","usuarios":42,"somente_leitura":false}`.

Prints em [prints-banco/](prints-banco/).

## 1. Painel com a fonte "banco de dados"

O rodapé mostra "Dados até 31/12/2017. Fonte: banco de dados.". Os números são os do teste da fatia 1 mais o lead de teste 88UBTBQ8 (aberto e encerrado como Perdido em 31/12/2017), o que confere com o banco:

| Cartão | Anna | Time Dustin | Admin |
|---|---|---|---|
| Leads novos (30 dias) | 8 (7 + 1), "1 hoje" | 19 (18 + 1), −37% | 118 (117 + 1), −57% |
| Em negociação | 57 · US$ 95.414 | 193 · US$ 283 mil | 1.589 · US$ 3,89 mi |
| Fechamentos | 2 hoje / 26 em 30 dias | 6 / 91 | 19 / 498 |
| Conversão em 30 dias | 83,9% (26 × 5) | 85,8% (91 × 15) | 78,5% (498 × 136), +24,8 p.p. |
| Receita ganha em 30 dias | US$ 36.454 | US$ 142 mil | US$ 1,1 mi |
| Total de leads | 449 | 1.584 | 8.801 |
| Funil (Perdido) | 129 | 440 | 2.474 |
| Em risco / esfriaram | 1 / 56 | 3 / 190 | 141 / 1.291 |

A coluna "Prioridades feitas hoje" do manager mostra 2 para a Anna, igual ao contador dela.

## 2. Funções

| # | Teste | Resultado |
|---|---|---|
| F1 | ✓ como vendedora, com tipo e comentário | ✅ 200; "Registrado na linha do tempo do lead · Desfazer"; contador 1 → 2 de 10. No banco: `acao_registros` com tipo `ligacao`, comentário, data do negócio 31/12/2017, hora real e item da lista |
| F2 | ✗ como vendedora + Desfazer | ✅ 200; "Pulado hoje. O deal não muda."; Desfazer (`/api/desfazer` 200) devolve o item e o contador |
| F3 | ✗ e ✓ como manager (item do deal B08R55ET, da Anna) + Desfazer | ✅ os dois gravam (200) e desfazem (200) |
| F4 | Formulário do ✓ no item seguinte | ✅ abre limpo (corrige M1) |
| F5 | Ganho com valor 0 | ✅ recusado: "Informe o valor de fechamento: um número inteiro maior que zero." (corrige M3) |
| F6 | Ganho com US$ 60 + Desfazer | ✅ grava (corrige B2); Desfazer volta para Em negociação |
| F7 | Perdido + Desfazer | ✅ grava (motivo opcional); Desfazer volta para Em negociação |
| F8 | Comentário + Apagar | ✅ "Comentário publicado."; o Apagar pede confirmação na própria tela (corrige M7) e "Comentário apagado · Desfazer" |
| F9 | Contato com nome, cargo, e-mail e telefone | ✅ grava (corrige M4); o card do Pipeline já mostra "Contato QA banco, Compras" sem recarregar (corrige M2) |
| F10 | Aplicar e remover tag | ✅ 200 e 200 |
| F11 | Lote "Comentar" em 1 lead + Desfazer | ✅ `/api/lotes` 200; Desfazer dentro dos 10 s (`/api/desfazer` 200) remove o comentário (3 → 2) |
| F12 | Persistência | ✅ depois de recarregar e cerca de 7 minutos: contador 2 de 10, contato no B08R55ET, estágio Em negociação, tag removida, comentário do lote no 88UBTBQ8. Os dados vêm do banco, não da memória da instância |

## 3. Segurança

| Teste | Resultado |
|---|---|
| Perfil "sistema" (`usuarioId: 1`) | ✅ 400 |
| JSON quebrado, tipos errados, id com aspas e ponto e vírgula, estágio inválido, valor negativo, comentário de 200 mil caracteres, e-mail inválido, lote com ids lixo | ✅ todos 400 com frase simples, nada gravado |
| Comentário com HTML | ✅ 400 "O comentário não pode ter HTML." |
| Token de desfazer vazio, lixo, número, gigante ou JSON quebrado | ✅ todos 400 |
| Método errado (PUT em `/api/prioridades`) | ✅ 405 |
| `/api/health` depois das entradas ruins | ✅ banco "ok", somente leitura falso |

## 4. Escritas feitas neste teste (auditoria 9076–9104)

| Hora (UTC) | Usuário | O quê | Estado final |
|---|---|---|---|
| 06:22:18 | Anna | ✓ no deal **0D8Y5JA0** (lead real da lista dela), tipo ligação, comentário "Teste QA banco: liguei, pediu retorno"; atualiza o último contato do deal para 31/12/2017 | **ficou** (não desfeito) |
| 06:22:32 | Anna | ✗ no deal 1FEHFRKX | desfeito |
| 06:23:27 / 06:23:48 | Anna | B08R55ET → Ganho (US$ 60) e → Perdido | os dois desfeitos; deal em Em negociação |
| 06:24:05 | Anna | Comentário no B08R55ET | apagado (remoção lógica) |
| 06:24:24 | Anna | Contato "Contato QA banco" (Compras, qa@example.com, 0000-0000) ligado ao B08R55ET | **ficou** |
| 06:26:09 | Anna | Lote 2: comentário "Teste QA banco: lote" no 88UBTBQ8 | **ficou** |
| 06:26:39 | Anna | Lote 3: comentário "Teste QA banco: lote 2" no 88UBTBQ8 | desfeito |
| 06:27:04 | Anna | Tag "teste" no B08R55ET | removida |
| 06:27:26 | Dustin | Lista do dia do manager montada ao abrir o Painel (3 itens) | ficou (é o funcionamento normal) |
| 06:27:42 / 06:27:59 | Dustin | ✗ e ✓ no B08R55ET | os dois desfeitos |

Nada foi apagado do banco. Todas as linhas estão auditadas com o usuário escolhido.

## 5. Achados

| # | Gravidade | Achado | Sugestão |
|---|---|---|---|
| N1 | Leve | O filtro livre "Teste de persistência" vira "Contém 'teste persistencia'" e não acha o lead "Teste de persistência (pode encerrar)". O interpretador tira o "de" e depois procura a frase sem ele | No "Contém", procurar cada palavra que sobrou (todas presentes), não a frase |
| N2 | Leve | Não existe o "Desfazer este lote" de 24 horas previsto em ESPEC-TELAS 6.1; só o aviso de 10 segundos | Pôr na tela (por exemplo, numa lista de lotes recentes) ou registrar a mudança na especificação |
| N3 | Leve | O contador "X de 10 feitas" também sobe com o ✗ (pulado) | Se a meta é de itens trabalhados, contar só o ✓, ou trocar o texto para "resolvidas" |
| N4 | Observação | Erros de validação de campo na API (ex.: e-mail inválido) voltam com a frase genérica "Não entendi o pedido" | A tela já valida antes; vale uma frase específica também na API |

Itens da fatia 1 confirmados como corrigidos: B1, B2, M1, M2, M3, M4 e M7. Não verificados de novo nesta rodada: M5 (FIT/HEAT na explicação da nota), M6 (rolagem ao abrir o Ganho) e o arraste entre colunas.
