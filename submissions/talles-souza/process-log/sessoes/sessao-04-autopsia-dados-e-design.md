# Sessão 04 — Autópsia do negócio, camada de dados e o sistema visual

**Data:** 2026-10-22 · **Ferramentas:** Claude Code (Claude Opus 5.5) como coordenador, subagentes da esteira de diagnóstico, worker do Orca · **Etapa:** f1 da esteira; início da E3 (só a parte mecânica)

## Problema

Antes de decidir como qualificar deals, entender o negócio da empresa do enunciado: onde ela sangra tempo, o que já tentou, qual é a dor que destrava as outras. Em paralelo, adiantar o que não depende dessa decisão: a camada de dados e o sistema visual.

**Critério de aceite:** a Autópsia aprovada pelo revisor, falando só do negócio e com cada afirmação com fonte; a camada de dados com testes de contagem passando contra o dataset real; o sistema visual conferido contra a spec do worker.

## O que foi feito, em ordem

1. **Autópsia (f1) com os formulários do meu framework de diagnóstico de negócio** (história do negócio, 7 pilares, cemitério de tentativas, dor principal, scorecard de maturidade). Quem respondeu foi a persona da empresa do enunciado (a Head de RevOps, que descreve a operação; a dor diagnosticada é a do vendedor, usuário da ferramenta), por roleplay, **só com o que o brief e o dataset sustentam**. Onde não havia dado, o campo ficou "sem dado" (4 dos 7 pilares) e a fase seguiu. Duas medições novas, cada uma com o chute gravado em arquivo antes de rodar (acertou 2 de 3).
2. **Corrigi o enquadramento no meio da fase.** O meu primeiro prompt para a Autópsia pedia a dor que a solução atacaria: a solução entrou no diagnóstico. Eu mesmo apontei: *"pq tu tá qualificando já? a gente tá olhando pro negócio ainda"*. A dor, a raiz e o grande dominó foram reescritos em termos da operação, e tudo que era solução foi para uma seção separada, "Levado para a próxima fase (não é diagnóstico)".
3. **Revisor adversarial, 3 voltas.** v1: 6 faltas (ex.: "fecharam 7% e 0%" quando o número era de ganho; fechamento real 14,1% e 1,0%; "forecast" citado como fato sem existir no brief nem no dataset). v2 e v3: trechos que ainda falavam de score, pela régua de "só o negócio". Aceitei a v3 com uma troca de texto no fechamento.
4. **O que a Autópsia diz:** sem critério comum para decidir onde pôr o esforço e sem rotina que encerre o que parou, o time gasta o tempo no que não anda e deixa esfriar o que ainda pode fechar. Raiz: a operação não tem critério comum de qualificação nem regra de encerramento; a decisão de foco fica com cada vendedor e o pipeline só acumula.
5. **Data de referência.** A idade dos deals é contada até 31/12/2017, o último fechamento do dataset. **Foi inferência, não orientação do desafio** (o brief não fixa data); contar até hoje daria ~9 anos para todos. Decidi manter, calculada do próprio dado e declarada como premissa.
6. **BANT, MEDDIC e SPICED** ficam como candidatos a método dentro da lógica de qualificação, avaliados contra os campos que o dataset tem, e não como uma etapa do processo.
7. **Camada de dados (E3, parte mecânica, sem regra de score).** `solution/data/preparar_dados.py` junta as 4 tabelas, normaliza "GTXPro"→"GTX Pro" e "technolgy"→"technology", calcula idade (abertos) e duração (fechados) e marca as lacunas. `test_preparar_dados.py`: **9 de 9 testes passando** contra o dataset real (8.800 deals sem duplicata, estágios, 2.089 abertos, todo produto casando com o catálogo, lacunas 1.088 + 337 sem conta e 500 sem data, idade dos abertos de 9 a 423 dias, duração máxima de 138).
8. **Sistema visual do G4.** O worker do Orca visitou 5 páginas públicas e entregou um DESIGN.md (27 cores, 4 famílias tipográficas com as pagas trocadas por equivalentes livres, 18 componentes, 19 efeitos de movimento com duração, easing, gatilho e origem), tokens em CSS e JSON (114 = 114) e uma página de demonstração. **Conferi o aceite antes de aceitar o "terminei":** 0 erros no console, 4 animações rodando, sem rolagem horizontal em 390 px, nenhum logo, foto ou fonte paga fora do material bruto, nenhum navegador órfão. O material fica fora deste repositório; a aplicação vai usar os tokens e os padrões de movimento, sem se apresentar como produto oficial.

## Onde desconfiei e conferi

- **Eu mesmo enviesei o diagnóstico** ao pôr a solução no prompt. Corrigido na mesma fase; a regra agora é que a fase de diagnóstico não recebe a solução.
- **O worker do design ficou ~1 h parado** sem erro visível. O orquestrador marcava a liveness como "não verificável", o que não prova que o processo morreu; mandei uma mensagem pelo canal da orquestração em vez de matar e relançar, e ele retomou.
- **"Terminei" não é aceite.** A contagem de tokens parecia não bater (114 × 343); a diferença era estrutura do JSON (3 entradas de metadados). Só depois de conferir os 114 dos dois lados, abrir a demo e checar o console, o worker foi liberado.

## Horas

O tempo declarado é só o tempo ativo da sessão principal, medido no fim por `process-log/scripts/tempo_ativo.mjs` (ver o README). A interface do Lead Scorer ainda não foi construída.

## Próximo passo

f2 (Raio-X): o que a IA pode e não pode fazer aqui, ideação de oportunidades para a dor da Autópsia, pré-mortem e priorização. A lógica de qualificação (e a escolha entre BANT, MEDDIC e SPICED) sai daí.
