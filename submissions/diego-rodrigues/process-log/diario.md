# Diário de sessões

> Uma entrada por sessão de trabalho, gravada **na hora** por `registrar.py`. Não editar à mão
> salvo para corrigir um erro de digitação: o valor deste arquivo é ser contemporâneo ao trabalho.
>
> Abrir sessão: `python3 registrar.py --inicio "<tarefa>" --modelo <id>`
> Registrar iteração: `python3 registrar.py --pedi "..." --veio "..." --mudei "..."`
> Registrar erro da IA: `python3 registrar.py --erro "..." --pego-por "..." --teste "..." --ficou "..."`
> Fechar sessão: `python3 registrar.py --fim "<resultado>"`

## 2026-11-11 10:49 · Tarefa 0 · modelo claude-haiku-5-5 · ferramenta Claude Code

- **10:50** — nota: Passo 3 do plano: kit copiado do template; MODELOS.md ganhou claude-haiku-5-5 e as linhas de exemplo foram removidas (modelos de exemplo não foram usados). Modelo padrão do registrar.py é claude-opus-5: passar --modelo sempre que a sessão for outra.

- **10:50** — nota: Passo 2 feito antes do registro: estrutura da solução e venv; CSVs baixados do zip oficial do Kaggle (agungpambudi, CC0) porque a cópia local em dados/ diferia só em fim de linha (CRLF vs LF). Dataset de churn (rivalytics) baixado por engano e descartado. SHA256SUMS conferido com shasum -c: OK.

- **11:00** — nota: Passo 4 (baseline): README colado sem dados em dois modelos. Nemotron-3.5-lightning via API OpenRouter (free), Gemini 3.1 via interface web (colado pelo Diego). Tentativas sem texto ou bloqueadas pelo provedor: gemma-4-31b (429), ernie-5.5-flash (429), liquid-lfm-3-1.7b (sem texto), nemotron-3-ultra (sem texto). Crítica escrita em baseline/critica.md. Verificações: Nemotron não compila (SyntaxError) e usa colunas inexistentes; Gemini compila; 1.480 deals GTXPro sem casamento de produto.

- **11:05** — nota: Terceiro baseline: ChatGPT 6.1 Sol, via interface web, colado pelo Diego (sem código). Salvo em baseline/chatgpt-6.1-sol.md e incluído na crítica. Verificado: taxa de ganho por produto varia 60% a 65%, então o peso de 30% do histórico de produto quase não diferencia; p75 de duração global = 85 dias.
