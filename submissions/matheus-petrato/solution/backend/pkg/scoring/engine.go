package scoring

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/matheus-petrato/sales-copilot-back/internal/models"
)

type Factor struct {
	Name      string `json:"factor"`
	Impact    int    `json:"impact"`
	Detail    string `json:"detail"`
	Sentiment string `json:"sentiment"`
}

type ScoringEngine struct {
	pool *pgxpool.Pool
}

func NewScoringEngine(pool *pgxpool.Pool) *ScoringEngine {
	return &ScoringEngine{pool: pool}
}

type ScoreResult struct {
	Score   int
	Label   string
	Reasons []string
	Factors []Factor
}

func (e *ScoringEngine) CalculateDealScore(ctx context.Context, dealID uuid.UUID) (*ScoreResult, error) {
	// 1. Fetch deal data with related info
	var deal models.Deal
	var product models.Product
	var agent models.SalesAgent
	var account models.Account
	var hasAccount bool

	err := e.pool.QueryRow(ctx, `
		SELECT 
			d.id, d.stage, d.engage_date, d.close_date,
			p.id, p.name, p.sales_price,
			a.id, a.name, a.manager_id,
			acc.id, acc.revenue_millions, acc.sector
		FROM deals d
		JOIN products p ON d.product_id = p.id
		JOIN sales_agents a ON d.sales_agent_id = a.id
		LEFT JOIN accounts acc ON d.account_id = acc.id
		WHERE d.id = $1`, dealID).Scan(
			&deal.ID, &deal.Stage, &deal.EngageDate, &deal.CloseDate,
			&product.ID, &product.Name, &product.SalesPrice,
			&agent.ID, &agent.Name, &agent.ManagerID,
			&account.ID, &account.RevenueMillions, &account.Sector,
		)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch deal info: %w", err)
	}
	
	if account.ID != uuid.Nil {
		hasAccount = true
	}

	const avgWonCycle = 52.0
	const avgLostCycle = 41.0

	var reasons []string
	var factors []Factor

	// --- FACTOR 1: TIMING (30%) ---
	timingImpact := 0
	timingSentiment := "neutral"
	timingDetail := "Data de engajamento não definida"
	if deal.EngageDate != nil {
		daysInPipe := time.Since(*deal.EngageDate).Hours() / 24
		timingDetail = fmt.Sprintf("%.0f dias vs %.0f dias (ciclo médio)", daysInPipe, avgWonCycle)
		
		if daysInPipe >= avgWonCycle*0.5 && daysInPipe <= avgWonCycle {
			timingImpact = 30
			timingSentiment = "positive"
			reasons = append(reasons, "✓ Deal dentro da janela ideal")
		} else if daysInPipe < avgWonCycle*0.5 {
			timingImpact = 20
			timingSentiment = "neutral"
		} else {
			timingImpact = -10
			timingSentiment = "negative"
			reasons = append(reasons, "⚠ Deal ultrapassou o ciclo médio")
		}
	}
	factors = append(factors, Factor{Name: "Timing vs ciclo médio", Impact: timingImpact, Detail: timingDetail, Sentiment: timingSentiment})

	// --- FACTOR 2: STAGE (20%) ---
	stageImpact := 0
	stageSentiment := "neutral"
	if deal.Stage == models.StageEngaging {
		stageImpact = 20
		stageSentiment = "positive"
		reasons = append(reasons, "✓ Estágio avançado")
	} else {
		stageImpact = 8
		reasons = append(reasons, "Estágio inicial")
	}
	factors = append(factors, Factor{Name: "Estágio do funil", Impact: stageImpact, Detail: string(deal.Stage), Sentiment: stageSentiment})

	// --- FACTOR 3: WIN RATE PRODUCT (20%) ---
	productWinRate := 0.63
	factors = append(factors, Factor{Name: "Conversão do produto", Impact: 20, Detail: fmt.Sprintf("%.0f%% win rate", productWinRate*100), Sentiment: "positive"})

	// --- FACTOR 4: WIN RATE AGENT (20%) ---
	agentWinRate := 0.65
	factors = append(factors, Factor{Name: "Sua performance no stage", Impact: 20, Detail: fmt.Sprintf("%.0f%% conversão", agentWinRate*100), Sentiment: "positive"})

	// --- FACTOR 5: ACCOUNT FIT (10%) ---
	accountImpact := 5
	accountDetail := "Receita não informada"
	if hasAccount && account.RevenueMillions != nil {
		accountDetail = fmt.Sprintf("Receita: $%.0fM", *account.RevenueMillions)
		if *account.RevenueMillions > 100 {
			accountImpact = 10
		}
	}
	factors = append(factors, Factor{Name: "Perfil da conta", Impact: accountImpact, Detail: accountDetail, Sentiment: "positive"})

	// Final Score Sum
	totalScore := 0
	for _, f := range factors {
		totalScore += f.Impact
	}
	// Normalize to 0-100 (Total possible impact = 30+20+20+20+10 = 100)
	if totalScore < 0 { totalScore = 0 }
	if totalScore > 100 { totalScore = 100 }

	label := "zombie"
	if totalScore >= 85 { label = "hot" } else if totalScore >= 70 { label = "warm" } else if totalScore >= 41 { label = "cold" }

	return &ScoreResult{
		Score:   totalScore,
		Label:   label,
		Reasons: reasons,
		Factors: factors,
	}, nil
}
