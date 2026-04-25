// Package db provides PostgreSQL connection pool management.
package db

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// ==========================================
// Connection Pool
// ==========================================

// NewPool creates and validates a new PostgreSQL connection pool.
func NewPool(ctx context.Context, dsn string) (*pgxpool.Pool, error) {
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, fmt.Errorf("db: failed to parse config: %w", err)
	}

	// Pool tuning
	cfg.MaxConns = 20
	cfg.MinConns = 2
	cfg.MaxConnLifetime = 30 * time.Minute
	cfg.MaxConnIdleTime = 5 * time.Minute

	pool, err := pgxpool.NewWithConfig(ctx, cfg)
	if err != nil {
		return nil, fmt.Errorf("db: failed to create pool: %w", err)
	}

	// Validate connectivity
	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("db: ping failed: %w", err)
	}

	return pool, nil
}
