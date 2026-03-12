package postgres

import (
	"context"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog/log"
)

var (
	pool *pgxpool.Pool
	once sync.Once
)

// Connect establishes a connection pool to PostgreSQL
func Connect(ctx context.Context) (*pgxpool.Pool, error) {
	var err error
	once.Do(func() {
		databaseURL := os.Getenv("DATABASE_URL")
		if databaseURL == "" {
			databaseURL = "postgres://compass:compass@localhost:5432/compass?sslmode=disable"
		}

		config, parseErr := pgxpool.ParseConfig(databaseURL)
		if parseErr != nil {
			err = fmt.Errorf("unable to parse database url: %w", parseErr)
			return
		}

		// Pool configuration
		config.MaxConns = 10
		config.MinConns = 2
		config.MaxConnLifetime = time.Hour
		config.MaxConnIdleTime = 30 * time.Minute

		pool, err = pgxpool.NewWithConfig(ctx, config)
		if err != nil {
			err = fmt.Errorf("unable to connect to database: %w", err)
			return
		}

		// Test connection
		if pingErr := pool.Ping(ctx); pingErr != nil {
			err = fmt.Errorf("unable to ping database: %w", pingErr)
			return
		}

		log.Info().Msg("Successfully connected to PostgreSQL")
	})

	return pool, err
}

// GetPool returns the established connection pool
func GetPool() *pgxpool.Pool {
	return pool
}

// Close gracefully closes the connection pool
func Close() {
	if pool != nil {
		pool.Close()
	}
}
