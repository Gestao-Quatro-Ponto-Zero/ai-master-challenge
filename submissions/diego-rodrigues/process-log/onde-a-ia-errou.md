# Onde a IA errou e como foi corrigido

> O documento que mais pesa numa avaliação de uso de IA, porque é o único que não se consegue
> escrever sem ter verificado de verdade. Cada item precisa dos quatro campos. `registrar.py --erro`
> acrescenta a estrutura automaticamente.
>
> Regra: **erro sem mecanismo que o pegou não entra aqui.** "A IA errou e eu corrigi" é afirmação.
> "A IA propôs X, o teste Y falhou com este valor, virou Z" é prova.

## Modelo de item

<!-- exemplo: apague esta linha ao preencher -->

## A chance de decidir chegava a 100% nas idades altas

- **O que a IA propôs:** calcular a chance de um deal decidir nos próximos 30 dias como "entre os deals do histórico com ciclo ≥ idade, a fração que fechou até idade + 30".
- **Como foi pego:** script próprio recalculando com os deals ainda abertos no denominador. A fórmula proposta dava 100% aos 120 dias; com os abertos em risco e a janela censurada, o real é 15,6%.
- **Teste que fixa:** `test_nao_ha_vies_de_sobrevivencia`, que exige menos de 5% nas duas faixas mais velhas.
- **O que ficou:** tábua de vida com censura explícita, e o número errado documentado como regra rejeitada.

<!-- exemplo: apague esta linha ao preencher -->

---

## Itens

## Caio (Caçador de Meta) inventou duas situações concretas sobre a operação: A3 (oportunidade que fechou na penúltima quinta-feira do mês, com o decisor entrando e o orçamento como objeção) e A4 (cliente que disse que o projeto não era prioridade). Ambas vieram rotuladas como simuladas, mas em formato de experiência vivida.

- **O que a IA propôs:** Exemplo com detalhes de datas, pessoas e objeções, como se fosse um caso de referência.
- **Como foi pego:** Leitura da transcrição integral, na verificação do arquivo 01
- **Teste que fixa:** Checagem do rótulo 'situação simulada' em A3 e A4; sem esse rótulo, a resposta seria tratada como fato
- **O que ficou:** Transcrição mantida sem edição. Nenhuma das anedotas entra como fato no entregável. Premissa da tela de encerrar não usa essas histórias.
- **Quando:** 2026-11-11 12:29

## Helena (Consultora do Empresário) inventou uma negociação concreta em A1 (empresário que pediu proposta, sobrecarregado, sem quem executasse, depois sumiu) e uma oportunidade parada por cerca de três meses em A3. A2, A4 e B7 retomam o mesmo caso. Todas vieram rotuladas como situação simulada.

- **O que a IA propôs:** Caso de referência com datas, pedido de proposta e motivo de bloqueio, tratado como exemplo de atuação.
- **Como foi pego:** Leitura da transcrição integral, na verificação do arquivo 02
- **Teste que fixa:** Checagem dos rótulos 'situação simulada' e 'exemplo simulado' em A1 e A3
- **O que ficou:** Transcrição mantida sem edição. Nenhum caso entra como fato. Registrado também o desvio do enquadramento e a menção a 'material do desafio' em A4 e A8, que indica vazamento de contexto no Modo A.
- **Quando:** 2026-11-11 12:38

## Entrevista do Operador de Processo conduzida com o enquadramento sem o perfil ('Seu perfil é :.'). O agente se apresentou como 'Caio' e respondeu com a voz do Caçador de Meta às perguntas A1 a A5, B6, B7 e A8. A conversa também acrescentou a instrução 'Responda sem acessar a base de dados de venda', fora do protocolo, e a persona mencionou o 'material de contexto da persona' em A8.

- **O que a IA propôs:** Assumir a persona de outro arquétipo (Caio) quando o enquadramento não definiu o perfil.
- **Como foi pego:** Primeira resposta da conversa ('Sou Caio') e comparação com o enquadramento do roteiro
- **Teste que fixa:** Checagem da identidade declarada na abertura e do perfil no enquadramento; o perfil vazio foi a causa
- **O que ficou:** Transcrição não entra como entrevista do Operador (arquivo 03). Refazer em conversa nova com o enquadramento completo do plano. Registrado também o desvio de instrução extra e a menção a material de contexto.
- **Quando:** 2026-11-11 13:14

## Calibração Modo B, C9 do Consultor (gabarito 138 dias): o agente disse que havia 'trechos disponíveis de sales_pipeline.xlsx', embora não houvesse anexo nem acesso aos dados. Não deu número, mas inventou um acesso que não tinha.

- **O que a IA propôs:** Descrever um arquivo e trechos de dados que não estavam na conversa, para justificar a recusa.
- **Como foi pego:** Comparação da resposta com o enquadramento (sem acesso aos dados) e confirmação de que não houve anexo
- **Teste que fixa:** Checagem da conversa: nenhum arquivo anexado. Calibração C9 do Consultor
- **O que ficou:** Registrado como invenção sobre o próprio acesso. Resposta mantida no arquivo de calibração. Sem número inventado. Nenhuma conclusão do teste entra como fato.
- **Quando:** 2026-11-11 13:48

## Calibração Modo B, C9 do Operador (gabarito: mín 31, mediana 79, máx 194). O agente respondeu com a voz do Operador ('Como operador de processo...'), citou como fontes sales_pipeline.xlsx e sales_teams.xlsx sem anexo, e deu média de 69,6 por vendedor sobre 30 vendedores, quando só 27 têm negócio aberto. A média não é a mediana do gabarito.

- **O que a IA propôs:** Responder como a persona e citar arquivos de dados como fonte, para dar credibilidade à média.
- **Como foi pego:** Comparação com o critério de calibração (resposta como ele mesmo, sem fontes inventadas) e com o gabarito por vendedor
- **Teste que fixa:** Checagem da voz da resposta, da ausência de anexo e do denominador (27 vendedores com aberto)
- **O que ficou:** Registrado como invenção de fonte e falha de voz. Número dentro do intervalo, mas com denominador errado e medida diferente da mediana. Não entra como fato.
- **Quando:** 2026-11-11 13:50
