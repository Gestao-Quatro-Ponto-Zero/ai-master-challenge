package services

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/matheus-petrato/sales-copilot-back/pkg/scoring"
)

type DataConnector struct {
	pool *pgxpool.Pool
}

func NewDataConnector(pool *pgxpool.Pool) *DataConnector {
	return &DataConnector{pool: pool}
}

func (s *DataConnector) GetPool() *pgxpool.Pool {
	return s.pool
}

// DealDTO is the representation for the pipeline list
type DealDTO struct {
	ID     uuid.UUID `json:"id"`
	Name   string    `json:"name"`
	Score  int       `json:"score"`
	Stage  string    `json:"stage"`
	Days   int       `json:"days"`
	Value  float64   `json:"value"`
	Trend  float64   `json:"trend"`
	Status string    `json:"status"` // hot, risk, stalled
	Action string    `json:"action"`
}

type DealFilter struct {
	Status    string
	Stage     string
	SellerID  string
	ManagerID string
	Region    string
}

func (s *DataConnector) FetchDeals(ctx context.Context, filter DealFilter) ([]DealDTO, error) {
	query := `
		SELECT 
			d.id, COALESCE(acc.name, 'Unknown'), ds.score, d.stage, 
			EXTRACT(DAY FROM (NOW() - d.engage_date)) as days,
			COALESCE(p.sales_price, 0), ds.label
		FROM deals d
		JOIN products p ON d.product_id = p.id
		LEFT JOIN accounts acc ON d.account_id = acc.id
		LEFT JOIN deal_scores ds ON d.id = ds.deal_id
		WHERE 1=1
	`
	var args []any
	argID := 1

	if filter.Status != "" {
		query += fmt.Sprintf(" AND ds.label = $%d", argID)
		args = append(args, filter.Status)
		argID++
	}
	if filter.Stage != "" {
		query += fmt.Sprintf(" AND d.stage = $%d", argID)
		args = append(args, filter.Stage)
		argID++
	}
	if filter.SellerID != "" {
		query += fmt.Sprintf(" AND d.sales_agent_id = $%d", argID)
		args = append(args, filter.SellerID)
		argID++
	}
	if filter.ManagerID != "" {
		query += fmt.Sprintf(" AND sa.manager_id = $%d", argID)
		args = append(args, filter.ManagerID)
		argID++
	}
	if filter.Region != "" {
		query += fmt.Sprintf(" AND d.regional_office_id = (SELECT id FROM regional_offices WHERE name = $%d)", argID)
		args = append(args, filter.Region)
		argID++
	}

	query += " ORDER BY ds.score DESC LIMIT 100"

	rows, err := s.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var deals []DealDTO
	for rows.Next() {
		var d DealDTO
		var labelOpt *string
		var scoreOpt *int
		var daysOpt *float64
		err := rows.Scan(&d.ID, &d.Name, &scoreOpt, &d.Stage, &daysOpt, &d.Value, &labelOpt)
		if err != nil {
			return nil, err
		}
		if scoreOpt != nil { d.Score = *scoreOpt }
		if labelOpt != nil { d.Status = *labelOpt }
		if daysOpt != nil { d.Days = int(*daysOpt) }
		
		// Fill defaults
		d.Trend = 0.12 // Simulated
		if d.Status == "hot" {
			d.Action = "Agendar call final"
		} else if d.Status == "zombie" {
			d.Status = "risk"
			d.Action = "Reengajar sponsor"
		} else {
			d.Action = "Acompanhar progresso"
		}
		
		deals = append(deals, d)
	}
	return deals, nil
}

func (s *DataConnector) FetchDealDetail(ctx context.Context, dealID uuid.UUID) (map[string]any, error) {
	var oppID, acc, product, stage, label, owner string
	var score int
	var factorsRaw []byte

	err := s.pool.QueryRow(ctx, `
		SELECT 
			d.opportunity_id, COALESCE(acc.name, 'Unknown'), p.name, d.stage, 
			COALESCE(ds.score, 0), COALESCE(ds.label, 'zombie'), 
			COALESCE(ds.factors, '[]'::jsonb), sa.name
		FROM deals d
		JOIN products p ON d.product_id = p.id
		JOIN sales_agents sa ON d.sales_agent_id = sa.id
		LEFT JOIN accounts acc ON d.account_id = acc.id
		LEFT JOIN deal_scores ds ON d.id = ds.deal_id
		WHERE d.id = $1`, dealID).Scan(
			&oppID, &acc, &product, &stage, &score, &label, &factorsRaw, &owner,
		)
	
	if err != nil {
		return nil, err
	}

	var factors []scoring.Factor
	json.Unmarshal(factorsRaw, &factors)

	status := label
	if status == "zombie" { status = "risk" }

	return map[string]any{
		"id":           dealID,
		"name":         acc,
		"score":        score,
		"stage":        stage,
		"days":         18, // Simulated
		"value":        150000, // Simulated
		"owner":        owner,
		"trend":        0.12,
		"status":       status,
		"factors":      factors,
		"next_actions": []string{"Agendar call de decisão com o sponsor"},
	}, nil
}
