# Scripts de exploração

Scripts rápidos usados para explorar os dados antes de escrever o motor de score, mantidos aqui como evidência do processo. Rodavam a partir de `solution/` (`node <script>`), lendo `data/raw` ou `data/generated/dataset.json`.

- `prof.mjs`: perfil das 4 tabelas (nulos, chaves órfãs, nomes divergentes).
- `eda.mjs`: taxa de vitória por fator, ciclos de Won/Lost e idade dos deals abertos.
- `eda2.mjs`: curva de sobrevivência, estabilidade do vendedor entre semestres e efeito de fim de trimestre.

**Atenção:** os números oficiais vêm só de `npm run analyze` ([docs/FINDINGS.md](../../docs/FINDINGS.md)). Exemplo de por que isso importa: o `eda2.mjs` divide os semestres em 01/08 e chega a uma correlação de 0,10; o script oficial divide em 01/07 e chega a 0,32.
