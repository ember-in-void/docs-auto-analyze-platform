// Package handler implements HTTP handlers for document endpoints.
package handler

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"
	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

// DocumentHandler handles HTTP requests for document resources.
type DocumentHandler struct {
	svc domain.DocumentService
}

// NewDocumentHandler creates a new DocumentHandler.
func NewDocumentHandler(svc domain.DocumentService) *DocumentHandler {
	return &DocumentHandler{svc: svc}
}

// ==========================================
// HTTP Handlers
// ==========================================

// GetByProjectID godoc — GET /api/v1/projects/{projectId}/documents
func (h *DocumentHandler) GetByProjectID(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "projectId")
	docs, err := h.svc.GetByProjectID(projectID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Не удалось получить документы")
		return
	}
	writeData(w, http.StatusOK, docs)
}

// GetByID godoc — GET /api/v1/documents/{id}
func (h *DocumentHandler) GetByID(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	doc, err := h.svc.GetByID(id)
	if err != nil {
		writeError(w, http.StatusNotFound, "Документ не найден")
		return
	}
	writeData(w, http.StatusOK, doc)
}

// Create godoc — POST /api/v1/projects/{projectId}/documents
func (h *DocumentHandler) Create(w http.ResponseWriter, r *http.Request) {
	projectID := chi.URLParam(r, "projectId")

	var req domain.CreateDocumentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Некорректное тело запроса")
		return
	}

	doc, err := h.svc.Create(projectID, &req)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	writeData(w, http.StatusCreated, doc)
}

// Delete godoc — DELETE /api/v1/documents/{id}
func (h *DocumentHandler) Delete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := h.svc.Delete(id); err != nil {
		writeError(w, http.StatusInternalServerError, "Не удалось удалить документ")
		return
	}
	writeMessage(w, http.StatusOK, "Документ успешно удалён")
}
