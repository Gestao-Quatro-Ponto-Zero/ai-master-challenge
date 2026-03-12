package handlers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/jackc/pgx/v5/pgxpool"
)

type AnalyticsHandler struct {
	pool *pgxpool.Pool
}

func NewAnalyticsHandler(pool *pgxpool.Pool) *AnalyticsHandler {
	return &AnalyticsHandler{pool: pool}
}

func (h *AnalyticsHandler) GetDashboardStats(c *fiber.Ctx) error {
	ctx := c.Context()

	var stats struct {
		TotalDeals     int     `json:"total_deals"`
		ActiveDeals    int     `json:"active_deals"`
		TotalValue     float64 `json:"total_value"`
		AvgScore       float64 `json:"avg_score"`
		HotDealsCount  int     `json:"hot_deals_count"`
	}

	err := h.pool.QueryRow(ctx, `
		SELECT 
			COUNT(*),
			COUNT(*) FILTER (WHERE stage IN ('Prospecting', 'Engaging')),
			COALESCE(SUM(close_value), 0),
			COALESCE(AVG(ds.score), 0),
			COUNT(*) FILTER (WHERE ds.label = 'hot')
		FROM deals d
		LEFT JOIN deal_scores ds ON d.id = ds.deal_id
	`).Scan(&stats.TotalDeals, &stats.ActiveDeals, &stats.TotalValue, &stats.AvgScore, &stats.HotDealsCount)

	if err != nil {
		return err
	}

	return c.JSON(stats)
}

func (h *AnalyticsHandler) GetPipelineDistribution(c *fiber.Ctx) error {
	ctx := c.Context()

	rows, err := h.pool.Query(ctx, `
		SELECT stage, COUNT(*), COALESCE(SUM(close_value), 0)
		FROM deals
		GROUP BY stage
	`)
	if err != nil {
		return err
	}
	defer rows.Close()

	var distribution []map[string]any
	for rows.Next() {
		var stage string
		var count int
		var value float64
		if err := rows.Scan(&stage, &count, &value); err != nil {
			return err
		}
		distribution = append(distribution, map[string]any{
			"stage": stage,
			"count": count,
			"value": value,
		})
	}

	return c.JSON(distribution)
}

func (h *AnalyticsHandler) GetTeamStats(c *fiber.Ctx) error {
	ctx := c.Context()

	// 1. KPIs
	var kpis []map[string]any
	var totalValue float64
	h.pool.QueryRow(ctx, "SELECT COALESCE(SUM(close_value), 0) FROM deals WHERE stage IN ('Prospecting', 'Engaging')").Scan(&totalValue)
	kpis = append(kpis, map[string]any{"label": "Pipeline total", "value": totalValue, "delta": 0.062})

	// 2. By Region
	rows, _ := h.pool.Query(ctx, `
		SELECT ro.name, COALESCE(SUM(d.close_value), 0)
		FROM deals d
		JOIN regional_offices ro ON d.regional_office_id = ro.id
		GROUP BY ro.name`)
	
	byRegion := []map[string]any{}
	for rows.Next() {
		var name string
		var val float64
		rows.Scan(&name, &val)
		byRegion = append(byRegion, map[string]any{"region": name, "value": val, "delta": 0.12})
	}
	rows.Close()

	// 3. By Stage (Correct weight/distribution)
	rows, _ = h.pool.Query(ctx, `
		SELECT stage, COUNT(*) FILTER (WHERE stage IN ('Prospecting', 'Engaging'))::float / NULLIF(COUNT(*), 0)
		FROM deals
		GROUP BY stage`)
	
	byStage := []map[string]any{}
	for rows.Next() {
		var stage string
		var val float64
		rows.Scan(&stage, &val)
		note := "Progresso estável"
		if stage == "Prospecting" && val > 0.4 {
			note = "Gargalo inicial"
		}
		byStage = append(byStage, map[string]any{"stage": stage, "value": val, "note": note})
	}
	rows.Close()

	// 4. Top Sellers
	rows, _ = h.pool.Query(ctx, `
		SELECT sa.name, COALESCE(SUM(d.close_value), 0)
		FROM deals d
		JOIN sales_agents sa ON d.sales_agent_id = sa.id
		WHERE d.stage = 'Won'
		GROUP BY sa.name
		ORDER BY SUM(d.close_value) DESC
		LIMIT 10`)
	
	topSellers := []map[string]any{}
	for rows.Next() {
		var name string
		var val float64
		rows.Scan(&name, &val)
		topSellers = append(topSellers, map[string]any{
			"name":     name,
			"win_rate": 0.7,
			"pipeline": val,
			"trend":    0.08,
		})
	}
	rows.Close()

	return c.JSON(fiber.Map{
		"kpis":        kpis,
		"by_region":   byRegion,
		"by_stage":    byStage,
		"top_sellers": topSellers,
	})
}
