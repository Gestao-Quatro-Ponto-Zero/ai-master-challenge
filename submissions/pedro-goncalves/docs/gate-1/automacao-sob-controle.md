# Automação sob controle humano

## Princípio

IA entra onde há **padrão reversível e evidência mensurável**. Humano permanece onde há consequência material, ambiguidade, dados sensíveis ou ação externa. No protótipo, nenhuma mensagem é enviada e nenhum sistema é alterado.

## Matriz de autonomia

| Etapa | Papel da IA | Papel humano | Regra |
|---|---|---|---|
| Mascarar PII por padrões | Executa localmente | Audita amostras | Antes de qualquer inferência |
| Detectar sinal de reclamação | Aplica regras explícitas | Lê e decide o tratamento | Qualquer sinal força revisão humana |
| Sugerir categoria | Recomenda | Confirma ou corrige | Shadow mode como padrão |
| Priorizar fila | Não implementado | Decide | Dataset não sustenta prioridade |
| Redigir resposta | Fora do escopo | Decide | Sem base de conhecimento validada |
| Enviar resposta | Bloqueado | Executa | Ação externa e irreversível |
| Reembolso, acesso e RH | Bloqueado | Executa | Alto risco |
| Medir aceite e override | Registra | Supervisiona | Sem texto bruto nos logs |

## Política de decisão

1. O texto passa por mascaramento local de email, telefone, IP e identificadores longos.
2. Regras explícitas procuram sinais de reincidência, dano financeiro, cancelamento, risco legal, segurança, privacidade ou forte insatisfação.
3. O kill switch ativo força revisão humana.
4. Qualquer sinal de reclamação força revisão humana antes da classificação.
5. `Access`, `Administrative rights` e `HR Support` são sempre humanas.
6. O classificador retorna categoria e confiança calibrada.
7. Confiança abaixo do threshold gera abstenção.
8. Shadow mode registra a sugestão, mas não executa.
9. O modo assistido permite recomendação explícita, ainda sem ação externa.
10. Automação existe apenas como simulação para demonstrar a fronteira.

## Threshold

Na validação exclusiva de threshold do Dataset 2:

| Threshold | Cobertura | Acurácia nos cobertos |
|---:|---:|---:|
| 0,70 | 74,9% | 94,9% |
| 0,75 | 70,1% | 96,0% |
| 0,80 | 64,5% | 97,1% |

O critério foi definido antes do teste final: maximizar cobertura com acurácia seletiva mínima de 95% na validação. O threshold escolhido foi **0,75**. No teste final, cobriu **69,7%** e acertou **96,6%** dos cobertos. Continua sendo apenas referência de shadow mode.

## Implantação progressiva

### Gate 0: instrumentação

Corrigir eventos operacionais e definir taxonomia, SLAs, risco por categoria e touch time.

### Gate 1: shadow mode

Executar sugestões em paralelo ao humano. Medir macro-F1, recall por classe, calibração, cobertura, override e erro crítico.

### Gate 2: assistência

Exibir recomendação ao agente. Medir aceite, tempo ativo, retrabalho, reabertura e CSAT.

### Gate 3: canário restrito

Somente tarefas reversíveis, de baixo risco e com confiança calibrada. Revisão amostral contínua e kill switch.

## Critérios de avanço

- Erro crítico dentro do limite definido pelo dono do processo.
- Recall mínimo por classe sensível.
- Override humano estável e investigado.
- Nenhum aumento material de reabertura ou queda de CSAT.
- Touch time medido, não inferido a partir de TTR.
- Auditoria e rollback testados.

## Critérios de interrupção

- Vazamento de PII.
- Ação executada fora da política.
- Mudança de distribuição não coberta.
- Aumento de erro crítico, reabertura ou reclamação.
- Queda de calibração ou crescimento abrupto de abstenções.

## Cenários econômicos fora do protótipo

Os documentos de decisão mantêm uma calculadora de capacidade com entradas explícitas:

`tickets x parcela elegível x adoção x taxa segura x minutos ativos poupados`

Depois subtrai minutos de revisão, retrabalho e custo da solução no mesmo período. Sem touch time medido e custo aprovado, o resultado é **cenário**, não economia comprovada. A calculadora não aparece no aplicativo de triagem, que permanece focado no trabalho diário.
