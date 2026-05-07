// main is the entry point of the NLP Platform backend server.
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"nlp-platform/internal/handler"
	"nlp-platform/internal/repository/postgres"
	"nlp-platform/internal/router"
	"nlp-platform/internal/service"
	"nlp-platform/pkg/config"
	"nlp-platform/pkg/db"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func main() {
	// ==========================================
	// Logging Setup
	// ==========================================
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr, TimeFormat: "15:04:05"})

	cfg, err := config.Load()
	if err != nil {
		log.Fatal().Err(err).Msg("failed to load config")
	}

	// ==========================================
	// Database
	// ==========================================
	ctx := context.Background()
	pool, err := db.NewPool(ctx, cfg.PostgresDSN)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to connect to database")
	}
	defer pool.Close()
	log.Info().Msg("✓ Connected to PostgreSQL")

	// ==========================================
	// Dependency Injection (Repositories)
	// ==========================================
	projectRepo := postgres.NewProjectRepository(pool)
	documentRepo := postgres.NewDocumentRepository(pool)
	predictionRepo := postgres.NewPredictionRepository(pool)
	userRepo := postgres.NewUserRepository(pool)

	// ==========================================
	// Dependency Injection (Services)
	// ==========================================
	projectSvc := service.NewProjectService(projectRepo)
	documentSvc := service.NewDocumentService(documentRepo)
	predictionSvc := service.NewPredictionService(predictionRepo, documentRepo, cfg.NLPServiceURL)
	authSvc := service.NewAuthService(userRepo, cfg.JWTSecret)

	// ==========================================
	// Dependency Injection (Handlers)
	// ==========================================
	projectH := handler.NewProjectHandler(projectSvc)
	documentH := handler.NewDocumentHandler(documentSvc)
	predictionH := handler.NewPredictionHandler(predictionSvc)
	authH := handler.NewAuthHandler(authSvc)

	// ==========================================
	// HTTP Server
	// ==========================================
	r := router.New(authH, authSvc, projectH, documentH, predictionH)

	srv := &http.Server{
		Addr:         fmt.Sprintf(":%s", cfg.AppPort),
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// ==========================================
	// Graceful Shutdown
	// ==========================================
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Info().Str("port", cfg.AppPort).Msg("🚀 Server started")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("server failed")
		}
	}()

	<-quit
	log.Info().Msg("Shutting down server...")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatal().Err(err).Msg("server forced shutdown")
	}
	log.Info().Msg("Server stopped gracefully")
}
