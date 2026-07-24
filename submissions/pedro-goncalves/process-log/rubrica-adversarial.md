# Rubrica adversarial

## Regra de decisão

- FAIL automático para qualquer achado crítico.
- FAIL para achado alto sem mitigação verificável.
- Claim sem denominador, janela, unidade, método e incerteza é não provado.

## Bloqueadores avaliados

| Frente | Bloqueador |
|---|---|
| Diagnóstico | Tratar 30 mil como volume medido ou correlação como causa |
| Métricas | Usar acurácia isolada, leakage ou confiança não calibrada |
| Claims | Afirmar produção, economia ou ROI sem protocolo |
| Datasets | Juntar taxonomias sem chave ou validar um domínio pelo outro |
| ROI | Converter TTR em esforço ou inventar custo-hora |
| Humano-IA | Automatizar ações críticas sem abstenção e override |
| Processo | Omitir erros da IA, iterações ou evidência contemporânea |
| Submissão | Alterar arquivos fora da pasta própria |

## Evidência mínima

- auditoria física e hash dos arquivos;
- baseline, validação de threshold, teste final e métricas por classe;
- claim ledger;
- ROI por parâmetros;
- matriz humano-IA;
- process log;
- testes reproduzíveis;
- diff restrito à pasta de submissão.
