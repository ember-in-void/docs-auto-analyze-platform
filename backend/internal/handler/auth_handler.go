// Package handler implements HTTP handlers for authentication.
package handler

import (
	"encoding/json"
	"net/http"

	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

// AuthHandler handles HTTP requests for /auth.
type AuthHandler struct {
	svc domain.AuthService
}

// NewAuthHandler creates a new AuthHandler.
func NewAuthHandler(svc domain.AuthService) *AuthHandler {
	return &AuthHandler{svc: svc}
}

// ==========================================
// HTTP Handlers
// ==========================================

// Register godoc — POST /api/v1/auth/register
func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req domain.RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Некорректное тело запроса")
		return
	}

	res, err := h.svc.Register(r.Context(), &req)
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	writeData(w, http.StatusCreated, res)
}

// Login godoc — POST /api/v1/auth/login
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req domain.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "Некорректное тело запроса")
		return
	}

	res, err := h.svc.Login(r.Context(), &req)
	if err != nil {
		writeError(w, http.StatusUnauthorized, err.Error())
		return
	}

	writeData(w, http.StatusOK, res)
}
