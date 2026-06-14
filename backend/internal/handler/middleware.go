// Package handler implements HTTP handlers and middleware.
package handler

import (
	"context"
	"net/http"
	"strings"

	"nlp-platform/internal/domain"
)

// ==========================================
// Types
// ==========================================

type contextKey string

const (
	UserContextKey contextKey = "user"
)

// ==========================================
// Middleware
// ==========================================

// AuthMiddleware validates the JWT token in the Authorization header.
func AuthMiddleware(svc domain.AuthService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				writeError(w, http.StatusUnauthorized, "Требуется авторизация")
				return
			}

			parts := strings.Split(authHeader, " ")
			if len(parts) != 2 || parts[0] != "Bearer" {
				writeError(w, http.StatusUnauthorized, "Некорректный формат токена")
				return
			}

			user, err := svc.ValidateToken(r.Context(), parts[1])
			if err != nil {
				writeError(w, http.StatusUnauthorized, "Недействительный токен")
				return
			}

			// Add user to context
			ctx := context.WithValue(r.Context(), UserContextKey, user)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetUserFromContext retrieves the user from the request context.
func GetUserFromContext(ctx context.Context) (*domain.User, bool) {
	user, ok := ctx.Value(UserContextKey).(*domain.User)
	return user, ok
}
