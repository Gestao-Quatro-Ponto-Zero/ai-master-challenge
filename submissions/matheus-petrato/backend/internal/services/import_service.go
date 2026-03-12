package services

import (
	"context"
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog/log"
)

// CSVMapping defines how CSV columns map to model fields
type CSVMapping map[string]string

// ImportService handles the logic for importing data from CSV files
type ImportService struct {
	pool *pgxpool.Pool
}

func NewImportService(pool *pgxpool.Pool) *ImportService {
	return &ImportService{pool: pool}
}

func (s *ImportService) GetPool() *pgxpool.Pool {
	return s.pool
}

// ReadCSV reads a CSV file and returns a slice of maps (column -> value)
func (s *ImportService) ReadCSV(filePath string) ([]map[string]string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	reader.TrimLeadingSpace = true

	header, err := reader.Read()
	if err != nil {
		return nil, fmt.Errorf("failed to read header: %w", err)
	}

	for i, h := range header {
		header[i] = strings.ToLower(strings.TrimSpace(h))
	}

	var results []map[string]string
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to read record: %w", err)
		}

		row := make(map[string]string)
		for i, value := range record {
			if i < len(header) {
				row[header[i]] = strings.TrimSpace(value)
			}
		}
		results = append(results, row)
	}

	return results, nil
}

// ValidateDeals checks if the CSV data for deals is valid
func (s *ImportService) ValidateDeals(data []map[string]string) []map[string]any {
	var errors []map[string]any
	required := []string{"opportunity_id", "sales_agent", "product", "deal_stage"}

	for i, row := range data {
		for _, field := range required {
			if row[field] == "" {
				errors = append(errors, map[string]any{
					"row":   i + 1,
					"field": field,
					"error": "required field is missing",
				})
			}
		}

		stage := row["deal_stage"]
		if stage != "" {
			validStages := map[string]bool{
				"Prospecting": true,
				"Engaging":    true,
				"Won":         true,
				"Lost":        true,
			}
			if !validStages[stage] {
				errors = append(errors, map[string]any{
					"row":   i + 1,
					"field": "deal_stage",
					"error": fmt.Sprintf("invalid stage: %s", stage),
				})
			}
		}
	}

	return errors
}

// ValidateAccounts checks if the CSV data for accounts is valid
func (s *ImportService) ValidateAccounts(data []map[string]string) []map[string]any {
	var errors []map[string]any
	required := []string{"account"}

	for i, row := range data {
		for _, field := range required {
			if row[field] == "" {
				errors = append(errors, map[string]any{
					"row":   i + 1,
					"field": field,
					"error": "required field is missing",
				})
			}
		}
	}

	return errors
}

// ValidateProducts checks if the CSV data for products is valid
func (s *ImportService) ValidateProducts(data []map[string]string) []map[string]any {
	var errors []map[string]any
	required := []string{"product", "sales_price"}

	for i, row := range data {
		for _, field := range required {
			if row[field] == "" {
				errors = append(errors, map[string]any{
					"row":   i + 1,
					"field": field,
					"error": "required field is missing",
				})
			}
		}
	}

	return errors
}

// ImportTeam processes the sales_teams.csv data
func (s *ImportService) ImportTeam(ctx context.Context, data []map[string]string) error {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	for _, row := range data {
		roID, _ := uuid.NewV7()
		err = tx.QueryRow(ctx, `
			INSERT INTO regional_offices (id, name)
			VALUES ($1, $2)
			ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
			RETURNING id`,
			roID, row["regional_office"]).Scan(&roID)
		if err != nil {
			log.Error().Err(err).Msg("failed to get/create regional office")
			continue
		}

		mID, _ := uuid.NewV7()
		err = tx.QueryRow(ctx, `
			INSERT INTO managers (id, name, regional_office_id, source)
			VALUES ($1, $2, $3, 'csv')
			ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
			RETURNING id`,
			mID, row["manager"], roID).Scan(&mID)
		if err != nil {
			log.Error().Err(err).Msg("failed to get/create manager")
			continue
		}

		aID, _ := uuid.NewV7()
		_, err = tx.Exec(ctx, `
			INSERT INTO sales_agents (id, name, manager_id, regional_office_id, source)
			VALUES ($1, $2, $3, $4, 'csv')
			ON CONFLICT (name) DO UPDATE SET updated_at = NOW()`,
			aID, row["sales_agent"], mID, roID)
		if err != nil {
			continue
		}
	}

	return tx.Commit(ctx)
}

// ImportAccounts processes the accounts.csv data
func (s *ImportService) ImportAccounts(ctx context.Context, data []map[string]string) error {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	for _, row := range data {
		id, _ := uuid.NewV7()
		_, err = tx.Exec(ctx, `
			INSERT INTO accounts (id, name, sector, year_established, revenue_millions, employees, office_location, subsidiary_of, source)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'csv')
			ON CONFLICT (name) DO UPDATE SET updated_at = NOW()`,
			id, row["account"], row["sector"], row["year_established"], row["revenue"], row["employees"], row["location"], row["subsidiary_of"])
		if err != nil {
			log.Error().Err(err).Str("account", row["account"]).Msg("failed to insert account")
		}
	}

	return tx.Commit(ctx)
}

// ImportProducts processes the products.csv data
func (s *ImportService) ImportProducts(ctx context.Context, data []map[string]string) error {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	for _, row := range data {
		id, _ := uuid.NewV7()
		_, err = tx.Exec(ctx, `
			INSERT INTO products (id, name, series, sales_price, source)
			VALUES ($1, $2, $3, $4, 'csv')
			ON CONFLICT (name) DO UPDATE SET updated_at = NOW()`,
			id, row["product"], row["series"], row["sales_price"])
		if err != nil {
			log.Error().Err(err).Str("product", row["product"]).Msg("failed to insert product")
		}
	}

	return tx.Commit(ctx)
}

// ImportDeals processes the sales_pipeline.csv data
func (s *ImportService) ImportDeals(ctx context.Context, data []map[string]string) error {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	for _, row := range data {
		id, _ := uuid.NewV7()
		
		var agentID, productID uuid.UUID

		err = tx.QueryRow(ctx, "SELECT id FROM sales_agents WHERE name = $1", row["sales_agent"]).Scan(&agentID)
		if err != nil {
			continue
		}

		err = tx.QueryRow(ctx, "SELECT id FROM products WHERE name = $1", row["product"]).Scan(&productID)
		if err != nil {
			continue
		}

		var accountID *uuid.UUID
		if row["account"] != "" {
			var accID uuid.UUID
			err = tx.QueryRow(ctx, "SELECT id FROM accounts WHERE name = $1", row["account"]).Scan(&accID)
			if err == nil {
				accountID = &accID
			}
		}

		_, err = tx.Exec(ctx, `
			INSERT INTO deals (id, opportunity_id, sales_agent_id, product_id, account_id, stage, engage_date, close_date, close_value, source)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'csv')
			ON CONFLICT (opportunity_id) DO UPDATE SET 
				stage = EXCLUDED.stage,
				close_date = EXCLUDED.close_date,
				close_value = EXCLUDED.close_value,
				updated_at = NOW()`,
			id, row["opportunity_id"], agentID, productID, accountID, row["deal_stage"], row["engage_date"], row["close_date"], row["close_value"])
		
		if err != nil {
			log.Error().Err(err).Str("opportunity", row["opportunity_id"]).Msg("failed to insert deal")
		}
	}

	return tx.Commit(ctx)
}
