package handler

import "github.com/go-playground/validator/v10"

var validate = validator.New()

// ValidateStruct checks structural tags like validate:"required,email"
func ValidateStruct(s interface{}) error {
	return validate.Struct(s)
}
