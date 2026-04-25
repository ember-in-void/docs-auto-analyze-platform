// Package handler provides shared HTTP response helpers.
package handler

import (
	"encoding/json"
	"net/http"
)

// ==========================================
// Response Envelope
// ==========================================

type response struct {
	Data    any    `json:"data,omitempty"`
	Error   string `json:"error,omitempty"`
	Message string `json:"message,omitempty"`
}

// ==========================================
// Helper Functions
// ==========================================

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeData(w http.ResponseWriter, status int, data any) {
	writeJSON(w, status, response{Data: data})
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, response{Error: msg})
}

func writeMessage(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, response{Message: msg})
}
