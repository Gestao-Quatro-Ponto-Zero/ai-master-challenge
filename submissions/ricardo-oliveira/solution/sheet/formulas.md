# Fórmulas da planilha `sales_pipeline`, aba por aba
Exportado da planilha em 23/10/2026 pela API do Google Sheets (userEnteredValue). Cada aba lista as células com fórmula. Fórmulas iguais preenchidas pra baixo aparecem uma vez, com `{r}` no lugar do número da própria linha e o intervalo de linhas em que valem. Textos de cabeçalho e notas estão em `config.md` quando são configuração; aqui ficam só fórmulas e os rótulos que ajudam a ler. Separador de argumentos `;` e de colunas `\` (planilha em pt-BR).
Reconstrução: crie uma planilha em pt-BR com as abas na ordem abaixo, cole os quatro CSVs nas abas `sales_pipeline`, `accounts`, `sales_teams` e `Products` (com o nome do pipeline na coluna A de Products), cole as fórmulas nas células indicadas e preencha as entradas de `config.md` na aba `Hoje`.

## Hoje
| Célula | Fórmula |
|---|---|
| `B2` | `=MAX(Won!G2:G)` |
| `B4` | `=B2+B3` |
| `B5` | `=MEDIAN(Won!I2:I)` |
| `B6` | `=MAX(Won!I2:I)` |
| `B16` | `=COUNTA('Lista do Dia'!A8:A)` |
| `B17` | `=COUNTIF('Lista do Dia'!S8:S;1)` |
| `B18` | `=COUNTIF('Lista do Dia'!S8:S;2)` |
| `B19` | `=COUNTIF('Lista do Dia'!S8:S;3)` |
| `B20` | `=COUNTIF('Lista do Dia'!S8:S;4)` |
| `B21` | `=COUNTIFS('Fila Sem Conta'!A8:A;"<>";'Fila Sem Conta'!K8:K;"<>Identificada")` |
| `B22` | `=COUNTIF('Fila Sem Conta'!N8:N;"Escalar pro manager")` |
| `B23` | `=COUNTIF('Lista do Dia'!S8:S;5)` |

## sales_pipeline
Dados brutos (sales_pipeline.csv do Kaggle, colado). Só a coluna J é fórmula: a conta identificada no app, lida da Fila Sem Conta.
| Célula | Fórmula |
|---|---|
| `I2` | `=IF(G2="";"";G2-F2)` |
| `J2` | `=ARRAYFORMULA(IF(A2:A="";"";IF(D2:D<>"";D2:D;IFERROR(VLOOKUP(VLOOKUP(A2:A;'Fila Sem Conta'!$A$8:$L$1500;12;FALSE);accounts!$A$2:$A$86;1;FALSE);""))))` |

## accounts
accounts.csv colado (A:G), com 'technolgy' e 'Philipines' corrigidos. H:R são fórmulas por linha, iguais da linha 2 à 86.
| Célula | Fórmula |
|---|---|
| `H2:H86` | `=IF(D{r}<ICP!$B$3;"1. under "&ICP!$B$3;IF(D{r}<ICP!$C$3;"2. "&ICP!$B$3&" to "&ICP!$C$3;IF(D{r}<ICP!$D$3;"3. "&ICP!$C$3&" to "&ICP!$D$3;"4. "&ICP!$D$3&" and up")))` |
| `I2:I86` | `=IF(E{r}<ICP!$B$4;"1. under "&ICP!$B$4;IF(E{r}<ICP!$C$4;"2. "&ICP!$B$4&" to "&ICP!$C$4;IF(E{r}<ICP!$D$4;"3. "&ICP!$C$4&" to "&ICP!$D$4;"4. "&ICP!$D$4&" and up")))` |
| `J2:J86` | `=IF(C{r}<ICP!$B$5;"1. before "&ICP!$B$5;IF(C{r}<ICP!$C$5;"2. "&ICP!$B$5&" to "&(ICP!$C$5-1);IF(C{r}<ICP!$D$5;"3. "&ICP!$C$5&" to "&(ICP!$D$5-1);"4. "&ICP!$D$5&" and later")))` |
| `K2:K86` | `=IF(G{r}="";"Independent";"Subsidiary")` |
| `L2:L86` | `=IF(F{r}="United States";"US";"Outside US")` |
| `M2:M86` | `=COUNTIF(Won!D$2:D;A{r})` |
| `N2:N86` | `=COUNTIF(Lost!D$2:D;A{r})` |
| `O2:O86` | `=SUMIF(Won!D$2:D;A{r};Won!H$2:H)` |
| `P2:P86` | `=IF(M{r}+N{r}=0;0;M{r}/(M{r}+N{r}))` |
| `Q2:Q86` | `=IFERROR(VLOOKUP(A{r};'Accounts (Won)'!A$7:E$91;5;FALSE);"")` |
| `R2:R86` | `=IF(OR(D{r}>=ICP!$G$3;B{r}=ICP!$G$5);"ICP 1";IF(D{r}>=ICP!$G$4;"ICP 2";"ICP 3"))` |

## sales_teams
sales_teams.csv colado. Sem fórmula.
Sem fórmulas.

## Products
Catálogo com o nome do pipeline (GTXPro) ao lado do nome do catálogo (GTX Pro). Sem fórmula.
Sem fórmulas.

## Won
FILTER do pipeline por estágio, mais região, faixa de receita, setor e ICP da conta por fórmula.
| Célula | Fórmula |
|---|---|
| `A1` | `=FILTER(sales_pipeline!A1:I; (ROW(sales_pipeline!A1:A)=1)+(sales_pipeline!E1:E="Won"))` |
| `J2` | `=ARRAYFORMULA(IF(B2:B="";"";VLOOKUP(B2:B;sales_teams!A$2:C$36;3;FALSE)))` |
| `K2` | `=ARRAYFORMULA(IF(D2:D="";"";VLOOKUP(D2:D;accounts!A$2:H$86;8;FALSE)))` |
| `L2` | `=ARRAYFORMULA(IF(D2:D="";"";VLOOKUP(D2:D;accounts!A$2:B$86;2;FALSE)))` |
| `M2` | `=ARRAYFORMULA(IF(D2:D="";"";VLOOKUP(D2:D;accounts!A$2:R$86;18;FALSE)))` |

## Lost
Idem Won, mais o preço de tabela (list_value) do produto perdido.
| Célula | Fórmula |
|---|---|
| `A1` | `=FILTER(sales_pipeline!A1:I; (ROW(sales_pipeline!A1:A)=1)+(sales_pipeline!E1:E="Lost"))` |
| `J2` | `=ARRAYFORMULA(IF(C2:C="";"";VLOOKUP(C2:C;Products!A$2:D$8;4;FALSE)))` |
| `K2` | `=ARRAYFORMULA(IF(B2:B="";"";VLOOKUP(B2:B;sales_teams!A$2:C$36;3;FALSE)))` |
| `L2` | `=ARRAYFORMULA(IF(D2:D="";"";VLOOKUP(D2:D;accounts!A$2:H$86;8;FALSE)))` |
| `M2` | `=ARRAYFORMULA(IF(D2:D="";"";VLOOKUP(D2:D;accounts!A$2:B$86;2;FALSE)))` |
| `N2` | `=ARRAYFORMULA(IF(D2:D="";"";VLOOKUP(D2:D;accounts!A$2:R$86;18;FALSE)))` |

## Engaging
| Célula | Fórmula |
|---|---|
| `A1` | `=FILTER(sales_pipeline!A1:I; (ROW(sales_pipeline!A1:A)=1)+(sales_pipeline!E1:E="Engaging"))` |

## Prospecting
| Célula | Fórmula |
|---|---|
| `A1` | `=FILTER(sales_pipeline!A1:I; (ROW(sales_pipeline!A1:A)=1)+(sales_pipeline!E1:E="Prospecting"))` |

## Accounts (Won)
| Célula | Fórmula |
|---|---|
| `B2` | `=PERCENTILE(B7:B91;0,75)` |
| `B3` | `=MEDIAN(B7:B91)` |
| `B4` | `=PERCENTILE(B7:B91;0,25)` |
| `A7` | `=QUERY(Won!A2:I;"select D, sum(H) where D <> '' group by D order by sum(H) desc label sum(H) ''";0)` |
| `C7:C91` | `=COUNTIF(Won!D$2:D;A{r})` |
| `D7:D91` | `=IF(C{r}=0;0;B{r}/C{r})` |
| `E7:E91` | `=IF(B{r}>=$B$2;"A";IF(B{r}>=$B$3;"B";IF(B{r}>=$B$4;"C";"D")))` |
| `F7:F91` | `=COUNTUNIQUEIFS(Won!B$2:B;Won!D$2:D;A{r})` |
| `G7:G91` | `=COUNTUNIQUEIFS(Won!C$2:C;Won!D$2:D;A{r})` |
| `H7:H91` | `=IF(G{r}=0;0;COUNTUNIQUE(FILTER(Won!B$2:B&"\|"&Won!C$2:C;Won!D$2:D=A{r}))/G{r})` |
| `I7:I91` | `=QUERY(Won!A$2:I;"select B, count(A) where D = '"&A{r}&"' group by B order by count(A) desc limit 1 label count(A) ''";0)` |
| `K7:K91` | `=QUERY(Won!A$2:I;"select B, sum(H) where D = '"&A{r}&"' group by B order by sum(H) desc limit 1 label sum(H) ''";0)` |
| `M7:M91` | `=IF(I{r}=K{r};"Yes";"No")` |
| `N7:N91` | `=TRANSPOSE(INDEX(QUERY(Won!A$2:I;"select C, count(A) where D = '"&A{r}&"' group by C order by count(A) desc limit 3 label count(A) ''";0);0;1))` |

## Accounts (Lost)
| Célula | Fórmula |
|---|---|
| `A2` | `=QUERY(Lost!A2:J;"select D, count(A) where D <> '' group by D order by count(A) desc label count(A) ''";0)` |
| `C2:C86` | `=SUMIF(Lost!D$2:D;A{r};Lost!J$2:J)` |
| `D2:D86` | `=IF(COUNTIF(Won!D$2:D;A{r})+B{r}=0;0;COUNTIF(Won!D$2:D;A{r})/(COUNTIF(Won!D$2:D;A{r})+B{r}))` |
| `E2:E86` | `=IFERROR(VLOOKUP(A{r};'Accounts (Won)'!A$7:E$91;5;FALSE);"")` |
| `F2:F86` | `=COUNTUNIQUEIFS(Lost!B$2:B;Lost!D$2:D;A{r})` |
| `G2:G86` | `=AVERAGEIF(Lost!D$2:D;A{r};Lost!I$2:I)` |
| `H2:H86` | `=QUERY(Lost!A$2:J;"select B, count(A) where D = '"&A{r}&"' group by B order by count(A) desc limit 1 label count(A) ''";0)` |
| `J2:J86` | `=QUERY(Lost!A$2:J;"select B, sum(J) where D = '"&A{r}&"' group by B order by sum(J) desc limit 1 label sum(J) ''";0)` |
| `L2:L86` | `=IF(H{r}=J{r};"Yes";"No")` |
| `M2:M86` | `=TRANSPOSE(INDEX(QUERY(Lost!A$2:J;"select C, count(A) where D = '"&A{r}&"' group by C order by count(A) desc limit 3 label count(A) ''";0);0;1))` |

## Reps (Won)
| Célula | Fórmula |
|---|---|
| `B3` | `=SUM(B4:B33)` |
| `C3` | `=SUM(C4:C33)` |
| `F3:F33` | `=IF(B{r}=0;0;C{r}/B{r})` |
| `G3` | `=COUNTUNIQUE(Won!D2:D)` |
| `H3` | `=COUNTUNIQUE(Won!C2:C)` |
| `I3` | `=AVERAGE(Won!I2:I)` |
| `J3` | `=AVERAGEIF(Won!$C$2:$C;J$2;Won!$I$2:$I)` |
| `K3` | `=AVERAGEIF(Won!$C$2:$C;K$2;Won!$I$2:$I)` |
| `L3` | `=AVERAGEIF(Won!$C$2:$C;L$2;Won!$I$2:$I)` |
| `M3` | `=AVERAGEIF(Won!$C$2:$C;M$2;Won!$I$2:$I)` |
| `N3` | `=AVERAGEIF(Won!$C$2:$C;N$2;Won!$I$2:$I)` |
| `O3` | `=AVERAGEIF(Won!$C$2:$C;O$2;Won!$I$2:$I)` |
| `P3` | `=AVERAGEIF(Won!$C$2:$C;P$2;Won!$I$2:$I)` |
| `Q3` | `=COUNTIF(Won!$C$2:$C;Q$2)` |
| `R3` | `=COUNTIF(Won!$C$2:$C;R$2)` |
| `S3` | `=COUNTIF(Won!$C$2:$C;S$2)` |
| `T3` | `=COUNTIF(Won!$C$2:$C;T$2)` |
| `U3` | `=COUNTIF(Won!$C$2:$C;U$2)` |
| `V3` | `=COUNTIF(Won!$C$2:$C;V$2)` |
| `W3` | `=COUNTIF(Won!$C$2:$C;W$2)` |
| `A4` | `=QUERY(Won!A2:I;"select B, count(A), sum(H) where B <> '' group by B order by sum(H) desc label count(A) '', sum(H) ''";0)` |
| `D4` | `=RANK(B4;B4:B$33)` |
| `E4` | `=RANK(C4;C4:C$33)` |
| `G4:G33` | `=COUNTUNIQUEIFS(Won!D$2:D;Won!B$2:B;$A{r})` |
| `H4:H33` | `=COUNTUNIQUEIFS(Won!C$2:C;Won!B$2:B;$A{r})` |
| `I4:I33` | `=AVERAGEIF(Won!B$2:B;$A{r};Won!I$2:I)` |
| `J4:J33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;J$2)=0;"";AVERAGEIFS(Won!$I$2:$I;Won!$B$2:$B;$A{r};Won!$C$2:$C;J$2))` |
| `K4:K33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;K$2)=0;"";AVERAGEIFS(Won!$I$2:$I;Won!$B$2:$B;$A{r};Won!$C$2:$C;K$2))` |
| `L4:L33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;L$2)=0;"";AVERAGEIFS(Won!$I$2:$I;Won!$B$2:$B;$A{r};Won!$C$2:$C;L$2))` |
| `M4:M33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;M$2)=0;"";AVERAGEIFS(Won!$I$2:$I;Won!$B$2:$B;$A{r};Won!$C$2:$C;M$2))` |
| `N4:N33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;N$2)=0;"";AVERAGEIFS(Won!$I$2:$I;Won!$B$2:$B;$A{r};Won!$C$2:$C;N$2))` |
| `O4:O33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;O$2)=0;"";AVERAGEIFS(Won!$I$2:$I;Won!$B$2:$B;$A{r};Won!$C$2:$C;O$2))` |
| `P4:P33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;P$2)=0;"";AVERAGEIFS(Won!$I$2:$I;Won!$B$2:$B;$A{r};Won!$C$2:$C;P$2))` |
| `Q4:Q33` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;Q$2)` |
| `R4:R33` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;R$2)` |
| `S4:S33` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;S$2)` |
| `T4:T33` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;T$2)` |
| `U4:U33` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;U$2)` |
| `V4:V33` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;V$2)` |
| `W4:W33` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;W$2)` |
| `D5:D32` | `=RANK(B{r};B$4:B$33)` |
| `E5:E32` | `=RANK(C{r};C$4:C$33)` |
| `D33` | `=RANK(B33;B$4:B33)` |
| `E33` | `=RANK(C33;C$4:C33)` |

