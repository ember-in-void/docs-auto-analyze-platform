// Package domain defines core entities and interfaces for the IT project platform.
package domain

import "time"

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
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Status      string    `json:"status"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// ==========================================
// Request DTOs
// ==========================================

// CreateProjectRequest is the payload for creating a new project.
type CreateProjectRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Status      string `json:"status"`
}

// UpdateProjectRequest is the payload for updating an existing project.
type UpdateProjectRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Status      string `json:"status"`
}

// ==========================================
// Repository Interface (implemented in infra layer)
// ==========================================

// ProjectRepository defines data access operations for projects.
type ProjectRepository interface {
	GetAll() ([]*Project, error)
	GetByID(id string) (*Project, error)
	Create(req *CreateProjectRequest) (*Project, error)
	Update(id string, req *UpdateProjectRequest) (*Project, error)
	Delete(id string) error
}

// ==========================================
// Service Interface (implemented in service layer)
// ==========================================

// ProjectService defines business logic operations for projects.
type ProjectService interface {
	GetAll() ([]*Project, error)
	GetByID(id string) (*Project, error)
	Create(req *CreateProjectRequest) (*Project, error)
	Update(id string, req *UpdateProjectRequest) (*Project, error)
	Delete(id string) error
}
