// Package domain defines core entities and interfaces for the IT project platform.
package domain

import (
	"context"
	"errors"
	"time"
)

var ErrNotFound = errors.New("resource not found")

// ==========================================
// Constants
// ==========================================

const (
	RoleUser  = "user"
	RoleAdmin = "admin"
)

// ==========================================
// Entity
// ==========================================

// User represents a system user.
type User struct {
	ID           string    `json:"id"`
	Email        string    `json:"email"`
	PasswordHash string    `json:"-"` // Never expose hash in JSON
	FullName     string    `json:"full_name"`
	Role         string    `json:"role"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

// ==========================================
// Request DTOs
// ==========================================

// RegisterRequest is the payload for creating a new user.
type RegisterRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=6"`
	FullName string `json:"full_name"`
}

// LoginRequest is the payload for authentication.
type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required"`
}

// AuthResponse is returned after successful login/register.
type AuthResponse struct {
	Token string `json:"token"`
	User  *User  `json:"user"`
}

// ==========================================
// Interfaces
// ==========================================

// UserRepository defines data access operations for users.
type UserRepository interface {
	Create(ctx context.Context, user *User) error
	GetByEmail(ctx context.Context, email string) (*User, error)
	GetByID(ctx context.Context, id string) (*User, error)
}

// AuthService defines business logic for authentication.
type AuthService interface {
	Register(ctx context.Context, req *RegisterRequest) (*AuthResponse, error)
	Login(ctx context.Context, req *LoginRequest) (*AuthResponse, error)
	ValidateToken(ctx context.Context, token string) (*User, error)
}
