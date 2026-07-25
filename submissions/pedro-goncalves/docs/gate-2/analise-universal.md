# Análise universal de duas planilhas

## Objetivo

Transformar o protótipo do Challenge 002 em um processo reutilizável para outra operação de
suporte. O sistema recebe duas planilhas, apresenta sua estrutura para validação humana, organiza
os campos, executa somente análises compatíveis e entrega um painel gerencial.

Universal não significa automático para qualquer base. Significa que o **processo de
descoberta, validação e decisão** pode ser repetido sem assumir que colunas com nomes parecidos
possuem o mesmo significado.

## Fluxo

1. o humano envia duas planilhas em CSV ou XLSX;
2. o sistema lista todas as colunas, tipos, preenchimento e valores distintos;
3. a IA sugere um papel para cada coluna;
4. o humano decide quais colunas usar, corrige papéis e define a ordem;
5. o humano informa se cada base é gerencial, atendimento ao cliente ou suporte de TI;
6. uma relação entre as planilhas só é aceita quando uma chave comum é confirmada;
7. o sistema calcula qualidade estrutural e indicadores compatíveis;
8. texto só entra na etapa de IA quando uma coluna foi validada como `Texto`;
9. o painel mostra métricas, distribuições, alertas e próximos passos;
10. as fontes originais permanecem intactas.

## Papéis de coluna

| Papel | Uso |
|---|---|
| Identificador | Preservar unicidade e rastreabilidade |
| Texto | Analisar mensagem ou descrição |
| Data | Avaliar cobertura temporal e consistência |
| Categoria | Segmentar volume e comportamento |
| Métrica | Calcular medidas quantitativas |
| Contexto | Manter informação útil sem cálculo automático |

## Fronteira humano e IA

### IA sugere

- papel provável da coluna;
- alertas de preenchimento e duplicidade;
- distribuições e resumo estrutural;
- triagem em observação quando existe texto validado;
- indicadores que os campos realmente permitem.

### Humano decide

- quais colunas entram;
- ordem e papel de cada coluna;
- contexto operacional da base;
- chave de relação entre planilhas;
- quais métricas fazem sentido para o negócio;
- se uma recomendação pode virar mudança de processo.

## O que o painel pode mostrar

Com os campos adequados, o painel pode cobrir volume, assuntos, status, recorrência, satisfação,
capacidade e distribuição temporal. FRT, TTR, NPS, custo, produtividade ou ROI só aparecem como
indicadores observados quando a planilha contém campos válidos, definições e janelas compatíveis.

## O que o sistema não faz

- não apaga coluna da fonte;
- não elimina texto repetido como duplicata sem identidade comprovada;
- não junta planilhas apenas porque os nomes das colunas coincidem;
- não inventa significado de campo;
- não aplica o modelo de TI em dados de clientes;
- não transforma qualidade estrutural em qualidade do negócio;
- não calcula ROI sem custo, esforço e adoção medidos.

## Aplicação em outra empresa

Em uma operação como a Cheers, o fluxo poderia receber uma planilha de atendimentos e outra de
capacidade, satisfação ou cadastro operacional. O líder validaria campos e relações antes da
análise. O painel então responderia o que os dados suportam: demanda por tipo, reincidência,
status, satisfação, carga do time e pontos que precisam de nova instrumentação.

O valor não está em aceitar qualquer arquivo. Está em impedir que a IA esconda uma decisão de
negócio dentro de uma inferência técnica.
