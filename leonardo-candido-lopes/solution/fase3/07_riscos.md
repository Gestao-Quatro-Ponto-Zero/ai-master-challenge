# 07 — Riscos e Governança

**Desafio 002 · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026
Escala: Probabilidade e Impacto em **Alta / Média / Baixa**. Para cada risco, indico a evidência dos dados que o fundamenta. Quando não há evidência, o risco está marcado como [HIPÓTESE].

## 1. Matriz de riscos

| # | Risco | Prob. | Impacto | Medida de mitigação | Responsável | Monitoramento |
|---|---|---|---|---|---|---|
| R1 | **Classificações incorretas** afetam o cliente (fila errada, atraso). Evidência: Hardware × Misc com similaridade de 0,625; 38 grupos com categorias conflitantes | Alta | Médio | Limiar de confiança (τ_alto/τ_baixo); faixa média assistida; modo sombra antes de ativar; F1 por categoria antes do go-live | Líder de Operações + dono do modelo | KPI 4 (erro), KPI 14 (reatribuição), por categoria e faixa de confiança |
| R2 | **Respostas automáticas inadequadas** (resolve errado ou não entende a intenção). Benchmark: Gartner, 45% das falhas de self-service por não entender a intenção | Média | Médio | Autoatendimento só em Purchase, Storage e subtipos de Access; respostas de base revisada; sempre com o botão "não resolveu → humano" | Curador da base de conhecimento | KPI 5, KPI 11 (reabertura do autoatendimento), KPI 12 (CSAT do autoatendimento) |
| R3 | **Vazamento de dados sensíveis** (dados pessoais em prompts ou logs; LGPD). O D1 tem nome, e-mail e idade (fictícios, mas o esquema real terá dados reais) | Média | Alto | Mascarar dados pessoais antes do NLP; minimização; fornecedor com contrato de tratamento de dados e sem uso para treino; logs com retenção definida; acesso por perfil | DPO / Segurança da Informação | Auditoria trimestral de logs; testes de reidentificação por amostra |
| R4 | **Dependência excessiva da automação** sem supervisão; equipe perde a habilidade de triar | Média | Médio | Amostra semanal de tickets automáticos revisada por humano; meta de automação com teto (11–26% de autoatendimento); plano de contingência ("modo manual") testado | Gerente de Suporte | % de tickets auditados; teste semestral do modo manual |
| R5 | **Viés de domínio nos dados de treino**: o D2 é TI interna, não B2C. Evidência: 98/300 palavras em comum; 31,5% do D1 sem categoria de TI | Alta | Alto | Detector de domínio antes do classificador; fila Financeiro/Comercial separada; não usar o modelo de TI em B2C sem novos dados rotulados | Dono do modelo | KPI 16; % de tickets "fora do escopo"; erro por domínio |
| R6 | **Degradação do modelo (drift)**: novos sistemas, termos e produtos mudam o vocabulário | Alta (no médio prazo) | Médio | Monitorar a distribuição de confiança e de categorias; retreino por gatilho (seção 2) | Dono do modelo | KPI 3 (P10 de confiança), KPI 4, mudança no mix de categorias vs linha de base |
| R7 | **Falhas de integração** com o sistema de tickets, diretório de usuários ou sistema de compras ([HIPÓTESE]: sistemas não conhecidos) | Média | Alto | Integração por API com fila de reprocessamento; se a IA falhar, o ticket vai para a fila humana padrão (*fail-safe*); testes ponta a ponta no piloto | TI / Arquitetura | Taxa de erro de API; tickets sem classificação em até X min |
| R8 | **Resistência dos agentes** (medo de substituição, desconfiança na sugestão) | Média | Médio | Comunicar que o modelo **não** assume cortes (`06_roi_model.md`, seção 4); agentes como revisores e curadores; mostrar ganhos (menos triagem repetitiva) | Gerente de Suporte + RH | Taxa de aceite das sugestões; pesquisa de clima; overrides sem justificativa |
| R9 | **Falta de ciclo de feedback estruturado**: correções não voltam ao modelo | Média | Alto | Campo obrigatório de correção de categoria; pipeline de retreino; revisão mensal de confusões | Dono do modelo | % de correções incorporadas no retreino; idade do modelo em produção |
| R10 | **Escalonamento incorreto: crítico tratado como baixo.** Evidência: a prioridade do D1 é aleatória, sem base de treino confiável | Média | **Alto** | Priorização por regras auditáveis + sinais no texto; Crítica nunca vai para autoatendimento; palavras de alerta forçam revisão humana; cada subpriorização é revisada (post-mortem) | Líder de Operações | KPI 15 (override para cima); SLA de Crítica (KPI 8) |
| R11 | **Ruído nos rótulos de treino** (o modelo aprende o erro). Evidência: 19,9% dos tickets com "password" estão em Hardware; 38 grupos conflitantes | Média | Médio | Exclusão dos 235 registros problemáticos; revisão das confusões na matriz depois do treino; guia de categorias para os rotuladores | Dono do modelo + curador | Concordância entre rotuladores em amostra |
| R12 | **ROI não se materializa** (horas liberadas viram ociosidade). Evidência: no cenário base, o resultado de caixa é −R$ 1.951/mês | Média | Médio | Piloto com decisão de escala baseada em KPI 13; definir antes o destino das horas (backlog, N2, base de conhecimento) | COO / Finanças | KPI 13 vs projeção; taxa de realização efetiva |
| R13 | **Registro de tempo inconsistente** (repetir o problema do D1) | Média | Alto | Validação na gravação (`first_response ≥ created`, etc.); relógio único em UTC | TI / Dados | KPI 17 (completude) |

