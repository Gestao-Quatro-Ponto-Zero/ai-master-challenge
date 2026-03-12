package handlers

import (
	"strconv"

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

	limit, _ := strconv.Atoi(c.Query("limit"))
	offset, _ := strconv.Atoi(c.Query("offset"))
	if limit <= 0 {
		limit = 20
	}

	filter := services.DealFilter{
		Status:    c.Query("status"),
		Stage:     c.Query("stage"),
		SellerID:  c.Query("seller_id"),
		ManagerID: c.Query("manager_id"),
		Region:    c.Query("region"),
		Limit:     limit,
		Offset:    offset,
	}

	// SECURITY: Enforce role-based restrictions
	if role == "seller" {
		ctx := c.Context()
		var agentID uuid.UUID
		err := h.Connector.GetPool().QueryRow(ctx, "SELECT sales_agent_id FROM users WHERE id = $1", userID).Scan(&agentID)
		if err != nil {
			return fiber.NewError(fiber.StatusForbidden, "Agent context not found")
		}
		filter.SellerID = agentID.String()
		filter.Region = ""
	}

	result, err := h.Connector.FetchDeals(c.Context(), filter)
	if err != nil {
		return err
	}

	return c.JSON(result)
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