## Reps (Lost)
| Célula | Fórmula |
|---|---|
| `B3` | `=SUM(B4:B33)` |
| `C3` | `=SUM(C4:C33)` |
| `F3` | `=COUNTA(Won!A2:A)/(COUNTA(Won!A2:A)+B3)` |
| `H3` | `=COUNTUNIQUE(Lost!D2:D)` |
| `I3` | `=AVERAGE(Lost!I2:I)` |
| `J3` | `=COUNTIF(Won!$C$2:$C;J$2)/(COUNTIF(Won!$C$2:$C;J$2)+COUNTIF(Lost!$C$2:$C;J$2))` |
| `K3` | `=COUNTIF(Won!$C$2:$C;K$2)/(COUNTIF(Won!$C$2:$C;K$2)+COUNTIF(Lost!$C$2:$C;K$2))` |
| `L3` | `=COUNTIF(Won!$C$2:$C;L$2)/(COUNTIF(Won!$C$2:$C;L$2)+COUNTIF(Lost!$C$2:$C;L$2))` |
| `M3` | `=COUNTIF(Won!$C$2:$C;M$2)/(COUNTIF(Won!$C$2:$C;M$2)+COUNTIF(Lost!$C$2:$C;M$2))` |
| `N3` | `=COUNTIF(Won!$C$2:$C;N$2)/(COUNTIF(Won!$C$2:$C;N$2)+COUNTIF(Lost!$C$2:$C;N$2))` |
| `O3` | `=COUNTIF(Won!$C$2:$C;O$2)/(COUNTIF(Won!$C$2:$C;O$2)+COUNTIF(Lost!$C$2:$C;O$2))` |
| `P3` | `=COUNTIF(Won!$C$2:$C;P$2)/(COUNTIF(Won!$C$2:$C;P$2)+COUNTIF(Lost!$C$2:$C;P$2))` |
| `Q3` | `=COUNTIF(Lost!$C$2:$C;Q$2)` |
| `R3` | `=COUNTIF(Lost!$C$2:$C;R$2)` |
| `S3` | `=COUNTIF(Lost!$C$2:$C;S$2)` |
| `T3` | `=COUNTIF(Lost!$C$2:$C;T$2)` |
| `U3` | `=COUNTIF(Lost!$C$2:$C;U$2)` |
| `V3` | `=COUNTIF(Lost!$C$2:$C;V$2)` |
| `W3` | `=COUNTIF(Lost!$C$2:$C;W$2)` |
| `A4` | `=QUERY(Lost!A2:J;"select B, count(A), sum(J) where B <> '' group by B order by count(A) desc label count(A) '', sum(J) ''";0)` |
| `D4` | `=RANK(B4;B4:B$33)` |
| `E4` | `=RANK(C4;C4:C$33)` |
| `F4:F33` | `=COUNTIF(Won!B$2:B;$A{r})/(COUNTIF(Won!B$2:B;$A{r})+B{r})` |
| `G4` | `=RANK(F4;F4:F$33)` |
| `H4:H33` | `=COUNTUNIQUEIFS(Lost!D$2:D;Lost!B$2:B;$A{r})` |
| `I4:I33` | `=AVERAGEIF(Lost!B$2:B;$A{r};Lost!I$2:I)` |
| `J4:J33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;J$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;J$2)=0;"";COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;J$2)/(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;J$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;J$2)))` |
| `K4:K33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;K$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;K$2)=0;"";COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;K$2)/(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;K$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;K$2)))` |
| `L4:L33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;L$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;L$2)=0;"";COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;L$2)/(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;L$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;L$2)))` |
| `M4:M33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;M$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;M$2)=0;"";COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;M$2)/(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;M$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;M$2)))` |
| `N4:N33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;N$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;N$2)=0;"";COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;N$2)/(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;N$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;N$2)))` |
| `O4:O33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;O$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;O$2)=0;"";COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;O$2)/(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;O$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;O$2)))` |
| `P4:P33` | `=IF(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;P$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;P$2)=0;"";COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;P$2)/(COUNTIFS(Won!$B$2:$B;$A{r};Won!$C$2:$C;P$2)+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;P$2)))` |
| `Q4:Q33` | `=COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;Q$2)` |
| `R4:R33` | `=COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;R$2)` |
| `S4:S33` | `=COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;S$2)` |
| `T4:T33` | `=COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;T$2)` |
| `U4:U33` | `=COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;U$2)` |
| `V4:V33` | `=COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;V$2)` |
| `W4:W33` | `=COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$C$2:$C;W$2)` |
| `D5:D32` | `=RANK(B{r};B$4:B$33)` |
| `E5:E32` | `=RANK(C{r};C$4:C$33)` |
| `G5:G32` | `=RANK(F{r};F$4:F$33)` |
| `D33` | `=RANK(B33;B$4:B33)` |
| `E33` | `=RANK(C33;C$4:C33)` |
| `G33` | `=RANK(F33;F$4:F33)` |

## Account x Product
Uma linha por par conta e produto com ganhos: compras, ciclo, primeira e última compra, intervalo médio, próxima compra estimada, flag de recompra. A base do 'relógio da conta'.
| Célula | Fórmula |
|---|---|
| `B1` | `=Hoje!B4` |
| `K1:K4` | `=COUNTIF(K$6:K;J{r})` |
| `M1` | `=COUNTIF(N$6:N;L1)` |
| `B2` | `=Hoje!B7` |
| `A6` | `=QUERY(Won!A2:I;"select D, C, count(A), avg(I), min(G), max(G) where D <> '' group by D, C order by D, C label count(A) '', avg(I) '', min(G) '', max(G) ''";0)` |
| `G6:G527` | `=IFERROR(VLOOKUP(A{r};'Accounts (Won)'!A$7:E$91;5;FALSE);"")` |
| `H6:H527` | `=IF(C{r}<2;"";(F{r}-E{r})/(C{r}-1))` |
| `I6:I527` | `=IF(H{r}="";"";F{r}+H{r})` |
| `J6:J527` | `=IF(I{r}="";"";I{r}-$B$1)` |
| `K6:K527` | `=IF(J{r}="";"Only 1 purchase";IF(J{r}<0;"Overdue";IF(J{r}<=$B$2;"Due soon";"Not due")))` |
| `L6:L527` | `=COUNTIFS(sales_pipeline!D$2:D;A{r};sales_pipeline!C$2:C;B{r};sales_pipeline!E$2:E;"Engaging")+COUNTIFS(sales_pipeline!D$2:D;A{r};sales_pipeline!C$2:C;B{r};sales_pipeline!E$2:E;"Prospecting")` |
| `M6:M527` | `=SUMIFS(Won!H$2:H;Won!D$2:D;A{r};Won!C$2:C;B{r})` |
| `N6:N527` | `=IF(AND(OR(K{r}="Overdue";K{r}="Due soon");L{r}>0);"Focus now";"")` |
| `G91` | `=IFERROR(VLOOKUP(A91;'Accounts (Won)'!A$7:E91;5;FALSE);"")` |

