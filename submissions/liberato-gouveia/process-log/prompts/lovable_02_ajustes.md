# Prompt 02 para o Lovable: ajustes depois da revisão da mensagem 1

> **Enviado pelo Claude em 04/11/2026** como a 2ª das 4 mensagens autorizadas pelo Liberato (Registro 10). O texto enviado é exatamente o que está depois da linha `---`.
> Motivo: (1) o agente do Lovable apontou que a chance mostrada diferia em 1 ponto do "porquê" (o Claude confirmou: 7 de 288 deals; a correção foi feita no motor, com o campo `chance_texto`); (2) o Claude viu, ao revisar o código, que o cartão exibia "#ordem_na_lista", que é a posição na empresa inteira e confunde quando se filtra por vendedor; (3) o motor passou a ter 13 testes.

---

Faça só estes 3 ajustes e não altere mais nada:

1. **Chance exibida.** O JSON agora traz o campo `chance_texto`, um texto pronto como "39%" ou "menos de 1%". Inclua `chance_texto: string | null` no tipo `Deal`. Na aba Foco, mostre "Chance: {chance_texto}" e **remova o cálculo e o arredondamento feitos a partir de `chance`**. Assim, a chance da tela fica idêntica à citada no texto do porquê.
2. **Posição no cartão.** Troque "#{ordem_na_lista}" pela posição do deal dentro da lista do filtro atual (1º, 2º, 3º…), mantendo a mesma ordem. A posição é contada antes da busca, para que buscar um deal mostre a posição real dele. Assim, ao filtrar por um vendedor, o primeiro deal dele aparece como 1º. Continue mostrando o ID do deal.
3. Na nota final da aba "Como a nota funciona", troque "12 testes automáticos" por "13 testes automáticos".
