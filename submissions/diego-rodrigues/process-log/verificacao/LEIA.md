# Verificação independente

> Pedir ao mesmo modelo que escreveu o código para revisar o próprio código confirma o viés dele.
> A verificação vale quando é **outro modelo**, **com código próprio**, **a partir dos dados brutos**,
> **num clone limpo**, e **sem ver a implementação** antes de chegar ao número.

## Protocolo

1. **Clone limpo.** Copie só os dados brutos e o documento que cita os números (README, relatório). Não copie o motor.
2. **Outro modelo, outra família.** Registre o id exato em `../MODELOS.md`.
3. **O pedido**, literalmente este:

   > Recalcule, a partir dos arquivos de dados e com código seu, cada número afirmado neste documento.
   > Para cada um, diga: confere, difere (com o valor que você obteve) ou não dá para recalcular (e por quê).
   > Depois procure, especificamente: vazamento temporal (alguma conta usa informação posterior à data de referência);
   > viés de sobrevivência (algum denominador exclui quem ainda não teve desfecho); limiar escrito à mão que deveria
   > ser aprendido; regra de negócio duplicada na interface; e número citado sem fonte rastreável.

4. **Guarde tudo aqui**: o script (`independente.py`), a saída bruta (`independente-saida.txt`) e o relatório (`relatorio.md`).
5. **Responda item a item** em `relatorio.md`: o que foi corrigido, o que foi recusado e por quê. Um achado recusado com razão escrita vale mais do que um achado aceito sem pensar.

## Estrutura do relatório

```markdown
# Relatório da verificação independente

**Modelo:** <id exato>   **Data:** <data>   **Clone:** <o que foi dado>

## Números recalculados

| Afirmação | Valor no documento | Valor recalculado | Veredito |
|---|---|---|---|

## Achados

### <título do achado>
- **Afirmação atacada:**
- **Como foi testado:**
- **Resultado:**
- **O que eu fiz:** corrigi / recusei, porque...

## O que não deu para recalcular
```

## O que fazer com um achado que você considera errado

Recuse por escrito, com o número. Receber crítica técnica e concordar por polidez estraga as duas coisas: o código e a credibilidade do registro.
