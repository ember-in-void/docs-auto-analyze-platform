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
// Gap Analysis Structures
// ==========================================

// GapSectionStatus defines validation status of sections.
type GapSectionStatus string

const (
	GapStatusPresent GapSectionStatus = "present"
	GapStatusPartial GapSectionStatus = "partial"
	GapStatusMissing GapSectionStatus = "missing"
)

// GapMetadata holds project metadata identified in document.
type GapMetadata struct {
	ProjectName  *string `json:"project_name"`
	DocumentDate *string `json:"document_date"`
	Deadline     *string `json:"deadline"`
	Budget       *string `json:"budget"`
}

// GapPurposeSection holds results for project essence.
type GapPurposeSection struct {
	Status        GapSectionStatus `json:"status"`
	ExtractedText *string          `json:"extracted_text"`
	Gaps          []string         `json:"gaps"`
}

// GapTechStackSection holds results for stack analysis.
type GapTechStackSection struct {
	Status                  GapSectionStatus `json:"status"`
	ExtractedTechnologies   []string         `json:"extracted_technologies"`
	ArchitectureDescription *string          `json:"architecture_description"`
	Gaps                    []string         `json:"gaps"`
}

// GapRiskItem holds a risk entity and category.
type GapRiskItem struct {
	Text     string  `json:"text"`
	Category *string `json:"category"`
}

// GapRisksSection holds results for project risks.
type GapRisksSection struct {
	Status         GapSectionStatus `json:"status"`
	ExtractedRisks []GapRiskItem    `json:"extracted_risks"`
	Gaps           []string         `json:"gaps"`
}

// GapMetricItem represents a financial metric.
type GapMetricItem struct {
	Metric string `json:"metric"`
	Value  string `json:"value"`
}

// GapEconomicsSection holds results for economic metrics.
type GapEconomicsSection struct {
	Status           GapSectionStatus `json:"status"`
	ExtractedMetrics []GapMetricItem  `json:"extracted_metrics"`
	Gaps             []string         `json:"gaps"`
}

// GapSections groups the 4 template sections.
type GapSections struct {
	Purpose   GapPurposeSection   `json:"purpose"`
	TechStack GapTechStackSection `json:"tech_stack"`
	Risks     GapRisksSection     `json:"risks"`
	Economics GapEconomicsSection `json:"economics"`
}

// GapAnalysisResult holds the complete result of project documentation gap analysis.
type GapAnalysisResult struct {
	Metadata            GapMetadata `json:"metadata"`
	Sections            GapSections `json:"sections"`
	CompletenessScore   float64     `json:"completeness_score"`
	ClarifyingQuestions []string    `json:"clarifying_questions"`
	// Advanced analysis fields:
	IntegrationComplexity   string   `json:"integration_complexity,omitempty"`
	IntegrationGaps         []string `json:"integration_gaps,omitempty"`
	VendorLockRisk          string   `json:"vendor_lock_risk,omitempty"`
	OpexInfraWarnings       []string `json:"opex_infra_warnings,omitempty"`
	ArchitectureSuitability string   `json:"architecture_suitability,omitempty"`
	FeasibilityTimeline     string   `json:"feasibility_timeline,omitempty"`
}

// Value implements driver.Valuer for database writes.
func (g GapAnalysisResult) Value() (driver.Value, error) {
	bytes, err := json.Marshal(g)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal GapAnalysisResult: %w", err)
	}
	return bytes, nil
}

// Scan implements sql.Scanner for database reads.
func (g *GapAnalysisResult) Scan(src interface{}) error {
	if src == nil {
		return nil
	}
	bytes, ok := src.([]byte)
	if !ok {
		return fmt.Errorf("failed to scan GapAnalysisResult: type assertion to []byte failed")
	}
	if err := json.Unmarshal(bytes, g); err != nil {
		return fmt.Errorf("failed to unmarshal GapAnalysisResult: %w", err)
	}
	return nil
}

// ==========================================
// Entity
// ==========================================

// Prediction holds the NLP analysis results for a project.
type Prediction struct {
	ID               string             `json:"id"`
	ProjectID        string             `json:"project_id"`
	Status           string             `json:"status"`
	MetaInfo         MetaInfo           `json:"meta_info"`
	ExecutiveSummary string             `json:"executive_summary"`
	TechStack        TechStack          `json:"tech_stack"`
	Metrics          MetricsList        `json:"metrics"`
	Keywords         []string           `json:"keywords"`
	Entities         json.RawMessage    `json:"entities"`
	ModelVersion     string             `json:"model_version"`
	GeneratedAt      time.Time          `json:"generated_at"`
	GapAnalysis      *GapAnalysisResult `json:"gap_analysis,omitempty"`
}

// ==========================================
// Repository Interface
// ==========================================

// PredictionRepository defines data access operations for predictions.
type PredictionRepository interface {
	GetByProjectID(ctx context.Context, projectID string) ([]*Prediction, error)
	Create(ctx context.Context, p *Prediction) (*Prediction, error)
	Update(ctx context.Context, p *Prediction) error
}

// ==========================================
// Service Interface
// ==========================================

// PredictionService defines business logic for analysis generation.
type PredictionService interface {
	GetByProjectID(ctx context.Context, projectID string) ([]*Prediction, error)
	Generate(ctx context.Context, projectID string) (*Prediction, error)
}
