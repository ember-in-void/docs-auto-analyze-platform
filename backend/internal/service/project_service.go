// Package service implements business logic for projects.
package service

import (
	"fmt"

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

func (s *projectService) GetAll() ([]*domain.Project, error) {
	return s.repo.GetAll()
}

func (s *projectService) GetByID(id string) (*domain.Project, error) {
	if id == "" {
		return nil, fmt.Errorf("project id is required")
	}
	return s.repo.GetByID(id)
}

func (s *projectService) Create(req *domain.CreateProjectRequest) (*domain.Project, error) {
	if req.Name == "" {
		return nil, fmt.Errorf("project name is required")
	}
	if req.Status == "" {
		req.Status = domain.ProjectStatusActive
	}
	return s.repo.Create(req)
}

func (s *projectService) Update(id string, req *domain.UpdateProjectRequest) (*domain.Project, error) {
	if id == "" {
		return nil, fmt.Errorf("project id is required")
	}
	if req.Name == "" {
		return nil, fmt.Errorf("project name is required")
	}
	return s.repo.Update(id, req)
}

func (s *projectService) Delete(id string) error {
	if id == "" {
		return fmt.Errorf("project id is required")
	}
	return s.repo.Delete(id)
}
