# F11 — Console do piloto refeito do zero: interface limpa e guiada (spec para o Claude Code)

- **Teto:** 75 min. Ao chegar a 90 min (120%), pare e proponha o corte no report.
- **Ordem de corte, se estourar:** (1) a versão para celular além do mínimo funcional; (2) a animação de transição entre telas. **Nunca cortar:** a arquitetura de 4 telas, a paridade de funcionalidades e as checagens de números.
- **Diagnóstico do Gustavo sobre a F10:** visual padrão de IA (tudo branco, fonte do sistema); poluído; quem abre não sabe para onde ir, onde clicar nem o que está vendo. **A causa é da spec:** a F10 pediu "denso" e pôs 3 colunas de informação e 8 controles numa tela só. Registre isso como erro do chat do Projeto no process log.
- **O que NÃO muda:** `console/data.js`, `solution/f10_console_dados.py` e os números (os testes da F10 continuam valendo). Só a interface é refeita: `index.html`, `styles.css`, `app.js`.

## Passo 0 — Skills de design, obrigatórias e antes de qualquer código

1. Rode a skill **`/ui-ux-pro-max:ui-ux-pro-max`** para definir o sistema de design. Contexto a passar: "console operacional B2B de triagem de tickets com IA, usado por supervisor e atendente de suporte; público executivo brasileiro (Diretor de Operações) que avalia em 5 minutos; tom confiável, sóbrio, moderno; não pode parecer landing page escura nem dashboard genérico de IA". Saia com: estilo, paleta (hex), par de fontes, escala tipográfica, espaçamentos, raio, sombras e estilo de gráfico.
2. Rode a skill **`/frontend-design`** para a direção estética e a composição das telas.
3. Se alguma das duas skills não estiver disponível nesta sessão, **pare e reporte**, sem improvisar.
4. Grave as escolhas em `console/DESIGN.md` (até 40 linhas): estilo, paleta com hex e papel de cada cor, fontes, a regra de cor das faixas e o motivo de cada escolha. Isso entra no process log como "o que a IA sugeriu".

## Passo 1 — Arquitetura da informação: 4 telas, cada uma responde a 1 pergunta

Navegação lateral fixa (no celular, barra inferior) com 4 itens, ícone + rótulo, e a tela ativa destacada. Cada tela tem como título a pergunta que responde.

### Tela 1 — "O piloto está saudável?" (abre por padrão)

- **Bloco "Comece aqui"**, dispensável, com 3 passos clicáveis que levam às outras telas: "1. Veja um ticket ser triado" → Fila; "2. Veja por que a IA não decide tudo" → Governança; "3. Tente quebrar o sistema" → Robustez.
- **No máximo 3 indicadores grandes:**
  - tickets que a IA resolve sozinha (cobertura de IA decide);
  - precisão medida contra a meta (98,7% × 96,8%), com um selo "acima da meta";
  - trabalho humano evitado.
  Cada indicador tem uma frase de uma linha explicando o que é.
- **Um único gráfico principal:** a distribuição das 3 faixas (barra empilhada horizontal ou rosca), com legenda em texto e %.
- **As 8 filas em chips compactos**, agrupadas por política (2 automáticas, 4 com sugestão, 2 com humano). Ao clicar, abre a categoria na Governança.
- Uma **faixa de alerta**, só se houver alerta ativo (hoje: Internal Project), com um link "ver".

### Tela 2 — "Como um ticket é triado?" (Fila do atendente)

- **À esquerda:** a lista da fila (id, 1 linha de texto, selo de faixa) e um filtro único por faixa (segmented control).
- **À direita, cartão do ticket com foco:**
  - texto;
  - **um grande selo de decisão** (por exemplo, "IA decide → Access");
  - a confiança numa barra com o marcador do limiar;
  - **um botão primário**: "Confirmar" (Enter);
  - um secundário: "Corrigir" (abre um seletor).
- "Por que esta decisão" fica **recolhido**, com 3–4 passos curtos ao abrir. Os termos do motivo, as duas mais prováveis e o detalhe técnico ficam dentro dele.
- O aviso "correção simulada pelo rótulo original" vira uma **nota discreta** no cartão, com um ícone de info, não uma caixa grande.
- **Retire desta tela:** dia do piloto, política, modo sombra, reentregar, reembolso e injeção. Tudo vai para a Tela 4.

### Tela 3 — "Por que a IA não decide tudo?" (Governança)

- Uma frase de topo: "Cada fila só é automatizada quando a precisão comprovada supera a meta humana."
- **Tabela enxuta**, uma linha por categoria:
  - nome;
  - política (selo);
  - uma barra de precisão com o IC e as 2 marcas de meta;
  - decisão da regra ("mantém", "pode subir", "alerta").
  O n e os números exatos vão para o tooltip ou o painel.
- **Ao clicar numa categoria**, abre um painel lateral (drawer) com:
  - o gráfico de evolução do limite inferior por dia, com as linhas da meta;
  - o controle "dia do piloto", que **só existe aqui**;
  - uma frase gerada: "Hardware: 95,4% de precisão, mas o limite inferior (94,3%) não alcança a meta de sugestão (95,5%). Continua com humano."

### Tela 4 — "O que acontece se…?" (Robustez)

