package handlers

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/websocket/v2"
	"github.com/golang-jwt/jwt/v5"
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

	convID, text, err := h.runAgent(c.Context(), userID, req)
	if err != nil {
		return err
	}

	// SSE Streaming
	c.Set("Content-Type", "text/event-stream")
	c.Set("Cache-Control", "no-cache")
	c.Set("Connection", "keep-alive")

	c.Context().SetBodyStreamWriter(fasthttp.StreamWriter(func(w *bufio.Writer) {
		jsonResp, _ := json.Marshal(map[string]any{
			"text":       text,
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

func (h *ChatHandler) WebSocketChat(c *websocket.Conn) {
	tokenString := c.Query("token")
	if tokenString == "" {
		_ = c.WriteJSON(fiber.Map{"error": "Missing token"})
		return
	}

	claims, err := parseJWT(tokenString)
	if err != nil {
		_ = c.WriteJSON(fiber.Map{"error": "Invalid token"})
		return
	}

	userIDStr := fmt.Sprintf("%v", claims["sub"])
	userID, _ := uuid.Parse(userIDStr)

	for {
		_, msg, err := c.ReadMessage()
		if err != nil {
			break
		}

		var req ChatRequest
		if err := json.Unmarshal(msg, &req); err != nil {
			_ = c.WriteJSON(fiber.Map{"error": "Invalid message"})
			continue
		}

		convID, text, err := h.runAgent(context.Background(), userID, req)
		if err != nil {
			_ = c.WriteJSON(fiber.Map{"error": err.Error()})
			continue
		}

		_ = c.WriteJSON(map[string]any{
			"channel":      "web",
			"chat_id":      userID.String(),
			"session_id":   convID.String(),
			"content":      text,
			"stream_state": "chunk",
		})
		_ = c.WriteJSON(map[string]any{
			"channel":      "web",
			"chat_id":      userID.String(),
			"session_id":   convID.String(),
			"content":      "",
			"stream_state": "done",
		})
	}
}

func parseJWT(tokenString string) (jwt.MapClaims, error) {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = "super-secret-key"
	}

	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fiber.NewError(fiber.StatusUnauthorized, "Unexpected signing method")
		}
		return []byte(secret), nil
	})

	if err != nil || !token.Valid {
		return nil, fiber.NewError(fiber.StatusUnauthorized, "Invalid or expired token")
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, fiber.NewError(fiber.StatusUnauthorized, "Invalid token claims")
	}

	return claims, nil
}

func (h *ChatHandler) runAgent(ctx context.Context, userID uuid.UUID, req ChatRequest) (uuid.UUID, string, error) {
	var convID uuid.UUID
	if req.SessionID != "" {
		convID, _ = uuid.Parse(req.SessionID)
	}

	if convID == uuid.Nil {
		conv, err := h.ConvService.CreateConversation(ctx, userID, nil)
		if err != nil {
			return uuid.Nil, "", err
		}
		convID = conv.ID
	}

	history, _ := h.ConvService.GetHistory(ctx, convID)

	apiKey := os.Getenv("MERCURY_API_KEY")
	model := os.Getenv("MERCURY_MODEL")
	provider := providers.NewMercuryProvider(apiKey, model, "")
	al := agent.NewAgentLoop(provider)

	agentID := uuid.MustParse("018e3000-0000-0000-0000-000000000000")
	al.Tools.Register(&services.GetMyDealsTool{BaseAgentTool: services.BaseAgentTool{Connector: h.DataConnector, AgentID: agentID}})
	al.Tools.Register(&services.GetDealDetailTool{BaseAgentTool: services.BaseAgentTool{Connector: h.DataConnector, AgentID: agentID}})
	al.Tools.Register(&services.SearchDealsTool{BaseAgentTool: services.BaseAgentTool{Connector: h.DataConnector, AgentID: agentID}})

	messages := []agent.Message{
		{Role: "system", Content: agent.CompassSystemPrompt},
	}
	for _, m := range history {
		messages = append(messages, agent.Message{Role: m.Role, Content: m.Content})
	}
	messages = append(messages, agent.Message{Role: "user", Content: req.Content})

	h.ConvService.SaveMessage(ctx, convID, "user", req.Content, nil)

	resp, err := al.Run(context.Background(), messages)
	if err != nil {
		return convID, "", err
	}

	h.ConvService.SaveMessage(context.Background(), convID, "assistant", resp.Text, nil)
	return convID, resp.Text, nil
}
