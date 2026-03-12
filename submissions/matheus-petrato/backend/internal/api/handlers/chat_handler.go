package handlers

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/matheus-petrato/sales-copilot-back/internal/services"
	"github.com/matheus-petrato/sales-copilot-back/pkg/agent"
	"github.com/matheus-petrato/sales-copilot-back/pkg/agent/providers"
	"github.com/valyala/fasthttp"
)

type ChatHandler struct {
	ConvService   *services.ConversationService
	DataConnector *services.DataConnector
}

func NewChatHandler(conv *services.ConversationService, data *services.DataConnector) *ChatHandler {
	return &ChatHandler{
		ConvService:   conv,
		DataConnector: data,
	}
}

type ChatRequest struct {
	Content   string `json:"content"`
	SessionID string `json:"session_id,omitempty"`
}

func (h *ChatHandler) SendMessage(c *fiber.Ctx) error {
	var req ChatRequest
	if err := c.BodyParser(&req); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "Invalid request body")
	}

	userIDStr := c.Locals("user_id").(string)
	userID, _ := uuid.Parse(userIDStr)

	// Determine Session ID
	var convID uuid.UUID
	if req.SessionID != "" {
		convID, _ = uuid.Parse(req.SessionID)
	}

	if convID == uuid.Nil {
		conv, err := h.ConvService.CreateConversation(c.Context(), userID, nil)
		if err != nil {
			return err
		}
		convID = conv.ID
	}

	// Get History
	history, _ := h.ConvService.GetHistory(c.Context(), convID)

	// Setup Agent
	apiKey := os.Getenv("MERCURY_API_KEY")
	model := os.Getenv("MERCURY_MODEL")
	provider := providers.NewMercuryProvider(apiKey, model, "")
	al := agent.NewAgentLoop(provider)

	// Register Tools
	agentID := uuid.MustParse("018e3000-0000-0000-0000-000000000000") // TODO: get from profile context
	al.Tools.Register(&services.GetMyDealsTool{BaseAgentTool: services.BaseAgentTool{Connector: h.DataConnector, AgentID: agentID}})
	al.Tools.Register(&services.GetDealDetailTool{BaseAgentTool: services.BaseAgentTool{Connector: h.DataConnector, AgentID: agentID}})
	al.Tools.Register(&services.SearchDealsTool{BaseAgentTool: services.BaseAgentTool{Connector: h.DataConnector, AgentID: agentID}})

	// Convert history to agent messages
	messages := []agent.Message{
		{Role: "system", Content: agent.CompassSystemPrompt},
	}
	for _, m := range history {
		messages = append(messages, agent.Message{Role: m.Role, Content: m.Content})
	}
	messages = append(messages, agent.Message{Role: "user", Content: req.Content})

	// Save User Message
	h.ConvService.SaveMessage(c.Context(), convID, "user", req.Content, nil)

	// SSE Streaming
	c.Set("Content-Type", "text/event-stream")
	c.Set("Cache-Control", "no-cache")
	c.Set("Connection", "keep-alive")

	c.Context().SetBodyStreamWriter(fasthttp.StreamWriter(func(w *bufio.Writer) {
		resp, err := al.Run(context.Background(), messages)
		if err != nil {
			fmt.Fprintf(w, "event: error\ndata: %v\n\n", err)
			w.Flush()
			return
		}

		// Save Assistant Message
		h.ConvService.SaveMessage(context.Background(), convID, "assistant", resp.Text, nil)

		// Send final text
		jsonResp, _ := json.Marshal(map[string]any{
			"text":       resp.Text,
			"session_id": convID,
		})
		fmt.Fprintf(w, "event: message\ndata: %s\n\n", jsonResp)
		w.Flush()
	}))

	return nil
}

func (h *ChatHandler) GetHistory(c *fiber.Ctx) error {
	userIDStr := c.Locals("user_id").(string)
	userID, _ := uuid.Parse(userIDStr)

	sessionIDStr := c.Query("session_id")
	var sessionID uuid.UUID
	
	if sessionIDStr != "" {
		sessionID, _ = uuid.Parse(sessionIDStr)
	} else {
		// FALLBACK: Get latest conversation for this user
		ctx := c.Context()
		err := h.ConvService.GetPool().QueryRow(ctx, `
			SELECT id FROM conversations WHERE user_id = $1 ORDER BY started_at DESC LIMIT 1
		`, userID).Scan(&sessionID)
		
		if err != nil {
			return c.JSON([]any{}) // No history found
		}
	}

	history, err := h.ConvService.GetHistory(c.Context(), sessionID)
	if err != nil {
		return err
	}

	return c.JSON(history)
}
