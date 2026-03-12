package handlers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/matheus-petrato/sales-copilot-back/internal/services"
)

type DealHandler struct {
	Connector *services.DataConnector
}

func NewDealHandler(conn *services.DataConnector) *DealHandler {
	return &DealHandler{Connector: conn}
}

func (h *DealHandler) ListDeals(c *fiber.Ctx) error {
	role := c.Locals("role").(string)
	userIDStr := c.Locals("user_id").(string)
	userID, _ := uuid.Parse(userIDStr)

	filter := services.DealFilter{
		Status:    c.Query("status"),
		Stage:     c.Query("stage"),
		SellerID:  c.Query("seller_id"),
		ManagerID: c.Query("manager_id"),
		Region:    c.Query("region"),
	}

	// SECURITY: Enforce role-based restrictions
	if role == "seller" {
		// Seller can ONLY see their own deals.
		// We must find the sales_agent_id for this user_id.
		ctx := c.Context()
		var agentID uuid.UUID
		err := h.Connector.GetPool().QueryRow(ctx, "SELECT sales_agent_id FROM users WHERE id = $1", userID).Scan(&agentID)
		if err != nil {
			return fiber.NewError(fiber.StatusForbidden, "Agent context not found")
		}
		filter.SellerID = agentID.String()
		filter.Region = "" // Sellers cannot filter by region (they are fixed to one anyway)
	} else if role == "manager" {
		// Managers can filter by anyone, but optional: 
		// restrict to their team if manager_id is not specified?
		// For now, allow global if they are managers, as per doc.
	}

	deals, err := h.Connector.FetchDeals(c.Context(), filter)
	if err != nil {
		return err
	}

	return c.JSON(deals)
}

func (h *DealHandler) GetDeal(c *fiber.Ctx) error {
	idStr := c.Params("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "Invalid deal ID")
	}

	deal, err := h.Connector.FetchDealDetail(c.Context(), id)
	if err != nil {
		return err
	}

	return c.JSON(deal)
}
