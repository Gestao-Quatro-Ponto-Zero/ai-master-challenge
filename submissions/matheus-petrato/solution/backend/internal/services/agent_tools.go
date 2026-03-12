package services

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/google/uuid"
	"github.com/matheus-petrato/sales-copilot-back/pkg/agent"
)

// BaseAgentTool contains common dependencies for tools
type BaseAgentTool struct {
	Connector *DataConnector
	SellerID  string
	ManagerID string
}

// GetMyDealsTool fetches the current agent's deals
type GetMyDealsTool struct {
	BaseAgentTool
}

func (t *GetMyDealsTool) Name() string { return "get_my_deals" }
func (t *GetMyDealsTool) Description() string {
	return "Fetches the current agent's pipeline deals. Can filter by status (hot, risk, warm, cold)."
}
func (t *GetMyDealsTool) Parameters() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"status": map[string]any{
				"type": "string",
				"enum": []string{"hot", "risk", "warm", "cold"},
				"description": "Filter by deal status",
			},
		},
	}
}

func (t *GetMyDealsTool) Execute(ctx context.Context, args map[string]any) (*agent.ToolResult, error) {
	status, _ := args["status"].(string)
	
	result, err := t.Connector.FetchDeals(ctx, DealFilter{
		Status:    status,
		SellerID:  t.SellerID,
		ManagerID: t.ManagerID,
	})
	if err != nil {
		return nil, err
	}

	content, _ := json.Marshal(result.Items)
	return &agent.ToolResult{
		Content: string(content),
	}, nil
}

// GetDealDetailTool fetches details for a specific deal
type GetDealDetailTool struct {
	BaseAgentTool
}

func (t *GetDealDetailTool) Name() string { return "get_deal_detail" }
func (t *GetDealDetailTool) Description() string {
	return "Fetches detailed information and score reasons for a specific deal ID."
}
func (t *GetDealDetailTool) Parameters() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"deal_id": map[string]any{
				"type": "string",
				"description": "The UUID of the deal",
			},
		},
		"required": []string{"deal_id"},
	}
}

func (t *GetDealDetailTool) Execute(ctx context.Context, args map[string]any) (*agent.ToolResult, error) {
	dealIDStr, _ := args["deal_id"].(string)
	dealID, err := uuid.Parse(dealIDStr)
	if err != nil {
		return nil, fmt.Errorf("invalid deal_id format")
	}

	detail, err := t.Connector.FetchDealDetail(ctx, dealID)
	if err != nil {
		return nil, err
	}

	content, _ := json.Marshal(detail)
	return &agent.ToolResult{
		Content: string(content),
	}, nil
}

// SearchDealsTool allows searching deals by account or product name
type SearchDealsTool struct {
	BaseAgentTool
}

func (t *SearchDealsTool) Name() string { return "search_deals" }
func (t *SearchDealsTool) Description() string {
	return "Search deals by account name."
}
func (t *SearchDealsTool) Parameters() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"query": map[string]any{
				"type": "string",
				"description": "Account name query",
			},
		},
		"required": []string{"query"},
	}
}

func (t *SearchDealsTool) Execute(ctx context.Context, args map[string]any) (*agent.ToolResult, error) {
	query, _ := args["query"].(string)
	
	// Fetch all agent deals and filter by name
	result, err := t.Connector.FetchDeals(ctx, DealFilter{
		SellerID:  t.SellerID,
		ManagerID: t.ManagerID,
	})
	if err != nil {
		return nil, err
	}

	var filtered []DealDTO
	q := strings.ToLower(query)
	for _, d := range result.Items {
		if strings.Contains(strings.ToLower(d.Name), q) {
			filtered = append(filtered, d)
		}
	}

	content, _ := json.Marshal(filtered)
	return &agent.ToolResult{
		Content: string(content),
	}, nil
}
