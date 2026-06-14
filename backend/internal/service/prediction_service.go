// Package service implements the mock NLP prediction logic.
// This module is a PLACEHOLDER for the future Python NLP microservice
// that will be integrated via gRPC in the full diploma implementation.
package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"strings"
	"time"

	"nlp-platform/internal/domain"

	"github.com/rs/zerolog/log"
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

type nlpAnalysisResult struct {
	MetaInfo         domain.MetaInfo           `json:"meta_info"`
	ExecutiveSummary string                    `json:"executive_summary"`
	TechStack        domain.TechStack          `json:"tech_stack"`
	Metrics          domain.MetricsList        `json:"metrics"`
	Entities         json.RawMessage           `json:"entities"`
	GapAnalysis      *domain.GapAnalysisResult `json:"gap_analysis"`
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

func (s *predictionService) GetByProjectID(ctx context.Context, projectID string) ([]*domain.Prediction, error) {
	return s.repo.GetByProjectID(ctx, projectID)
}

// Generate produces a real NLP analysis for a project based on its documents.
func (s *predictionService) Generate(ctx context.Context, projectID string) (*domain.Prediction, error) {
	docs, err := s.docRepo.GetByProjectID(ctx, projectID)
	if err != nil {
		return nil, fmt.Errorf("predictionService.Generate: fetch docs: %w", err)
	}

	if len(docs) == 0 {
		return nil, fmt.Errorf("недостаточно документов для анализа")
	}

	// 1. Combine text
	var sb strings.Builder
	for i, d := range docs {
		if i > 0 {
			sb.WriteString("\n\n")
		}
		sb.WriteString(d.Content)
	}
	combinedText := sb.String()

	// 2. Create placeholder prediction with status = "pending"
	pred := &domain.Prediction{
		ProjectID:        projectID,
		Status:           "pending",
		MetaInfo:         domain.MetaInfo{Budget: "В процессе...", Timeline: "В процессе...", Domain: "В процессе..."},
		ExecutiveSummary: "Анализ документа выполняется нейросетью. Пожалуйста, подождите...",
		TechStack:        domain.TechStack{Detected: []string{}, Missing: []string{}},
		Metrics: domain.MetricsList{
			{Type: "risk", Label: "Уровень риска", Score: 0.0, Level: "Оценка...", Reasoning: "Расчет...", Recommendations: []string{}},
			{Type: "profitability", Label: "Потенциал окупаемости", Score: 0.0, Level: "Оценка...", Reasoning: "Расчет...", Recommendations: []string{}},
			{Type: "relevance", Label: "Соответствие требованиям", Score: 0.0, Level: "Оценка...", Reasoning: "Расчет...", Recommendations: []string{}},
		},
		Keywords:     []string{},
		Entities:     json.RawMessage("[]"),
		ModelVersion: "rubert-tiny2",
		GeneratedAt:  time.Now(),
		GapAnalysis:  nil,
	}

	createdPred, err := s.repo.Create(ctx, pred)
	if err != nil {
		return nil, fmt.Errorf("predictionService.Generate: create pending prediction: %w", err)
	}

	// 3. Start background analysis goroutine
	go func() {
		bgCtx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
		defer cancel()

		result, err := s.callNLP(bgCtx, combinedText)
		var finalPred domain.Prediction

		if err != nil {
			log.Warn().Err(err).Str("project_id", projectID).Msg("NLP service call failed, falling back to mock scoring")
			mockResult := s.mockScore(docs)

			finalPred = domain.Prediction{
				ID:               createdPred.ID,
				ProjectID:        projectID,
				Status:           "completed",
				MetaInfo:         mockResult.MetaInfo,
				ExecutiveSummary: mockResult.ExecutiveSummary + "\n\n(Внимание: Нейросеть недоступна, применен частотный анализ-заглушка)",
				TechStack:        mockResult.TechStack,
				Metrics:          mockResult.Metrics,
				Keywords:         mockResult.TechStack.Detected,
				Entities:         mockResult.Entities,
				ModelVersion:     "rubert-tiny2-fallback",
				GeneratedAt:      time.Now(),
				GapAnalysis:      mockResult.GapAnalysis,
			}
		} else {
			finalPred = domain.Prediction{
				ID:               createdPred.ID,
				ProjectID:        projectID,
				Status:           "completed",
				MetaInfo:         result.MetaInfo,
				ExecutiveSummary: result.ExecutiveSummary,
				TechStack:        result.TechStack,
				Metrics:          result.Metrics,
				Keywords:         result.TechStack.Detected,
				Entities:         result.Entities,
				ModelVersion:     "rubert-tiny2",
				GeneratedAt:      time.Now(),
				GapAnalysis:      result.GapAnalysis,
			}
		}

		if err := s.repo.Update(context.Background(), &finalPred); err != nil {
			log.Error().Err(err).Str("prediction_id", createdPred.ID).Msg("Failed to update prediction in background")
		} else {
			log.Info().Str("prediction_id", createdPred.ID).Msg("✓ Prediction analysis successfully completed and saved")
		}
	}()

	return createdPred, nil
}

// callNLP makes an HTTP request to the Python service with a 15-second timeout.
func (s *predictionService) callNLP(ctx context.Context, text string) (*nlpAnalysisResult, error) {
	payload, _ := json.Marshal(map[string]string{"text": text})

	// Create a custom HTTP client with a timeout
	client := &http.Client{
		Timeout: 90 * time.Second,
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.nlpURL+"/analyze", bytes.NewBuffer(payload))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("nlp service request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("nlp service returned status: %d", resp.StatusCode)
	}

	var res nlpAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return nil, fmt.Errorf("failed to decode nlp response: %w", err)
	}

	// If the python service doesn't return entities yet, make it an empty array instead of null
	if res.Entities == nil || string(res.Entities) == "null" {
		res.Entities = json.RawMessage("[]")
	}

	return &res, nil
}

