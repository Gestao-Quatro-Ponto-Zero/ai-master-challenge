package handlers

import (
	"context"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

type AlertHandler struct {
	pool *pgxpool.Pool
}

func NewAlertHandler(pool *pgxpool.Pool) *AlertHandler {
	return &AlertHandler{pool: pool}
}

func (h *AlertHandler) GetAlerts(c *fiber.Ctx) error {
	userIDStr := c.Locals("user_id").(string)
	userID, _ := uuid.Parse(userIDStr)

	ctx := context.Background()

	// 1. Today's alerts
	rows, _ := h.pool.Query(ctx, `
		SELECT a.id, a.title, COALESCE(acc.name, 'Unknown'), a.type, a.action_url, to_char(a.created_at, 'HH24:MI')
		FROM alerts a
		LEFT JOIN deals d ON a.deal_id = d.id
		LEFT JOIN accounts acc ON d.account_id = acc.id
		WHERE a.user_id = $1 AND a.created_at >= CURRENT_DATE
		ORDER BY a.created_at DESC`, userID)
	
	todayAlerts := []map[string]any{}
	for rows.Next() {
		var id uuid.UUID
		var title, deal, alertType, action, timeStr string
		rows.Scan(&id, &title, &deal, &alertType, &action, &timeStr)
		todayAlerts = append(todayAlerts, map[string]any{
			"id":     id,
			"title":  title,
			"deal":   deal,
			"type":   alertType,
			"action": "Agendar call final", // Mock action
			"time":   timeStr,
		})
	}
	rows.Close()

	// 2. Week's alerts
	rows, _ = h.pool.Query(ctx, `
		SELECT a.id, a.title, COALESCE(acc.name, 'Unknown'), a.type, a.action_url, to_char(a.created_at, 'Dy, HH24:MI')
		FROM alerts a
		LEFT JOIN deals d ON a.deal_id = d.id
		LEFT JOIN accounts acc ON d.account_id = acc.id
		WHERE a.user_id = $1 AND a.created_at < CURRENT_DATE AND a.created_at >= CURRENT_DATE - INTERVAL '7 days'
		ORDER BY a.created_at DESC`, userID)
	
	weekAlerts := []map[string]any{}
	for rows.Next() {
		var id uuid.UUID
		var title, deal, alertType, action, timeStr string
		rows.Scan(&id, &title, &deal, &alertType, &action, &timeStr)
		weekAlerts = append(weekAlerts, map[string]any{
			"id":     id,
			"title":  title,
			"deal":   deal,
			"type":   alertType,
			"action": "Reengajar sponsor",
			"time":   timeStr,
		})
	}
	rows.Close()

	return c.JSON(fiber.Map{
		"today": todayAlerts,
		"week":  weekAlerts,
	})
}
