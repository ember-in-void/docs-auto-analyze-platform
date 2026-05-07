// Package config loads application configuration from environment variables.
package config

import (
	"fmt"
	"os"
)

// ==========================================
// Config Struct
// ==========================================

// Config holds all application configuration values.
type Config struct {
	AppPort       string
	PostgresDSN   string
	JWTSecret     string
	NLPServiceURL string
}

// ==========================================
// Constructor
// ==========================================

// Load reads configuration from environment variables.
// Returns an error if any required variable is missing.
func Load() (*Config, error) {
	dsn := os.Getenv("POSTGRES_DSN")
	if dsn == "" {
		return nil, fmt.Errorf("POSTGRES_DSN environment variable is required")
	}

	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8080"
	}

	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "very-secret-key-change-it"
	}

	nlpURL := os.Getenv("NLP_SERVICE_URL")
	if nlpURL == "" {
		nlpURL = "http://localhost:5000"
	}

	return &Config{
		AppPort:       port,
		PostgresDSN:   dsn,
		JWTSecret:     jwtSecret,
		NLPServiceURL: nlpURL,
	}, nil
}
