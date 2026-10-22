# 00 · Preparação do terreno

> **Data:** 22/10/2026
> **Ferramenta:** Claude Code (Opus 5.5), no app desktop
> **Duração:** cerca de 1h30
> **Resultado:** case escolhido, concorrência mapeada, critérios do avaliador entendidos, repositório e dados prontos.

Antes de abrir qualquer dado, eu quis entender três coisas. O que a vaga pede de verdade. O que as outras pessoas já entregaram. E o que o G4 elogia e o que derruba. Só depois disso faz sentido decidir o que construir.

---

## 1. O que a vaga pede

Li a descrição da vaga de AI Master e o repositório do desafio inteiro: README, guia de submissão, CONTRIBUTING, template e os 4 cases.

O que ficou claro:

- O cargo é de quem entrega sozinho o que antes pedia um time. Do diagnóstico até medir o resultado.
- O desafio avalia **processo**, não só entrega. "A solução sozinha não basta."
- Eles já rodaram cada case no Claude, no GPT e no Gemini. Uma entrega parecida com o que a IA faz sozinha não passa.
- A entrega é por PR. Fork, branch `submission/nome`, tudo dentro de `submissions/nome/`.

---

## 2. Por que o case 002

| Case | O que pede | PRs até hoje |
|---|---|---|
| 001 · Churn | Relatório de causa raiz | 41 |
| **002 · Suporte** | **Diagnóstico, o que automatizar e o que não, protótipo** | **45** |
| 003 · Lead Scorer | Ferramenta pro vendedor | 88 |
| 004 · Social Media | Estratégia com dados | 16 |

*18 PRs não dizem o case no título. Contagem pelo título de cada PR.*

Escolhi o 002 porque é o mais próximo do que eu faço hoje. Eu opero atendimento com IA em escritórios de contabilidade: triagem de demanda, resposta ao cliente do escritório, decidir o que a IA responde e o que fica com uma pessoa. O case cobra exatamente as três coisas da vaga juntas: análise, desenho de processo e construção.

O 003 seria o caminho óbvio pra mostrar que sei construir. Mas é o case com mais entregas, e um painel de pontuação tende a ficar parecido com o que a IA faz sozinha.

---

## 3. O que já foi entregue no case 002

Pedi pro Claude Code baixar todos os PRs do case 002 e extrair o que cada um entregou. Li os resumos executivos de todos e abri os demos que ainda estão no ar.

**48 PRs** tocam o case 002. A conta por palavra-chave mostra o padrão:

| O que aparece na entrega | PRs |
|---|---|
| Percebeu que o Dataset 1 é sintético (tempo invertido, satisfação aleatória) | 42 de 48 |
| Treinou um classificador no Dataset 2 | 43 de 48 |
| Usou trava de confiança pra decidir o que vai sozinho | 42 de 48 |
| Reembolso e cancelamento sempre com uma pessoa | 28 de 48 |
| Comparou LLM contra classificador | 14 de 48 |
| Publicou demo online | 15 de 48 |
| Mandou link de vídeo ou Drive | 10 de 48 |

*Contagem aproximada, por palavra-chave no texto e no código de cada PR. Script: [`00-preparacao/levantamento_prs.py`](00-preparacao/levantamento_prs.py).*

### O caminho que quase todo mundo fez

1. Audita o Dataset 1 e descobre que ele é gerado. Em 49,3% dos tickets fechados a resolução vem antes da primeira resposta. A nota de satisfação é aleatória.
2. Diz que não dá pra apontar gargalo com esse dado.
3. Treina um classificador simples nos 48 mil tickets de TI do Dataset 2. Acerta por volta de 86%.
4. Põe uma trava de confiança. A máquina roteia de 50% a 75% sozinha, com uns 96% de acerto. O resto vai pra uma pessoa.
5. Reembolso e cancelamento ficam fora da IA.
6. Recomenda medir a operação antes de automatizar, e testar em modo sombra.

Em março isso era uma sacada. Hoje é o padrão. **Repetir esse caminho é entregar o que outras 40 pessoas já entregaram.**

### Os demos que abri

| PR | O que é | Como está hoje |
|---|---|---|
| #43 | Painel com simulador e chat de atendimento | Abre, mas o chat dá erro ao criar conversa |
| #68 | Central de ajuda do próprio G4, com busca na base antes de abrir ticket | Funciona. Testei uma dúvida de acesso e ele sugeriu resposta com 50% de confiança |
| #126 | Triagem que roda no navegador, mostra fila, motivo e palavras que pesaram | Funciona. Ticket de cancelamento foi direto pra pessoa, pela regra |
| #133 | Painel de diagnóstico com intervalo de confiança em todo número | Funciona |
| #158 | Narrativa da auditoria + chat em que a IA pede informação e o atendente aprova | Funciona. É o mais completo que vi |
| #178 | Caixa de entrada estilo help desk com agente | Pede login, não entrei |

---

## 4. O que o avaliador do G4 valoriza

O avaliador comentou em 19 PRs do case 002, alguns com nota. Os comentários são públicos e dizem com clareza o que pesa.

**O que derrubou ou atrasou candidato:**

