---
id: Z8N3
parent: 8W2N
project: LeadScorer
subject: Revisão e correção das fases 1 a 6 da interface web
author: dradicchi@
priority: high
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Revisar os artefatos das fases 1 a 6 da tarefa 8W2N (interface web) quanto à qualidade e à
aderência à especificação, e aplicar as correções decorrentes. O relatório completo da revisão,
com os achados ordenados por gravidade e a disposição de cada um, reside em
'docs/revisao-8w2n-fases-1-6.md'. As correções abrangem os grupos A (correção), B (aderência,
exceto o indicador de cross-selling, diferido), C1 (fixação de sessão), D (qualidade) e E
(convenções).


# Motivações (por que será feito)

A tarefa-pai 8W2N foi concluída, mas uma revisão independente das fases 1 a 6 identificou dois
defeitos de correção que produzem HTTP 500 (crash na lista de engajadas por NULL não tratado e
filtro de data do gerente sobre eixo temporal incompatível), quatro lacunas de aderência às
estórias de usuário (filtros e colunas de contexto) e itens de qualidade, segurança e convenção.
A correção restaura a definição de pronto das fases 5 e 6.


# Recursos e dados necessários

- Relatório de revisão: 'docs/revisao-8w2n-fases-1-6.md';
- Especificação: 'docs/concepcao-inicial.md' e a definição de pronto de 8W2N;
- Código sob revisão: 'src/web/' e 'tests/web/';
- Verificação: Quicklisp global com o registro ASDF apontado ao worktree (qlot ausente neste
  ambiente); Parachute e o linter 'mallet' executáveis; testes dependentes de banco não
  executáveis por ausência de PostgreSQL/PGDATABASE.


# Plano de trabalho (como será feito)

1. Grupo A: corrigir A1 (denull na lista de engajadas do agente) e A2 (eixo temporal do filtro
   ':since' do gerente), com testes;
2. Grupo B: B2 (filtro por data de disponibilização), B3 (filtro por data de engajamento e série,
   sem cross-selling) e B4 (colunas de porte, receita e fundação); diferir B1 (cross-selling);
3. Grupo C: C1 (rotação do identificador de sessão no login); ressalvar C2 (cautela de
   implantação, sem código);
4. Grupo D: D1 a D5 (fatorações de KPI, portão de autorização, reescore no serviço de ciclo,
   pesos a partir da configuração e desduplicação de filtro/ordenação e literais);
5. Grupo E: quebrar as linhas acima de 96 colunas.


# Riscos e ressalvas

- A verificação dependente de banco não é executável neste ambiente; a cobertura das correções é
  escrita sobre funções puras e sobre as funções '-for' com as indireções '*...-fn*' mockadas;
- B1 (cross-selling) foi descopado após a revisão da especificação: não há campo no dataset e a
  derivação seria um incremento de modelagem não justificado no MVP; o requisito foi removido da
  concepção (Limitações intencionais de escopo), resolvendo B1 por exclusão.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- Os achados A1, A2, B2, B3 (exceto cross-selling), B4, C1, D1 a D5 e E1 estão corrigidos, com
  cobertura de teste onde aplicável sem banco;
- O sistema web compila e carrega sem avisos, a suíte Parachute da camada web passa (excetuados
  os testes que exigem banco) e o linter 'mallet' não relata achados;
- B1 (cross-selling) foi resolvido por descopagem na concepção (requisito removido); C2
  permanece registrado como cautela de implantação.
