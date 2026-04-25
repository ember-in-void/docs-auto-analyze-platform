// Package handler implements HTTP handlers for prediction endpoints.
package handler

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

// PredictionHandler handles HTTP requests for prediction resources.
type PredictionHandler struct {
	svc domain.PredictionService
}

// NewPredictionHandler creates a new PredictionHandler.
func NewPredictionHandler(svc domain.PredictionService) *PredictionHandler {
	return &PredictionHandler{svc: svc}
}

// ==========================================
// HTTP Handlers
// ==========================================

// GetByProjectID godoc — GET /api/v1/projects/{projectId}/predictions
func (h *PredictionHandler) GetByProjectID(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "projectId")
	preds, err := h.svc.GetByProjectID(projectID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Не удалось получить прогнозы")
		return
	}
	writeData(w, http.StatusOK, preds)
}

// Generate godoc — POST /api/v1/projects/{projectId}/predictions/generate
// Triggers mock NLP analysis for the project. Placeholder for the real NLP service.
func (h *PredictionHandler) Generate(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "projectId")
	pred, err := h.svc.Generate(projectID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Не удалось выполнить анализ: "+err.Error())
		return
	}
	writeData(w, http.StatusCreated, pred)
}