Cenários em cartões, cada um com **um botão "rodar"** e o resultado em linguagem simples, com o número e a fonte:
1. **"…alguém tentar enganar a IA?"** Escolha o ataque e veja, lado a lado, a política F8 (dano silencioso) × a F9 (contido). Use o ticket 10244 como padrão.
2. **"…o webhook entregar duas vezes?"** Reentrega o mesmo evento e mostra "duplicado, nenhuma nova decisão" e a linha do log.
3. **"…o ticket for um reembolso?"** Regra de ação: vai para humano, mesmo com confiança alta.
4. **"…precisarmos desligar a IA agora?"** Chave do modo sombra: a cobertura cai, o alerta dispara e o log continua.
5. **"…uma política nova for pior?"** Seletor F9 / F8 / F4, com o efeito na cobertura e no dano de injeção (rollback).

O log da tela fica recolhido no fim desta tela.

## Passo 2 — Regras visuais e de limpeza (critérios verificáveis)

- **Cada tela tem uma ação principal** visualmente dominante; as demais são secundárias ou terciárias.
- **No máximo 4 números grandes por tela.** Os demais ficam em tooltip, painel ou bloco recolhido.
- Nenhum parágrafo visível com mais de 2 linhas sem estar recolhido.
- **Cor com significado:** uma cor de marca (navegação e ação primária) e 3 cores semânticas para as faixas, seguras para daltonismo, sempre com rótulo e ícone. Nada de cor decorativa. O fundo **não** é todo branco: navegação com a cor da marca, área de conteúdo em tom suave e cartões brancos com sombra leve.
- **Fontes:** o par definido pela skill, **auto-hospedado** em `console/fonts/` (woff2), com `font-display: swap` e fallback de sistema. Sem CDN em tempo de execução. Números tabulares.
- **Gráficos:** SVG próprio ou uma biblioteca pequena copiada para `console/vendor/` (sem CDN). Todo gráfico tem título-pergunta, rótulo de dados direto (sem depender da legenda) e uma frase de leitura ("o que este gráfico diz").
- Números em pt-BR (vírgula decimal, `Intl.NumberFormat('pt-BR')`), incluindo os textos gerados.
- **Movimento:** transições curtas (≤ 200 ms) entre telas e ao abrir o painel, respeitando `prefers-reduced-motion`.
- **Acessibilidade:** contraste AA; foco visível; navegação por teclado (Enter confirma, Esc fecha o painel); `aria-label` nos ícones.
- **Responsivo:** 1440, 1024 e 390 px, sem rolagem horizontal.
- **Proibido:** página de apresentação escura com manchete em gradiente (o padrão dos concorrentes); fundo inteiramente branco com fonte padrão (o padrão da F10); mais de 3 colunas; emojis como ícones (use SVG inline).

## Passo 3 — Paridade de funcionalidades (checklist obrigatória no report)

Tudo que a F10 fazia precisa continuar acessível, em no máximo 2 cliques a partir da Tela 1:
- fila com filtro;
- confirmar e corrigir com teclado;
- o "por que" da decisão;
- as duas mais prováveis e os termos;
- governança por categoria com IC e metas;
- evolução por dia;
- dia do piloto;
- modo sombra;
- seletor de política;
- os 5 ataques;
- duplicado;
- reembolso;
- alertas;
- log;
- premissas de custo editáveis (no painel de "trabalho humano evitado" da Tela 1);
- o aviso de simulação;
- o rodapé de fontes.

Para cada item, informe a tela e o caminho.

## Passo 4 — Verificação

- Playwright por `file://` e por `python -m http.server`, a 1440 × 900, 1024 × 768 e 390 × 844: nenhum erro de JavaScript e nenhuma rolagem horizontal.
- **Teste de 5 segundos (registre):** na Tela 1, o primeiro elemento clicável e dominante precisa ser o "Comece aqui" ou a navegação. Descreva o que aparece acima da dobra a 1440 × 900.
- **Números:** confira por script que os números da Tela 1 batem com `data.js` (13,37%; 98,75%; 1.279 de 9.567).
- `pytest` passa (os testes da F10 continuam).

## Passo 5 — Screenshots, docs, commit

- Screenshots (deviceScaleFactor 2) em `process-log/screenshots/`, **substituindo** `c1`–`c4` (use `git rm` nos antigos):
  - `v1_saude.png`, `v2_fila.png`, `v3_governanca_hardware.png` (com o painel aberto), `v4_robustez_injecao.png`, `v5_robustez_sombra.png`, `v6_celular.png` (Tela 1 a 390 px);
  - mais `antes_depois.png`: a F10 ao lado da Tela 1 nova, para o process log.
- **README:** troque a imagem embutida por `v1_saude.png` e liste as demais.
- **Process log:**
  - linha da F11 com "Decisão minha" vazia;
  - na tabela de erros: "F10-spec (chat do Projeto) pediu interface 'densa' com 3 colunas e 8 controles; resultado poluído e sem caminho claro. Detectado pelo Gustavo. Corrigido na F11 com 4 telas, 1 pergunta por tela e as skills de design.";
  - em "O que a IA sugeriu", um resumo do `DESIGN.md`.
- Checagens de commit da F10 (incluindo abortar se aparecer `console/.vercel/`) e da regra de texto (`data.js` inalterado). Commit `F11: console refeito do zero — 4 telas guiadas, sistema de design, robustez como cenários`. Sem push.
- `planning/F11-report.md` no formato da seção 8 do `CLAUDE.md`, com a checklist de paridade e a descrição acima da dobra.
- **Lembrete para o Gustavo no fim do report:** redeploy com `npx vercel --prod` na pasta `console`.
