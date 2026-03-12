package providers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/matheus-petrato/sales-copilot-back/pkg/agent"
	"github.com/sashabaranov/go-openai"
)

type MercuryProvider struct {
	client  *openai.Client
	model   string
	apiKey  string
	baseURL string
}

func NewMercuryProvider(apiKey string, model string, baseURL string) *MercuryProvider {
	if baseURL == "" {
		baseURL = "https://api.inceptionlabs.ai/v1"
	}
	config := openai.DefaultConfig(apiKey)
	config.BaseURL = baseURL

	return &MercuryProvider{
		client:  openai.NewClientWithConfig(config),
		model:   model,
		apiKey:  apiKey,
		baseURL: baseURL,
	}
}

func (p *MercuryProvider) Chat(
	ctx context.Context,
	messages []agent.Message,
	tools []agent.ToolDefinition,
	options map[string]any,
) (*agent.LLMResponse, error) {
	// Map messages to OpenAI format
	openAIMessages := make([]openai.ChatCompletionMessage, 0, len(messages))
	for _, msg := range messages {
		oaMsg := openai.ChatCompletionMessage{
			Role:    msg.Role,
			Content: msg.Content,
		}

		if len(msg.ToolCalls) > 0 {
			oaMsg.ToolCalls = make([]openai.ToolCall, 0, len(msg.ToolCalls))
			for _, tc := range msg.ToolCalls {
				oaMsg.ToolCalls = append(oaMsg.ToolCalls, openai.ToolCall{
					ID:   tc.ID,
					Type: openai.ToolTypeFunction,
					Function: openai.FunctionCall{
						Name:      tc.Name,
						Arguments: tc.Function.Arguments,
					},
				})
			}
		}

		if msg.ToolCallID != "" {
			oaMsg.ToolCallID = msg.ToolCallID
		}

		openAIMessages = append(openAIMessages, oaMsg)
	}

	// Map tools to OpenAI format
	var openAITools []openai.Tool
	if len(tools) > 0 {
		openAITools = make([]openai.Tool, 0, len(tools))
		for _, t := range tools {
			params, _ := json.Marshal(t.Function.Parameters)
			openAITools = append(openAITools, openai.Tool{
				Type: openai.ToolTypeFunction,
				Function: &openai.FunctionDefinition{
					Name:        t.Function.Name,
					Description: t.Function.Description,
					Parameters:  json.RawMessage(params),
				},
			})
		}
	}

	// Custom request for Mercury models to support reasoning
	reqMap := map[string]any{
		"model":             p.model,
		"messages":          openAIMessages,
		"reasoning_effort":  "medium",
		"reasoning_summary": true,
	}
	if len(openAITools) > 0 {
		reqMap["tools"] = openAITools
	}

	// Custom response types to capture reasoning_summary
	type customChoice struct {
		Index   int `json:"index"`
		Message struct {
			openai.ChatCompletionMessage
			ReasoningSummary string `json:"reasoning_summary"`
		} `json:"message"`
		FinishReason string `json:"finish_reason"`
	}
	type customResponse struct {
		openai.ChatCompletionResponse
		Choices []customChoice `json:"choices"`
	}

	url := p.baseURL + "/chat/completions"
	payload, _ := json.Marshal(reqMap)
	httpReq, _ := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(payload))
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+p.apiKey)

	httpResp, err := http.DefaultClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("http request failed: %w", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != 200 {
		var errBody map[string]any
		json.NewDecoder(httpResp.Body).Decode(&errBody)
		return nil, fmt.Errorf("mercury api error (status %d): %v", httpResp.StatusCode, errBody)
	}

	var customResp customResponse
	if err := json.NewDecoder(httpResp.Body).Decode(&customResp); err != nil {
		return nil, fmt.Errorf("failed to decode mercury response: %w", err)
	}

	if len(customResp.Choices) == 0 {
		return nil, fmt.Errorf("mercury returned no choices")
	}

	choice := customResp.Choices[0].Message
	result := &agent.LLMResponse{
		Content:   choice.Content,
		Reasoning: choice.ReasoningSummary,
		Usage: agent.UsageInfo{
			PromptTokens:     customResp.Usage.PromptTokens,
			CompletionTokens: customResp.Usage.CompletionTokens,
			TotalTokens:      customResp.Usage.TotalTokens,
		},
	}

	if len(choice.ToolCalls) > 0 {
		result.ToolCalls = make([]agent.ToolCall, 0, len(choice.ToolCalls))
		for _, tc := range choice.ToolCalls {
			result.ToolCalls = append(result.ToolCalls, agent.ToolCall{
				ID:   tc.ID,
				Type: "function",
				Name: tc.Function.Name,
				Function: &agent.FunctionCall{
					Name:      tc.Function.Name,
					Arguments: tc.Function.Arguments,
				},
			})
		}
	}

	return result, nil
}

func (p *MercuryProvider) GetDefaultModel() string {
	return p.model
}
