// Package postgres implements domain.UserRepository using pgx/v5.
package postgres

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

type userRepository struct {
	db *pgxpool.Pool
}

// NewUserRepository creates a new postgres-backed UserRepository.
func NewUserRepository(db *pgxpool.Pool) domain.UserRepository {
	return &userRepository{db: db}
}

// ==========================================
// Operations
// ==========================================

func (r *userRepository) Create(ctx context.Context, user *domain.User) error {
	const q = `
		INSERT INTO users (email, password_hash, full_name, role)
		VALUES ($1, $2, $3, $4)
		RETURNING id, created_at, updated_at`

	err := r.db.QueryRow(ctx, q, user.Email, user.PasswordHash, user.FullName, user.Role).
		Scan(&user.ID, &user.CreatedAt, &user.UpdatedAt)
	if err != nil {
		return fmt.Errorf("userRepo.Create: %w", err)
	}
	return nil
}

func (r *userRepository) GetByEmail(ctx context.Context, email string) (*domain.User, error) {
	const q = `
		SELECT id, email, password_hash, full_name, role, created_at, updated_at
		FROM users
		WHERE email = $1`

	u := &domain.User{}
	err := r.db.QueryRow(ctx, q, email).
		Scan(&u.ID, &u.Email, &u.PasswordHash, &u.FullName, &u.Role, &u.CreatedAt, &u.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrNotFound
		}
		return nil, fmt.Errorf("userRepo.GetByEmail: %w", err)
	}
	return u, nil
}

func (r *userRepository) GetByID(ctx context.Context, id string) (*domain.User, error) {
	const q = `
		SELECT id, email, password_hash, full_name, role, created_at, updated_at
		FROM users
		WHERE id = $1`

	u := &domain.User{}
	err := r.db.QueryRow(ctx, q, id).
		Scan(&u.ID, &u.Email, &u.PasswordHash, &u.FullName, &u.Role, &u.CreatedAt, &u.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrNotFound
		}
		return nil, fmt.Errorf("userRepo.GetByID: %w", err)
	}
	return u, nil
}
