// Package domain defines core entities and interfaces for the IT project platform.
package domain

import (
	"encoding/json"
	"time"
)

// ==========================================
// Entity
// ==========================================

// Prediction holds the NLP analysis results for a project.
// In MVP the scores are produced by a mock keyword-based algorithm.
// TODO: replace Generate() implementation with gRPC call to Python NLP service.
type Prediction struct {
	ID                 string          `json:"id"`
	ProjectID          string          `json:"project_id"`
	ProfitabilityScore float64         `json:"profitability_score"` // 0.0 – 1.0
	RiskScore          float64         `json:"risk_score"`          // 0.0 – 1.0
	RelevanceScore     float64         `json:"relevance_score"`     // 0.0 – 1.0
	Summary            string          `json:"summary"`
	Keywords           []string        `json:"keywords"`
	Entities           json.RawMessage `json:"entities"`
	ModelVersion       string          `json:"model_version"`
	GeneratedAt        time.Time       `json:"generated_at"`
}

// ==========================================
// Repository Interface
// ==========================================

// PredictionRepository defines data access operations for predictions.
type PredictionRepository interface {
	GetByProjectID(projectID string) ([]*Prediction, error)
	Create(p *Prediction) (*Prediction, error)
}

// ==========================================
// Service Interface
// ==========================================

// PredictionService defines business logic for analysis generation.
type PredictionService interface {
	GetByProjectID(projectID string) ([]*Prediction, error)
	Generate(projectID string) (*Prediction, error)
}
