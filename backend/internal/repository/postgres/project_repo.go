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

func (r *projectRepository) GetAll(ctx context.Context, ownerID string) ([]*domain.Project, error) {
	const q = `
		SELECT p.id, p.owner_id, p.name, p.description, p.status, p.created_at, p.updated_at,
		       COALESCE(pr.risk_score, 0) as risk_score, COALESCE(pr.profitability_score, 0) as profitability_score
		FROM projects p
		LEFT JOIN LATERAL (
			SELECT risk_score, profitability_score
			FROM predictions
			WHERE project_id = p.id
			ORDER BY generated_at DESC
			LIMIT 1
		) pr ON TRUE
		WHERE p.owner_id = $1
		ORDER BY p.created_at DESC`

	rows, err := r.db.Query(ctx, q, ownerID)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.GetAll: query: %w", err)
	}
	defer rows.Close()

	projects := make([]*domain.Project, 0)
	for rows.Next() {
		p := &domain.Project{}
		if err := rows.Scan(&p.ID, &p.OwnerID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt, &p.RiskScore, &p.ProfitabilityScore); err != nil {
			return nil, fmt.Errorf("projectRepo.GetAll: scan: %w", err)
		}
		projects = append(projects, p)
	}
	return projects, rows.Err()
}

func (r *projectRepository) GetByID(ctx context.Context, id string, ownerID string) (*domain.Project, error) {
	const q = `
		SELECT p.id, p.owner_id, p.name, p.description, p.status, p.created_at, p.updated_at,
		       COALESCE(pr.risk_score, 0) as risk_score, COALESCE(pr.profitability_score, 0) as profitability_score
		FROM projects p
		LEFT JOIN LATERAL (
			SELECT risk_score, profitability_score
			FROM predictions
			WHERE project_id = p.id
			ORDER BY generated_at DESC
			LIMIT 1
		) pr ON TRUE
		WHERE p.id = $1 AND p.owner_id = $2`

	p := &domain.Project{}
	err := r.db.QueryRow(ctx, q, id, ownerID).
		Scan(&p.ID, &p.OwnerID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt, &p.RiskScore, &p.ProfitabilityScore)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.GetByID: %w", err)
	}
	return p, nil
}

// ==========================================
// Write Operations
// ==========================================

func (r *projectRepository) Create(ctx context.Context, ownerID string, req *domain.CreateProjectRequest) (*domain.Project, error) {
	status := req.Status
	if status == "" {
		status = domain.ProjectStatusActive
	}

	const q = `
		INSERT INTO projects (owner_id, name, description, status)
		VALUES ($1, $2, $3, $4)
		RETURNING id, owner_id, name, description, status, created_at, updated_at`

	p := &domain.Project{}
	err := r.db.QueryRow(ctx, q, ownerID, req.Name, req.Description, status).
		Scan(&p.ID, &p.OwnerID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.Create: %w", err)
	}
	return p, nil
}

func (r *projectRepository) Update(ctx context.Context, id string, ownerID string, req *domain.UpdateProjectRequest) (*domain.Project, error) {
	const q = `
		UPDATE projects
		SET name = $3, description = $4, status = $5
		WHERE id = $1 AND owner_id = $2
		RETURNING id, owner_id, name, description, status, created_at, updated_at`

	p := &domain.Project{}
	err := r.db.QueryRow(ctx, q, id, ownerID, req.Name, req.Description, req.Status).
		Scan(&p.ID, &p.OwnerID, &p.Name, &p.Description, &p.Status, &p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("projectRepo.Update: %w", err)
	}
	return p, nil
}

func (r *projectRepository) Delete(ctx context.Context, id string, ownerID string) error {
	const q = `DELETE FROM projects WHERE id = $1 AND owner_id = $2`
	_, err := r.db.Exec(ctx, q, id, ownerID)
	if err != nil {
		return fmt.Errorf("projectRepo.Delete: %w", err)
	}
	return nil
}
