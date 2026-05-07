// Package handler implements HTTP handlers for document endpoints.
package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"path/filepath"
	"strings"

	"nlp-platform/internal/domain"
	"nlp-platform/pkg/parser"

	"github.com/go-chi/chi/v5"
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
	contentType := r.Header.Get("Content-Type")

	var docReq domain.CreateDocumentRequest

	// --- Handle Multipart (File Upload) ---
	if strings.HasPrefix(contentType, "multipart/form-data") {
		if err := r.ParseMultipartForm(10 << 20); err != nil { // 10MB limit
			writeError(w, http.StatusBadRequest, "Ошибка парсинга формы")
			return
		}

		file, header, err := r.FormFile("file")
		if err != nil {
			writeError(w, http.StatusBadRequest, "Файл не найден в запросе")
			return
		}
		defer file.Close()

		docType := r.FormValue("doc_type")
		if docType == "" {
			docType = domain.DocTypeOther
		}

		// Extract text based on extension
		ext := strings.ToLower(filepath.Ext(header.Filename))
		var content string
		var pErr error

		switch ext {
		case ".pdf":
			content, pErr = parser.ParsePDF(file, header.Size)
		case ".docx":
			content, pErr = parser.ParseDocx(file, header.Size)
		case ".txt":
			content, pErr = parser.ParsePlainText(file)
		default:
			writeError(w, http.StatusBadRequest, "Неподдерживаемый формат файла. Используйте PDF, DOCX или TXT.")
			return
		}

		if pErr != nil {
			writeError(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка парсинга файла: %v", pErr))
			return
		}

		docReq = domain.CreateDocumentRequest{
			Title:   header.Filename,
			Content: content,
			DocType: docType,
		}

	} else {
		// --- Handle JSON (Text entry) ---
		if err := json.NewDecoder(r.Body).Decode(&docReq); err != nil {
			writeError(w, http.StatusBadRequest, "Некорректное тело запроса")
			return
		}
	}

	if docReq.Content == "" {
		writeError(w, http.StatusBadRequest, "Документ не содержит текста")
		return
	}

	doc, err := h.svc.Create(projectID, &docReq)
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
