// Package postgres implements domain.ProjectRepository using pgx/v5.
package postgres

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

type projectRepository struct {
	db *pgxpool.Pool
}

// NewProjectRepository creates a new postgres-backed ProjectRepository.
func NewProjectRepository(db *pgxpool.Pool) domain.ProjectRepository {
	return &projectRepository{db: db}
}

// ==========================================
// Read Operations
// ==========================================

func (r *projectRepository) GetAll() ([]*domain.Project, error) {
	const q = `
		SELECT id, name, description, status, created_at, updated_at
		FROM projects
		ORDER BY created_at DESC`

	rows, err := r.db.Query(context.Background(), q)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.GetAll: query: %w", err)
	}
	defer rows.Close()

	projects := make([]*domain.Project, 0)
	for rows.Next() {
		p := &domain.Project{}
		if err := rows.Scan(&p.ID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt); err != nil {
			return nil, fmt.Errorf("projectRepo.GetAll: scan: %w", err)
		}
		projects = append(projects, p)
	}
	return projects, rows.Err()
}

func (r *projectRepository) GetByID(id string) (*domain.Project, error) {
	const q = `
		SELECT id, name, description, status, created_at, updated_at
		FROM projects
		WHERE id = $1`

	p := &domain.Project{}
	err := r.db.QueryRow(context.Background(), q, id).
		Scan(&p.ID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.GetByID: %w", err)
	}
	return p, nil
}

// ==========================================
// Write Operations
// ==========================================

func (r *projectRepository) Create(req *domain.CreateProjectRequest) (*domain.Project, error) {
	status := req.Status
	if status == "" {
		status = domain.ProjectStatusActive
	}

	const q = `
		INSERT INTO projects (name, description, status)
		VALUES ($1, $2, $3)
		RETURNING id, name, description, status, created_at, updated_at`

	p := &domain.Project{}
	err := r.db.QueryRow(context.Background(), q, req.Name, req.Description, status).
		Scan(&p.ID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.Create: %w", err)
	}
	return p, nil
}

func (r *projectRepository) Update(id string, req *domain.UpdateProjectRequest) (*domain.Project, error) {
	const q = `
		UPDATE projects
		SET name = $2, description = $3, status = $4
		WHERE id = $1
		RETURNING id, name, description, status, created_at, updated_at`

	p := &domain.Project{}
	err := r.db.QueryRow(context.Background(), q, id, req.Name, req.Description, req.Status).
		Scan(&p.ID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.Update: %w", err)
	}
	return p, nil
}

func (r *projectRepository) Delete(id string) error {
	const q = `DELETE FROM projects WHERE id = $1`
	_, err := r.db.Exec(context.Background(), q, id)
	if err != nil {
		return fmt.Errorf("projectRepo.Delete: %w", err)
	}
	return nil
}
