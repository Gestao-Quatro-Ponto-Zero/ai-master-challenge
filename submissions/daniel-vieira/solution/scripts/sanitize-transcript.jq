# sanitize-transcript.jq --- Regras canonicas de higienizacao da transcricao de sessao.
#
# Aplicado por 'scripts/export-session' a cada linha (objeto JSON) do JSONL bruto do
# Claude Code. Adota deny-by-default: cada tipo de registro conhecido e mapeado para uma lista
# explicita de campos preservados, e qualquer tipo desconhecido colapsa para um esqueleto
# minimo. Preserva os prompts, o texto do assistente, o raciocinio ('thinking') e as chamadas
# de ferramenta como nome mais argumentos de entrada. Descarta ou trunca as superficies onde se
# concentra o risco de exposicao de segredos: as saidas de ferramenta (campo 'toolUseResult' e
# blocos 'tool_result'), os anexos, os snapshots de arquivo e o conteudo das mensagens de
# sistema. Um tipo de registro novo ou inesperado nunca passa intacto.

# Reescreve um bloco de conteudo de mensagem preservando apenas os campos de baixo risco.
def scrub_block:
  if type != "object" then "[block stripped]"
  elif .type == "text" then {type, text}
  elif .type == "thinking" then {type, thinking}
  elif .type == "tool_use" then {type, id, name, input}
  elif .type == "tool_result" then {type, tool_use_id, content: "[tool output stripped]"}
  elif .type == "image" then {type, source: "[image stripped]"}
  else {type, note: "[block stripped]"}
  end;

# Higieniza o corpo de uma mensagem 'user' ou 'assistant'. Um conteudo em cadeia e um prompt e e
# preservado; um conteudo em arranjo tem cada bloco reescrito por 'scrub_block'.
def scrub_message:
  if . == null then null
  elif .content == null then .
  elif (.content | type) == "array" then .content |= map(scrub_block)
  else .
  end;

# Campos de roteamento preservados nos registros de mensagem.
def keep_routing: {type, uuid, parentUuid, timestamp, sessionId};

if .type == "user" or .type == "assistant" then
  keep_routing + {message: (.message | scrub_message)}
elif .type == "attachment" then
  keep_routing + {attachment: "[attachment stripped]"}
elif .type == "file-history-snapshot" then
  {type, messageId, snapshot: "[snapshot stripped]"}
elif .type == "system" then
  keep_routing + {subtype, level, content: "[system content stripped]"}
elif .type == "mode" then
  {type, sessionId, mode}
elif .type == "ai-title" then
  {type, sessionId, aiTitle}
elif .type == "last-prompt" then
  {type, sessionId, leafUuid, lastPrompt}
elif .type == "agent-name" then
  {type, sessionId, agentName}
elif .type == "permission-mode" then
  {type, sessionId, permissionMode}
elif .type == "queue-operation" then
  {type, sessionId, timestamp, operation, content}
else
  {type: (.type // "unknown"), note: "[unknown record type stripped]"}
end
