# CRP-UX-09 — Testes de UI orientados ao requisito da competição

## Objetivo
Impedir regressões que devolvam a solução para o modo demo ou técnico demais.

## Problema
Sem testes orientados ao requisito do challenge, a UI pode voltar a:
- usar demo data
- mostrar JSON cru
- perder explainability
- quebrar filtros críticos

## Tarefas
1. Criar testes para:
   - carregar ranking real
   - aplicar filtros
   - abrir detalhe
   - exibir score e explicação
   - exibir próxima ação
2. Adicionar smoke visual/funcional do fluxo principal.
3. Incluir asserts negativos:
   - não mostrar JSON cru
   - não depender do caminho demo no runtime principal

## Impacto na Submissão
- Dá confiança para a reta final.
- Protege os requisitos mínimos da competição.

## Evidências obrigatórias
- logs de testes passando
- diff da suíte de testes
- nota humana explicando o que está protegido
- evidência de que JSON cru e demo path ficaram cobertos

## Atualizações obrigatórias de process log
Registrar:
- quais regressões estavam em risco
- quais testes foram criados
- o que esses testes protegem
- evidências de execução

## Atualizações obrigatórias de README/Submission
- opcionalmente mencionar smoke tests ou checks relevantes se isso fortalecer a submissão

## Definition of Done
- testes cobrindo ranking real
- testes cobrindo filtros
- testes cobrindo detalhe explicável
- testes falhando se JSON cru voltar
- `PROCESS_LOG.md` atualizado
- evidências salvas
- README atualizado quando aplicável
- verificação humana explícita realizada
