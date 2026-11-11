# G4 Sight: usuários, operação do pipeline e auditoria

> Descreve as regras como o app as aplica hoje. O modelo do banco (tabelas, chaves, functions e gatilhos) é mantido em `solution/db/`, que é a fonte oficial; este arquivo não repete o SQL.

## Decisões que as telas seguem

| # | Decisão |
|---|---|
| 12 | Sem login e sem senha: a pessoa escolhe o perfil (vendedor, manager ou admin) e, se for vendedor ou manager, o nome. |
| 15 | Os usuários vêm do dataset: 35 vendedores, 6 managers e 1 admin. O usuário "sistema" assina as cargas e nunca é aceito pela tela. |
| 16 | Sistema operacional: inserir e alterar liberados; apagar proibido. O servidor não bloqueia por dono do deal. |
| 20 | O produto é o CRM único do time, com a prioridade embutida no pipeline. |
| 37 | O ✓ nas Prioridades do dia registra o que foi feito: tipo de atividade e comentário obrigatórios, com data e hora. |

## O que cada perfil vê e faz

| Perfil | Abre em | Enxerga | Só ele faz |
|---|---|---|---|
| Vendedor | Painel | os deals dele | — |
| Manager | Painel | os deals do time, com filtro por vendedor | reabrir deal encerrado; criar tag |
| Admin | Painel | tudo, com filtros de região, manager e vendedor | o mesmo do manager |

O perfil organiza a tela e assina as ações. Sem senha, ele não protege nada: qualquer pessoa pode escolher qualquer nome.

## Regras aplicadas

| Ação | Regra |
|---|---|
| Mudar estágio | Prospecção → Em negociação (grava a data de abertura) ou Perdido; Em negociação → Ganho (pede o valor, inteiro e maior que zero) ou Perdido (motivo opcional). Reabrir (Ganho/Perdido → Em negociação) só manager e admin. |
| Edição ao mesmo tempo | A tela envia a versão que leu. Se o deal mudou no meio, a mudança é recusada (409) com a frase "Este deal foi alterado por … Recarregue para ver a versão atual." |
| Liguei, Requalifiquei, Desisti | Só em deal aberto; nota opcional de até 280 caracteres. Liguei e Requalifiquei contam como contato. |
| ✓ / ✗ nas Prioridades | ✓ exige tipo de atividade (ligação, e-mail, mensagem, reunião, proposta enviada, requalificado, sem resposta) e comentário; conta como contato. ✗ pula o deal hoje, sem mudar nada. Um item só pode ser marcado uma vez por dia. |
| Comentário | 1 a 1.000 caracteres, sem HTML. "Apagar" é remoção lógica: some da tela e da linha do tempo, mas fica guardado. Quem apaga: o autor, o manager ou o admin. |
| Tags | Aplicar e remover: todos. Criar: manager e admin. Até 10 tags por deal. Remover é remoção lógica. |
| Lote | Até 500 leads por vez; "selecionar os N do filtro" é recalculado no servidor na hora de aplicar. Os que não se aplicam são pulados e contados. Dá para desfazer o lote inteiro. |
| Novo lead | Produto obrigatório; empresa opcional (precisa estar cadastrada). Vendedor cadastra para si; manager e admin escolhem o vendedor ou deixam distribuir. |
| Empresa | Criar e editar: todos. O nome não muda depois de criado; a empresa-mãe precisa estar cadastrada. |
| Desfazer | Toda mudança mostra "Desfazer" por 10 segundos. Desfazer nunca apaga: devolve o estado anterior ou marca como desfeito. |

## Onde isso mora hoje

- Nesta versão de validação, as regras estão em `src/server/repositorio.ts` e as mudanças ficam em memória no servidor.
- No banco, as mesmas regras estão nas functions de `solution/db/` (mudança de estágio, ações, comentários, tags, lote, prioridades, roteamento), com auditoria por gatilho e bloqueio de DELETE.
- Quando o app ligar no banco, o repositório passa a chamar essas functions; as rotas e as telas não mudam.

## Segurança nas rotas

- Limite de escritas por endereço de rede (60 por minuto), porque sem login o limite por usuário é fácil de contornar.
- `correlation_id` gerado no servidor a cada pedido e mostrado como "código para suporte" nas mensagens de erro.
- Entrada validada com zod; nenhum texto digitado entra na página como HTML; nenhuma fonte de dados vem da URL.

## Ainda em aberto

- Repasse por falta de atendimento e avisos aos vendedores: a tela já mostra o contador "Perdidos por falta de atendimento", que fica em 0 até a rotina do score existir.
- Roteamento por FIT: enquanto não há nota, o lead distribuído automaticamente vai para o vendedor com menos deals abertos.
