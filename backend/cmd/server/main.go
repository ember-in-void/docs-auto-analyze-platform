// main is the entry point of the NLP Platform backend server.
package main

import (
	"context"
	"fmt"
	"log"
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
)

func main() {
	// ==========================================
	// Configuration
	// ==========================================
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config: %v", err)
	}

	// ==========================================
	// Database
	// ==========================================
	ctx := context.Background()
	pool, err := db.NewPool(ctx, cfg.PostgresDSN)
	if err != nil {
		log.Fatalf("db: %v", err)
	}
	defer pool.Close()
	log.Println("✓ Connected to PostgreSQL")

	// ==========================================
	// Dependency Injection (Repositories)
	// ==========================================
	projectRepo := postgres.NewProjectRepository(pool)
	documentRepo := postgres.NewDocumentRepository(pool)
	predictionRepo := postgres.NewPredictionRepository(pool)

	// ==========================================
	// Dependency Injection (Services)
	// ==========================================
	projectSvc := service.NewProjectService(projectRepo)
	documentSvc := service.NewDocumentService(documentRepo)
	predictionSvc := service.NewPredictionService(predictionRepo, documentRepo)

	// ==========================================
	// Dependency Injection (Handlers)
	// ==========================================
	projectH := handler.NewProjectHandler(projectSvc)
	documentH := handler.NewDocumentHandler(documentSvc)
	predictionH := handler.NewPredictionHandler(predictionSvc)

	// ==========================================
	// HTTP Server
	// ==========================================
	r := router.New(projectH, documentH, predictionH)

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
		log.Printf("✓ Server started on :%s", cfg.AppPort)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server: %v", err)
		}
	}()

	<-quit
	log.Println("Shutting down server...")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("server forced shutdown: %v", err)
	}
	log.Println("Server stopped gracefully")
}
