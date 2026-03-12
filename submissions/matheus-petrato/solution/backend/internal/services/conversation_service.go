package services

import (
	"context"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/matheus-petrato/sales-copilot-back/internal/models"
)

type ConversationService struct {
	pool *pgxpool.Pool
}

func NewConversationService(pool *pgxpool.Pool) *ConversationService {
	return &ConversationService{pool: pool}
}

func (s *ConversationService) GetPool() *pgxpool.Pool {
	return s.pool
}

func (s *ConversationService) CreateConversation(ctx context.Context, userID uuid.UUID, contextData map[string]any) (*models.Conversation, error) {
	id, _ := uuid.NewV7()
	conv := &models.Conversation{
		ID:      id,
		UserID:  userID,
		Context: contextData,
	}

	err := s.pool.QueryRow(ctx, `
		INSERT INTO conversations (id, user_id, context)
		VALUES ($1, $2, $3)
		RETURNING started_at`,
		id, userID, contextData).Scan(&conv.StartedAt)
	
	return conv, err
}

func (s *ConversationService) GetHistory(ctx context.Context, conversationID uuid.UUID) ([]models.Message, error) {
	rows, err := s.pool.Query(ctx, `
		SELECT role, content, COALESCE(tool_name, ''), created_at
		FROM messages
		WHERE conversation_id = $1
		ORDER BY created_at ASC`, conversationID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var history []models.Message
	for rows.Next() {
		var m models.Message
		var toolName string
		err := rows.Scan(&m.Role, &m.Content, &toolName, &m.CreatedAt)
		if err != nil {
			return nil, err
		}
		if toolName != "" { m.ToolName = &toolName }
		history = append(history, m)
	}
	return history, nil
}

func (s *ConversationService) SaveMessage(ctx context.Context, conversationID uuid.UUID, role, content string, toolName *string) error {
	id, _ := uuid.NewV7()
	_, err := s.pool.Exec(ctx, `
		INSERT INTO messages (id, conversation_id, role, content, tool_name)
		VALUES ($1, $2, $3, $4, $5)`,
		id, conversationID, role, content, toolName)
	return err
}
