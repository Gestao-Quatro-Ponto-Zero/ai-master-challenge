package protocoltypes

type Message struct {
	Role             string     `json:"role"`
	Content          string     `json:"content"`
	ToolCallID       string     `json:"tool_call_id,omitempty"`
	ToolCalls        []ToolCall `json:"tool_calls,omitempty"`
	ThoughtSignature string     `json:"thought_signature,omitempty"`
}

type ToolCall struct {
	ID               string        `json:"id"`
	Type             string        `json:"type"`
	Name             string        `json:"name"`
	Function         *FunctionCall `json:"function,omitempty"`
	ThoughtSignature string        `json:"thought_signature,omitempty"`
}

type FunctionCall struct {
	Name             string `json:"name"`
	Arguments        string `json:"arguments"`
	ThoughtSignature string `json:"thought_signature,omitempty"`
}

type LLMResponse struct {
	Content          string     `json:"content"`
	ToolCalls        []ToolCall `json:"tool_calls,omitempty"`
	ThoughtSignature string     `json:"thought_signature,omitempty"`
	Reasoning        string     `json:"reasoning,omitempty"`
	Usage            UsageInfo  `json:"usage,omitempty"`
}

type UsageInfo struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

type ToolDefinition struct {
	Type     string                 `json:"type"`
	Function ToolFunctionDefinition `json:"function"`
}

type ToolFunctionDefinition struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Parameters  map[string]any `json:"parameters"`
}