## Tier x Product
| Célula | Fórmula |
|---|---|
| `B3:B6` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;B$2)/$I{r})` |
| `C3:C6` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;C$2)/$I{r})` |
| `D3:D6` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;D$2)/$I{r})` |
| `E3:E6` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;E$2)/$I{r})` |
| `F3:F6` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;F$2)/$I{r})` |
| `G3:G6` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;G$2)/$I{r})` |
| `H3:H6` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;H$2)/$I{r})` |
| `I3:I6` | `=SUMIFS('Account x Product'!$C$6:$C;'Account x Product'!$G$6:$G;$A{r})` |
| `B10:B13` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;B$9)/$I{r})` |
| `C10:C13` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;C$9)/$I{r})` |
| `D10:D13` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;D$9)/$I{r})` |
| `E10:E13` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;E$9)/$I{r})` |
| `F10:F13` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;F$9)/$I{r})` |
| `G10:G13` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;G$9)/$I{r})` |
| `H10:H13` | `=IF($I{r}=0;0;SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r};'Account x Product'!$B$6:$B;H$9)/$I{r})` |
| `I10:I13` | `=SUMIFS('Account x Product'!$M$6:$M;'Account x Product'!$G$6:$G;$A{r})` |

## ICP
| Célula | Fórmula |
|---|---|
| `A10` | `="1. under "&$B$3` |
| `B10:B13` | `=COUNTIF(accounts!$H$2:$H$86;$A{r})` |
| `C10:C13` | `=SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$M$2:$M$86)+SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$N$2:$N$86)` |
| `D10:D13` | `=IF(C{r}=0;0;SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$M$2:$M$86)/C{r})` |
| `E10:E13` | `=IF(B{r}=0;0;SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$M$2:$M$86)/B{r})` |
| `F10:F13` | `=IF(B{r}=0;0;SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$O$2:$O$86)/B{r})` |
| `G10:G13` | `=IF(SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$M$2:$M$86)=0;0;SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$O$2:$O$86)/SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$M$2:$M$86))` |
| `H10:H13` | `=SUMIF(accounts!$H$2:$H$86;$A{r};accounts!$O$2:$O$86)/SUM(accounts!$O$2:$O$86)` |
| `A11` | `="2. "&$B$3&" to "&$C$3` |
| `A12` | `="3. "&$C$3&" to "&$D$3` |
| `A13` | `="4. "&$D$3&" and up"` |
| `A17` | `="1. under "&$B$4` |
| `B17:B20` | `=COUNTIF(accounts!$I$2:$I$86;$A{r})` |
| `C17:C20` | `=SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$M$2:$M$86)+SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$N$2:$N$86)` |
| `D17:D20` | `=IF(C{r}=0;0;SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$M$2:$M$86)/C{r})` |
| `E17:E20` | `=IF(B{r}=0;0;SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$M$2:$M$86)/B{r})` |
| `F17:F20` | `=IF(B{r}=0;0;SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$O$2:$O$86)/B{r})` |
| `G17:G20` | `=IF(SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$M$2:$M$86)=0;0;SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$O$2:$O$86)/SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$M$2:$M$86))` |
| `H17:H20` | `=SUMIF(accounts!$I$2:$I$86;$A{r};accounts!$O$2:$O$86)/SUM(accounts!$O$2:$O$86)` |
| `A18` | `="2. "&$B$4&" to "&$C$4` |
| `A19` | `="3. "&$C$4&" to "&$D$4` |
| `A20` | `="4. "&$D$4&" and up"` |
| `A24:A62` | `=SORT(UNIQUE(accounts!B2:B86))` |
| `B24:B33` | `=COUNTIF(accounts!$B$2:$B$86;$A{r})` |
| `C24:C33` | `=SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$M$2:$M$86)+SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$N$2:$N$86)` |
| `D24:D33` | `=IF(C{r}=0;0;SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$M$2:$M$86)/C{r})` |
| `E24:E33` | `=IF(B{r}=0;0;SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$M$2:$M$86)/B{r})` |
| `F24:F33` | `=IF(B{r}=0;0;SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$O$2:$O$86)/B{r})` |
| `G24:G33` | `=IF(SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$M$2:$M$86)=0;0;SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$O$2:$O$86)/SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$M$2:$M$86))` |
| `H24:H33` | `=SUMIF(accounts!$B$2:$B$86;$A{r};accounts!$O$2:$O$86)/SUM(accounts!$O$2:$O$86)` |
| `A37` | `="1. before "&$B$5` |
| `B37:B40` | `=COUNTIF(accounts!$J$2:$J$86;$A{r})` |
| `C37:C40` | `=SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$M$2:$M$86)+SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$N$2:$N$86)` |
| `D37:D40` | `=IF(C{r}=0;0;SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$M$2:$M$86)/C{r})` |
| `E37:E40` | `=IF(B{r}=0;0;SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$M$2:$M$86)/B{r})` |
| `F37:F40` | `=IF(B{r}=0;0;SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$O$2:$O$86)/B{r})` |
| `G37:G40` | `=IF(SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$M$2:$M$86)=0;0;SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$O$2:$O$86)/SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$M$2:$M$86))` |
| `H37:H40` | `=SUMIF(accounts!$J$2:$J$86;$A{r};accounts!$O$2:$O$86)/SUM(accounts!$O$2:$O$86)` |
| `A38` | `="2. "&$B$5&" to "&($C$5-1)` |
| `A39` | `="3. "&$C$5&" to "&($D$5-1)` |
| `A40` | `="4. "&$D$5&" and later"` |
| `B44:B45` | `=COUNTIF(accounts!$K$2:$K$86;$A{r})` |
| `C44:C45` | `=SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$M$2:$M$86)+SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$N$2:$N$86)` |
| `D44:D45` | `=IF(C{r}=0;0;SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$M$2:$M$86)/C{r})` |
| `E44:E45` | `=IF(B{r}=0;0;SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$M$2:$M$86)/B{r})` |
| `F44:F45` | `=IF(B{r}=0;0;SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$O$2:$O$86)/B{r})` |
| `G44:G45` | `=IF(SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$M$2:$M$86)=0;0;SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$O$2:$O$86)/SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$M$2:$M$86))` |
| `H44:H45` | `=SUMIF(accounts!$K$2:$K$86;$A{r};accounts!$O$2:$O$86)/SUM(accounts!$O$2:$O$86)` |
| `B49:B50` | `=COUNTIF(accounts!$L$2:$L$86;$A{r})` |
| `C49:C50` | `=SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$M$2:$M$86)+SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$N$2:$N$86)` |
| `D49:D50` | `=IF(C{r}=0;0;SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$M$2:$M$86)/C{r})` |
| `E49:E50` | `=IF(B{r}=0;0;SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$M$2:$M$86)/B{r})` |
| `F49:F50` | `=IF(B{r}=0;0;SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$O$2:$O$86)/B{r})` |
| `G49:G50` | `=IF(SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$M$2:$M$86)=0;0;SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$O$2:$O$86)/SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$M$2:$M$86))` |
| `H49:H50` | `=SUMIF(accounts!$L$2:$L$86;$A{r};accounts!$O$2:$O$86)/SUM(accounts!$O$2:$O$86)` |
| `A54` | `=A10` |
| `B54:B57` | `=IF(E{r}=0;"";COUNTIFS(Won!$K$2:$K;$A{r};Won!$J$2:$J;B$53)/E{r})` |
| `C54:C57` | `=IF(F{r}=0;"";COUNTIFS(Won!$K$2:$K;$A{r};Won!$J$2:$J;C$53)/F{r})` |
| `D54:D57` | `=IF(G{r}=0;"";COUNTIFS(Won!$K$2:$K;$A{r};Won!$J$2:$J;D$53)/G{r})` |
| `E54:E57` | `=COUNTIFS(Won!$K$2:$K;$A{r};Won!$J$2:$J;B$53)+COUNTIFS(Lost!$L$2:$L;$A{r};Lost!$K$2:$K;B$53)` |
| `F54:F57` | `=COUNTIFS(Won!$K$2:$K;$A{r};Won!$J$2:$J;C$53)+COUNTIFS(Lost!$L$2:$L;$A{r};Lost!$K$2:$K;C$53)` |
| `G54:G57` | `=COUNTIFS(Won!$K$2:$K;$A{r};Won!$J$2:$J;D$53)+COUNTIFS(Lost!$L$2:$L;$A{r};Lost!$K$2:$K;D$53)` |
| `A55` | `=A11` |
| `A56` | `=A12` |
| `A57` | `=A13` |
| `B58` | `=COUNTIF(Won!$J$2:$J;B$53)/E58` |
| `C58` | `=COUNTIF(Won!$J$2:$J;C$53)/F58` |
| `D58` | `=COUNTIF(Won!$J$2:$J;D$53)/G58` |
| `E58` | `=COUNTIF(Won!$J$2:$J;B$53)+COUNTIF(Lost!$K$2:$K;B$53)` |
| `F58` | `=COUNTIF(Won!$J$2:$J;C$53)+COUNTIF(Lost!$K$2:$K;C$53)` |
| `G58` | `=COUNTIF(Won!$J$2:$J;D$53)+COUNTIF(Lost!$K$2:$K;D$53)` |
| `B62:B71` | `=IF(E{r}=0;"";COUNTIFS(Won!$L$2:$L;$A{r};Won!$J$2:$J;B$61)/E{r})` |
| `C62:C71` | `=IF(F{r}=0;"";COUNTIFS(Won!$L$2:$L;$A{r};Won!$J$2:$J;C$61)/F{r})` |
| `D62:D71` | `=IF(G{r}=0;"";COUNTIFS(Won!$L$2:$L;$A{r};Won!$J$2:$J;D$61)/G{r})` |
| `E62:E71` | `=COUNTIFS(Won!$L$2:$L;$A{r};Won!$J$2:$J;B$61)+COUNTIFS(Lost!$M$2:$M;$A{r};Lost!$K$2:$K;B$61)` |
| `F62:F71` | `=COUNTIFS(Won!$L$2:$L;$A{r};Won!$J$2:$J;C$61)+COUNTIFS(Lost!$M$2:$M;$A{r};Lost!$K$2:$K;C$61)` |
| `G62:G71` | `=COUNTIFS(Won!$L$2:$L;$A{r};Won!$J$2:$J;D$61)+COUNTIFS(Lost!$M$2:$M;$A{r};Lost!$K$2:$K;D$61)` |

## ICP x Team
| Célula | Fórmula |
|---|---|
| `A5` | `=UNIQUE(sales_teams!B2:B36)` |
| `B5:B10` | `=INDEX(sales_teams!$C$2:$C$36;MATCH($A{r};sales_teams!$B$2:$B$36;0))` |
| `C5:C10` | `=IF(F{r}=0;"";SUMIF($B$15:$B$44;$A{r};J$15:J$44)/F{r})` |
| `D5:D10` | `=IF(G{r}=0;"";SUMIF($B$15:$B$44;$A{r};K$15:K$44)/G{r})` |
| `E5:E10` | `=IF(H{r}=0;"";SUMIF($B$15:$B$44;$A{r};L$15:L$44)/H{r})` |
| `F5:F10` | `=SUMIF($B$15:$B$44;$A{r};G$15:G$44)` |
| `G5:G10` | `=SUMIF($B$15:$B$44;$A{r};H$15:H$44)` |
| `H5:H10` | `=SUMIF($B$15:$B$44;$A{r};I$15:I$44)` |
| `I5:I10` | `=IF(F{r}=0;"";SUMIF($B$15:$B$44;$A{r};M$15:M$44)/F{r})` |
| `J5:J10` | `=IF(G{r}=0;"";SUMIF($B$15:$B$44;$A{r};N$15:N$44)/G{r})` |
| `K5:K10` | `=IF(H{r}=0;"";SUMIF($B$15:$B$44;$A{r};O$15:O$44)/H{r})` |
| `C11` | `=SUM(J15:J44)/SUM(G15:G44)` |
| `D11` | `=SUM(K15:K44)/SUM(H15:H44)` |
| `E11` | `=SUM(L15:L44)/SUM(I15:I44)` |
| `F11` | `=SUM(G15:G44)` |
| `G11` | `=SUM(H15:H44)` |
| `H11` | `=SUM(I15:I44)` |
| `I11` | `=SUM(M15:M44)/SUM(G15:G44)` |
| `J11` | `=SUM(N15:N44)/SUM(H15:H44)` |
| `K11` | `=SUM(O15:O44)/SUM(I15:I44)` |
| `A15` | `=INDEX(QUERY(Won!A2:B;"select B, count(A) where B <> '' group by B order by B label count(A) ''";0);0;1)` |
| `B15:B44` | `=INDEX(sales_teams!$B$2:$B$36;MATCH($A{r};sales_teams!$A$2:$A$36;0))` |
| `C15:C44` | `=INDEX(sales_teams!$C$2:$C$36;MATCH($A{r};sales_teams!$A$2:$A$36;0))` |
| `D15:D44` | `=IF(G{r}=0;"";J{r}/G{r})` |
| `E15:E44` | `=IF(H{r}=0;"";K{r}/H{r})` |
| `F15:F44` | `=IF(I{r}=0;"";L{r}/I{r})` |
| `G15:G44` | `=J{r}+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$N$2:$N;"ICP 1")` |
| `H15:H44` | `=K{r}+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$N$2:$N;"ICP 2")` |
| `I15:I44` | `=L{r}+COUNTIFS(Lost!$B$2:$B;$A{r};Lost!$N$2:$N;"ICP 3")` |
| `J15:J44` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$M$2:$M;"ICP 1")` |
| `K15:K44` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$M$2:$M;"ICP 2")` |
| `L15:L44` | `=COUNTIFS(Won!$B$2:$B;$A{r};Won!$M$2:$M;"ICP 3")` |
| `M15:M44` | `=SUMIFS(Won!$H$2:$H;Won!$B$2:$B;$A{r};Won!$M$2:$M;"ICP 1")` |
| `N15:N44` | `=SUMIFS(Won!$H$2:$H;Won!$B$2:$B;$A{r};Won!$M$2:$M;"ICP 2")` |
| `O15:O44` | `=SUMIFS(Won!$H$2:$H;Won!$B$2:$B;$A{r};Won!$M$2:$M;"ICP 3")` |
| `B36` | `=INDEX(sales_teams!$B$2:$B36;MATCH($A36;sales_teams!$A$2:$A36;0))` |
| `C36` | `=INDEX(sales_teams!$C$2:$C36;MATCH($A36;sales_teams!$A$2:$A36;0))` |

## Books
| Célula | Fórmula |
|---|---|
| `B4:B88` | `=IFERROR(VLOOKUP(A{r};accounts!A:R;18;FALSE);"")` |
| `D4:D88` | `=VLOOKUP(C{r};sales_teams!A:C;2;FALSE)` |
| `E4:E88` | `=VLOOKUP(C{r};sales_teams!A:C;3;FALSE)` |
| `F4:F88` | `=IF(D{r}=$B$2;"Pilot";"Wave 2")` |
| `G4:G88` | `=SUMIFS(Won!H:H;Won!D:D;A{r};Won!C:C;"<>GTK 500")` |
| `H4:H88` | `=SUMIFS(Won!H:H;Won!D:D;A{r};Won!B:B;C{r};Won!C:C;"<>GTK 500")` |
| `I4:I89` | `=IF(G{r}=0;0;H{r}/G{r})` |
| `J4:J88` | `=COUNTIFS(sales_pipeline!D:D;A{r};sales_pipeline!E:E;"Engaging")+COUNTIFS(sales_pipeline!D:D;A{r};sales_pipeline!E:E;"Prospecting")` |
| `K4:K88` | `=COUNTIFS(sales_pipeline!D:D;A{r};sales_pipeline!B:B;C{r};sales_pipeline!E:E;"Engaging")+COUNTIFS(sales_pipeline!D:D;A{r};sales_pipeline!B:B;C{r};sales_pipeline!E:E;"Prospecting")` |
| `L4:L88` | `=J{r}-K{r}` |
| `N4:N88` | `=VLOOKUP(M{r};sales_teams!A:C;2;FALSE)` |
| `O4:O88` | `=IF(D{r}=N{r};"OK";"Other team: needs RevOps")` |
| `Q4:Q88` | `=IF(C{r}=M{r};"";IF(P{r}="";"Add a reason";"OK"))` |
| `G89` | `=SUM(G4:G88)` |
| `H89` | `=SUM(H4:H88)` |
| `J89` | `=SUM(J4:J88)` |
| `K89` | `=SUM(K4:K88)` |
| `L89` | `=SUM(L4:L88)` |

## Open Deals
| Célula | Fórmula |
|---|---|
| `B2` | `=Hoje!B4` |
| `B3` | `=Hoje!B5` |
| `B4` | `=Hoje!B6` |
| `A8` | `=FILTER(sales_pipeline!A2:F;(sales_pipeline!E2:E="Engaging")+(sales_pipeline!E2:E="Prospecting");sales_pipeline!D2:D<>"")` |
| `G8:G671` | `=IF(F{r}="";"";$B$2-F{r})` |
| `H8:H671` | `=IF(E{r}="Prospecting";"No activity recorded";IF(G{r}<=$B$3;"Recent";IF(G{r}<=$B$4;"In cycle";"Past longest cycle")))` |
| `I8:I671` | `=IF(C{r}="GTK 500";IF(COUNTIF('GTK 500 KPIs'!$B$3:$B$5;B{r});B{r};'GTK 500 KPIs'!$B$3);IF(H{r}="No activity recorded";K{r};IF(G{r}<=$B$4;B{r};K{r})))` |
| `J8:J671` | `=IF(I{r}<>B{r};"Moves";IF(I{r}=K{r};"Stays";"Stays until it closes"))` |
| `K8:K671` | `=IF(C{r}="GTK 500";I{r};VLOOKUP(D{r};Books!$A$4:$C$88;3;FALSE))` |
| `L8:L671` | `=IF(J{r}="Stays";"Keep working";IF(J{r}="Stays until it closes";"Current rep finishes it. After it closes or is lost, the account is the owner's only";IF(H{r}="Past longest cycle";"New owner re-qualifies within 30 days or closes it as lost";"New owner starts outreach")))` |
| `M8:M671` | `=VLOOKUP(C{r};Products!A:D;4;FALSE)` |
| `K88` | `=IF(C88="GTK 500";I88;VLOOKUP(D88;Books!$A$4:$C88;3;FALSE))` |

## Rep Books
| Célula | Fórmula |
|---|---|
| `B4:B38` | `=VLOOKUP(A{r};sales_teams!A:C;2;FALSE)` |
| `C4:C38` | `=VLOOKUP(A{r};sales_teams!A:C;3;FALSE)` |
| `E4:E38` | `=COUNTIF(Books!C$4:C$88;A{r})` |
| `F4:F38` | `=SUMIF(Books!C$4:C$88;A{r};Books!G$4:G$88)` |
| `G4:G38` | `=SUMIFS(Won!H:H;Won!B:B;A{r};Won!C:C;"<>GTK 500")` |
| `H4:H38` | `=IF(G{r}=0;0;F{r}/G{r}-1)` |
| `I4:I38` | `=SUMIFS(Won!H:H;Won!B:B;A{r};Won!C:C;"GTK 500")` |
| `J4:J38` | `=COUNTIFS(sales_pipeline!B:B;A{r};sales_pipeline!E:E;"Engaging")+COUNTIFS(sales_pipeline!B:B;A{r};sales_pipeline!E:E;"Prospecting")` |
| `K4:K38` | `=COUNTIF('Open Deals'!I$8:I$671;A{r})` |
| `L4:L38` | `=SUMIF('Open Deals'!B$8:B$671;A{r};'Open Deals'!M$8:M$671)` |
| `M4:M38` | `=SUMIF('Open Deals'!I$8:I$671;A{r};'Open Deals'!M$8:M$671)` |
| `N4:N38` | `=COUNTIFS('Open Deals'!B$8:B$671;A{r};'Open Deals'!J$8:J$671;"Stays until it closes")` |
| `O4:O38` | `=IF(G{r}=0;"";IF(ABS(H{r})<=$B$2;"OK";"Outside band"))` |
| `B41:B46` | `=VLOOKUP(A{r};sales_teams!B:C;2;FALSE)` |
| `C41:C46` | `=COUNTIFS(B$4:B$38;A{r};E$4:E$38;">0")` |
| `D41:D46` | `=SUMIF(B$4:B$38;A{r};E$4:E$38)` |
| `E41:E46` | `=SUMIF(B$4:B$38;A{r};F$4:F$38)` |
| `F41:F46` | `=SUMIF(B$4:B$38;A{r};G$4:G$38)` |
| `G41:G47` | `=IF(F{r}=0;0;E{r}/F{r}-1)` |
| `H41:H46` | `=SUMIF(B$4:B$38;A{r};I$4:I$38)` |
| `I41:I46` | `=SUMIF(B$4:B$38;A{r};J$4:J$38)` |
| `C47` | `=SUM(C41:C46)` |
| `D47` | `=SUM(D41:D46)` |
| `E47` | `=SUM(E41:E46)` |
| `F47` | `=SUM(F41:F46)` |
| `H47` | `=SUM(H41:H46)` |
| `I47` | `=SUM(I41:I46)` |
| `E48` | `=E47-Books!G89` |

## GTK 500 KPIs
| Célula | Fórmula |
|---|---|
| `B6` | `=Products!D8` |
| `B7` | `=DATE(2017;12;31)` |
| `C10` | `=COUNTIFS(sales_pipeline!C:C;"GTK 500";sales_pipeline!F:F;">="&DATE(2017;1;1);sales_pipeline!F:F;"<="&B7)/4` |
| `C11` | `=COUNTIFS(sales_pipeline!C:C;"GTK 500";sales_pipeline!F:F;">="&DATE(2017;10;1);sales_pipeline!F:F;"<="&B7)` |
| `C12` | `=SUMPRODUCT(COUNTIFS(sales_pipeline!C:C;"GTK 500";sales_pipeline!B:B;B3:B5))/COUNTIF(sales_pipeline!C:C;"GTK 500")` |
| `C13` | `=COUNTUNIQUE(FILTER(sales_pipeline!D:D;sales_pipeline!C:C="GTK 500";sales_pipeline!D:D<>""))` |
| `C14` | `=COUNTUNIQUE(FILTER(Won!D:D;Won!C:C="GTK 500"))` |
| `C15` | `=SUMPRODUCT(COUNTIFS(Won!C:C;"GTK 500";Won!B:B;B3:B5))/(SUMPRODUCT(COUNTIFS(Won!C:C;"GTK 500";Won!B:B;B3:B5))+SUMPRODUCT(COUNTIFS(Lost!C:C;"GTK 500";Lost!B:B;B3:B5)))` |
| `D15` | `=C15` |
| `C16` | `=AVERAGEIFS(Won!H:H;Won!C:C;"GTK 500")/B6` |
| `C17` | `=MEDIAN(FILTER(Won!G:G-Won!F:F;Won!C:C="GTK 500"))` |
| `C18` | `=MEDIAN(FILTER(Won!G2:G-Won!F2:F;Won!C2:C<>""))` |
| `C19` | `=COUNTIFS(sales_pipeline!C:C;"GTK 500";sales_pipeline!E:E;"Engaging";sales_pipeline!F:F;"<"&(B7-C17))` |
| `C20` | `=(SUMPRODUCT(SUMIF('Rep Books'!A:A;B3:B5;'Rep Books'!F:F))+SUMPRODUCT(SUMIF('Rep Books'!A:A;B3:B5;'Rep Books'!I:I)))/(SUMPRODUCT(SUMIF('Rep Books'!A:A;B3:B5;'Rep Books'!G:G))+SUMPRODUCT(SUMIF('Rep Books'!A:A;B3:B5;'Rep Books'!I:I)))` |

## Lista do Dia
O motor da prioridade. Todas as colunas são fórmulas de matriz na linha 8, uma por coluna. Passo 5 = Confirmar.
| Célula | Fórmula |
|---|---|
| `B2` | `=Hoje!B4` |
| `D2` | `=Hoje!B9` |
| `F2` | `=Hoje!B13` |
| `B3` | `=COUNTIF(S8:S;1)` |
| `D3` | `=COUNTIF(S8:S;2)` |
| `F3` | `=COUNTIF(S8:S;3)` |
| `H3` | `=COUNTIF(S8:S;4)` |
| `J3` | `=COUNTIF(S8:S;5)` |
| `B4` | `=COUNTA(A8:A)` |
| `D4` | `=COUNTA(UNIQUE(FILTER(J8:J;J8:J<>"")))` |
| `A8` | `=ARRAYFORMULA(FILTER({sales_pipeline!A2:C\sales_pipeline!J2:J\sales_pipeline!E2:F};(sales_pipeline!E2:E="Engaging")+(sales_pipeline!E2:E="Prospecting");sales_pipeline!J2:J<>"";ISNA(MATCH(sales_pipeline!A2:A;Atividades!$M$2:$M$2000;0))))` |
| `G8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(F8:F="";"";Hoje!$B$4-F8:F)))` |
| `H8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(E8:E="Prospecting";"Sem data";IF(G8:G<=Hoje!$B$6;"Vivo";"Passou do ciclo"))))` |
| `I8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(D8:D;Books!$A$4:$C$88;3;FALSE);"")))` |
| `J8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(Hoje!$B$9="Como está hoje";B8:B;IFERROR(VLOOKUP(A8:A;'Open Deals'!$A$8:$I$671;9;FALSE);IF(H8:H="Vivo";B8:B;IF(C8:C="GTK 500";'GTK 500 KPIs'!$B$3;IF(I8:I="";B8:B;I8:I)))))))` |
| `K8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(J8:J;sales_teams!$A$2:$C$36;2;FALSE);"")))` |
| `L8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(J8:J;sales_teams!$A$2:$C$36;3;FALSE);"")))` |
| `M8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(D8:D;accounts!$A$2:$R$86;18;FALSE);"")))` |
| `N8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(C8:C;Products!$A$2:$D8;4;FALSE);0)))` |
| `O8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(D8:D&"\|"&C8:C;{'Account x Product'!$A$6:$A&"\|"&'Account x Product'!$B$6:$B\'Account x Product'!$K$6:$K};2;FALSE);"Never bought")))` |
| `P8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(O8:O="Overdue";"Fora da janela";IF(O8:O="Due soon";"Entrando na janela";IF(O8:O="Not due";"Dentro da janela";IF(O8:O="Only 1 purchase";"Só 1 compra";"Nunca comprou"))))))` |
| `Q8` | `=ARRAYFORMULA(IF(A8:A="";"";IF((O8:O="Only 1 purchase")+(O8:O="Never bought");"";IFERROR(VLOOKUP(D8:D&"\|"&C8:C;{'Account x Product'!$A$6:$A&"\|"&'Account x Product'!$B$6:$B\'Account x Product'!$J$6:$J};2;FALSE);""))))` |
| `R8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(O8:O="Never bought";0;IFERROR(VLOOKUP(D8:D&"\|"&C8:C;{'Account x Product'!$A$6:$A&"\|"&'Account x Product'!$B$6:$B\'Account x Product'!$C$6:$C};2;FALSE);0))))` |
| `S8` | `=ARRAYFORMULA(IF(A8:A="";"";IF((AI8:AI<>"")*(AI8:AI>0)*(AN8:AN<>TRUE);5;IF(H8:H="Vivo";IF((O8:O="Overdue")+(O8:O="Due soon");1;2);IF((O8:O="Overdue")+(O8:O="Due soon");3;4)))))` |
| `T8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(S8:S=3;IF(Q8:Q>=-Hoje!$B$8;1;2);1)))` |
| `U8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(M8:M="";3;VALUE(RIGHT(M8:M;1)))))` |
| `V8` | `=ARRAYFORMULA(IF(A8:A="";"";LET(q;IF(Q8:Q="";500;Q8:Q);urg;IF((S8:S=3)*(q<-Hoje!$B$8);600+IF(-q>399;399;-q);q+500);IF(AB8:AB=TRUE;10^15;0)+S8:S*10^13+urg*10^9+IF(Hoje!$B$13="Valor depois ICP";(99999-N8:N)*10^4+U8:U*10^3+(999-IF(G8:G="";0;IF(G8:G>999;999;G8:G)));U8:U*10^8+(99999-N8:N)*10^2))))` |
| `W8` | `=ARRAYFORMULA(IF(A8:A="";"";COUNTIFS(J8:J;J8:J;V8:V;"<"&V8:V)+1))` |
| `X8` | `=ARRAYFORMULA(IF(A8:A="";"";LET(qn;IF(Q8:Q="";0;Q8:Q);agn;IF(AG8:AG="";0;AG8:AG);"Conta "&IF(M8:M="";"sem ICP";M8:M&": "&AF8:AF)&". "&IF(E8:E="Prospecting";"Este deal de "&C8:C&" ainda não tem data de engajamento";IF(H8:H="Vivo";"Este deal de "&C8:C&" está aberto há "&G8:G&" dias (ciclo normal "&Hoje!$B$5&", limite "&Hoje!$B$6&")";"Este deal de "&C8:C&" está aberto há "&G8:G&" dias, acima do limite de "&Hoje!$B$6&": nenhum deal ganho levou tanto"))&". "&IF((AI8:AI<>"")*(AI8:AI>0);"Depois de o deal abrir, a conta comprou "&C8:C&" "&AI8:AI&" vez(es) de outro(s) vendedor(es) ("&AL8:AL&"), a última há "&AM8:AM&" dia(s). ";IF(E8:E="Prospecting";"";"Nesse período nenhum outro vendedor fechou "&C8:C&" nesta conta. "))&IF(O8:O="Overdue";D8:D&" compra "&C8:C&" a cada "&AG8:AG&" dias ("&R8:R&" compras em 14 meses, "&AK8:AK&" vendedores diferentes); a recompra esperada já passou há "&ROUND(-qn)&" dias"&IF(-qn>2*agn;" (mais que o dobro do ritmo: a conta pode ter parado de comprar ou comprado em outro lugar)";"");IF(O8:O="Due soon";D8:D&" compra "&C8:C&" a cada "&AG8:AG&" dias ("&R8:R&" compras em 14 meses, "&AK8:AK&" vendedores diferentes); a próxima compra esperada é em "&ROUND(qn)&" dias";IF(O8:O="Not due";D8:D&" compra "&C8:C&" a cada "&AG8:AG&" dias ("&R8:R&" compras em 14 meses, "&AK8:AK&" vendedores diferentes); a próxima compra só em "&ROUND(qn)&" dias";IF(O8:O="Only 1 purchase";D8:D&" só comprou "&C8:C&" uma vez (há "&AH8:AH&" dias), sem ritmo pra estimar";D8:D&" nunca comprou "&C8:C))))&". "&IF(S8:S=5;"Leitura: pode ser o mesmo pedido, já atendido por um colega, ou demanda separada (outro departamento, outra quantidade, compra recorrente). Os dados não dizem qual: confirmar com a conta antes de encerrar.";IF(H8:H="Passou do ciclo";"Leitura: deal parado além do que qualquer ganho levou; requalificar ou encerrar.";IF(S8:S=1;"Leitura: deal limpo, vivo e conta na hora de comprar."&IF(O8:O="Overdue";IF(-qn>2*agn;" Confirme se a conta ainda compra "&C8:C&" antes de contar com essa recompra.";"");"");IF(S8:S=2;"Leitura: deal limpo e vivo, recompra ainda não chegou.";""))))&IF(AN8:AN=TRUE;" A conta confirmou que é demanda separada: o deal voltou pros passos.";"")&IF(Z8:Z="";"";IF(AB8:AB=TRUE;" Trabalhado hoje.";" Último contato há "&(Hoje!$B$4-Z8:Z)&" dias.")))))` |
| `Y8` | `=ARRAYFORMULA(IF(A8:A="";"";LET(qn;IF(Q8:Q="";0;Q8:Q);agn;IF(AG8:AG="";0;AG8:AG);sa;IF(S8:S=1;IF(O8:O="Overdue";"ligar hoje: a recompra de "&C8:C&" já passou há "&ROUND(-qn)&" dias"&IF(-qn>2*agn;". Confirme primeiro se a conta ainda compra "&C8:C;"");"ligar hoje: a próxima recompra de "&C8:C&" é em "&ROUND(qn)&" dias");IF(S8:S=2;"trabalhar o deal: ainda dentro do ciclo";IF(S8:S=3;IF(E8:E="Prospecting";"engajar hoje e registrar a data: a conta está na hora de recomprar "&C8:C;IF(qn>=-Hoje!$B$8;"requalificar em até "&Hoje!$B$11&" dias ou fechar como perdido: a conta está na hora de recomprar "&C8:C;"recuperação: a conta está há mais de "&Hoje!$B$8&" dias fora da janela e pode ter comprado em outro lugar. Requalificar ou fechar como perdido"));IF(E8:E="Prospecting";"engajar e registrar a data; ordenado pelo valor do produto";"requalificar em até "&Hoje!$B$11&" dias ou fechar como perdido: recompra ainda não chegou"))));IF(S8:S=5;"Confirmar com a conta antes de qualquer coisa: é o mesmo pedido que "&AJ8:AJ&" fechou há "&AM8:AM&" dia(s), ou demanda separada (outro departamento, outra quantidade, compra recorrente)? Mesmo pedido: juntar ao deal de "&AJ8:AJ&" ou fechar como perdido. Demanda separada: marque 'Demanda separada' e o deal volta pros passos";UPPER(LEFT(sa;1))&MID(sa;2;999))&IF(C8:C="GTK 500";". Trazer um especialista GTK 500";"")&IF((J8:J<>B8:B)*(H8:H<>"Vivo");". Deal veio de "&B8:B;"")&".")))` |
| `Z8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(A8:A;Atividades!$J$2:$K$2000;2;FALSE);"")))` |
| `AA8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(A8:A;Atividades!$M$2:$N$2000;2;FALSE);"aberto")))` |
| `AB8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(Z8:Z="";FALSE;Z8:Z=Hoje!$B$4)))` |
| `AC8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(D8:D;accounts!$A$2:$E$86;4;FALSE);"")))` |
| `AD8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(D8:D;accounts!$A$2:$E$86;5;FALSE);"")))` |
| `AE8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(D8:D;accounts!$A$2:$E$86;2;FALSE);"")))` |
| `AF8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(M8:M="ICP 1";IF(AC8:AC>=ICP!$G$3;"receita de US$ "&ROUND(AC8:AC/1000;1)&" bi (regra: "&ICP!$G$3/1000&" bi ou mais)";"setor "&AE8:AE&" (regra: software entra no ICP 1)");IF(M8:M="ICP 2";"receita de US$ "&ROUND(AC8:AC/1000;1)&" bi (regra: entre "&ICP!$G$4/1000&" e "&ICP!$G$3/1000&" bi)";IF(M8:M="ICP 3";"receita de US$ "&ROUND(AC8:AC)&" mi (regra: abaixo de "&ICP!$G$4/1000&" bi)";"")))))` |
| `AG8` | `=ARRAYFORMULA(IF(A8:A="";"";IF((O8:O="Only 1 purchase")+(O8:O="Never bought");"";IFERROR(ROUND(VLOOKUP(D8:D&"\|"&C8:C;{'Account x Product'!$A$6:$A$600&"\|"&'Account x Product'!$B$6:$B$600\'Account x Product'!$H$6:$H$600};2;FALSE));""))))` |
| `AH8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(O8:O="Never bought";"";IFERROR(Hoje!$B$4-VLOOKUP(D8:D&"\|"&C8:C;{'Account x Product'!$A$6:$A$600&"\|"&'Account x Product'!$B$6:$B$600\'Account x Product'!$F$6:$F$600};2;FALSE);""))))` |
| `AI8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(F8:F="";"";COUNTIFS(Won!$D$2:$D;D8:D;Won!$C$2:$C;C8:C;Won!$G$2:$G;">"&F8:F;Won!$B$2:$B;"<>"&B8:B))))` |
| `AJ8` | `=MAP(D8:D;C8:C;F8:F;B8:B;AM8:AM;LAMBDA(a;p;e;v;d;IF((a="")+(d="");"";IFERROR(INDEX(FILTER(Won!$B$2:$B;Won!$D$2:$D=a;Won!$C$2:$C=p;Won!$G$2:$G=Hoje!$B$4-d;Won!$B$2:$B<>v);1);""))))` |
| `AK8` | `=MAP(D8:D;C8:C;LAMBDA(a;p;IF(a="";"";COUNTUNIQUEIFS(Won!$B$2:$B;Won!$D$2:$D;a;Won!$C$2:$C;p))))` |
| `AL8` | `=MAP(D8:D;C8:C;F8:F;B8:B;LAMBDA(a;p;e;v;IF((a="")+(e="");"";IFERROR(TEXTJOIN(", ";TRUE;UNIQUE(FILTER(Won!$B$2:$B;Won!$D$2:$D=a;Won!$C$2:$C=p;Won!$G$2:$G>e;Won!$B$2:$B<>v)));""))))` |
| `AM8` | `=MAP(D8:D;C8:C;F8:F;B8:B;AI8:AI;LAMBDA(a;p;e;v;n;IF((a="")+(e="")+(n="");"";IF(n=0;"";Hoje!$B$4-MAXIFS(Won!$G$2:$G;Won!$D$2:$D;a;Won!$C$2:$C;p;Won!$G$2:$G;">"&e;Won!$B$2:$B;"<>"&v)))))` |
| `AN8` | `=ARRAYFORMULA(IF(A8:A="";"";ISNUMBER(MATCH(A8:A;Atividades!$O$2:$O$2000;0))))` |

## Fila Sem Conta
| Célula | Fórmula |
|---|---|
| `B2` | `=Hoje!B4` |
| `D2` | `=Hoje!B10` |
| `F2` | `=COUNTIFS(A8:A;"<>";K8:K;"<>Identificada")` |
| `H2` | `=COUNTIF(H8:H;"Vivo")` |
| `J2` | `=COUNTIF(N8:N;"Escalar pro manager")` |
| `L2` | `=COUNTIF(K8:K;"Identificada")` |
| `A8` | `=FILTER({sales_pipeline!A2:C\sales_pipeline!E2:F};(sales_pipeline!E2:E="Engaging")+(sales_pipeline!E2:E="Prospecting");sales_pipeline!D2:D="")` |
| `F8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(E8:E="";"";Hoje!$B$4-E8:E)))` |
| `G8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(C8:C;Products!$A$2:$D8;4;FALSE);0)))` |
| `H8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(D8:D="Prospecting";"Sem data";IF(F8:F<=Hoje!$B$6;"Vivo";"Passou do ciclo"))))` |
| `I8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(B8:B;sales_teams!$A$2:$C$36;2;FALSE);"")))` |
| `J8` | `=ARRAYFORMULA(IF(A8:A="";"";WORKDAY(Hoje!$B$2;Hoje!$B$10)))` |
| `M8` | `=ARRAYFORMULA(IF(L8:L="";"";IFERROR(VLOOKUP(L8:L;Books!$A$4:$C$88;3;FALSE);"Não é nenhuma das 85: new logo")))` |
| `N8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(K8:K="Identificada";"Pronto: deal entra na Lista do Dia";IF(K8:K="Não é nenhuma das 85";"New logo: regra própria";IF(Hoje!$B$4>J8:J;"Escalar pro manager";"No prazo")))))` |
| `O8` | `=ARRAYFORMULA(IF(A8:A="";"";COUNTIFS(B8:B;B8:B;P8:P;"<"&P8:P)+1))` |
| `P8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(H8:H="Vivo";0;1)*10^6+(99999-G8:G)*10+IF(F8:F="";9;0)))` |

## Recompra sem deal
| Célula | Fórmula |
|---|---|
| `B2` | `=Hoje!B4` |
| `D2` | `=COUNTA(A8:A)` |
| `F2` | `=COUNTIF(N8:N;TRUE)` |
| `A8` | `=FILTER({'Account x Product'!A6:B600\'Account x Product'!H6:H600\'Account x Product'!C6:C600\'Account x Product'!F6:F600\'Account x Product'!J6:J600\'Account x Product'!K6:K600};('Account x Product'!K6:K600="Overdue")+('Account x Product'!K6:K600="Due soon"))` |
| `H8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(A8:A;Books!$A$4:$C$88;3;FALSE);"")))` |
| `I8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(H8:H;sales_teams!$A$2:$C$36;2;FALSE);"")))` |
| `J8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(A8:A;accounts!$A$2:$R$86;18;FALSE);"")))` |
| `K8` | `=ARRAYFORMULA(IF(A8:A="";"";IFERROR(VLOOKUP(B8:B;Products!$A$2:$D8;4;FALSE);0)))` |
| `L8` | `=ARRAYFORMULA(IF(A8:A="";"";Hoje!$B$4-E8:E))` |
| `M8` | `=ARRAYFORMULA(IF(A8:A="";"";COUNTIFS('Lista do Dia'!$D$8:$D$700;A8:A;'Lista do Dia'!$C$8:$C$700;B8:B;'Lista do Dia'!$S$8:$S$700;"<>5")))` |
| `N8` | `=ARRAYFORMULA(IF(A8:A="";"";S8:S=0))` |
| `O8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(N8:N<>TRUE;"";COUNTIFS(H8:H;H8:H;R8:R;"<"&R8:R)+1)))` |
| `P8` | `=ARRAYFORMULA(IF(A8:A="";"";A8:A&" compra "&B8:B&" a cada "&ROUND(C8:C)&" dias ("&D8:D&" compras em 14 meses); a última foi há "&L8:L&" dias"&IF(G8:G="Overdue";", e a recompra esperada já passou há "&ROUND(-F8:F)&" dias"&IF(-F8:F>2*C8:C;" (mais que o dobro do ritmo: a conta pode ter parado de comprar ou comprado em outro lugar)";"");", e a próxima é esperada em "&ROUND(F8:F)&" dias")&". "&IF(S8:S=0;"Não existe nenhum deal aberto pra isso: a oportunidade está sem dono no CRM.";IF(M8:M=0;"Já existe deal aberto pra isso ("&U8:U&"), mas a conta comprou o produto de outro vendedor depois de ele abrir: confirmar esse deal antes de abrir outro.";"Já tem "&M8:M&" deal(s) limpo(s) aberto(s) na lista."))&IF(T8:T=TRUE;" Feito hoje.";"")))` |
| `Q8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(S8:S=0;"Abrir o deal de "&B8:B&" na "&A8:A&" e ligar "&IF(G8:G="Overdue";"hoje";"nesta semana")&": US$ "&K8:K&" de tabela"&IF(G8:G="Overdue";IF(-F8:F>2*C8:C;". Confirme primeiro se a conta ainda compra "&B8:B;"");"")&".";IF(M8:M=0;"Não abrir outro: confirmar o deal "&U8:U&" com a conta (mesmo pedido ou demanda separada).";"Nada a abrir: trabalhar o deal que já existe."))))` |
| `R8` | `=ARRAYFORMULA(IF(A8:A="";"";IF(N8:N=TRUE;(F8:F+500)*10^6+(99999-K8:K)+IF(T8:T=TRUE;10^12;0);9*10^12)))` |
| `S8` | `=ARRAYFORMULA(IF(A8:A="";"";COUNTIFS('Lista do Dia'!$D$8:$D$700;A8:A;'Lista do Dia'!$C$8:$C$700;B8:B)))` |
| `T8` | `=ARRAYFORMULA(IF(A8:A="";"";ISNUMBER(MATCH(A8:A&"\|"&B8:B;Atividades!$P$2:$P$2000;0))))` |
| `U8` | `=MAP(A8:A;B8:B;M8:M;S8:S;LAMBDA(a;p;m;s;IF(a="";"";IF((m=0)*(s>0);IFERROR(INDEX(FILTER('Lista do Dia'!$A$8:$A$700&" (com "&'Lista do Dia'!$J$8:$J$700&")";'Lista do Dia'!$D$8:$D$700=a;'Lista do Dia'!$C$8:$C$700=p);1);"");""))))` |

## Visão Manager
| Célula | Fórmula |
|---|---|
| `B2` | `=Hoje!B4` |
| `D2` | `=Hoje!B9` |
| `F2` | `=Hoje!B12` |
| `A5` | `=ARRAYFORMULA(sales_teams!A2:A36)` |
| `B5` | `=ARRAYFORMULA(IF(A5:A39="";"";VLOOKUP(A5:A39;sales_teams!$A$2:$C$36;2;FALSE)))` |
| `C5` | `=ARRAYFORMULA(IF(A5:A39="";"";VLOOKUP(A5:A39;sales_teams!$A$2:$C$36;3;FALSE)))` |
| `D5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIF('Lista do Dia'!$B$8:$B;A5:A39)))` |
| `E5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIF('Open Deals'!$I$8:$I$671;A5:A39)))` |
| `F5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIF('Lista do Dia'!$J$8:$J;A5:A39)))` |
| `G5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;1)))` |
| `H5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;2)))` |
| `I5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;3)))` |
| `J5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;4)))` |
| `K5` | `=ARRAYFORMULA(IF(A5:A39="";"";G5:G39+H5:H39+I5:I39))` |
| `L5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Fila Sem Conta'!$B$8:$B;A5:A39;'Fila Sem Conta'!$K$8:$K;"<>Identificada")))` |
| `M5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Fila Sem Conta'!$B$8:$B;A5:A39;'Fila Sem Conta'!$N$8:$N;"Escalar pro manager")))` |
| `N5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$H$8:$H;"Vivo";'Lista do Dia'!$I$8:$I;"<>"&A5:A39)))` |
| `O5` | `=ARRAYFORMULA(IF(A5:A39="";"";IFERROR(VLOOKUP(A5:A39;'Rep Books'!$A$4:$O$38;8;FALSE);"")))` |
| `P5` | `=ARRAYFORMULA(IF(A5:A39="";"";IFERROR(VLOOKUP(A5:A39;'Rep Books'!$A$4:$O$38;15;FALSE);"")))` |
| `Q5` | `=ARRAYFORMULA(IF(A5:A39="";"";IF(P5:P39="Outside band";"Carteira fora da faixa";IF(M5:M39>0;"Fila fora do prazo";IF(K5:K39>(Hoje!$B$12*3)/2;"Carga alta pra semana";"")))))` |
| `R5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;5)))` |
| `A43` | `=UNIQUE(sales_teams!B2:B36)` |
| `B43` | `=ARRAYFORMULA(IF(A43:A48="";"";VLOOKUP(A43:A48;sales_teams!$B$2:$C$36;2;FALSE)))` |
| `C43` | `=ARRAYFORMULA(IF(A43:A48="";"";COUNTIF($B$5:$B$39;A43:A48)))` |
| `D43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$D$5:$D$39)))` |
| `E43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$E$5:$E$39)))` |
| `F43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$G$5:$G$39)))` |
| `G43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$H$5:$H$39)))` |
| `H43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$I$5:$I$39)))` |
| `I43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$J$5:$J$39)))` |
| `J43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$L$5:$L$39)))` |
| `K43` | `=ARRAYFORMULA(IF(A43:A48="";"";SUMIF($B$5:$B$39;A43:A48;$M$5:$M$39)))` |
| `L43` | `=ARRAYFORMULA(IF(A43:A48="";"";COUNTIFS($B$5:$B$39;A43:A48;$Q$5:$Q$39;"?*")))` |

