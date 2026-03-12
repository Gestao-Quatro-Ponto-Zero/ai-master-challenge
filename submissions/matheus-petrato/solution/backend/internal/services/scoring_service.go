package services

import (
	"context"
	"encoding/json"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/matheus-petrato/sales-copilot-back/pkg/scoring"
	"github.com/rs/zerolog/log"
)

// ScoringService recalculates and persists deal scores
type ScoringService struct {
	pool   *pgxpool.Pool
	engine *scoring.ScoringEngine
}

func NewScoringService(pool *pgxpool.Pool) *ScoringService {
	return &ScoringService{
		pool:   pool,
		engine: scoring.NewScoringEngine(pool),
	}
}

// RecalculateAllDealScores fetches all deals, calculates scores and upserts into deal_scores
func (s *ScoringService) RecalculateAllDealScores(ctx context.Context) (int, error) {
	rows, err := s.pool.Query(ctx, "SELECT id FROM deals WHERE stage IN ('Prospecting', 'Engaging')")
	if err != nil {
		return 0, err
	}
	defer rows.Close()

	var dealIDs []uuid.UUID
	for rows.Next() {
		var id uuid.UUID
		if err := rows.Scan(&id); err != nil {
			return 0, err
		}
		dealIDs = append(dealIDs, id)
	}

	count := 0
	for _, dealID := range dealIDs {
		result, err := s.engine.CalculateDealScore(ctx, dealID)
		if err != nil {
			log.Warn().Err(err).Str("deal_id", dealID.String()).Msg("failed to calculate deal score, skipping")
			continue
		}

		reasonsJSON, _ := json.Marshal(result.Reasons)
		factorsJSON, _ := json.Marshal(result.Factors)

		_, err = s.pool.Exec(ctx, `
			INSERT INTO deal_scores (id, deal_id, score, label, reasons, factors)
			VALUES ($1, $2, $3, $4, $5, $6)
			ON CONFLICT (deal_id) DO UPDATE SET
				score = EXCLUDED.score,
				label = EXCLUDED.label,
				reasons = EXCLUDED.reasons,
				factors = EXCLUDED.factors,
				calculated_at = NOW()`,
			uuid.Must(uuid.NewV7()), dealID, result.Score, result.Label, reasonsJSON, factorsJSON)
		if err != nil {
			log.Warn().Err(err).Str("deal_id", dealID.String()).Msg("failed to persist deal score")
			continue
		}
		count++
	}

	return count, nil
}
