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

Em ordem: primeiro o que impede o pipeline de estar inteiro no CRM, depois o que mais trava o uso diário.

| # | Função | Por que faz falta | O que muda no desenho | Tamanho |
|---|---|---|---|---|
| 1 | **Criar deal** | Sem isso, oportunidade nova não entra no CRM e o vendedor volta para a planilha | Rota `POST /api/deals` e função `core_criar_deal` (vendedor, produto, empresa e estágio inicial Prospecting). O deal novo aparece com "Sem nota ainda" até a próxima rodada de score | P |
| 2 | **Importar deals (CSV)** | Para ser o CRM único, o time precisa trazer de uma vez o pipeline que hoje está em planilhas e em outros sistemas, sem digitar deal a deal | Tela `/importar` e função `core_importar_deals`, com histórico em `system_importacoes`. Detalhes abaixo | M |
| 3 | **Pipeline em colunas por estágio** | É a tela que todo vendedor espera de um CRM; mostra onde cada deal está | Tela `/pipeline` com Prospecção, Em negociação, Ganhos e Perdidos (estes dois só do mês). Cada cartão mostra o score e o selo. Arrastar entre colunas usa a mesma função de mudar estágio, que já tem auditoria e controle de versão | M |
| 4 | **Ficha da empresa** | O vendedor precisa ver a empresa inteira antes de ligar | Tela `/contas/[nome]`: dados (setor, receita, funcionários, país, empresa-mãe), deals abertos com score, ganhos e perdidos e a taxa de fechamento. Só leitura; tudo já existe em `core_contas` e `core_deals` | P |
| 5 | **Cadastrar empresa nova** | 68% dos deals abertos estão sem empresa; se a empresa não existe, o vendedor não consegue preencher (e a importação recusa a linha) | Função `core_criar_conta`, com auditoria. Liga com a decisão (a) de [DESENHO-ACOES.md](DESENHO-ACOES.md): só escolher ou também criar | P |
| 6 | **Próximo passo com data** | O CRM avisa "ligar para X na quinta" e alimenta o "Meu dia" | Colunas `proximo_passo` e `proximo_passo_em` em `core_deals`, e uma lista "Para hoje" no topo do "Meu dia" | P |
| 7 | **Passar deal para outro vendedor** | Férias, saída de alguém, rebalanceamento do time | Função `core_reatribuir_deal`, só para manager e admin (regra de dado), com auditoria | P |
| 8 | **Contatos da empresa** (pessoas, cargo, e-mail, telefone) | Todo CRM guarda com quem falar | Tabela nova `core_contatos` → `core_contas`. O dataset não tem contatos, então a lista começa vazia | M |
| 9 | **Exportar para planilha** | A Head de RevOps vai querer os números fora da tela | `GET /api/exportar?filtros` gera CSV do que está na tela | P |

P = pequeno (uma tela ou uma função), M = médio (tela nova com interação ou tabela nova).

## Detalhe: Importar deals (CSV)

**Quem usa:** manager e admin. A tela só aparece para eles (proposta).

**Arquivo aceito:**
- CSV em UTF-8, separado por vírgula ou ponto e vírgula, com cabeçalho. A ordem das colunas é livre.
- Até 10 mil linhas por arquivo (o dataset inteiro tem 8.800).
- Colunas iguais às do `sales_pipeline` exportado do sistema anterior:

| Coluna | Obrigatória | Regra |
|---|---|---|
| `opportunity_id` | sim | identifica o deal; é ela que impede duplicar |
| `sales_agent` | sim | precisa existir em `core_vendedores` |
| `product` | sim | precisa existir em `core_produtos` |
| `account` | não | vazia = deal sem empresa; preenchida, precisa existir em `core_contas` |
| `deal_stage` | sim | Prospecting, Engaging, Won ou Lost |
| `engage_date` | não (obrigatória fora de Prospecting) | data AAAA-MM-DD |
| `close_date` | só em Won e Lost | data AAAA-MM-DD, não anterior a `engage_date` |
| `close_value` | só em Won | maior que zero |

Os nomes passam pela mesma normalização da limpeza de dados (espaços extras, maiúsculas e minúsculas, e grafias conhecidas como "GTXPro" → "GTX Pro") antes de serem procurados nas tabelas.

