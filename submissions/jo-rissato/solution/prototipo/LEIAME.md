# Protótipo: conversa, roteador, painel e dashboard

Implementa as etapas 2, 5 e 6 do fluxo aprovado, com a revisão da rodada 59, (`docs/fluxo-proposto.md`) sobre o classificador medido em
`docs/relatorio-classificador.md`, e mostra a linha de base do Dataset 1 ao lado das decisões do roteador.

## Como rodar

```bash
pip install pandas scikit-learn joblib streamlit requests pytest
python modelo.py        # treina com os 80% de treino do Dataset 2 (mesma separação do relatório)
python lote.py          # roteia os 9.568 tickets reais do teste e imprime o resumo
pytest -q tests         # regras, dados pessoais e conversa com a IA simulada
python bateria_ia.py ../../docs/bateria.md --canal e-mail   # bateria de IA real num canal (precisa de chave)
streamlit run app.py    # página com Conversa, Painel do atendente e Dashboard
```

Os CSVs do Kaggle ficam em `dados/support/` e `dados/it/` na raiz do repositório, ou nos caminhos das variáveis
`DATASET1` e `DATASET2`.

## IA conversacional

- Com chave: copie `env.exemplo` para `.env` (ou aponte `ARQUIVO_ENV` para outro arquivo) e preencha
  `DEEPSEEK_API_KEY`. A DeepSeek conduz o atendimento em português e, a cada mensagem, devolve um resumo do
  pedido, diz se é reembolso ou cancelamento, se o cliente desistiu e se ele confirmou que resolveu.
- Sem chave: a página roda com mensagens fixas. Reembolso e cancelamento seguem iguais; qualquer outro caso passa
  para uma pessoa, porque sem IA não há quem conduza o suporte.
- A chave nunca entra no git (`.gitignore` local).

## Conversa (`conversa.py`)

Regra do Jó (process log, rodada 59): a IA atende até resolver; só reembolso e cancelamento passam para o time.

1. A assistente pergunta como chamar o cliente e usa o nome com parcimônia (no máximo uma vez a cada três respostas).
2. Suporte: perguntas específicas, uma por vez (qual sistema ou aparelho, onde exatamente, qual mensagem aparece
   na tela), sem frases de cortesia vazias; depois, a solução em passos numerados, no máximo 3 por mensagem, com
   pedido de confirmação. A conversa só fecha quando o cliente confirma que resolveu ou desiste.
3. Reembolso e cancelamento: o código pede o detalhe do pedido (reembolso: o pedido exato; cancelamento: o que
   cancelar; cobrança em dobro ou indevida: o valor e o pedido que gerou a cobrança) e depois CPF usado na compra,
   telefone com DDD e e-mail, validados no código (`dados_pessoais.py`). Dado inválido é pedido de novo uma vez; o
   cliente pode recusar e o atendimento segue.
4. Nome, CPF, telefone e e-mail nunca vão para a IA externa: o nome vira `[NOME]`, números e e-mails digitados viram
   marcadores e a coleta usa mensagens fixas. No log (`saida/conversas.jsonl`) o contato fica mascarado.
5. Cada mensagem atualiza a chamada no log, então o painel mostra também as conversas em andamento.
6. Defeito de aparelho (pedido do Jó, 2026-11-12): depois dos passos de verificação, o código pede o CPF usado na
   compra e busca o cadastro. Achou: pergunta se o cliente está no endereço do cadastro (mostra só bairro e cidade).
   Sim: usa o CEP do cadastro. Não, ou CPF sem cadastro: pede o CEP de onde ele está. Indica a assistência autorizada
   mais perto desse CEP (`assistencias.py`), com o endereço e o número do atendimento. CPF, CEP e endereço não passam
   pela IA externa; no log o CEP fica com os 3 últimos dígitos mascarados.

7. Assunto incerto (Jó, 2026-11-16): abaixo de 0,8 de confiança, a IA só faz perguntas de esclarecimento. Se esgotar 3
   perguntas, ou se já fosse dar a solução, a resposta é descartada, o contato é coletado e uma pessoa assume.
8. Comando restrito (Jó, 2026-11-16): pedido para mudar ou contornar política, excluir site ou domínio, ou mexer na
   infraestrutura (porta, firewall, servidor, DNS, VPN, acesso de administrador a servidor) é travado por regra antes
   de ir à IA externa, com o sinal da IA como segunda camada. Nada é executado, alterado ou repassado; a chamada vai
   ao departamento especializado com etiqueta ATENÇÃO.
