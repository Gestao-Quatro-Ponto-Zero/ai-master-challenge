# Contrato JSON do build

Gerado por `python build.py --hoje AAAA-MM-DD` em `app/data/`. O front só lê estes arquivos; nenhuma regra de negócio mora nele.

## scored.json

- `gerado_em`: quando o build rodou (excluído do hash)
- `hoje`: data de referência usada no recorte
- `semana_do_trimestre`: semana do trimestre de `hoje` (1 a 13)
- `config`: cópia de `config.json` usada no build
- `janela.ciclo_max`: maior ciclo entre os fechamentos conhecidos, em dias
- `janela.usa_prazo_trimestre`: se a regra do fim do trimestre seguinte está ativa
- `janela.n_fechamentos`: quantos fechamentos conhecidos sustentam a janela
- `janela.fechamentos_apos_prazo`: quantos fecharam depois do fim do trimestre seguinte
- `datas_analogas`: datas passadas (3, 6 e 9 meses antes de `hoje`) de onde a tabela de destino foi aprendida
- `tabela_destino[].faixa`: rótulo da faixa de idade, por exemplo `1-15` ou `76-138`
- `tabela_destino[].n`: deals abertos observados nessa faixa, somando as datas análogas
- `tabela_destino[].decidiram_28d`: quantos desses decidiram nos 28 dias seguintes
- `tabela_destino[].ganharam_28d`: quantos desses ganharam nos 28 dias seguintes
- `tabela_destino[].decidiram_trimestre`: quantos desses decidiram até o fim do trimestre
- `tabela_destino[].ganharam_trimestre`: quantos desses ganharam até o fim do trimestre
- `tabela_destino[].p_decide`: `decidiram_28d / n`, ou 0 quando `n` é 0
- `tabela_destino[].p_ganha_28d`: `ganharam_28d / n`, ou 0 quando `n` é 0
- `tabela_destino[].p_ganha_trimestre`: `ganharam_trimestre / n`, ou 0 quando `n` é 0
- `tabela_destino[].agrupada`: se a faixa foi juntada com a vizinha por ter `n` abaixo do mínimo
- `deals[].opportunity_id`: identificador do deal no CRM
- `deals[].vendedor`: nome do vendedor responsável
- `deals[].gerente`: gerente do vendedor, pelo cadastro
- `deals[].regiao`: região do vendedor, pelo cadastro
- `deals[].produto`: nome do produto no catálogo
- `deals[].produto_crm`: nome do produto como veio no CRM
- `deals[].conta`: conta do deal, ou nulo quando não há conta no CRM
- `deals[].setor`: setor da conta, ou nulo
- `deals[].stage`: estágio do deal no CRM
- `deals[].engage_date`: data de engajamento, ou nulo
- `deals[].idade`: dias desde o engajamento até `hoje`
- `deals[].faixa`: faixa de idade em que o deal cai, ou nulo quando não está vivo
- `deals[].prazo`: data limite pela janela, ou nulo quando não há data de engajamento
- `deals[].dias_restantes`: dias de `hoje` até o prazo, ou nulo
- `deals[].estado`: `vivo`, `vencido` ou `sem_data`
- `deals[].p_decide`: chance de decidir em 28 dias, da faixa do deal; nulo quando não está vivo
- `deals[].valor_tabela`: preço de tabela do produto
- `deals[].ve_28`: valor esperado de ganho em 28 dias, `valor_tabela × p_ganha_28d`
- `deals[].ve_trimestre`: valor esperado de ganho até o fim do trimestre, `valor_tabela × p_ganha_trimestre`
- `deals[].fila`: `fechar`, `preparar`, `iniciar` ou `encerrar`
- `deals[].fila_ordem`: ordem numérica da fila, de 0 (`fechar`) a 3 (`encerrar`)
- `deals[].chave`: valor usado para ordenar dentro da fila
- `deals[].posicao`: posição do deal dentro do vendedor e da fila, a partir de 1
- `deals[].em_foco`: se está entre os primeiros deals do vendedor que a tela mostra no dia
- `deals[].indice`: de 1 a 100 para os vivos, 0 para os vencidos, nulo para os sem data
- `deals[].verbo`: ação sugerida para a fila
- `deals[].cartoes.valor`: preço de tabela e posição do deal na fila do vendedor, em texto
- `deals[].cartoes.momento`: o que a história diz sobre quando deals dessa idade decidem, em texto
- `deals[].cartoes.prazo`: dias até o prazo e qual limite manda, em texto
- `deals[].nao_sabe`: lista de coisas que o score não sabe sobre o deal, em texto
- `vendedores[].vendedor`: nome do cadastro
- `vendedores[].gerente`: gerente do cadastro
- `vendedores[].regiao`: região do cadastro
- `vendedores[].tem_deal`: se o vendedor aparece em algum deal do export
- `vendedores[].vivos`: quantos deals vivos ele tem hoje
- `vendedores[].por_fila`: contagem de deals abertos por fila
- `vendedores[].valor_por_fila`: soma do preço de tabela por fila
- `vendedores[].carga_referencia`: mediana de deals abertos que depois fecharam, nas datas análogas
- `vendedores[].frase_vazio`: texto de estado vazio quando não há deal vivo, senão nulo
- `time.total_abertos`: número de deals abertos
- `time.valor_aberto`: soma do preço de tabela de todos os abertos
- `time.valor_vivo`: soma do preço de tabela dos vivos
- `time.valor_vencido`: soma do preço de tabela dos vencidos
- `time.pct_vencido`: `valor_vencido / valor_aberto`
- `time.ve_trimestre`: soma do valor esperado de ganho até o fim do trimestre
- `time.por_regiao`: por região, `abertos`, `valor_aberto`, `valor_vivo` e `valor_vencido`
- `time.por_gerente`: por gerente, com os mesmos quatro campos de `por_regiao`

## qualidade.json

- `apelidos_de_produto`: mapa de nome no CRM para nome no catálogo
- `produtos_sem_par`: produtos do CRM sem nenhuma entrada no catálogo
- `setores_corrigidos`: correções de setor aplicadas, de nome errado para o correto
- `paises_corrigidos`: correções de país aplicadas, de nome errado para o correto
- `total_linhas`: linhas do export
- `abertos_sem_conta`: abertos sem conta no CRM
- `prospecting_sem_data`: deals em Prospecting sem data de engajamento
- `maior_data`: maior data de fechamento do export
- `primeiro_fechamento`: menor data de fechamento do export
- `vendedores_cadastro`: vendedores no cadastro
- `vendedores_com_deal`: vendedores com algum deal no export
- `vendedores_com_deal_aberto`: vendedores com algum deal aberto
- `vendedores_sem_deal`: vendedores do cadastro sem nenhum deal no export

## hash.txt

- SHA-256 do `scored.json` sem `gerado_em`, serializado com `sort_keys` e `indent=1`. Duas execuções com os mesmos dados e a mesma data dão o mesmo hash.
