// Package router wires all HTTP routes and middleware.
package router

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/cors"

	"nlp-platform/internal/domain"
	"nlp-platform/internal/handler"
)

// ==========================================
// Router Builder
// ==========================================

// New creates the main application router with all registered routes.
func New(
	authH *handler.AuthHandler,
	authSvc domain.AuthService,
	projectH *handler.ProjectHandler,
	documentH *handler.DocumentHandler,
	predictionH *handler.PredictionHandler,
) http.Handler {
	r := chi.NewRouter()

	// ==========================================
	// Global Middleware
	// ==========================================
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	// ==========================================
	// CORS — allow frontend dev server
	// ==========================================
	corsMiddleware := cors.New(cors.Options{
		AllowedOrigins:   []string{"http://localhost:5173", "http://localhost:3000", "http://localhost"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Content-Type", "Authorization"},
		AllowCredentials: false,
		MaxAge:           300,
	})
	r.Use(corsMiddleware.Handler)

	// ==========================================
	// Health Check
	// ==========================================
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	})

	// ==========================================
	// API v1 Routes
	// ==========================================
	r.Route("/api/v1", func(r chi.Router) {

		// --- Public Auth ---
		r.Route("/auth", func(r chi.Router) {
			r.Post("/register", authH.Register)
			r.Post("/login", authH.Login)
		})

		// ==========================================
		// Protected Routes
		// All routes in this group require a valid JWT token.
		// Protects: /projects, /documents, /predictions
		// ==========================================
		r.Group(func(r chi.Router) {
			r.Use(handler.AuthMiddleware(authSvc))

			// --- Projects ---
			r.Route("/projects", func(r chi.Router) {
				r.Get("/", projectH.GetAll)
				r.Post("/", projectH.Create)

				r.Route("/{projectId}", func(r chi.Router) {
					r.Get("/", projectH.GetByID)
					r.Put("/", projectH.Update)
					r.Delete("/", projectH.Delete)

					// --- Documents (nested under project) ---
					r.Get("/documents", documentH.GetByProjectID)
					r.Post("/documents", documentH.Create)

					// --- Predictions (nested under project) ---
					r.Get("/predictions", predictionH.GetByProjectID)
					r.Post("/predictions/generate", predictionH.Generate)
				})
			})

			// --- Documents (standalone) ---
			r.Route("/documents/{id}", func(r chi.Router) {
				r.Get("/", documentH.GetByID)
				r.Delete("/", documentH.Delete)
			})
		})
	})

	return r
}
