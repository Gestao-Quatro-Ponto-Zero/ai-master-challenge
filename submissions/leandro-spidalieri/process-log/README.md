# Process log

Leandro definiu o escopo, forneceu a especificação e autorizou a execução local. O Codex no desktop conduziu os ciclos técnicos com terminal e Chrome. O trabalho foi dividido em auditoria dos dados, avaliação do classificador, construção do app e validação reproduzível.

## Do briefing à evidência

1. **Conferência.** Leitura do briefing, inspeção do workspace e conferência das seis fontes oficiais na revisão `4aed364d572f`.
2. **Auditoria.** O Dataset 1 tinha menos linhas do que o enunciado estimava e os campos temporais eram timestamps. A recontagem mostrou pares invertidos e ausência de abertura. O Codex descartou medir FRT/TTR ou monetizar espera e manteve a leitura de carga e cobertura. Uma consulta exploratória de extremos de satisfação tentou ordenar cortes sem nota junto com percentuais. O Codex refez o corte exigindo notas válidas suficientes.
3. **Protótipo.** O Codex agrupou quase duplicatas, ajustou TF-IDF só no treino, fixou 0,55 na validação e só depois executou a avaliação reservada. O risco de acesso privilegiado apareceu no resultado e foi destacado na área de evidências e na proposta de piloto. O modelo e a política congelados foram preservados.
4. **Correções verificadas.** O AppTest falhou por selecionar o segundo rádio por posição. O Codex passou a usar o rótulo do controle. O primeiro roteiro do Chrome avançou antes de o seletor de amostra aparecer. O teste passou a esperar o controle certo e o gráfico renderizado. A inspeção da captura encontrou o `R$` sendo interpretado como Markdown matemático. O Codex escapou o cifrão e recapturou. O downloader Python recebeu HTTP 404 em pasta limpa. O Codex confirmou que o endpoint público responde com cabeçalhos explícitos e refez a aquisição e o pipeline. As correções foram do agente.
5. **Revisão técnica.** O caminho independente leu os arquivos com a biblioteca padrão. A reprodução limpa reinstalou o lockfile, baixou os CSVs sem reaproveitar o diretório bruto e chegou a partições e predições idênticas. O Codex verificou a sequência de uso no Chrome local.

A verificação teve três ciclos de correção e reteste descritos acima, no AppTest, no navegador e na reprodução limpa. [Saídas de execução](checks.txt)

## Decisões confirmadas por Leandro

- **Diagnóstico.** Testar a coleta em chamados técnicos de redes sociais e comparar os quatro canais com o mesmo protocolo antes de intervir.
- **Automação.** Avaliar primeiro em modo sombra. Mostrar sugestões ao atendente somente se a avaliação no domínio alvo sustentar o avanço, com confirmação humana da fila.
- **Impacto.** Apresentar 18 h/mês como hipótese base, 3,15 h/mês como cenário conservador e conversão em caixa de 0%.

[Protocolo de piloto](../docs/analysis.md#protocolo-de-piloto).

## Capturas reais do app local

Capturas do Chrome headless em loopback, sem texto bruto dos tickets. As telas de triagem usam o primeiro ID da seleção determinística de sugestão correta. Na revisão por prioridade crítica, foi usada a mesma entrada com a prioridade alterada para testar a guarda. As capturas mostram as telas e os resultados do protótipo.

- [Diagnóstico e distribuição por canal](screenshots/01-diagnostico.png)
- [Sugestão temática no teste reservado](screenshots/02-triagem.png)
- [Revisão humana com prioridade crítica](screenshots/03-revisao.png)
- [Qualidade e métricas por classe](screenshots/04-qualidade.png)
- [Simulação base e premissas](screenshots/05-impacto.png)
- [Diagnóstico em viewport móvel](screenshots/06-diagnostico-mobile.png)
