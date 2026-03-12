package utils

import (
	"github.com/google/uuid"
)

// NewUUIDv7 generates a new UUID v7
func NewUUIDv7() (uuid.UUID, error) {
	return uuid.NewV7()
}

// NewUUIDv7String generates a new UUID v7 and returns it as a string
func NewUUIDv7String() string {
	id, err := uuid.NewV7()
	if err != nil {
		// Fallback to v4 if v7 fails for some reason (extremely rare)
		return uuid.New().String()
	}
	return id.String()
}
