# Fase 0 — Escolha do desafio e exploração inicial

**Ferramenta:** Claude (app, sessão com acesso a ferramentas), com os modelos Claude Sonnet 5.5 e, a partir do desenho dos blocos, Claude Opus 5.5.
**Data:** 25/10/2026
**Duração aproximada:** 1h

## 1. Leitura do repositório e escolha do desafio
- **Tentativa de leitura via web falhou:** o GitHub bloqueia acesso automatizado à página. O repositório foi clonado via git.
- O Claude leu os 4 desafios e estimou solução e esforço de cada um:

  | Desafio | Esforço | Risco |
  |---|---|---|
  | 001 | médio | correlação ≠ causa |
  | 002 | alto (3 entregas) | datasets não se conectam |
  | 003 | médio | diferenciação |
  | 004 | médio | dataset sintético, efeitos fracos |

- **Minha decisão:** 003. O escopo é fechado, o entregável é verificável e a explicabilidade e validação conversam com meu histórico em governança de IA.

## 2. Obtenção dos dados
- O conector MCP do Kaggle listou os arquivos e gerou links de download, mas a rede do ambiente bloqueou o domínio (403 no proxy).
- **Decisão:** não contornar o bloqueio. Usei os CSVs que eu já tinha baixado no meu computador.

## 3. Exploração (scripts em `scripts/eda.py` e `scripts/eda2.py`)
Achados principais:
- 8.800 deals; win rate dos fechados de 63,2%.
- **Integridade:** "GTXPro" (pipeline) ≠ "GTX Pro" (catálogo). Sem corrigir, 1.480 deals somem no join. Também há o setor "technolgy".
- 1.425 deals sem conta, todos abertos; Prospecting sem datas; 5 vendedores sem deals.
- **Nenhum atributo prevê vitória:** produto, setor, região, manager e porte ficam entre 60% e 65% (qui-quadrado: produto p=0,37, vendedor p=0,26; AUC das numéricas ≈ 0,50).
- O único sinal é o ciclo: os perdidos perdem rápido.
- 81% dos Engaging estão parados há mais tempo que o maior ciclo já observado (138 dias).

## 4. Onde a IA precisou de correção ou ressalva
- **Métrica otimista:** o primeiro cálculo de poder preditivo por categoria usou target encoding dentro da própria amostra. Foi marcado como inflado, e a decisão foi exigir backtest temporal.
- **Win rate de 82% no 2017-Q1:** levantado como possível artefato de recorte, não como insight. Fica para investigar no bloco 2.
- **O plano inicial assumia um score por atributos** (win rate por produto/setor). Os dados derrubaram essa premissa, e o plano pivotou para o frescor.

## 5. Validação da hipótese de frescor (`scripts/snapshot.py`)
- **Pergunta:** a idade de um deal aberto numa data passada prevê o que aconteceu com ele depois?
- **Resposta, com corte em 30/09/2017:** até 30 dias de idade, 50% foram ganhos; de 31 a 60 dias, 34%; de 61 a 90 dias, 7%; acima de 90 dias, 0%. O corte em 30/06/2017 mostra o mesmo padrão.
- **Ressalva:** nenhum deal fechado passou de 138 dias, em nenhuma coorte. É provavelmente um artefato do gerador sintético, então não vou usar como regra fixa.

## 6. Decisões de desenho
- Projeto dividido em blocos: escopo → curadoria → scoring e validação → produto → documentação → revisão independente → PR.
- **Ferramenta de entrega:** motor em Python + página estática no GitHub Pages, **não Streamlit**. Motivos: Streamlit é o default do baseline; a página estática roda sem instalação (o avaliador clica e usa); e separar a lógica da interface atende ao critério de código mantível.
- **Diferenciais definidos:** a tese do frescor validada; backtest visível na interface; a lista "Limpe" (~US$3,2 mi de pipeline inflado); e um model card, que vem do meu ângulo de governança.
- **O vendedor não entra como fator do score:** a diferença entre vendedores é compatível com ruído, e usá-la penalizaria pessoas injustamente.
