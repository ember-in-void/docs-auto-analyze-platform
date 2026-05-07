// Package parser provides utilities to extract text from various file formats.
package parser

import (
	"bytes"
	"fmt"
	"io"
	"strings"

	"github.com/nguyenthenguyen/docx"
	"rsc.io/pdf"
)

// ==========================================
// Public Functions
// ==========================================

// ParsePDF extracts text from a PDF file.
func ParsePDF(r io.ReaderAt, size int64) (string, error) {
	reader, err := pdf.NewReader(r, size)
	if err != nil {
		return "", fmt.Errorf("parser.ParsePDF: %w", err)
	}

	var sb strings.Builder
	numPages := reader.NumPage()
	for i := 1; i <= numPages; i++ {
		page := reader.Page(i)
		if page.V.IsNull() {
			continue
		}
		content := page.Content()
		for _, text := range content.Text {
			sb.WriteString(text.S)
			sb.WriteString(" ")
		}
		sb.WriteString("\n")
	}

	return sb.String(), nil
}

// ParseDocx extracts text from a .docx file.
func ParseDocx(r io.Reader, size int64) (string, error) {
	// docx.ReadDocxFromMemory expects a byte slice
	data, err := io.ReadAll(r)
	if err != nil {
		return "", fmt.Errorf("parser.ParseDocx: read: %w", err)
	}

	doc, err := docx.ReadDocxFromMemory(bytes.NewReader(data), size)
	if err != nil {
		return "", fmt.Errorf("parser.ParseDocx: parse: %w", err)
	}
	defer doc.Close()

	return doc.Editable().GetContent(), nil
}

// ParsePlainText extracts text from a plain text file.
func ParsePlainText(r io.Reader) (string, error) {
	buf := new(bytes.Buffer)
	if _, err := buf.ReadFrom(r); err != nil {
		return "", fmt.Errorf("parser.ParsePlainText: %w", err)
	}
	return buf.String(), nil
}
