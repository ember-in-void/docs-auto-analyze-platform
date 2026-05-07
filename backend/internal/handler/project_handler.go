// Package handler implements HTTP handlers for project endpoints.
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

// ProjectHandler handles HTTP requests for /projects.
type ProjectHandler struct {
	svc domain.ProjectService
}

// NewProjectHandler creates a new ProjectHandler.
func NewProjectHandler(svc domain.ProjectService) *ProjectHandler {
	return &ProjectHandler{svc: svc}
}

// ==========================================
// HTTP Handlers
// ==========================================

// GetAll godoc — GET /api/v1/projects
func (h *ProjectHandler) GetAll(w http.ResponseWriter, r *http.Request) {
	user, _ := GetUserFromContext(r.Context())
	projects, err := h.svc.GetAll(user.ID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Не удалось получить список проектов")
		return
	}
	writeData(w, http.StatusOK, projects)
}

// GetByID godoc — GET /api/v1/projects/{id}
func (h *ProjectHandler) GetByID(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	user, _ := GetUserFromContext(r.Context())
	project, err := h.svc.GetByID(id, user.ID)
	if err != nil {
		writeError(w, http.StatusNotFound, "Проект не найден")
		return
	}
	writeData(w, http.StatusOK, project)
}

// Create godoc — POST /api/v1/projects
func (h *ProjectHandler) Create(w http.ResponseWriter, r *http.Request) {
	var req domain.CreateProjectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Некорректное тело запроса")
		return
	}

	user, _ := GetUserFromContext(r.Context())
	project, err := h.svc.Create(user.ID, &req)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	writeData(w, http.StatusCreated, project)
}

// Update godoc — PUT /api/v1/projects/{id}
func (h *ProjectHandler) Update(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")

	var req domain.UpdateProjectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Некорректное тело запроса")
		return
	}

	user, _ := GetUserFromContext(r.Context())
	project, err := h.svc.Update(id, user.ID, &req)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}
	writeData(w, http.StatusOK, project)
}

// Delete godoc — DELETE /api/v1/projects/{id}
func (h *ProjectHandler) Delete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	user, _ := GetUserFromContext(r.Context())
	if err := h.svc.Delete(id, user.ID); err != nil {
		writeError(w, http.StatusInternalServerError, "Не удалось удалить проект")
		return
	}
	writeMessage(w, http.StatusOK, "Проект успешно удалён")
}
