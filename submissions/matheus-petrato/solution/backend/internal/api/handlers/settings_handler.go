package handlers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/jackc/pgx/v5/pgxpool"
)

type SettingsHandler struct {
	pool *pgxpool.Pool
}

func NewSettingsHandler(pool *pgxpool.Pool) *SettingsHandler {
	return &SettingsHandler{pool: pool}
}

func (h *SettingsHandler) GetSettings(c *fiber.Ctx) error {
	// userIDStr := c.Locals("user_id").(string)
	
	// Mock preferences for now
	return c.JSON(fiber.Map{
		"notifications": true,
		"briefing_time": "08:00",
		"alert_preferences": map[string]bool{
			"hot_deals": true,
			"risk_deals": true,
		},
	})
}

func (h *SettingsHandler) UpdateSettings(c *fiber.Ctx) error {
	var req map[string]any
	if err := c.BodyParser(&req); err != nil {
		return err
	}
	
	return c.JSON(fiber.Map{
		"message": "Settings updated",
		"settings": req,
	})
}