- **Process log só em texto.** Um candidato aprovado com 7,8 teve a aprovação revista dois dias depois. O motivo foi falta de evidência visual do processo.
- **Não dar pra ver o que foi decisão da pessoa e o que foi da IA.** A entrega mais completa tecnicamente do case levou 6,5 de primeira, porque "a estratégia de análise foi gerada pela IA antes de qualquer exploração independente dos dados".
- **Número sem código.** Acurácia citada no README sem o script de treino no repositório.
- **ROI sem premissa.** Economia mensal sem custo por hora, taxa ou volume explicados.
- **Código fora do repositório**, ou só um zip.
- **Tudo num commit só.** Dificulta ver a evolução.

**O que tirou nota alta (9,0 e "Excepcional"):**

- Auditar os dados antes de qualquer análise.
- Trava de confiança com limite tirado dos dados, não chutado.
- Um arquivo dizendo o que não automatizar e por quê.
- Lista dos erros da IA com a correção.
- Business case como fórmula com as premissas declaradas, sem inventar custo.
- Testes automatizados.

**Um alerta:** o último comentário do avaliador é de 03/08/2026. 29 PRs do case 002 foram abertos depois disso e nenhum tem comentário. Vou confirmar com o recrutamento se o desafio ainda está sendo avaliado pelo GitHub.

---

## 5. Onde ainda tem espaço

Ninguém trouxe uma operação de suporte real pra contrastar com um dataset de brinquedo. E quase todo mundo parou na triagem: classificar e mandar pra fila certa.

O que quase ninguém mediu é a **resposta**. Todo mundo provou que o LLM classifica mal. Quase ninguém testou se ele responde bem e com segurança quando tem trava: se inventa prazo, promete reembolso ou fala o que não pode.

Isso ainda é hipótese. A direção da entrega eu decido na próxima etapa, depois de olhar os dados com os meus olhos.

**O que não vou fazer:** copiar código, número ou estrutura de nenhuma entrega. Do levantamento eu levo só o entendimento do que já existe e do que o avaliador cobra.

---

## 6. Terreno montado

| Item | Onde |
|---|---|
| Fork | [Pauloviniciusd/ai-master-challenge](https://github.com/Pauloviniciusd/ai-master-challenge) |
| Branch | `submission/vinicius-alves` |
| Pasta | `submissions/vinicius-alves/` com `solution/`, `process-log/`, `docs/` e `data/` |

**Uma pegadinha:** o `.gitignore` do repositório ignora a pasta `submissions/`. Um `git add` normal não pega nada e o PR sobe vazio. Vou usar `git add -f` só na minha pasta, sem mexer no `.gitignore`, porque a regra é não alterar nada fora da própria pasta.

**Dados** (baixados do Kaggle, não vão pro repositório):

| Dataset | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
| D1 · Customer Support Tickets (suraj520) | `customer_support_tickets.csv` | 3,9 MB | `b06a9cde…bf8bea` |
| D2 · IT Service Ticket Classification (adisongoh) | `all_tickets_processed_improved_v3.csv` | 14,6 MB | `044fdace…b9dd4d4` |

Pra baixar:

```bash
cd submissions/vinicius-alves/data
curl -L -o d1.zip https://www.kaggle.com/api/v1/datasets/download/suraj520/customer-support-ticket-dataset
curl -L -o d2.zip https://www.kaggle.com/api/v1/datasets/download/adisongoh/it-service-ticket-classification-dataset
unzip d1.zip -d d1 && unzip d2.zip -d d2
```

---

## 7. Como vou trabalhar daqui pra frente

1. **Eu leio o problema primeiro.** Antes da IA rodar qualquer coisa nos dados, escrevo a minha leitura.
2. **Etapa por etapa, com aprovação.** A IA propõe, eu aprovo ou mudo, e só então ela executa.
3. **Decisões registradas na hora**, em `decisoes.md`: o que a IA sugeriu, o que eu decidi e por quê.
4. **Erros da IA registrados** em `erros-da-ia.md`, com como percebi e como corrigi.
5. **Um commit por etapa.**
6. **Todo número tem o script que gera ele.**
7. **Nada de dado de cliente.** A experiência com escritórios entra contada, nunca como dado.
8. **Entre 4 e 6 horas.** Inteligência no uso do tempo, não quantidade de horas.

---

## Quem fez o quê nesta etapa

| Eu | Claude Code |
|---|---|
| Decidi me candidatar e trouxe a vaga e o repositório | Leu a vaga e o repositório e resumiu |
| Pedi pra estudar o que já foi entregue antes de começar | Baixou os 208 PRs, separou os 48 do case 002 e extraiu os resumos |
| Perguntei como o process log chega no G4 | Achou e organizou os comentários públicos do avaliador |
| Pedi pra abrir os demos e ver cada um funcionando | Abriu 6 demos no navegador e testou um caso em cada |
| Escolhi o case 002 | Sugeriu o 002 com base no meu histórico e na concorrência |
| Defini que vou mostrar um sistema funcionando, não só documento | Achou a pegadinha do `.gitignore` |
| Defini as regras de trabalho e que esta etapa entra no processo | Fez o fork, a branch, as pastas e baixou os dados |
