// Package domain defines core entities and interfaces for the IT project platform.
package domain

import "time"

// ==========================================
// Constants
// ==========================================

const (
	DocTypeTZ           = "TZ"
	DocTypeArchitecture = "ARCHITECTURE"
	DocTypeRequirements = "REQUIREMENTS"
	DocTypeLogs         = "LOGS"
	DocTypeOther        = "OTHER"
)

// ==========================================
// Entity
// ==========================================

// Document represents a project document (TZ, architecture, requirements, etc.).
type Document struct {
	ID         string    `json:"id"`
	ProjectID  string    `json:"project_id"`
	Title      string    `json:"title"`
	Content    string    `json:"content"`
	DocType    string    `json:"doc_type"`
	UploadedAt time.Time `json:"uploaded_at"`
}

// ==========================================
// Request DTOs
// ==========================================

// CreateDocumentRequest is the payload for adding a document to a project.
type CreateDocumentRequest struct {
	Title   string `json:"title"`
	Content string `json:"content"`
	DocType string `json:"doc_type"`
}

// ==========================================
// Repository Interface
// ==========================================

// DocumentRepository defines data access operations for documents.
type DocumentRepository interface {
	GetByProjectID(projectID string) ([]*Document, error)
	GetByID(id string) (*Document, error)
	Create(projectID string, req *CreateDocumentRequest) (*Document, error)
	Delete(id string) error
}

// ==========================================
// Service Interface
// ==========================================

// DocumentService defines business logic operations for documents.
type DocumentService interface {
	GetByProjectID(projectID string) ([]*Document, error)
	GetByID(id string) (*Document, error)
	Create(projectID string, req *CreateDocumentRequest) (*Document, error)
	Delete(id string) error
}
