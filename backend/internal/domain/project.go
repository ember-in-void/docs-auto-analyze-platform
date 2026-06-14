// Package domain defines core entities and interfaces for the IT project platform.
package domain

import (
	"context"
	"time"
)

// ==========================================
// Constants
// ==========================================

const (
	ProjectStatusActive    = "active"
	ProjectStatusArchived  = "archived"
	ProjectStatusCompleted = "completed"
)

// ==========================================
// Entity
// ==========================================

// Project represents an IT project in the system.
type Project struct {
	ID                 string    `json:"id"`
	OwnerID            string    `json:"owner_id"`
	Name               string    `json:"name"`
	Description        string    `json:"description"`
	Status             string    `json:"status"`
	CreatedAt          time.Time `json:"created_at"`
	UpdatedAt          time.Time `json:"updated_at"`
	RiskScore          float64   `json:"risk_score"`
	ProfitabilityScore float64   `json:"profitability_score"`
}

// ==========================================
// Request DTOs
// ==========================================

// CreateProjectRequest is the payload for creating a new project.
type CreateProjectRequest struct {
	Name        string `json:"name" validate:"required"`
	Description string `json:"description"`
	Status      string `json:"status"`
}

// UpdateProjectRequest is the payload for updating an existing project.
type UpdateProjectRequest struct {
	Name        string `json:"name" validate:"required"`
	Description string `json:"description"`
	Status      string `json:"status"`
}

// ==========================================
// Repository Interface (implemented in infra layer)
// ==========================================

// ProjectRepository defines data access operations for projects.
type ProjectRepository interface {
	GetAll(ctx context.Context, ownerID string) ([]*Project, error)
	GetByID(ctx context.Context, id string, ownerID string) (*Project, error)
	Create(ctx context.Context, ownerID string, req *CreateProjectRequest) (*Project, error)
	Update(ctx context.Context, id string, ownerID string, req *UpdateProjectRequest) (*Project, error)
	Delete(ctx context.Context, id string, ownerID string) error
}

// ==========================================
// Service Interface (implemented in service layer)
// ==========================================

// ProjectService defines business logic operations for projects.
type ProjectService interface {
	GetAll(ctx context.Context, ownerID string) ([]*Project, error)
	GetByID(ctx context.Context, id string, ownerID string) (*Project, error)
	Create(ctx context.Context, ownerID string, req *CreateProjectRequest) (*Project, error)
	Update(ctx context.Context, id string, ownerID string, req *UpdateProjectRequest) (*Project, error)
	Delete(ctx context.Context, id string, ownerID string) error
}