**Como funciona, em dois passos:**
1. **Conferir:** a pessoa envia o arquivo e o CRM valida linha por linha, sem gravar nada.
2. **Importar:** a tela mostra o relatório, e o botão principal diz exatamente o que vai acontecer ("Importar 1.240 deals"). As linhas aceitas são gravadas numa transação só: entram todas ou nenhuma.

**Relatório em frase simples:**

> 1.240 deals prontos para importar.
> 12 já estavam no CRM e serão ignorados.
> 3 linhas recusadas:
> - Linha 15: o vendedor "Ana Snelling" não está no time. Você quis dizer "Anna Snelling"?
> - Linha 88: a empresa "Acme Corp" não está cadastrada. Cadastre a empresa ou deixe a coluna vazia.
> - Linha 301: deal ganho sem valor de fechamento.

- As recusas podem ser baixadas como CSV, com uma coluna "motivo", para corrigir e enviar de novo.
- O que é técnico (nome e tamanho do arquivo, código para suporte) fica em "Ver detalhes".

**Vínculo com as tabelas existentes:** vendedor, produto e empresa são gravados como as chaves estrangeiras de `core_deals` (`vendedor_nome`, `produto_nome`, `conta_nome`). Uma linha que aponta para algo inexistente é recusada na conferência, e o próprio banco recusaria também (DB-02).

**Importar de novo não duplica:**
- `opportunity_id` é a chave de `core_deals`. A função usa `insert … on conflict (opportunity_id) do nothing`, e o relatório conta esses deals como "já estavam no CRM".
- A importação não sobrescreve deals existentes, porque isso apagaria em silêncio o que o vendedor mudou no CRM. Atualizar por planilha fica como decisão em aberto.
- Se o mesmo `opportunity_id` aparece duas vezes no arquivo, a segunda linha é recusada.

**Mesma auditoria:**
- A gravação passa pela função `core_importar_deals(usuario_id, correlation_id, linhas)`. O gatilho `system_auditar()` grava um registro por deal inserido em `system_auditoria`, com o usuário, o papel e o mesmo `correlation_id` da importação.
- O resumo vai para uma tabela nova:

```sql
create table system_importacoes (
  id             bigint generated always as identity primary key,
  usuario_id     bigint not null references config_usuarios(id) on delete restrict,
  arquivo_nome   text   not null,
  arquivo_sha256 text   not null,
  linhas_total   int    not null,
  aceitas        int    not null,
  ja_existiam    int    not null,
  recusadas      int    not null,
  correlation_id uuid   not null,
  criado_em      timestamptz not null default now()
);
create index on system_importacoes (usuario_id);
create index on system_importacoes (correlation_id);
```

- A tela `/importar` mostra as importações anteriores (quem, quando, quantos deals). Pelo `correlation_id`, chega-se a cada deal criado.

**Depois da importação:** os deals novos aparecem com "Sem nota ainda" até a próxima rodada de score.

**No desenho atual:**
- rota `POST /api/importar` com `{etapa: "conferir" | "importar"}`;
- a função de validação em `src/lib/importacao.ts` (pura, testada);
- uma dependência pequena de leitura de CSV;
- um caminho crítico a mais no Playwright: enviar arquivo, ver o relatório, importar e reimportar sem duplicar.

**Opção para a sessão do score:** a migração inicial do CRM antigo pode usar esta mesma função, assinada pelo usuário "sistema". Assim existe um caminho só para entrar deal em massa, sempre auditado.

## Proposta de corte para a primeira versão

- **Entram:** 1 a 5. Com eles o time traz o pipeline atual para dentro do CRM, cria, acompanha e fecha deals sem sair dele. A ficha da empresa e o cadastro de empresa resolvem o problema dos 68% sem empresa.
- **Logo depois:** 6 e 7, que são pequenos e completam a rotina do vendedor e do manager.
- **Depois:** 8 e 9. Contatos começariam vazios (o dataset não tem), e a exportação pode esperar a primeira conversa com a Head de RevOps.

## Fora do mínimo

Ficam de fora: e-mail e agenda integrados, cotação e proposta, metas por vendedor, previsão de receita, campos personalizados, permissões finas e login de verdade. Todos estão fora do dataset e do pedido da Head de RevOps.

## Decisões para o Leandro

1. Quais destas nove funções entram na primeira versão (proposta acima: 1 a 5).
2. Importação: só manager e admin (proposta) ou também o vendedor?
3. Importação: deal que já existe é ignorado (proposta) ou atualizado pela planilha?
