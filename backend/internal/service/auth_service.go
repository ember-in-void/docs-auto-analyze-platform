// Package service implements authentication business logic.
package service

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"

	"nlp-platform/internal/domain"
)

// ==========================================
// Internal Types
// ==========================================

type authService struct {
	repo      domain.UserRepository
	jwtSecret []byte
}

// ==========================================
// Constructor
// ==========================================

// NewAuthService creates a new AuthService.
func NewAuthService(repo domain.UserRepository, jwtSecret string) domain.AuthService {
	return &authService{
		repo:      repo,
		jwtSecret: []byte(jwtSecret),
	}
}

// ==========================================
// Business Logic
// ==========================================

func (s *authService) Register(ctx context.Context, req *domain.RegisterRequest) (*domain.AuthResponse, error) {
	// 1. Check if user already exists
	existing, _ := s.repo.GetByEmail(ctx, req.Email)
	if existing != nil {
		return nil, errors.New("пользователь с таким email уже существует")
	}

	// 2. Hash password
	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("authService.Register: hash password: %w", err)
	}

	// 3. Create user
	user := &domain.User{
		Email:        req.Email,
		PasswordHash: string(hash),
		FullName:     req.FullName,
		Role:         domain.RoleUser,
	}

	if err := s.repo.Create(ctx, user); err != nil {
		return nil, fmt.Errorf("authService.Register: create user: %w", err)
	}

	// 4. Generate token
	token, err := s.generateToken(user)
	if err != nil {
		return nil, fmt.Errorf("authService.Register: generate token: %w", err)
	}

	return &domain.AuthResponse{
		Token: token,
		User:  user,
	}, nil
}

func (s *authService) Login(ctx context.Context, req *domain.LoginRequest) (*domain.AuthResponse, error) {
	// 1. Find user
	user, err := s.repo.GetByEmail(ctx, req.Email)
	if err != nil {
		return nil, errors.New("неверный email или пароль")
	}

	// 2. Check password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		return nil, errors.New("неверный email или пароль")
	}

	// 3. Generate token
	token, err := s.generateToken(user)
	if err != nil {
		return nil, fmt.Errorf("authService.Login: generate token: %w", err)
	}

	return &domain.AuthResponse{
		Token: token,
		User:  user,
	}, nil
}

func (s *authService) ValidateToken(tokenString string) (*domain.User, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return s.jwtSecret, nil
	})

	if err != nil {
		return nil, fmt.Errorf("authService.ValidateToken: parse: %w", err)
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		userID := claims["sub"].(string)
		return s.repo.GetByID(context.Background(), userID)
	}

	return nil, errors.New("invalid token claims")
}

// ==========================================
// Helpers
// ==========================================

func (s *authService) generateToken(user *domain.User) (string, error) {
	claims := jwt.MapClaims{
		"sub":  user.ID,
		"exp":  time.Now().Add(time.Hour * 72).Unix(),
		"role": user.Role,
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.jwtSecret)
}
