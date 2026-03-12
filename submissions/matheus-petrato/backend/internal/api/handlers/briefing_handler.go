package handlers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

type BriefingHandler struct {
	pool *pgxpool.Pool
}

func NewBriefingHandler(pool *pgxpool.Pool) *BriefingHandler {
	return &BriefingHandler{pool: pool}
}

func (h *BriefingHandler) GetBriefing(c *fiber.Ctx) error {
	role := c.Locals("role").(string)
	userIDStr := c.Locals("user_id").(string)
	userID, _ := uuid.Parse(userIDStr)

	if role == "manager" {
		return h.getManagerBriefing(c, userID)
	}
	return h.getSellerBriefing(c, userID)
}

func (h *BriefingHandler) getSellerBriefing(c *fiber.Ctx, userID uuid.UUID) error {
	ctx := c.Context()

	// 1. Get Agent ID from User
	var agentID uuid.UUID
	err := h.pool.QueryRow(ctx, "SELECT sales_agent_id FROM users WHERE id = $1", userID).Scan(&agentID)
	if err != nil {
		return fiber.NewError(fiber.StatusNotFound, "Agent not found for user")
	}

	// 2. Aggregate KPIs
	var kpis []map[string]any
	var pipelineTotal float64
	h.pool.QueryRow(ctx, `
		SELECT COALESCE(SUM(close_value), 0)
		FROM deals
		WHERE sales_agent_id = $1 AND stage IN ('Prospecting', 'Engaging')`, agentID).Scan(&pipelineTotal)
	
	kpis = append(kpis, map[string]any{
		"label": "Pipeline total",
		"value": pipelineTotal,
		"delta": 0.062,
	})

	var riskCount int
	h.pool.QueryRow(ctx, `
		SELECT COUNT(*)
		FROM deals d
		JOIN deal_scores ds ON d.id = ds.deal_id
		WHERE d.sales_agent_id = $1 AND ds.label = 'zombie'`, agentID).Scan(&riskCount)
	
	kpis = append(kpis, map[string]any{
		"label": "Deals em risco",
		"value": riskCount,
		"delta": 4.0,
	})

	// 3. Hot Deals
	rows, _ := h.pool.Query(ctx, `
		SELECT d.id, acc.name, ds.score, d.stage, EXTRACT(DAY FROM (NOW() - d.engage_date)), p.sales_price
		FROM deals d
		JOIN products p ON d.product_id = p.id
		LEFT JOIN accounts acc ON d.account_id = acc.id
		JOIN deal_scores ds ON d.id = ds.deal_id
		WHERE d.sales_agent_id = $1 AND ds.label = 'hot'
		LIMIT 5`, agentID)
	
	hotDeals := []map[string]any{}
	for rows.Next() {
		var id uuid.UUID
		var name, stage string
		var score int
		var days float64
		var value float64
		rows.Scan(&id, &name, &score, &stage, &days, &value)
		hotDeals = append(hotDeals, map[string]any{
			"id":     id,
			"name":   name,
			"score":  score,
			"stage":  stage,
			"days":   int(days),
			"value":  value,
			"action": "Agendar call final",
		})
	}
	rows.Close()

	// 4. Risk Deals
	rows, _ = h.pool.Query(ctx, `
		SELECT d.id, acc.name, ds.score, d.stage, EXTRACT(DAY FROM (NOW() - d.engage_date)), p.sales_price
		FROM deals d
		JOIN products p ON d.product_id = p.id
		LEFT JOIN accounts acc ON d.account_id = acc.id
		JOIN deal_scores ds ON d.id = ds.deal_id
		WHERE d.sales_agent_id = $1 AND ds.label = 'zombie'
		LIMIT 5`, agentID)
	
	riskDeals := []map[string]any{}
	for rows.Next() {
		var id uuid.UUID
		var name, stage string
		var score int
		var days float64
		var value float64
		rows.Scan(&id, &name, &score, &stage, &days, &value)
		riskDeals = append(riskDeals, map[string]any{
			"id":     id,
			"name":   name,
			"score":  score,
			"stage":  stage,
			"days":   int(days),
			"value":  value,
			"action": "Reengajar sponsor",
		})
	}
	rows.Close()

	return c.JSON(fiber.Map{
		"kpis":       kpis,
		"hot_deals":  hotDeals,
		"risk_deals": riskDeals,
		"insights":   []string{"3 deals entraram na janela ideal esta semana."},
	})
}

func (h *BriefingHandler) getManagerBriefing(c *fiber.Ctx, userID uuid.UUID) error {
	ctx := c.Context()
	
	// 1. Get Manager ID
	var managerID uuid.UUID
	err := h.pool.QueryRow(ctx, "SELECT manager_id FROM users WHERE id = $1", userID).Scan(&managerID)
	if err != nil {
		return fiber.NewError(fiber.StatusNotFound, "Manager context not found")
	}

	// 2. Team Snapshot (Aggregate across all their sellers)
	var snapshot struct {
		TotalValue   float64 `json:"total_value"`
		ActiveAgents int     `json:"active_agents"`
		AvgHealth    float64 `json:"avg_health"`
	}

	h.pool.QueryRow(ctx, `
		SELECT 
			COALESCE(SUM(d.close_value), 0),
			COUNT(DISTINCT sa.id),
			COALESCE(AVG(ds.score), 0)
		FROM deals d
		JOIN sales_agents sa ON d.sales_agent_id = sa.id
		LEFT JOIN deal_scores ds ON d.id = ds.deal_id
		WHERE sa.manager_id = $1 AND d.stage IN ('Prospecting', 'Engaging')
	`, managerID).Scan(&snapshot.TotalValue, &snapshot.ActiveAgents, &snapshot.AvgHealth)

	// 3. Aggregate KPIs for Team
	kpis := []map[string]any{
		{"label": "Pipeline do Time", "value": snapshot.TotalValue, "delta": 0.08},
		{"label": "Saúde Média", "value": snapshot.AvgHealth, "delta": -0.02},
	}

	// 4. Critical Items across the team
	rows, _ := h.pool.Query(ctx, `
		SELECT d.id, acc.name, ds.score, sa.name, d.stage
		FROM deals d
		JOIN sales_agents sa ON d.sales_agent_id = sa.id
		JOIN accounts acc ON d.account_id = acc.id
		JOIN deal_scores ds ON d.id = ds.deal_id
		WHERE sa.manager_id = $1 AND ds.label = 'zombie'
		ORDER BY ds.score ASC LIMIT 5`, managerID)
	
	criticalDeals := []map[string]any{}
	for rows.Next() {
		var id uuid.UUID
		var acc, seller, stage string
		var score int
		rows.Scan(&id, &acc, &score, &seller, &stage)
		criticalDeals = append(criticalDeals, map[string]any{
			"id":     id,
			"name":   acc,
			"score":  score,
			"seller": seller,
			"stage":  stage,
		})
	}
	rows.Close()

	return c.JSON(fiber.Map{
		"team_snapshot": snapshot,
		"kpis":          kpis,
		"critical_deals": criticalDeals,
		"insights":      []string{"Time precisa focar em reengajar 5 deals críticos."},
	})
}
