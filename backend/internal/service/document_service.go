// Package service implements business logic for documents.
package service

import (
	"fmt"

	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

type documentService struct {
	repo domain.DocumentRepository
}

// NewDocumentService creates a new DocumentService backed by the given repository.
func NewDocumentService(repo domain.DocumentRepository) domain.DocumentService {
	return &documentService{repo: repo}
}

// ==========================================
// Business Logic
// ==========================================

func (s *documentService) GetByProjectID(projectID string) ([]*domain.Document, error) {
	if projectID == "" {
		return nil, fmt.Errorf("project id is required")
	}
	return s.repo.GetByProjectID(projectID)
}

func (s *documentService) GetByID(id string) (*domain.Document, error) {
	if id == "" {
		return nil, fmt.Errorf("document id is required")
	}
	return s.repo.GetByID(id)
}

func (s *documentService) Create(projectID string, req *domain.CreateDocumentRequest) (*domain.Document, error) {
	if projectID == "" {
		return nil, fmt.Errorf("project id is required")
	}
	if req.Title == "" {
		return nil, fmt.Errorf("document title is required")
	}
	if req.Content == "" {
		return nil, fmt.Errorf("document content is required")
	}
	if req.DocType == "" {
		req.DocType = domain.DocTypeOther
	}
	return s.repo.Create(projectID, req)
}

func (s *documentService) Delete(id string) error {
	if id == "" {
		return fmt.Errorf("document id is required")
	}
	return s.repo.Delete(id)
}