## KPIs Vendedor
| Célula | Fórmula |
|---|---|
| `B2` | `=Hoje!B4` |
| `D2` | `=Hoje!B9` |
| `A5` | `=ARRAYFORMULA(sales_teams!A2:A36)` |
| `B5` | `=ARRAYFORMULA(IF(A5:A39="";"";VLOOKUP(A5:A39;sales_teams!$A$2:$C$36;2;FALSE)))` |
| `C5` | `=ARRAYFORMULA(IF(A5:A39="";"";VLOOKUP(A5:A39;sales_teams!$A$2:$C$36;3;FALSE)))` |
| `D5` | `=ARRAYFORMULA(IF(A5:A39="";"";LOWER(SUBSTITUTE(A5:A39;" ";"."))&"@g4demo.com"))` |
| `E5` | `=ARRAYFORMULA(IF(A5:A39="";"";"vendedor"))` |
| `F5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIF('Lista do Dia'!$J$8:$J;A5:A39)))` |
| `G5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIF(Won!$B$2:$B;A5:A39)+COUNTIFS(Atividades!$D$2:$D$2000;A5:A39;Atividades!$E$2:$E$2000;"ganho")))` |
| `H5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIF(Lost!$B$2:$B;A5:A39)+COUNTIFS(Atividades!$D$2:$D$2000;A5:A39;Atividades!$E$2:$E$2000;"perdido")))` |
| `I5` | `=ARRAYFORMULA(IF(A5:A39="";"";G5:G39+H5:H39))` |
| `J5` | `=ARRAYFORMULA(IF(A5:A39="";"";IF(I5:I39=0;0;G5:G39/I5:I39)))` |
| `K5` | `=MAP(A5:A39;LAMBDA(rep;IF(rep="";"";SUMIF(Won!$B$2:$B;rep;Won!$H$2:$H)+SUMIFS(Atividades!$F$2:$F$2000;Atividades!$D$2:$D$2000;rep;Atividades!$E$2:$E$2000;"ganho"))))` |
| `L5` | `=MAP(A5:A39;LAMBDA(rep;IF(rep="";"";IFERROR(IF(Hoje!$B$9="Carteiras";COUNTIF($X5:$X$89;rep);SUMPRODUCT(--ISNUMBER(MATCH($W5:$W$89;FILTER('Lista do Dia'!$D$8:$D;'Lista do Dia'!$B$8:$B=rep);0))));0))))` |
| `M5` | `=MAP(A5:A39;LAMBDA(rep;IF(rep="";"";IFERROR(IF(Hoje!$B$9="Carteiras";IF(COUNTIF($X5:$X$89;rep)=0;0;SUMIF($X5:$X$89;rep;$Y5:$Y$89)/COUNTIF($X5:$X$89;rep));AVERAGE(FILTER($Y5:$Y$89;ISNUMBER(MATCH($W5:$W$89;FILTER('Lista do Dia'!$D$8:$D;'Lista do Dia'!$B$8:$B=rep);0)))));0))))` |
| `N5` | `=MAP(A5:A39;LAMBDA(rep;IF(rep="";"";IFERROR(IF(Hoje!$B$9="Carteiras";SUMIF($X5:$X$89;rep;$Z5:$Z$89);SUM(FILTER($Z5:$Z$89;ISNUMBER(MATCH($W5:$W$89;FILTER('Lista do Dia'!$D$8:$D;'Lista do Dia'!$B$8:$B=rep);0)))));0))))` |
| `O5` | `=ARRAYFORMULA(IF(A5:A39="";"";IF(L5:L39=0;0;N5:N39/L5:L39)))` |
| `P5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Fila Sem Conta'!$B$8:$B;A5:A39;'Fila Sem Conta'!$K$8:$K;"<>Identificada")))` |
| `Q5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;1)))` |
| `R5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;2)))` |
| `S5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;3)))` |
| `T5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;4)))` |
| `U5` | `=ARRAYFORMULA(IF(A5:A39="";"";Q5:Q39+R5:R39+S5:S39))` |
| `V5` | `=ARRAYFORMULA(IF(A5:A39="";"";COUNTIFS('Lista do Dia'!$J$8:$J;A5:A39;'Lista do Dia'!$S$8:$S;5)))` |
| `W5` | `=ARRAYFORMULA(Books!A4:A88)` |
| `X5` | `=ARRAYFORMULA(Books!C4:C88)` |
| `Y5` | `=ARRAYFORMULA(IF(W5:W89="";"";COUNTIF('Account x Product'!$A$6:$A;W5:W89)))` |
| `Z5` | `=ARRAYFORMULA(IF(W5:W89="";"";SUMIF(Won!$D$2:$D;W5:W89;Won!$H$2:$H)))` |
| `A41` | `=UNIQUE(sales_teams!B2:B36)` |
| `B41` | `=ARRAYFORMULA(IF(A41:A46="";"";A41:A46))` |
| `C41` | `=ARRAYFORMULA(IF(A41:A46="";"";VLOOKUP(A41:A46;sales_teams!$B$2:$C$36;2;FALSE)))` |
| `D41` | `=ARRAYFORMULA(IF(A41:A46="";"";LOWER(SUBSTITUTE(A41:A46;" ";"."))&"@g4demo.com"))` |
| `E41` | `=ARRAYFORMULA(IF(A41:A46="";"";"manager"))` |

