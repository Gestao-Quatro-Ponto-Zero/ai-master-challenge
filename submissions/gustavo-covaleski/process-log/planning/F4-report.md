# F4 — Report (Política e fluxo)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

## 1. O que foi feito

1. Li o portão F3 no process log: clássico com 3 faixas, LLM fora do caminho de decisão, *e*_Q2 = 3,82%.
2. `solution/f4_politica.py`:
   - métricas por categoria **prevista** no holdout por grupo;
   - regra por categoria (LI de Wilson da precisão na faixa IA decide contra 1 − *e*_inf = 0,9680 e 1 − *e*_sup = 0,9545);
   - cobertura depois da regra;
   - exemplos sorteados com seed 42: os ids ficam no repositório e os textos em `planning/F4/f4_exemplos.csv`.
3. `solution/tests/test_f4.py`: 3 políticas, caso sem tickets e regra de teto. `pytest` → **31 passed**.
4. `docs/politica.md`: premissa de transferência, regra, tabela única com as 8 categorias e os 5 tipos do DS1, exemplos da faixa humana e ambíguos, cobertura e tela do "IA sugere".
5. `docs/fluxo.md`: Mermaid `flowchart TD`, as 7 etapas e uma tabela com 6 falhas.
6. Verificação programática:
   - 14 trechos, todos com ≤ 120 caracteres e prefixos exatos do texto do DS2;
   - nenhum nome nem e-mail do DS1 nos docs;
   - `f1_splits.csv` com o mesmo hash.

## 2. Resultados

Origem: `solution/outputs/f4_politica_por_categoria.csv` e `f4_politica.json` (`f4_politica.py`).

| Categoria prevista | n | n na faixa IA decide | Precisão (LI–LS Wilson) | F1 | 2 maiores confusões (verdadeiro → esta) | Política |
|---|---|---|---|---|---|---|
| Access | 1.260 | 852 | 98,59% (97,55–99,19) | 0,872 | Hardware 33, HR Support 18 | **IA decide** |
| Purchase | 434 | 390 | 99,49% (98,15–99,86) | 0,917 | Hardware 9, Administrative rights 0 | **IA decide** |
| HR Support | 2.254 | 1.387 | 97,12% (96,10–97,88) | 0,867 | Hardware 124, Miscellaneous 75 | IA sugere |
| Internal Project | 351 | 227 | 98,24% (95,56–99,31) | 0,841 | Access 8, Hardware 5 | IA sugere |
| Miscellaneous | 1.377 | 610 | 98,03% (96,59–98,87) | 0,830 | HR Support 67, Hardware 64 | IA sugere |
| Storage | 479 | 329 | 98,48% (96,49–99,35) | 0,882 | Hardware 8, HR Support 5 | IA sugere |
| Hardware | 3.182 | 1.556 | 95,89% (94,78–96,77) | 0,837 | HR Support 162, Miscellaneous 155 | **humano decide** |
| Administrative rights | 230 | 118 | 95,76% (90,46–98,18) | 0,715 | Hardware 8, Storage 6 | **humano decide** |

**Cobertura depois da regra por categoria** (holdout por grupo, n = 9.567):

| Faixa | Cobertura | Precisão (IC 95%) |
|---|---|---|
| IA decide | **12,98%** (1.242) | 98,87% (98,12–99,33) |
| IA sugere | 31,41% (3.005) | 96,67% (95,97–97,26) |
| humano decide | 55,61% (5.320) | 75,30% |

## 3. O que contraria a hipótese ou a expectativa

- **A regra por categoria derruba a faixa IA decide de 57,17% (F3) para 12,98%.**
  - Hardware é a maior categoria prevista (3.182). A precisão dela na faixa é de 95,89%, com LI 0,9478, abaixo das duas metas, porque recebe tickets de HR Support (162) e Miscellaneous (155). Pela regra pré-registrada, vai inteira para humano decide.
  - HR Support e Miscellaneous ficam pouco abaixo da meta mais exigente (LI 0,9610 e 0,9659).
  - O número de capa da F3 (57,17%) **não sobrevive** à regra por categoria. A economia do cenário A calculada na F3 (R$ 30.014/ano na base) passa a superestimar o ganho em cerca de 4,4 vezes, se a política for adotada como está. **Não recalculei a economia**, porque a spec da F4 não pede.
- **Internal Project tem precisão de 98,24% e mesmo assim vai para IA sugere.** O motivo é o n pequeno (227), que alarga o IC: o LI fica em 0,9556. É efeito de amostra, não de qualidade observada.
- **Administrative rights** confirma a H2: LI de 0,9046 e 6 de 6 "original errado" na revisão.
- **Um ticket ambíguo** sorteado tem `p_max` de 0,996 (id 5827). Confiança alta não garante rótulo inequívoco.
- **Os assuntos do DS1 não combinam com o tipo** (Billing inquiry com assunto "Network problem"; Refund request com "Data loss"). É coerente com o dado sintético da F1.

## 4. Desvios da spec

- **Categoria = categoria prevista** (não a verdadeira), porque a política é aplicada na hora da decisão, quando só a previsão existe. O F1 é o da classe verdadeira (`f3_classico.json`). As confusões são as colunas da matriz: quais classes verdadeiras caem nesta categoria prevista.
- **Leitura de "humano decide" por categoria como teto.** A spec diz que a categoria "fica em humano decide". Implementei a política como teto da faixa global: categoria humana → todos os tickets dela vão para humano, inclusive os que estariam em IA sugere. Categoria IA sugere → a faixa IA decide é rebaixada, e o resto fica como está. A outra leitura (rebaixar só os tickets da faixa IA decide) mudaria a cobertura de IA sugere. Os números acima usam a leitura de teto.
- **Exemplos de roteamento:** foram sorteados dentro da faixa **efetiva** da categoria (depois do teto). Por isso o exemplo de Hardware (humano decide) tem `p_max` de 0,792.
- **Arquivos extras com ids** (`f4_exemplos_ids.csv`, `f4_exemplos_ds1.csv`) em `solution/outputs/`, para tornar o sorteio verificável. Não têm texto do DS2. O do DS1 tem `Ticket ID`, tipo, assunto, canal e prioridade.
- O motivo (termos TF-IDF de maior peso) e a tela do "IA sugere" estão só descritos. A implementação é da F5.

## 5. Erros e correções durante a execução

- No rascunho de `docs/politica.md`, o motivo do cancelamento fugia da spec ("encerra a relação com o cliente"). Corrigido para o texto da spec: "movimenta dinheiro e é difícil de reverter".
- Fora isso, nenhum erro de execução.

## 6. Pendências e decisões que dependem do Gustavo

1. **Adotar a regra por categoria como está?** Ela reduz IA decide para 12,98%. Alternativas (todas mudam regra pré-registrada, então são decisão sua):
   - manter a regra (mais conservador; Hardware e Administrative rights com humano);
   - usar a meta 1 − *e*_sup como corte de IA decide por categoria;
   - aplicar a regra só a Administrative rights, que tem evidência de H2.
2. Leitura de "humano decide" como teto (ver §4).
3. O portão F3 diz "câmbio retirado da entrega", mas `f3_premissas.json` e `f3_faixas.json`, já commitados, ainda contêm a grade de câmbio. Não mexi (fora do escopo da F4).
4. A economia da F3 deve ser recalculada com a cobertura de 12,98%? Hoje, `f3_faixas.json` usa 57,17%.

## 7. Tempo gasto × orçado

Orçado: 25 min (teto de 30). Relógio: das 23:15 às ~23:19, cerca de 5 min de execução, mais a escrita dos docs.
