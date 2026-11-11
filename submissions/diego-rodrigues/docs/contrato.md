# Contrato JSON do build

Gerado por `python build.py --hoje AAAA-MM-DD` em `app/data/`. O front só lê estes arquivos; nenhuma regra de negócio mora nele.

## scored.json

- `gerado_em`: quando o build rodou (fora do hash)
- `hoje`: data de referência usada no recorte
- `semana_do_trimestre`: semana do trimestre de `hoje` (1 a 13)
- `config`: cópia de `config.json` usada no build
- `janela`: `ciclo_max`, `usa_prazo_trimestre`, `n_fechamentos`, `fechamentos_apos_prazo`
- `tabela_destino`: uma linha por faixa de idade (`faixa`), com `n`, contagens de decisão e ganho, `p_decide`, `p_ganha_28d`, `p_ganha_trimestre` e `agrupada`
- `deals`: uma entrada por deal aberto, com `opportunity_id`, `vendedor`, `gerente`, `regiao`, `produto`, `produto_crm`, `conta`, `setor`, `stage`, `engage_date`, `idade`, `faixa`, `prazo`, `dias_restantes`, `estado`, `p_decide`, `valor_tabela`, `ve_28`, `ve_trimestre`, `fila`, `fila_ordem`, `chave`, `posicao`, `em_foco`, `indice`, `verbo`, `cartoes` (`valor`, `momento`, `prazo`) e `nao_sabe`
- `vendedores`: todos os 35 do cadastro, com `tem_deal`, `vivos`, `por_fila` (contagens), `valor_por_fila`, `carga_referencia` e `frase_vazio`
- `time`: `total_abertos`, `valor_aberto`, `valor_vivo`, `valor_vencido`, `pct_vencido`, `ve_trimestre`, `por_regiao` e `por_gerente`

## qualidade.json

- Todos os campos de `Dados.qualidade` (apelidos, produtos sem par, correções de setor e país, contagens do export)
- `vendedores_sem_deal`: lista dos cadastrados sem nenhum deal no export

## hash.txt

SHA-256 do `scored.json` sem `gerado_em`, com `sort_keys` e `indent=1`. Duas execuções com os mesmos dados e a mesma data dão o mesmo hash.
