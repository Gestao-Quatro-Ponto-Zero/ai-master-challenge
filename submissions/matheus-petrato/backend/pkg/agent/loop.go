package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/rs/zerolog/log"
)

const (
	colorReset  = "\033[0m"
	colorCyan   = "\033[36m"
	colorPurple = "\033[35m"
	colorBlue   = "\033[34m"
	colorGreen  = "\033[32m"
	colorYellow = "\033[33m"
	colorRed    = "\033[31m"
)

type AgentLoop struct {
	Provider      LLMProvider
	Tools         *ToolRegistry
	MaxIterations int
}

func NewAgentLoop(provider LLMProvider) *AgentLoop {
	return &AgentLoop{
		Provider:      provider,
		Tools:         NewToolRegistry(),
		MaxIterations: 10,
	}
}

func (al *AgentLoop) Run(ctx context.Context, messages []Message) (*AgentResponse, error) {
	runID := "run_" + time.Now().Format("20060102150405")
	
	runLog := log.With().
		Str("agent_run_id", runID).
		Str("model", al.Provider.GetDefaultModel()).
		Logger()

	iteration := 0
	agentMessages := make([]Message, len(messages))
	copy(agentMessages, messages)

	toolDefs := al.Tools.ToProviderDefs()
	finalResponse := &AgentResponse{}
	totalUsage := UsageInfo{}

	for iteration < al.MaxIterations {
		iteration++

		runLog.Info().
			Int("iteration", iteration).
			Msg("Agent reasoning...")
		
		resp, err := al.Provider.Chat(ctx, agentMessages, toolDefs, nil)
		if err != nil {
			runLog.Error().Err(err).Msg("LLM call failed")
			return nil, fmt.Errorf("llm call failed: %w", err)
		}

		totalUsage.PromptTokens += resp.Usage.PromptTokens
		totalUsage.CompletionTokens += resp.Usage.CompletionTokens
		totalUsage.TotalTokens += resp.Usage.TotalTokens

		if resp.Reasoning != "" {
			runLog.Info().Msg(colorCyan + "[🧠 MERCURY REASONING] " + resp.Reasoning + colorReset)
		}

		if resp.Content != "" {
			runLog.Info().Msg(colorPurple + "[🧑🏼‍💻 AGENT THOUGHT] " + resp.Content + colorReset)
		}

		agentMessages = append(agentMessages, Message{
			Role:      "assistant",
			Content:   resp.Content,
			ToolCalls: resp.ToolCalls,
		})

		if len(resp.ToolCalls) == 0 {
			runLog.Info().
				Int("total_iterations", iteration).
				Int("total_tokens", totalUsage.TotalTokens).
				Msg(colorGreen + "[🤖 AGENT FINAL RESPONSE] " + resp.Content + colorReset)

			finalResponse.Text = resp.Content
			return finalResponse, nil
		}

		finalResponse.ToolCalls = append(finalResponse.ToolCalls, resp.ToolCalls...)

		runLog.Info().
			Int("tool_count", len(resp.ToolCalls)).
			Msg(colorYellow + "[🛠️ AGENT ACTION] Agent decided to use tools" + colorReset)

		var wg sync.WaitGroup
		var mu sync.Mutex

		toolResults := make([]Message, len(resp.ToolCalls))
		var toolActions []AgentAction

		for i, tc := range resp.ToolCalls {
			wg.Add(1)
			go func(index int, toolCall ToolCall) {
				defer wg.Done()

				var args map[string]any
				var toolContent string
				var action *AgentAction

				if err := json.Unmarshal([]byte(toolCall.Function.Arguments), &args); err != nil {
					toolContent = fmt.Sprintf("Error: failed to unmarshal arguments: %v", err)
				} else {
					result, err := al.Tools.Execute(ctx, toolCall.Name, args)
					if err != nil {
						toolContent = fmt.Sprintf("Error: %v", err)
					} else {
						toolContent = result.Content
						if result.Data != nil {
							action = &AgentAction{
								Type: toolCall.Name,
								Data: result.Data,
							}
						}
					}
				}

				mu.Lock()
				toolResults[index] = Message{
					Role:       "tool",
					Content:    toolContent,
					ToolCallID: toolCall.ID,
				}
				if action != nil {
					toolActions = append(toolActions, *action)
				}
				mu.Unlock()

			}(i, tc)
		}

		wg.Wait()
		agentMessages = append(agentMessages, toolResults...)
		if len(toolActions) > 0 {
			finalResponse.Actions = append(finalResponse.Actions, toolActions...)
		}
	}

	return nil, fmt.Errorf("exceeded max iterations (%d)", al.MaxIterations)
}
