// Package postgres implements domain.PredictionRepository using pgx/v5.
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

type predictionRepository struct {
	db *pgxpool.Pool
}

// NewPredictionRepository creates a new postgres-backed PredictionRepository.
func NewPredictionRepository(db *pgxpool.Pool) domain.PredictionRepository {
	return &predictionRepository{db: db}
}

// ==========================================
// Read Operations
// ==========================================

func (r *predictionRepository) GetByProjectID(ctx context.Context, projectID string) ([]*domain.Prediction, error) {
	const q = `
		SELECT id, project_id, keywords, entities, model_version, generated_at,
		       meta_info, executive_summary, tech_stack, metrics
		FROM predictions
		WHERE project_id = $1
		ORDER BY generated_at DESC`

	rows, err := r.db.Query(ctx, q, projectID)
	if err != nil {
		return nil, fmt.Errorf("predictionRepo.GetByProjectID: query: %w", err)
	}
	defer rows.Close()

	preds := make([]*domain.Prediction, 0)
	for rows.Next() {
		p := &domain.Prediction{}
		if err := rows.Scan(
			&p.ID, &p.ProjectID,
			&p.Keywords, &p.Entities,
			&p.ModelVersion, &p.GeneratedAt,
			&p.MetaInfo, &p.ExecutiveSummary, &p.TechStack, &p.Metrics,
		); err != nil {
			return nil, fmt.Errorf("predictionRepo.GetByProjectID: scan: %w", err)
		}
		preds = append(preds, p)
	}
	return preds, rows.Err()
}

// ==========================================
// Write Operations
// ==========================================

func (r *predictionRepository) Create(ctx context.Context, p *domain.Prediction) (*domain.Prediction, error) {
	// Extract scores for flat DB columns so existing project queries still function correctly.
	var profitabilityScore, riskScore, relevanceScore float64
	for _, m := range p.Metrics {
		switch m.Type {
		case "profitability":
			profitabilityScore = m.Score
		case "risk":
			riskScore = m.Score
		case "relevance":
			relevanceScore = m.Score
		}
	}

	const q = `
		INSERT INTO predictions
			(project_id, profitability_score, risk_score, relevance_score, summary, keywords, entities, model_version,
			 meta_info, executive_summary, tech_stack, metrics)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
		RETURNING id, project_id, keywords, entities, model_version, generated_at,
		          meta_info, executive_summary, tech_stack, metrics`

	result := &domain.Prediction{}
	err := r.db.QueryRow(ctx, q,
		p.ProjectID,
		profitabilityScore,
		riskScore,
		relevanceScore,
		p.ExecutiveSummary,
		p.Keywords,
		p.Entities,
		p.ModelVersion,
		p.MetaInfo,
		p.ExecutiveSummary,
		p.TechStack,
		p.Metrics,
	).Scan(
		&result.ID, &result.ProjectID,
		&result.Keywords, &result.Entities,
		&result.ModelVersion, &result.GeneratedAt,
		&result.MetaInfo, &result.ExecutiveSummary, &result.TechStack, &result.Metrics,
	)
	if err != nil {
		return nil, fmt.Errorf("predictionRepo.Create: %w", err)
	}
	return result, nil
}
