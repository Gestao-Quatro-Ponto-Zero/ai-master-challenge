Esta submissão investiga o Challenge 002 e entrega diagnóstico com fontes, triagem IT assistida e um protótipo local reproduzível. O candidato orientou escopo, evidências, clareza e valor de negócio; a IA implementou, analisou e testou sob essa direção.

O diagnóstico encontrou 5.700 não encerrados em 8.469 registros e explicita que os dados não permitem medir duração total ou esforço ativo. O classificador teve macro F1 0,844612 contra 0,646094 do baseline em 7.175 casos; toda sugestão exige confirmação humana. Os datasets têm papéis complementares, sem join ou transferência validada de desempenho.

A aplicação oferece visões Empresa/Instrutor, resultados e ações, triagem individual/em lote, revisão persistida, exportação e simulação de capacidade. Um ensaio com operador declarado teve maior concordância no assistido (7/8 contra 1/8), mas maior tempo (52,72 s contra 41,58 s); não se alega economia operacional. Integrações e IA analista são continuidade planejada.

Para revisar, comece em `submissions/giovanne-berteli-comba/docs/start-here.md`. Na raiz, execute:

```bash
bash submissions/giovanne-berteli-comba/run.sh
```

Linux x86_64/glibc; primeiro preparo requer internet. Selecione Instrutor para o roteiro. `--overview` consulta agregados sem dados/modelo. O CodeTour de 13 paradas abre com `bash submissions/giovanne-berteli-comba/review.sh` (VS Code necessário).

Validação: 93 testes de software passaram; decisões e exports H01 reconciliados; 7.175 resultados finais salvos conferidos sem novos ajustes/predições. Evidências, limites e participação humano/IA estão no README e process log. O diff está restrito à pasta da submissão; dados brutos, modelos e bancos locais não integram o envio.
