// Package domain defines core entities and interfaces for the IT project platform.
package domain

import (
	"context"
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"time"
)

// ==========================================
// Value Objects / JSON Contracts
// ==========================================

// MetaInfo holds project meta information like budget, timeline, and domain.
type MetaInfo struct {
	Budget   string `json:"budget"`
	Timeline string `json:"timeline"`
	Domain   string `json:"domain"`
}

// Value implements driver.Valuer for database writes.
func (m MetaInfo) Value() (driver.Value, error) {
	return json.Marshal(m)
}

// Scan implements sql.Scanner for database reads.
func (m *MetaInfo) Scan(src interface{}) error {
	if src == nil {
		return nil
	}
	bytes, ok := src.([]byte)
	if !ok {
		return fmt.Errorf("MetaInfo.Scan: type assertion to []byte failed")
	}
	return json.Unmarshal(bytes, m)
}

// TechStack holds detected and missing technologies.
type TechStack struct {
	Detected []string `json:"detected"`
	Missing  []string `json:"missing"`
}

// Value implements driver.Valuer for database writes.
func (t TechStack) Value() (driver.Value, error) {
	return json.Marshal(t)
}

// Scan implements sql.Scanner for database reads.
func (t *TechStack) Scan(src interface{}) error {
	if src == nil {
		return nil
	}
	bytes, ok := src.([]byte)
	if !ok {
		return fmt.Errorf("TechStack.Scan: type assertion to []byte failed")
	}
	return json.Unmarshal(bytes, t)
}

// Metric represents an analysis metric (risk, profitability, relevance).
type Metric struct {
	Type            string   `json:"type"`
	Label           string   `json:"label"`
	Score           float64  `json:"score"`
	Level           string   `json:"level"`
	Reasoning       string   `json:"reasoning"`
	Recommendations []string `json:"recommendations"`
}

// MetricsList is a slice of Metric that implements sql.Scanner and driver.Valuer.
type MetricsList []Metric

// Value implements driver.Valuer for database writes.
func (m MetricsList) Value() (driver.Value, error) {
	return json.Marshal(m)
}

// Scan implements sql.Scanner for database reads.
func (m *MetricsList) Scan(src interface{}) error {
	if src == nil {
		return nil
	}
	bytes, ok := src.([]byte)
	if !ok {
		return fmt.Errorf("MetricsList.Scan: type assertion to []byte failed")
	}
	return json.Unmarshal(bytes, m)
}

// ==========================================
// Entity
// ==========================================

// Prediction holds the NLP analysis results for a project.
type Prediction struct {
	ID               string          `json:"id"`
	ProjectID        string          `json:"project_id"`
	MetaInfo         MetaInfo        `json:"meta_info"`
	ExecutiveSummary string          `json:"executive_summary"`
	TechStack        TechStack       `json:"tech_stack"`
	Metrics          MetricsList     `json:"metrics"`
	Keywords         []string        `json:"keywords"`
	Entities         json.RawMessage `json:"entities"`
	ModelVersion     string          `json:"model_version"`
	GeneratedAt      time.Time       `json:"generated_at"`
}

// ==========================================
// Repository Interface
// ==========================================

// PredictionRepository defines data access operations for predictions.
type PredictionRepository interface {
	GetByProjectID(ctx context.Context, projectID string) ([]*Prediction, error)
	Create(ctx context.Context, p *Prediction) (*Prediction, error)
}

// ==========================================
// Service Interface
// ==========================================

// PredictionService defines business logic for analysis generation.
type PredictionService interface {
	GetByProjectID(ctx context.Context, projectID string) ([]*Prediction, error)
	Generate(ctx context.Context, projectID string) (*Prediction, error)
}
