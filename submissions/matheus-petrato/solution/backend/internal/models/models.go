package models

import (
	"time"

	"github.com/google/uuid"
)

type DealStage string

const (
	StageProspecting DealStage = "Prospecting"
	StageEngaging    DealStage = "Engaging"
	StageWon         DealStage = "Won"
	StageLost        DealStage = "Lost"
)

type RegionalOffice struct {
	ID        uuid.UUID `json:"id"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Manager struct {
	ID               uuid.UUID `json:"id"`
	Name             string    `json:"name"`
	RegionalOfficeID uuid.UUID `json:"regional_office_id"`
	ExternalID       *string   `json:"external_id"`
	Source           string    `json:"source"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
}

type SalesAgent struct {
	ID               uuid.UUID `json:"id"`
	Name             string    `json:"name"`
	ManagerID        uuid.UUID `json:"manager_id"`
	RegionalOfficeID uuid.UUID `json:"regional_office_id"`
	ExternalID       *string   `json:"external_id"`
	Source           string    `json:"source"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
}

type Account struct {
	ID              uuid.UUID `json:"id"`
	Name            string    `json:"name"`
	Sector          *string   `json:"sector"`
	YearEstablished *int      `json:"year_established"`
	RevenueMillions *float64  `json:"revenue_millions"`
	Employees       *int      `json:"employees"`
	OfficeLocation  *string   `json:"office_location"`
	SubsidiaryOf    *string   `json:"subsidiary_of"`
	ExternalID      *string   `json:"external_id"`
	Source          string    `json:"source"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

type Product struct {
	ID         uuid.UUID `json:"id"`
	Name       string    `json:"name"`
	Series     *string   `json:"series"`
	SalesPrice float64   `json:"sales_price"`
	ExternalID *string   `json:"external_id"`
	Source     string    `json:"source"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}

type Deal struct {
	ID            uuid.UUID  `json:"id"`
	OpportunityID string     `json:"opportunity_id"`
	SalesAgentID  uuid.UUID  `json:"sales_agent_id"`
	ProductID     uuid.UUID  `json:"product_id"`
	AccountID     *uuid.UUID `json:"account_id"`
	Stage         DealStage  `json:"stage"`
	EngageDate    *time.Time `json:"engage_date"`
	CloseDate     *time.Time `json:"close_date"`
	CloseValue    *float64   `json:"close_value"`
	ExternalID    *string    `json:"external_id"`
	Source        string     `json:"source"`
	CreatedAt     time.Time  `json:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at"`
}

type User struct {
	ID           uuid.UUID  `json:"id"`
	Name         string     `json:"name"`
	Email        string     `json:"email"`
	PasswordHash string     `json:"-"`
	Role         string     `json:"role"`
	SalesAgentID *uuid.UUID `json:"sales_agent_id"`
	ManagerID    *uuid.UUID `json:"manager_id"`
	LastLoginAt  *time.Time `json:"last_login_at"`
	CreatedAt    time.Time  `json:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at"`

	// Frontend context fields
	Region string     `json:"region"`
	TeamID *uuid.UUID `json:"team_id"`
}

type DealScore struct {
	ID           uuid.UUID      `json:"id"`
	DealID       uuid.UUID      `json:"deal_id"`
	Score        int            `json:"score"`
	Label        string         `json:"label"`
	Reasons      []string       `json:"reasons"`
	Factors      map[string]any `json:"factors"`
	CalculatedAt time.Time      `json:"calculated_at"`
}

type DealScoreHistory struct {
	ID           uuid.UUID `json:"id"`
	DealID       uuid.UUID `json:"deal_id"`
	Score        int       `json:"score"`
	Label        string    `json:"label"`
	CalculatedAt time.Time `json:"calculated_at"`
}

type AlertType string

const (
	AlertHotWindow      AlertType = "hot_window"
	AlertStaleDeal      AlertType = "stale_deal"
	AlertWeeklyBriefing AlertType = "weekly_briefing"
	AlertScoreDrop      AlertType = "score_drop"
	AlertNewOpportunity AlertType = "new_opportunity"
)

type Alert struct {
	ID        uuid.UUID  `json:"id"`
	UserID    uuid.UUID  `json:"user_id"`
	DealID    *uuid.UUID `json:"deal_id"`
	Type      AlertType  `json:"type"`
	Title     string     `json:"title"`
	Body      string     `json:"body"`
	ReadAt    *time.Time `json:"read_at"`
	ActionURL *string    `json:"action_url"`
	CreatedAt time.Time  `json:"created_at"`
}

type Conversation struct {
	ID        uuid.UUID      `json:"id"`
	UserID    uuid.UUID      `json:"user_id"`
	Context   map[string]any `json:"context"`
	StartedAt time.Time      `json:"started_at"`
	EndedAt   *time.Time     `json:"ended_at"`
}

type Message struct {
	ID             uuid.UUID      `json:"id"`
	ConversationID uuid.UUID      `json:"conversation_id"`
	Role           string         `json:"role"` // user, assistant, tool
	Content        string         `json:"content"`
	ToolName       *string        `json:"tool_name"`
	ToolInput      map[string]any `json:"tool_input"`
	ToolResult     map[string]any `json:"tool_result"`
	CreatedAt      time.Time      `json:"created_at"`
}

type ImportStatus string

const (
	ImportPending    ImportStatus = "pending"
	ImportValidating ImportStatus = "validating"
	ImportPreview    ImportStatus = "preview"
	ImportImporting  ImportStatus = "importing"
	ImportDone       ImportStatus = "done"
	ImportFailed     ImportStatus = "failed"
	ImportRolledBack ImportStatus = "rolled_back"
)

type ImportSourceType string

const (
	ImportSourceDeals    ImportSourceType = "deals"
	ImportSourceAccounts ImportSourceType = "accounts"
	ImportSourceProducts ImportSourceType = "products"
	ImportSourceTeam     ImportSourceType = "team"
)

type DataImport struct {
	ID               uuid.UUID        `json:"id"`
	UploadedBy       uuid.UUID        `json:"uploaded_by"`
	SourceType       ImportSourceType `json:"source_type"`
	Filename         string           `json:"filename"`
	FileSizeByes     int64            `json:"file_size_bytes"`
	Status           ImportStatus     `json:"status"`
	ValidationErrors []map[string]any `json:"validation_errors"`
	RowsTotal        int              `json:"rows_total"`
	RowsInserted     int              `json:"rows_inserted"`
	RowsUpdated      int              `json:"rows_updated"`
	RowsSkipped      int              `json:"rows_skipped"`
	SnapshotTable    *string          `json:"snapshot_table"`
	ErrorMessage     *string          `json:"error_message"`
	StartedAt        *time.Time       `json:"started_at"`
	FinishedAt       *time.Time       `json:"finished_at"`
	CreatedAt        time.Time        `json:"created_at"`
}
