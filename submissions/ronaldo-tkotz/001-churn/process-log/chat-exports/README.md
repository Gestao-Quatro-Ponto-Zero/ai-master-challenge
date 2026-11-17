# Conversas com a IA

| Arquivo | O que é |
|---|---|
| [`01-sessao-principal-claude-code.md`](01-sessao-principal-claude-code.md) | A conversa principal com o Claude Code, de 14/11 (início do desafio 001) a 17/11/2026: exploração, contestações, base SQL, dashboard, ferramenta, relatório e submissão. |
| [`02-sessao-ponte-gemini.md`](02-sessao-ponte-gemini.md) | Uma conversa lateral (14 e 15/11) em que o Claude leu a planilha com as minhas análises no Gemini e conferiu os números dela contra os CSVs. |
| [`exporta_chat.py`](exporta_chat.py) | O script que gerou os dois arquivos a partir do `.jsonl` que o Claude Code grava de cada sessão. |

## Critério do export

O Claude Code roda no meu ambiente pessoal, e o arquivo bruto de cada sessão carrega instruções de sistema com dados meus que não têm a ver com o desafio. Por isso o export é curado por regra fixa, e não à mão:

- **Ficou:** tudo o que eu digitei, o texto de cada resposta da IA, a data e a hora de cada mensagem e, em blocos recolhíveis, o nome e a descrição de cada ferramenta chamada (1.348 chamadas na sessão principal).
- **Saiu:** a saída das ferramentas (está reproduzível nos scripts de `verification/` e no banco); o raciocínio interno do modelo; os resumos automáticos de compactação da conversa (marcados no texto onde aconteceram); as instruções de sistema e de hooks do meu ambiente; o caminho da minha pasta pessoal (trocado por `~`), endereços de e-mail e alguns termos pessoais de uma lista local, que aparecem como `[removido]`.
- **Recorte de início:** a sessão principal começou com cerca de duas horas e meia sobre assuntos pessoais e de preparação do ambiente (a escolha do desafio, o download dos dados). O export começa na mensagem "Vamos começar pelo desafio 1" (14/11, 18h08 UTC). O recorte foi proposto pela IA e confirmado por mim.

O export passou pelo `gitleaks` (nenhum segredo encontrado) e por uma busca por dados pessoais antes de entrar no repositório.

As planilhas do Gemini estão abertas para leitura nos links do [README da submissão](../../../README.md#evidências).
