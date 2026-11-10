# Proposta: o mínimo de CRM que falta

> Proposta para o Leandro escolher. Nada disto está construído nem entra no escopo sem a escolha dele.
> Decisão 20: o produto é o CRM único do time, com a prioridade embutida no pipeline.

## O que o desenho já cobre

| Função de CRM | Onde está |
|---|---|
| Usuários e papéis (vendedor, manager, admin) | `config_usuarios`, escolha de perfil |
| Lista de deals com busca, filtros e ordenação | `/deals` |
| Ficha do deal: dados, estágio, empresa, histórico | painel do deal (`?deal=ID`) |
| Avançar estágio, encerrar como ganho ou perdido | `core_atualizar_deal`, `core_encerrar_deal` |
| Registrar atividade (Liguei, Requalifiquei, Desisti) | `acao_registros` |
| Visão do manager e do admin | `/time` |
| Limpeza do pipeline | `/limpeza` |
| Trilha de auditoria | `system_auditoria` |
| **Prioridade**: score, motivos, ação sugerida, deals esfriando | em todas as telas |

## O que falta para ser o único sistema do time

Ordenado pelo que mais trava o uso diário se faltar.

| # | Função | Por que faz falta | O que muda no desenho | Tamanho |
|---|---|---|---|---|
| 1 | **Criar deal** | Sem isso, oportunidade nova não entra no CRM e o vendedor volta para a planilha | Rota `POST /api/deals` e função `core_criar_deal` (vendedor, produto, empresa e estágio inicial Prospecting). O deal novo aparece com "Sem nota ainda" até a próxima rodada de score | P |
| 2 | **Pipeline em colunas por estágio** | É a tela que todo vendedor espera de um CRM; mostra onde cada deal está | Tela `/pipeline` com Prospecção, Em negociação, Ganhos e Perdidos (estes dois só do mês). Cada cartão mostra o score e o selo. Arrastar entre colunas usa a mesma função de mudar estágio, que já tem auditoria e controle de versão | M |
| 3 | **Ficha da empresa** | O vendedor precisa ver a empresa inteira antes de ligar | Tela `/contas/[nome]`: dados (setor, receita, funcionários, país, empresa-mãe), deals abertos com score, ganhos e perdidos e a taxa de fechamento. Só leitura; tudo já existe em `core_contas` e `core_deals` | P |
| 4 | **Cadastrar empresa nova** | 68% dos deals abertos estão sem empresa; se a empresa não existe, o vendedor não consegue preencher | Função `core_criar_conta`, com auditoria. Liga com a decisão (a) de [DESENHO-ACOES.md](DESENHO-ACOES.md): só escolher ou também criar | P |
| 5 | **Próximo passo com data** | O CRM avisa "ligar para X na quinta" e alimenta o "Meu dia" | Coluna `proximo_passo` e `proximo_passo_em` em `core_deals`, e uma lista "Para hoje" no topo do "Meu dia" | P |
| 6 | **Passar deal para outro vendedor** | Férias, saída de alguém, rebalanceamento do time | Função `core_reatribuir_deal`, só para manager e admin (regra de dado), com auditoria | P |
| 7 | **Contatos da empresa** (pessoas, cargo, e-mail, telefone) | Todo CRM guarda com quem falar | Tabela nova `core_contatos` → `core_contas`. O dataset não tem contatos, então a lista começa vazia | M |
| 8 | **Exportar para planilha** | A Head de RevOps vai querer os números fora da tela | `GET /api/exportar?filtros` gera CSV do que está na tela | P |

P = pequeno (uma tela ou uma função), M = médio (tela nova com interação ou tabela nova).

## Proposta de corte para a primeira versão

- **Entram:** 1 a 4. Com eles o vendedor cria, acompanha e fecha um deal sem sair do CRM, e a ficha da empresa resolve o problema dos 68% sem empresa.
- **Logo depois:** 5 e 6, que são pequenos e completam a rotina do vendedor e do manager.
- **Depois:** 7 e 8. Contatos começariam vazios (o dataset não tem), e a exportação pode esperar a primeira conversa com a Head de RevOps.

## Fora do mínimo

Ficam de fora: e-mail e agenda integrados, cotação e proposta, metas por vendedor, previsão de receita, campos personalizados, permissões finas e login de verdade. Todos estão fora do dataset e do pedido da Head de RevOps.

## Decisão para o Leandro

Quais destas oito funções entram na primeira versão (proposta acima: 1 a 4).