// ==========================================
// Mock Keyword Scoring (Placeholder for NLP)
// ==========================================

// mockScore implements simple keyword-frequency analysis as a stand-in for NLP.
// Scores are bounded to [0.1, 0.95] to avoid extreme edge cases.
func (s *predictionService) mockScore(docs []*domain.Document) nlpAnalysisResult {
	if len(docs) == 0 {
		return nlpAnalysisResult{
			MetaInfo: domain.MetaInfo{
				Budget:   "Не указано",
				Timeline: "Не указано",
				Domain:   "Не указано",
			},
			ExecutiveSummary: "Документация отсутствует. Анализ невозможен. Добавьте документы в проект для получения прогноза.",
			TechStack: domain.TechStack{
				Detected: []string{},
				Missing:  []string{"Redis", "Message Broker"},
			},
			Metrics: domain.MetricsList{
				{Type: "risk", Label: "Уровень риска", Score: 50.0, Level: "Средний", Reasoning: "Документация отсутствует", Recommendations: []string{}},
				{Type: "profitability", Label: "Потенциал окупаемости", Score: 50.0, Level: "Средний", Reasoning: "Документация отсутствует", Recommendations: []string{}},
				{Type: "relevance", Label: "Соответствие требованиям", Score: 50.0, Level: "Средний", Reasoning: "Документация отсутствует", Recommendations: []string{}},
			},
			Entities: json.RawMessage("[]"),
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
	profitability := clamp(0.35+float64(posHits)/wordCount*80, 0.10, 0.95) * 100
	risk := clamp(0.15+float64(riskHits)/wordCount*70, 0.10, 0.90) * 100
	relevance := clamp(0.40+float64(relHits)/wordCount*85, 0.10, 0.95) * 100

	// Collect unique found keywords
	found := collectFound(allText, append(append(profitabilityKeywords, riskKeywords...), relevanceKeywords...))

	summary := fmt.Sprintf(
		"Проанализировано %d документ(ов). Найдено %d релевантных терминов. "+
			"Оценка рассчитана методом частотного анализа ключевых слов (mock-v1).",
		len(docs), len(found),
	)

	return nlpAnalysisResult{
		MetaInfo: domain.MetaInfo{
			Budget:   "Не указано",
			Timeline: "Не указано",
			Domain:   "Не указано",
		},
		ExecutiveSummary: summary,
		TechStack: domain.TechStack{
			Detected: found,
			Missing:  []string{"Redis", "Message Broker"},
		},
		Metrics: domain.MetricsList{
			{Type: "risk", Label: "Уровень риска", Score: risk, Level: "Средний", Reasoning: "Оценка риска на основе частотного анализа.", Recommendations: []string{}},
			{Type: "profitability", Label: "Потенциал окупаемости", Score: profitability, Level: "Средний", Reasoning: "Оценка доходности на основе частотного анализа.", Recommendations: []string{}},
			{Type: "relevance", Label: "Соответствие требованиям", Score: relevance, Level: "Средний", Reasoning: "Оценка соответствия на основе частотного анализа.", Recommendations: []string{}},
		},
		Entities: json.RawMessage("[]"),
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