## 2. Governança

### 2.1 Papéis

| Papel | Responsabilidade |
|---|---|
| **Dono do modelo** (analista de dados/IA) | Métricas do modelo, retreino, versionamento, documentação |
| **Líder de Operações** | KPIs operacionais, limiares de confiança, regras de prioridade |
| **Curador da base de conhecimento** | Respostas do autoatendimento e revisão de amostras |
| **DPO / Segurança** | Privacidade, logs, fornecedores |
| **Comitê mensal** (COO + os papéis acima) | Aprova mudanças de escopo de automação e de limiares |

### 2.2 Revisão periódica do modelo

| Cadência | O que revisar |
|---|---|
| **Semanal** | KPIs 2, 3, 4, 5, 11, 14, 15; amostra de 50 tickets automáticos estratificada por categoria, com prioridade para Hardware e Misc |
| **Mensal** | Matriz de confusão em produção (a partir das correções humanas); F1-macro e F1 por categoria; recalibração dos limiares; revisão dos casos de Crítica subpriorizada |
| **Trimestral** | Auditoria completa: viés por domínio, canal e categoria; privacidade; ROI medido vs projetado; decisão sobre expandir ou reduzir o autoatendimento |

### 2.3 Critérios para retreino (qualquer um dispara)

1. **F1-macro em produção** cai mais de 5 pontos percentuais em relação à validação (proposta para validação).
2. **Taxa de erro de classificação (KPI 4)** na faixa de confiança alta acima de 5% por duas semanas seguidas.
3. **P10 da confiança (KPI 3)** cai mais de 0,10 em relação à linha de base, o que indica drift.
4. **Mix de categorias** muda mais de 5 pontos percentuais em alguma categoria, ou aparece um novo padrão recorrente em Misc.
5. **Mais de 1.000 correções humanas** acumuladas desde o último treino.
6. **Mudança de sistema ou processo** (novo ERP, nova ferramenta de acesso).

Todo retreino segue três regras:
- validação em holdout separado por grupo de quase-duplicatas;
- comparação com o modelo em produção (*champion × challenger*);
- aprovação do comitê antes do deploy e rollback disponível.

### 2.4 Processo de auditoria de classificações

1. **Amostragem estratificada** por categoria × faixa de confiança, com sobreamostragem das categorias ambíguas.
2. **Revisão cega**: o revisor não vê a sugestão do modelo. Mede-se a concordância modelo × humano e humano × humano.
3. **Registro do erro**, com tipo (domínio, categoria ou prioridade) e causa (texto ambíguo, rótulo ruim, termo novo).
4. **Ações:** corrigir o rótulo, atualizar o guia de categorias, ajustar regra ou limiar, e incluir no próximo retreino.
5. **Trilha de auditoria** por ticket: `model_version`, `confidence`, decisão, override, motivo. Retenção conforme a política de LGPD.
