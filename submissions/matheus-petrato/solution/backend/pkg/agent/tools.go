package agent

import (
	"context"
	"fmt"
	"sync"
)

type ToolRegistry struct {
	tools map[string]Tool
	mu    sync.RWMutex
}

func NewToolRegistry() *ToolRegistry {
	return &ToolRegistry{
		tools: make(map[string]Tool),
	}
}

func (r *ToolRegistry) Register(t Tool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.tools[t.Name()] = t
}

func (r *ToolRegistry) Get(name string) (Tool, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	t, ok := r.tools[name]
	return t, ok
}

func (r *ToolRegistry) ToProviderDefs() []ToolDefinition {
	r.mu.RLock()
	defer r.mu.RUnlock()

	defs := make([]ToolDefinition, 0, len(r.tools))
	for _, t := range r.tools {
		defs = append(defs, ToolDefinition{
			Type: "function",
			Function: ToolFunctionDefinition{
				Name:        t.Name(),
				Description: t.Description(),
				Parameters:  t.Parameters(),
			},
		})
	}
	return defs
}

func (r *ToolRegistry) Execute(ctx context.Context, name string, args map[string]any) (*ToolResult, error) {
	t, ok := r.Get(name)
	if !ok {
		return nil, fmt.Errorf("tool not found: %s", name)
	}

	return t.Execute(ctx, args)
}
