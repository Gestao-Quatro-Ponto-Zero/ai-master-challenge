package agent

import (
	"context"

	"github.com/matheus-petrato/sales-copilot-back/pkg/agent/protocoltypes"
)

type (
	Message                = protocoltypes.Message
	ToolCall               = protocoltypes.ToolCall
	FunctionCall           = protocoltypes.FunctionCall
	LLMResponse            = protocoltypes.LLMResponse
	UsageInfo              = protocoltypes.UsageInfo
	ToolDefinition         = protocoltypes.ToolDefinition
	ToolFunctionDefinition = protocoltypes.ToolFunctionDefinition
)

// LLMProvider defines the interface for different AI models
type LLMProvider interface {
	Chat(
		ctx context.Context,
		messages []Message,
		tools []ToolDefinition,
		options map[string]any,
	) (*LLMResponse, error)
	GetDefaultModel() string
}

// Tool defines the interface for capabilities the agent can use
type Tool interface {
	Name() string
	Description() string
	Parameters() map[string]any
	Execute(ctx context.Context, args map[string]any) (*ToolResult, error)
}

// ToolResult represents the output of a tool execution
type ToolResult struct {
	Content string // Content to be sent back to the LLM
	Data    any    // Structured data for internal app use
	Error   error
}

// AgentResponse is the response format that the backend will use
type AgentResponse struct {
	Text      string        // Final text answer for the user
	ToolCalls []ToolCall    // Any tools that were called
	Actions   []AgentAction // High-level actions processed
}

// AgentAction represents a structured operation to be performed by the system
type AgentAction struct {
	Type string
	Data any
}
