# Protocolo de aprovação em duas rodadas

## Objetivo

Liberar a entrega somente quando Pedro conseguir avaliá-la duas vezes, em sessões separadas, sem
explicação externa e sem bloqueador material.

## Rodada 1: descoberta

1. Abrir o protótipo em `Visão geral`.
2. Explicar em uma frase o problema resolvido.
3. Executar os casos do case e confirmar os resultados `PASS`.
4. Em `Triagem diária`, testar reincidência com cobrança e confirmar decisão humana.
5. Testar o erro conhecido de compra e confirmar que a memória foi acionada.
6. Em `Aprendizado`, localizar seis lições operacionais e a correção de compra.
7. Abrir o painel gerencial do case e identificar fatos, limitações e próxima decisão.
8. Em `Análise da operação`, usar os dados do case e validar a estrutura.
9. Em `Entregáveis`, abrir os onze documentos na ordem apresentada.
10. Registrar toda dúvida, fricção, claim confuso ou ação que exigiu ajuda externa.

Qualquer erro, ausência de evidência, dado pessoal exposto ou dúvida sobre o próximo passo bloqueia
a aprovação.

## Correção entre rodadas

Corrigir os bloqueadores observados e repetir os 66 testes automatizados. Não alterar claims ou
comportamentos sem atualizar a evidência correspondente.

## Rodada 2: confirmação

Reiniciar o aplicativo e repetir o roteiro sem consultar as anotações da primeira rodada. A
aprovação exige:

- casos do case aprovados;
- 66 de 66 testes automatizados aprovados;
- nenhum texto bruto em logs ou exportações;
- nenhuma ação externa executada;
- todos os documentos acessíveis;
- compreensão independente de onde a IA atua e onde o humano decide.

## Liberação

Somente após dois `PASS` humanos a versão recebe bundle final, commit de entrega e envio. Até lá,
o estado correto é **candidato de submissão**.
