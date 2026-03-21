# CRP-UX-02 — Matar o JSON cru do painel de detalhe

## Objetivo
Transformar o painel de detalhe em explicação de negócio legível para vendedor.

## Problema
O detalhe atual despeja JSON cru. Isso serve para desenvolvedor, não para usuário comercial.

## Tarefas
1. Remover a exibição de payload JSON cru.
2. Substituir por cards ou seções com:
   - score
   - banda de prioridade
   - por que está alta
   - o que reduz a prioridade
   - flags de risco
   - próxima ação
3. Usar os view models existentes como contrato de apresentação.
4. Garantir que o conteúdo esteja orientado à decisão, não à inspeção técnica.

## Impacto na Submissão
- Ataca diretamente o requisito de explainability.
- Melhora a percepção de “algo que um vendedor pode usar”.

## Evidências obrigatórias
- screenshot antes/depois
- captura da oportunidade aberta no detalhe
- diff do componente de detalhe
- nota humana justificando a nova estrutura

## Atualizações obrigatórias de process log
Registrar:
- por que JSON cru era inadequado
- como o payload foi transformado em experiência legível
- decisões visuais e de conteúdo
- iterações relevantes

## Atualizações obrigatórias de README/Submission
- atualizar screenshots e descrição da UX do detalhe
- reforçar a explicabilidade da solução

## Definition of Done
- nenhum JSON cru visível ao usuário
- score destacado
- banda de prioridade visível
- fatores positivos/negativos/riscos/next action visíveis
- `PROCESS_LOG.md` atualizado
- evidências salvas
- README atualizado quando aplicável
- verificação humana explícita realizada
