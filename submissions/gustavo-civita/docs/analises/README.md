# Análises de apoio

Scripts e saídas das verificações independentes citadas no process log. Foram
gerados por subagentes do Claude Code, cada um sem acesso às conclusões dos
outros.

Todos rodam de dentro da própria pasta, com caminhos relativos à submissão
(`python nome.py` ou `node nome.js`, depois de `pip install -r
../../solution/requirements.txt`). Foram conferidos numa cópia limpa da
submissão. Três deles foram ajustados depois de escritos, só para continuarem
rodando contra o código atual, sem mudar o que medem: `auditoria/a2.py` (uma
coluna do teste histórico mudou de nome), `verificacao2/sim.js` e `sim2.js` (a
tela ganhou arquivos e textos novos). As saídas guardadas (`.out`, `.csv`) são
as da época em que cada verificação foi feita.

| Pasta | O que é |
|---|---|
| `sinais/` | Busca de sinais ainda não usados (103 testes registrados nos CSVs da pasta, com validação no tempo) |
| `auditoria/` | Primeira auditoria da solução contra o enunciado |
| `verificacao2/` | Segunda verificação, com olhar de cliente |
| `diabo/` | Advogado do diabo: a ferramenta gera resultado ou mascara? |
| `alternativas/` | Outras formas de atacar os dois problemas, conferidas nos dados |
| `metricas/` | Linha de base das métricas e conta de poder do piloto |
| `conferencia/` | Scripts com que os números dos relatórios foram conferidos |
