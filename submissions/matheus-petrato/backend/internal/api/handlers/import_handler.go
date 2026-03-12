package handlers

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/matheus-petrato/sales-copilot-back/internal/models"
	"github.com/matheus-petrato/sales-copilot-back/internal/services"
)

type ImportHandler struct {
	Service *services.ImportService
}

func NewImportHandler(service *services.ImportService) *ImportHandler {
	return &ImportHandler{Service: service}
}

func (h *ImportHandler) UploadCSV(c *fiber.Ctx) error {
	sourceType := models.ImportSourceType(c.FormValue("type"))
	if sourceType == "" {
		return fiber.NewError(fiber.StatusBadRequest, "type is required (deals, accounts, products, team)")
	}

	file, err := c.FormFile("file")
	if err != nil {
		return err
	}

	// Save file temporarily
	id, _ := uuid.NewV7()
	tempPath := filepath.Join("data", "csv", fmt.Sprintf("upload_%s_%s", id.String(), file.Filename))
	if err := c.SaveFile(file, tempPath); err != nil {
		return err
	}
	defer os.Remove(tempPath)

	// Read CSV
	data, err := h.Service.ReadCSV(tempPath)
	if err != nil {
		return err
	}

	ctx := c.Context()
	var importErr error

	switch sourceType {
	case models.ImportSourceTeam:
		importErr = h.Service.ImportTeam(ctx, data)
	case models.ImportSourceAccounts:
		importErr = h.Service.ImportAccounts(ctx, data)
	case models.ImportSourceProducts:
		importErr = h.Service.ImportProducts(ctx, data)
	case models.ImportSourceDeals:
		importErr = h.Service.ImportDeals(ctx, data)
	default:
		return fiber.NewError(fiber.StatusBadRequest, "invalid source type")
	}

	if importErr != nil {
		return fiber.NewError(fiber.StatusInternalServerError, importErr.Error())
	}

	return c.JSON(fiber.Map{
		"message": "Import successful",
		"rows":    len(data),
	})
}

func (h *ImportHandler) ListImports(c *fiber.Ctx) error {
	ctx := c.Context()
	rows, err := h.Service.GetPool().Query(ctx, `
		SELECT id, filename, file_size_bytes, status, updated_at
		FROM data_imports
		ORDER BY created_at DESC`)
	if err != nil {
		return err
	}
	defer rows.Close()

	var imports []map[string]any
	for rows.Next() {
		var id uuid.UUID
		var filename, status string
		var size int64
		var updatedAt interface{}
		rows.Scan(&id, &filename, &size, &status, &updatedAt)
		imports = append(imports, map[string]any{
			"id":         id,
			"file":       filename,
			"size":       size,
			"status":     status,
			"updated_at": updatedAt,
		})
	}

	return c.JSON(imports)
}

func (h *ImportHandler) DeleteImport(c *fiber.Ctx) error {
	idStr := c.Params("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "Invalid ID")
	}

	_, err = h.Service.GetPool().Exec(c.Context(), "DELETE FROM data_imports WHERE id = $1", id)
	if err != nil {
		return err
	}

	return c.SendStatus(fiber.StatusNoContent)
}

func (h *ImportHandler) ReprocessImport(c *fiber.Ctx) error {
	// Skeleton: logic to find the file and run h.Service again
	return c.SendStatus(fiber.StatusNotImplemented)
}