9. Posicionamento: toda chamada que passa para uma pessoa fica "Aguardando posicionamento" no painel, com o tempo de
   espera, e só fecha quando alguém registra o posicionamento do caso (mínimo de 20 caracteres).

## Canais

A conversa roda em chat, e-mail, rede social (com a rede de entrada: Instagram, Facebook, X, LinkedIn, TikTok) ou
telefone. As regras são as mesmas; muda a forma: e-mail com saudação, assinatura e até 5 passos; telefone com fala
curta, passos falados ("Passo 1: ...") e transcrição no painel com o resultado da ligação; rede social curta, com a
etiqueta da rede. Na aba Conversa, o canal é escolhido antes da primeira mensagem.

## Versão em apresentação

`VERSAO_ROBO` (config.py) marca as regras atuais. Chamadas de versões anteriores ficam em `saida/conversas.jsonl` e no
process log, mas não aparecem no painel nem no dashboard. A bateria conta tokens em `saida/uso-ia-bateria.json`,
separado do teto diário da página pública.

## Regras do roteador (`roteador.py`)

| Situação | Destino |
|---|---|
| Comando restrito (política, exclusão de site, infraestrutura) | Departamento especializado, etiqueta ATENÇÃO, sem executar nem alterar |
| Confiança abaixo de 0,8 depois de 3 perguntas, ou quando a IA já daria a solução | Uma pessoa assume e dá o posicionamento |
| Reembolso, cancelamento, cobrança em dobro ou indevida | Detalhe do pedido, contato e pessoa decide e executa |
| Defeito de aparelho (bateria, aquecimento, carregamento, não liga, peça, tela) ou garantia, depois de ao menos um passo de verificação | Assistência técnica autorizada da empresa (rodada 60), mesmo que o sintoma tenha aliviado |
| Cliente confirma que resolveu | Resolvida pela IA |
| Cliente desiste | Conversa encerrada sem encaminhar |
| IA fora do ar ou sem chave | Coleta de contato e uma pessoa assume |
| Qualquer outro caso | A IA segue atendendo |

A trava de reembolso e cancelamento é por regra em português e inglês, além do sinal da IA, porque o texto do
Dataset 1 não prevê o tipo do ticket (19,7% de acerto contra 20,7% da linha de base). O padrão de cancelamento
pede o objeto ("cancelar a assinatura"), porque "cliquei em cancelar" é comum numa conversa de suporte.

O classificador continua marcando o assunto de cada chamada (painel e dashboard). O limite 0,8 (rodada 45) vale
para a simulação em lote do Dataset 2, que mede o classificador.

## Resultado no teste real (`python lote.py`)

9.568 tickets nunca vistos no treino: a IA roteia 68,4% com 96,4% de acerto; 31,6% vão para triagem humana.

## Limites

- O classificador é de TI interna (8 categorias do Dataset 2). As filas reais dependem do levantamento do processo.
- A IA só pode dar passos da ajuda oficial de sistemas e aparelhos conhecidos. Procedimento interno da empresa
  (sistema próprio, política, prazo) ela não sabe e não pode inventar: isso depende da base de conhecimento do
  cliente real, que não existe nos datasets.
- Não lê imagem: a DeepSeek não lê print, e print pode trazer dado pessoal, que pela regra de 2026-11-03 só vai para
  IA local no Brasil. A IA pede o texto que aparece na tela.
- A conversa não foi medida com clientes reais. O ganho de perguntar está estimado por um teste substituto
  (acerto de 78,2% com 10 palavras contra 87,0% com o texto inteiro).

## Placeholders pendentes

- Departamentos especializados (`roteador.py`, 2026-11-16): Segurança da informação, Web e sistemas e Infraestrutura
  são nomes de exemplo; a setorização real do atendimento não está nos dados (lacuna 2).
- Prazo para o posicionamento: a definir com o diretor; o painel mostra há quanto tempo cada chamada espera.
- Rede de assistência técnica e cadastro de clientes (`assistencias.py`, 2026-11-12): os datasets não trazem
  endereço de cliente nem de assistência. As 9 assistências e os 10 cadastros são DE EXEMPLO, fictícios, e os nomes
  das assistências levam "(exemplo)". Na operação real, entram o cadastro de clientes e a rede autorizada da empresa.
  "Mais perto" é o maior começo de CEP igual (região postal), não distância em quilômetros.
  CPFs de demonstração para testar o caminho do cadastro: 100.000.001-08 (Campinas), 200.000.002-99 (São Paulo),
  300.000.003-88 (Rio de Janeiro), 400.000.004-77 (Belo Horizonte), 500.000.005-66 (Curitiba). Qualquer outro CPF
  válido cai no pedido de CEP.
