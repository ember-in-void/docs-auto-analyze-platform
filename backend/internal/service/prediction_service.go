// Package service implements the mock NLP prediction logic.
// This module is a PLACEHOLDER for the future Python NLP microservice
// that will be integrated via gRPC in the full diploma implementation.
package service

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"strings"
	"time"

	"nlp-platform/internal/domain"
)

// ==========================================
// Constants — Keyword Dictionaries
// ==========================================

var profitabilityKeywords = []string{
	"прибыль", "доход", "рост", "рентабельность", "выгода",
	"эффективность", "успех", "достижение", "экономия", "оптимизация",
	"конверсия", "монетизация", "инвестиции", "масштабирование",
}

var riskKeywords = []string{
	"риск", "угроза", "проблема", "сбой", "ошибка", "задержка",
	"уязвимость", "нарушение", "инцидент", "перегрузка", "приостановлен",
	"задолженность", "штраф", "санкция",
}

var relevanceKeywords = []string{
	"актуальный", "современный", "инновационный", "перспективный",
	"востребованный", "автоматизация", "цифровой", "интеграция",
	"облачный", "микросервисный", "трансформация", "искусственный",
}

// ==========================================
// Internal Types
// ==========================================

type mockScoreResult struct {
	Profitability float64
	Risk          float64
	Relevance     float64
	Keywords      []string
	Summary       string
}

// ==========================================
// Struct & Constructor
// ==========================================

type predictionService struct {
	repo    domain.PredictionRepository
	docRepo domain.DocumentRepository
	nlpURL  string
}

// NewPredictionService creates a new PredictionService.
func NewPredictionService(repo domain.PredictionRepository, docRepo domain.DocumentRepository, nlpURL string) domain.PredictionService {
	return &predictionService{repo: repo, docRepo: docRepo, nlpURL: nlpURL}
}

// ==========================================
// Business Logic
// ==========================================

func (s *predictionService) GetByProjectID(projectID string) ([]*domain.Prediction, error) {
	return s.repo.GetByProjectID(projectID)
}

// Generate produces a real NLP analysis for a project based on its documents.
func (s *predictionService) Generate(projectID string) (*domain.Prediction, error) {
	docs, err := s.docRepo.GetByProjectID(projectID)
	if err != nil {
		return nil, fmt.Errorf("predictionService.Generate: fetch docs: %w", err)
	}

	if len(docs) == 0 {
		return nil, fmt.Errorf("недостаточно документов для анализа")
	}

	// 1. Combine text
	var sb strings.Builder
	for _, d := range docs {
		sb.WriteString(d.Title + "\n" + d.Content + "\n\n")
	}

	// 2. Call Python Service
	result, err := s.callNLP(sb.String())
	if err != nil {
		return nil, fmt.Errorf("predictionService.Generate: nlp call: %w", err)
	}

	pred := &domain.Prediction{
		ProjectID:          projectID,
		ProfitabilityScore: result.Profitability,
		RiskScore:          result.Risk,
		RelevanceScore:     result.Relevance,
		Summary:            result.Summary,
		Keywords:           result.Keywords,
		ModelVersion:       "rubert-v1",
		GeneratedAt:        time.Now(),
	}

	return s.repo.Create(pred)
}

// callNLP makes an HTTP request to the Python service.
func (s *predictionService) callNLP(text string) (*mockScoreResult, error) {
	payload, _ := json.Marshal(map[string]string{"text": text})

	resp, err := http.Post(s.nlpURL+"/analyze", "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("nlp service returned status: %d", resp.StatusCode)
	}

	var res mockScoreResult
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return nil, err
	}

	return &res, nil
}

// ==========================================
// Mock Keyword Scoring (Placeholder for NLP)
// ==========================================

// mockScore implements simple keyword-frequency analysis as a stand-in for NLP.
// Scores are bounded to [0.1, 0.95] to avoid extreme edge cases.
func (s *predictionService) mockScore(docs []*domain.Document) mockScoreResult {
	if len(docs) == 0 {
		return mockScoreResult{
			Profitability: 0.50,
			Risk:          0.50,
			Relevance:     0.50,
			Keywords:      []string{},
			Summary:       "Документация отсутствует. Анализ невозможен. Добавьте документы в проект для получения прогноза.",
		}
	}

	// Combine all document text
	var sb strings.Builder
	for _, d := range docs {
		sb.WriteString(strings.ToLower(d.Title))
		sb.WriteString(" ")
		sb.WriteString(strings.ToLower(d.Content))
		sb.WriteString(" ")
	}
	allText := sb.String()
	wordCount := float64(max(len(strings.Fields(allText)), 1))

	posHits := countHits(allText, profitabilityKeywords)
	riskHits := countHits(allText, riskKeywords)
	relHits := countHits(allText, relevanceKeywords)

	// Normalize scores with baseline offset
	profitability := clamp(0.35+float64(posHits)/wordCount*80, 0.10, 0.95)
	risk := clamp(0.15+float64(riskHits)/wordCount*70, 0.10, 0.90)
	relevance := clamp(0.40+float64(relHits)/wordCount*85, 0.10, 0.95)

	// Collect unique found keywords
	found := collectFound(allText, append(append(profitabilityKeywords, riskKeywords...), relevanceKeywords...))

	summary := fmt.Sprintf(
		"Проанализировано %d документ(ов). Найдено %d релевантных терминов. "+
			"Оценка рассчитана методом частотного анализа ключевых слов (mock-v1). "+
			"В будущей версии этот модуль будет заменён на NLP-сервис на базе трансформерных моделей.",
		len(docs), len(found),
	)

	return mockScoreResult{
		Profitability: profitability,
		Risk:          risk,
		Relevance:     relevance,
		Keywords:      found,
		Summary:       summary,
	}
}

// ==========================================
// Helper Functions
// ==========================================

func countHits(text string, keywords []string) int {
	count := 0
	for _, kw := range keywords {
		count += strings.Count(text, kw)
	}
	return count
}

func collectFound(text string, keywords []string) []string {
	seen := make(map[string]bool)
	result := make([]string, 0)
	for _, kw := range keywords {
		if !seen[kw] && strings.Contains(text, kw) {
			seen[kw] = true
			result = append(result, kw)
		}
	}
	return result
}

func clamp(val, min, max float64) float64 {
	return math.Max(min, math.Min(max, val))
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