## Backtest
Snapshot editável em B2. Fórmulas de matriz na linha 22; o bloco AJ:AP é o acaso pareado por vendedor.
| Célula | Fórmula |
|---|---|
| `B2` | `=DATE(2017;9;30)` |
| `E2` | `=COUNTA(A22:A)` |
| `B3` | `=Hoje!B2` |
| `E3` | `=COUNTIF(E22:E;"Won")` |
| `G3` | `=COUNTIF(E22:E;"Lost")` |
| `I3` | `=E2-E3-G3` |
| `B4` | `=Hoje!B12` |
| `E4` | `=SUMIFS(H22:H;E22:E;"Won")` |
| `G4` | `=IF(E3+G3=0;"";E3/(E3+G3))` |
| `A6` | `="Leitura exploratória, não prova: um snapshot só, dado gerado, sem relação de causa (seguir a ordem não garante mais vendas). Os cortes de 57 e 138 dias vêm do arquivo inteiro, inclusive do que fechou depois do snapshot, então o teste conhece um pouco do futuro. Top N exato por vendedor (empates desfeitos pela linha) e acaso pareado por vendedor. Atropelados (outro vendedor fechou o produto na conta depois de o deal abrir) fecharam Won em "&TEXT(H12;"0%")&" contra "&TEXT(M12;"0%")&" dos limpos: o sinal não separa quem fecha, por isso a regra é confirmar, não encerrar."` |
| `E8:E11` | `=COUNTIF($L$22:$L;D{r})` |
| `F8:F11` | `=COUNTIFS($L$22:$L;D{r};$E$22:$E;"Won")` |
| `G8:G11` | `=COUNTIFS($L$22:$L;D{r};$E$22:$E;"Lost")` |
| `H8:H11` | `=E{r}-F{r}-G{r}` |
| `I8:I11` | `=IF(F{r}+G{r}=0;"";F{r}/(F{r}+G{r}))` |
| `J8:J11` | `=SUMIFS($H$22:$H;$L$22:$L;D{r};$E$22:$E;"Won")` |
| `E12` | `=COUNTIF($AF$22:$AF;">0")` |
| `F12` | `=COUNTIFS($AF$22:$AF;">0";$E$22:$E;"Won")` |
| `G12` | `=COUNTIFS($AF$22:$AF;">0";$E$22:$E;"Lost")` |
| `H12` | `=IF(F12+G12=0;"";F12/(F12+G12))` |
| `J12` | `=COUNTIF($AF$22:$AF;0)` |
| `K12` | `=COUNTIFS($AF$22:$AF;0;$E$22:$E;"Won")` |
| `L12` | `=COUNTIFS($AF$22:$AF;0;$E$22:$E;"Lost")` |
| `M12` | `=IF(K12+L12=0;"";K12/(K12+L12))` |
| `E14` | `=COUNTIF($Q$22:$Q;"<="&$B$4)` |
| `F14` | `=COUNTIFS($Q$22:$Q;"<="&$B$4;$E$22:$E;"Won")` |
| `G14:G19` | `=IF(E{r}=0;"";F{r}/E{r})` |
| `H14` | `=SUMIFS($H$22:$H;$Q$22:$Q;"<="&$B$4;$E$22:$E;"Won")` |
| `E15` | `=COUNTIF($R$22:$R;"<="&$B$4)` |
| `F15` | `=COUNTIFS($R$22:$R;"<="&$B$4;$E$22:$E;"Won")` |
| `H15` | `=SUMIFS($H$22:$H;$R$22:$R;"<="&$B$4;$E$22:$E;"Won")` |
| `E16` | `=COUNTIF($S$22:$S;"<="&$B$4)` |
| `F16` | `=COUNTIFS($S$22:$S;"<="&$B$4;$E$22:$E;"Won")` |
| `H16` | `=SUMIFS($H$22:$H;$S$22:$S;"<="&$B$4;$E$22:$E;"Won")` |
| `E17` | `=COUNTIF($T$22:$T;"<="&$B$4)` |
| `F17` | `=COUNTIFS($T$22:$T;"<="&$B$4;$E$22:$E;"Won")` |
| `H17` | `=SUMIFS($H$22:$H;$T$22:$T;"<="&$B$4;$E$22:$E;"Won")` |
| `E18` | `=SUM(AN22:AN)` |
| `F18` | `=SUM(AO22:AO)` |
| `H18` | `=SUM(AP22:AP)` |
| `E19` | `=COUNTIF($AH$22:$AH;"<="&$B$4)` |
| `F19` | `=COUNTIFS($AH$22:$AH;"<="&$B$4;$E$22:$E;"Won")` |
| `H19` | `=SUMIFS($H$22:$H;$AH$22:$AH;"<="&$B$4;$E$22:$E;"Won")` |
| `A22` | `=FILTER(sales_pipeline!A2:H;sales_pipeline!E2:E<>"Prospecting";sales_pipeline!D2:D<>"";sales_pipeline!F2:F<=$B$2;(sales_pipeline!G2:G="")+(sales_pipeline!G2:G>$B$2))` |
| `I22` | `=ARRAYFORMULA(IF(A22:A="";"";$B$2-F22:F))` |
| `J22` | `=ARRAYFORMULA(IF(A22:A="";"";IF(I22:I<=Hoje!$B$6;"Vivo";"Passou do ciclo")))` |
| `K22` | `=ARRAYFORMULA(IF(A22:A="";"";IFERROR(VLOOKUP(D22:D&"\|"&C22:C;{W22:W&"\|"&X22:X\AE22:AE};2;FALSE);"Never bought")))` |
| `L22` | `=ARRAYFORMULA(IF(A22:A="";"";IF(J22:J="Vivo";IF((K22:K="Overdue")+(K22:K="Due soon");1;2);IF((K22:K="Overdue")+(K22:K="Due soon");3;4))))` |
| `M22` | `=ARRAYFORMULA(IF(A22:A="";"";IFERROR(VALUE(RIGHT(VLOOKUP(D22:D;accounts!$A$2:$R$86;18;FALSE);1));3)))` |
| `N22` | `=ARRAYFORMULA(IF(A22:A="";"";IFERROR(VLOOKUP(C22:C;Products!$A$2:$D$8;4;FALSE);0)))` |
| `O22` | `=ARRAYFORMULA(IF(A22:A="";"";L22:L*10^12+IF(L22:L=3;IF(U22:U>=-Hoje!$B$8;1;2);1)*10^11+M22:M*10^9+(99999-N22:N)*10^4+(9999-IF(I22:I>9999;9999;I22:I))))` |
| `P22` | `=ARRAYFORMULA(IF(A22:A="";"";L22:L*10^12+IF(L22:L=3;IF(U22:U>=-Hoje!$B$8;1;2);1)*10^11+(99999-N22:N)*10^5+M22:M*10^4+(9999-IF(I22:I>9999;9999;I22:I))))` |
| `Q22` | `=ARRAYFORMULA(IF(A22:A="";"";COUNTIFS(B22:B;B22:B;O22:O;"<"&O22:O)+COUNTIFS(B22:B;B22:B;O22:O;O22:O;V22:V;"<"&V22:V)+1))` |
| `R22` | `=ARRAYFORMULA(IF(A22:A="";"";COUNTIFS(B22:B;B22:B;P22:P;"<"&P22:P)+COUNTIFS(B22:B;B22:B;P22:P;P22:P;V22:V;"<"&V22:V)+1))` |
| `S22` | `=ARRAYFORMULA(IF(A22:A="";"";COUNTIFS(B22:B;B22:B;N22:N;">"&N22:N)+COUNTIFS(B22:B;B22:B;N22:N;N22:N;I22:I;"<"&I22:I)+COUNTIFS(B22:B;B22:B;N22:N;N22:N;I22:I;I22:I;V22:V;"<"&V22:V)+1))` |
| `T22` | `=ARRAYFORMULA(IF(A22:A="";"";COUNTIFS(B22:B;B22:B;I22:I;"<"&I22:I)+COUNTIFS(B22:B;B22:B;I22:I;I22:I;V22:V;"<"&V22:V)+1))` |
| `U22` | `=ARRAYFORMULA(IF(A22:A="";"";IF((K22:K="Only 1 purchase")+(K22:K="Never bought");"";IFERROR(VLOOKUP(D22:D&"\|"&C22:C;{W22:W&"\|"&X22:X\AD22:AD};2;FALSE);""))))` |
| `V22` | `=ARRAYFORMULA(IF(A22:A="";"";ROW(A22:A)))` |
| `W22` | `=QUERY(Won!A2:I;"select D, C, count(A), min(G), max(G) where D <> '' and G <= date '"&YEAR($B$2)&"-"&TEXT(MONTH($B$2);"00")&"-"&TEXT(DAY($B$2);"00")&"' group by D, C label count(A) '', min(G) '', max(G) ''";0)` |
| `AB22` | `=ARRAYFORMULA(IF(W22:W="";"";IF(Y22:Y<2;"";(AA22:AA-Z22:Z)/(Y22:Y-1))))` |
| `AC22` | `=ARRAYFORMULA(IF(W22:W="";"";IF(AB22:AB="";"";AA22:AA+AB22:AB)))` |
| `AD22` | `=ARRAYFORMULA(IF(W22:W="";"";IF(AC22:AC="";"";AC22:AC-$B$2)))` |
| `AE22` | `=ARRAYFORMULA(IF(W22:W="";"";IF(AD22:AD="";"Only 1 purchase";IF(AD22:AD<0;"Overdue";IF(AD22:AD<=Hoje!$B$7;"Due soon";"Not due")))))` |
| `AF22` | `=ARRAYFORMULA(IF(A22:A="";"";COUNTIFS(Won!$D$2:$D;D22:D;Won!$C$2:$C;C22:C;Won!$G$2:$G;">"&F22:F;Won!$G$2:$G;"<="&$B$2;Won!$B$2:$B;"<>"&B22:B)))` |
| `AG22` | `=ARRAYFORMULA(IF(A22:A="";"";LET(st;IF(AF22:AF>0;5;L22:L);q;IF(U22:U="";500;U22:U);urg;IF((st=3)*(q<-Hoje!$B$8);600+IF(-q>399;399;-q);q+500);st*10^13+urg*10^9+(99999-N22:N)*10^4+M22:M*10^3)))` |
| `AH22` | `=ARRAYFORMULA(IF(A22:A="";"";COUNTIFS(B22:B;B22:B;AG22:AG;"<"&AG22:AG)+COUNTIFS(B22:B;B22:B;AG22:AG;AG22:AG;V22:V;"<"&V22:V)+1))` |
| `AJ22` | `=UNIQUE(FILTER(B22:B;B22:B<>""))` |
| `AK22` | `=ARRAYFORMULA(IF(AJ22:AJ="";"";COUNTIF($B22:$B;AJ22:AJ)))` |
| `AL22` | `=ARRAYFORMULA(IF(AJ22:AJ="";"";COUNTIFS($B22:$B;AJ22:AJ;$E22:$E;"Won")))` |
| `AM22` | `=ARRAYFORMULA(IF(AJ22:AJ="";"";SUMIFS($H22:$H;$B22:$B;AJ22:AJ;$E22:$E;"Won")))` |
| `AN22` | `=ARRAYFORMULA(IF(AJ22:AJ="";"";IF(AK22:AK<$B$4;AK22:AK;$B$4)))` |
| `AO22` | `=ARRAYFORMULA(IF(AJ22:AJ="";"";IF(AK22:AK=0;0;AN22:AN*AL22:AL/AK22:AK)))` |
| `AP22` | `=ARRAYFORMULA(IF(AJ22:AJ="";"";IF(AK22:AK=0;0;AN22:AN*AM22:AM/AK22:AK)))` |

## Atividades
A:G é o que o app grava (sem fórmula). J:P são colunas auxiliares em fórmula que a Lista do Dia e a Recompra sem deal leem.
| Célula | Fórmula |
|---|---|
| `J2` | `=IFERROR(UNIQUE(FILTER(C2:C;C2:C<>"";E2:E<>"conta"));"")` |
| `K2` | `=MAP(J2:J;LAMBDA(d;IF(d="";"";MAXIFS(B2:B;C2:C;d;E2:E;"<>conta"))))` |
| `L2` | `=MAP(J2:J;LAMBDA(d;IF(d="";"";COUNTIF(C2:C;d))))` |
| `M2` | `=IFERROR(UNIQUE(FILTER(C2:C;(E2:E="ganho")+(E2:E="perdido")));"")` |
| `N2` | `=MAP(M2:M;LAMBDA(d;IF(d="";"";INDEX(FILTER(E2:E;C2:C=d;(E2:E="ganho")+(E2:E="perdido"));1))))` |
| `O2` | `=IFERROR(UNIQUE(FILTER(C2:C;E2:E="separado"));"")` |
| `P2` | `=IFERROR(UNIQUE(FILTER(C2:C;E2:E="recompra";B2:B=Hoje!$B$4));"")` |
