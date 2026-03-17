# Submissão — [Seu Nome] — Challenge [Otimização de Atendimento e SLA]

## Sobre mim

- **Nome:** [Mateus Chiqueto]
- **LinkedIn:** [https://www.linkedin.com/in/mateuschiqueto/]
- **Challenge escolhido:** Challenge 002 — Redesign de Suporte

---

## Executive Summary

Foi realizada uma análise dos gargalos operacionais e reestruturação do sistema de suporte com inteligência artificial. Identificou-se que problemas simples congestionam canais complexos e geram alto tempo de espera em produtos específicos. A recomendação principal é dividir o fluxo: IA para triagem e casos simples, e humanos para situações críticas, visando uma economia operacional estimada em mais de R$ 60 mil.

---

## Solução

### Abordagem

Primeiramente iniciamos entendendo o problema, ficou claro que precisamos aumentar a nota de CX. Depois identificamos um SLA oficial baseado em clusters entre os casos com maiores notas, isso para termos noção de quais tickets não foram bem atendidos. Segundamente a análise de dados históricos com scripts Python e IA para processamento numérico para ter noção dos gargalos e descobrir o problema. Descobrimos que o problema é que o chat precisa ser melhor utilizado e que os tickets devem ser direcionados a ele. Realizamos um plano de mudança de FAQ. Nesse redesign de FAQ deixamos o chat como principal e ele com um sistema de classificação de texto indica se o ticket irá para chatbot ou para humano.

### Resultados / Findings

* **SLA Definido:** Oficial de 11 horas.
* **Gargalos:** Tickets mais simples aumentam a fila dificultado a resolução de outros tickets simples. Atendimento por telefone e email com notas baixas.
* **Desperdício:** Desperdício de cerca de R$24k de trabalho que poderia ter sido em algo mais complicado (quando acima do SLA).
* **Finanças:** Custo de IA por ticket junto a economia de tempo gera R$ 63258.95 de economia total do que já é gasto.
* **Protótipo Inicial:** Classificador utilizando TF-IDF + Regressão Logística para direcionar tickets para chatbot ou para humano.

### Recomendações

* **Parte 1: Implementar Chatbot:** Focar em Instalação, Setup, Redes, Consultoria (recomendações de produtos), manuais. O chatbot será um agente com diversas tools para ajudar o usuário, porém transferir para humano quando necessário. Como foi criado pelo Gemini não foi necessário utilizar RAG ou qualquer outro método de vetorização ou treinamento de LLM, somente é necessário sinalizar ao GEM do Gemini os dois csvs que contém cada ticket e para onde foi direcionado, nisso o bot conseguirá identificar rapidamente qual a categoria e com quais tipos de problema está lidando.
* **Parte 2: Reorganizar FAQ:** FAQ baseado no chatbot. O chatbot irá guiar user para resolver por IA ou por humano. O chatbot irá também recomendar novos produtos ao usuário. O chatbot deve ser um Agente com diversas tools para cada problema a ser resolvido.
* **Parte 3: Integração:** Conectar o bot ao CRM da empresa e a uma API com a base de dados de produtos para consultas de manuais e vendas cruzadas. Isso é necessário para abrir tickets com os consultores humanos.
* **Parte 3: Integração Classificador x CHatbot:** Você pode se perguntar, para que um classificador se já teremos um chatbot de LLM muito potente. O problema está que se em cada abertura de tickets rodarmos uma conversa na IA teremos um gasto grande e desperdiçado, por isso é importante uma triagem com um classificador simples para que nem todo ticket gere tokens na IA. Logo, precisamos integrar o classificador com o chatbot e todo o sistema de transferência do CRM.

### Limitações

Devido a não ter acesso ao CRM utilizado ou conta business da openai não foi possível implementar um chatbot.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Gemini 3.5 Pro | Processamento do csv dos tickets e criação do agente protótipo |
| Python (Scripts - Utilizado ipynb por fins didáticos) | Análise dos dados, classificador, cálculos de viabilidade econômica.|

### Workflow

1. Entendimento do problema.
2. Cálculo do melhor SLA.
3. Análise dos dados para encontrar o problema.
4. Criação de novo flow do faq.
5. Implementação do classficador.
6. Restante das implementações posteriormente com mais informações.

### Onde a IA errou e como corrigi

Nenhum "erro", a IA somente nos dá ideias, basta aprovarmos ou não.

### O que eu adicionei que a IA sozinha não faria

As ideias foram de meu raciocínio, utilizei a IA para escrever os códigos, por conta de otimizar tempo e para analisar os dados e me entregar insights. Porém, a noção de negócio precisa ser minha. Utilizo a IA como um ajudante.

---

## Evidências

- [x] Chat exports: Análise dos Dados.pdf, Checagem de categorias dos tickets.pdf, Custos.pdf, Data prep.pdf, Geração da imagem.pdf, Treinamento.pdf
- [x] Outro: Fluxo.png, heatmap_volume_notas.png, relatorio_gargalo_custos.csv
- [x] Outro: Scripts Python (`Análise_dos_Dados.py`, `Classificador.py`, `Custos.py`, `Preparação_dos_dados.py`)

---
