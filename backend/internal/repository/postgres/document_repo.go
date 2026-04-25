// Package postgres implements domain.DocumentRepository using pgx/v5.
package postgres

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
	"nlp-platform/internal/domain"
)

// ==========================================
// Struct & Constructor
// ==========================================

type documentRepository struct {
	db *pgxpool.Pool
}

// NewDocumentRepository creates a new postgres-backed DocumentRepository.
func NewDocumentRepository(db *pgxpool.Pool) domain.DocumentRepository {
	return &documentRepository{db: db}
}

// ==========================================
// Read Operations
// ==========================================

func (r *documentRepository) GetByProjectID(projectID string) ([]*domain.Document, error) {
	const q = `
		SELECT id, project_id, title, content, doc_type, uploaded_at
		FROM documents
		WHERE project_id = $1
		ORDER BY uploaded_at DESC`

	rows, err := r.db.Query(context.Background(), q, projectID)
	if err != nil {
		return nil, fmt.Errorf("documentRepo.GetByProjectID: query: %w", err)
	}
	defer rows.Close()

	docs := make([]*domain.Document, 0)
	for rows.Next() {
		d := &domain.Document{}
		if err := rows.Scan(&d.ID, &d.ProjectID, &d.Title, &d.Content, &d.DocType, &d.UploadedAt); err != nil {
			return nil, fmt.Errorf("documentRepo.GetByProjectID: scan: %w", err)
		}
		docs = append(docs, d)
	}
	return docs, rows.Err()
}

func (r *documentRepository) GetByID(id string) (*domain.Document, error) {
	const q = `
		SELECT id, project_id, title, content, doc_type, uploaded_at
		FROM documents
		WHERE id = $1`

	d := &domain.Document{}
	err := r.db.QueryRow(context.Background(), q, id).
		Scan(&d.ID, &d.ProjectID, &d.Title, &d.Content, &d.DocType, &d.UploadedAt)
	if err != nil {
		return nil, fmt.Errorf("documentRepo.GetByID: %w", err)
	}
	return d, nil
}

// ==========================================
// Write Operations
// ==========================================

func (r *documentRepository) Create(projectID string, req *domain.CreateDocumentRequest) (*domain.Document, error) {
	docType := req.DocType
	if docType == "" {
		docType = domain.DocTypeOther
	}

	const q = `
		INSERT INTO documents (project_id, title, content, doc_type)
		VALUES ($1, $2, $3, $4)
		RETURNING id, project_id, title, content, doc_type, uploaded_at`

	d := &domain.Document{}
	err := r.db.QueryRow(context.Background(), q, projectID, req.Title, req.Content, docType).
		Scan(&d.ID, &d.ProjectID, &d.Title, &d.Content, &d.DocType, &d.UploadedAt)
	if err != nil {
		return nil, fmt.Errorf("documentRepo.Create: %w", err)
	}
	return d, nil
}

func (r *documentRepository) Delete(id string) error {
	const q = `DELETE FROM documents WHERE id = $1`
	_, err := r.db.Exec(context.Background(), q, id)
	if err != nil {
		return fmt.Errorf("documentRepo.Delete: %w", err)
	}
	return nil
}
