// Package service implements business logic for projects.
package service

import (
	"context"
	"errors"

	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

type projectService struct {
	repo domain.ProjectRepository
}

// NewProjectService creates a new ProjectService backed by the given repository.
func NewProjectService(repo domain.ProjectRepository) domain.ProjectService {
	return &projectService{repo: repo}
}

// ==========================================
// Business Logic
// ==========================================

func (s *projectService) GetAll(ctx context.Context, ownerID string) ([]*domain.Project, error) {
	return s.repo.GetAll(ctx, ownerID)
}

func (s *projectService) GetByID(ctx context.Context, id string, ownerID string) (*domain.Project, error) {
	if id == "" {
		return nil, errors.New("id проекта обязателен")
	}
	return s.repo.GetByID(ctx, id, ownerID)
}

func (s *projectService) Create(ctx context.Context, ownerID string, req *domain.CreateProjectRequest) (*domain.Project, error) {
	if req.Name == "" {
		return nil, errors.New("название проекта обязательно")
	}
	if req.Status == "" {
		req.Status = domain.ProjectStatusActive
	}
	return s.repo.Create(ctx, ownerID, req)
}

func (s *projectService) Update(ctx context.Context, id string, ownerID string, req *domain.UpdateProjectRequest) (*domain.Project, error) {
	if id == "" {
		return nil, errors.New("id проекта обязателен")
	}
	if req.Name == "" {
		return nil, errors.New("название проекта обязательно")
	}
	return s.repo.Update(ctx, id, ownerID, req)
}

func (s *projectService) Delete(ctx context.Context, id string, ownerID string) error {
	if id == "" {
		return errors.New("id проекта обязателен")
	}
	return s.repo.Delete(ctx, id, ownerID)
}
