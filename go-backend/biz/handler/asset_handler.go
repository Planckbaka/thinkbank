// Package handler contains HTTP handlers
package handler

import (
	"context"
	"fmt"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/cloudwego/hertz/pkg/app"
	"github.com/cloudwego/hertz/pkg/protocol/consts"
	"github.com/google/uuid"

	"thinkbank/backend/biz/dal/minio"
	"thinkbank/backend/biz/dal/postgres"
	"thinkbank/backend/biz/dal/redis"
	"thinkbank/backend/biz/model"
	"thinkbank/backend/biz/pkg/errno"
)

// UploadRequest represents file upload request
type UploadRequest struct {
	// File is handled via multipart form
}

// UploadResponse represents upload response
type UploadResponse struct {
	AssetID string `json:"asset_id"`
	Message string `json:"message"`
}

// AssetResponse represents a single asset
type AssetResponse struct {
	ID               string                 `json:"id"`
	FileName         string                 `json:"file_name"`
	MimeType         string                 `json:"mime_type"`
	SizeBytes        int64                  `json:"size_bytes"`
	Caption          string                 `json:"caption,omitempty"`
	ProcessingStatus string                 `json:"processing_status"`
	URL              string                 `json:"url,omitempty"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
	CreatedAt        time.Time              `json:"created_at"`
}

// AssetListResponse represents list of assets
type AssetListResponse struct {
	Assets  []AssetResponse `json:"assets"`
	Total   int64           `json:"total"`
	Page    int             `json:"page"`
	PerPage int             `json:"per_page"`
}

// Upload handles file upload
func Upload(ctx context.Context, c *app.RequestContext) {
	// Get file from form
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(consts.StatusBadRequest, errno.FileUploadErr)
		return
	}

	// Validate file size (max 100MB)
	if file.Size > 100*1024*1024 {
		c.JSON(consts.StatusBadRequest, errno.FileTooLarge)
		return
	}

	// Validate file type
	contentType := file.Header.Get("Content-Type")
	if !isValidFileType(contentType) {
		c.JSON(consts.StatusBadRequest, errno.InvalidFileType)
		return
	}

	// Generate asset ID
	assetID := uuid.New()

	// Determine file extension
	objectName := fmt.Sprintf("%s/%s", assetID.String(), assetID.String())

	// Upload to MinIO
	bucket := minio.GetBucket()
	objectPath, err := minio.UploadFile(ctx, bucket, objectName, file)
	if err != nil {
		c.JSON(consts.StatusInternalServerError, errno.MinIOErr)
		return
	}

	// Create asset record in database
	asset := &model.Asset{
		ID:               assetID,
		BucketName:       bucket,
		ObjectName:       objectPath,
		MimeType:         contentType,
		SizeBytes:        file.Size,
		ProcessingStatus: model.StatusPending,
	}

	if err := postgres.DB.Create(asset).Error; err != nil {
		c.JSON(consts.StatusInternalServerError, errno.DBErr)
		return
	}

	// Create processing task
	task := &model.ProcessingTask{
		AssetID: assetID,
		Status:  model.StatusPending,
		Stage:   model.StageQueued,
	}
	if err := postgres.DB.Create(task).Error; err != nil {
		c.JSON(consts.StatusInternalServerError, errno.DBErr)
		return
	}

	// Push to Redis queue for async processing
	if err := redis.PushTask(ctx, assetID.String()); err != nil {
		c.JSON(consts.StatusInternalServerError, errno.RedisErr)
		return
	}

	c.JSON(consts.StatusOK, UploadResponse{
		AssetID: assetID.String(),
		Message: "File uploaded successfully",
	})
}

// ListAssets lists all assets with pagination
func ListAssets(ctx context.Context, c *app.RequestContext) {
	page := c.DefaultQuery("page", "1")
	perPage := c.DefaultQuery("per_page", "20")
	status := c.Query("status")
	pageNum, perPageNum := parsePagination(page, perPage)

	var assets []model.Asset
	var total int64

	query := postgres.DB.Model(&model.Asset{})

	if status != "" {
		query = query.Where("processing_status = ?", status)
	}

	// Get total count
	if err := query.Count(&total).Error; err != nil {
		c.JSON(consts.StatusInternalServerError, errno.DBErr)
		return
	}

	// Get paginated results
	offset := (pageNum - 1) * perPageNum
	if err := query.Order("created_at DESC").Offset(offset).Limit(perPageNum).Find(&assets).Error; err != nil {
		c.JSON(consts.StatusInternalServerError, errno.DBErr)
		return
	}

	// Convert to response
	responses := make([]AssetResponse, len(assets))
	for i, asset := range assets {
		responses[i] = AssetResponse{
			ID:               asset.ID.String(),
			FileName:         filepath.Base(asset.ObjectName),
			MimeType:         asset.MimeType,
			SizeBytes:        asset.SizeBytes,
			Caption:          asset.Caption,
			ProcessingStatus: asset.ProcessingStatus,
			Metadata:         asset.Metadata,
			CreatedAt:        asset.CreatedAt,
		}
	}

	c.JSON(consts.StatusOK, AssetListResponse{
		Assets:  responses,
		Total:   total,
		Page:    pageNum,
		PerPage: perPageNum,
	})
}

// GetAsset gets a single asset by ID
func GetAsset(ctx context.Context, c *app.RequestContext) {
	assetID := c.Param("id")

	var asset model.Asset
	if err := postgres.DB.Where("id = ?", assetID).First(&asset).Error; err != nil {
		c.JSON(consts.StatusNotFound, errno.AssetNotFound)
		return
	}

	// Generate presigned URL
	url, err := minio.GetFileURL(ctx, asset.BucketName, asset.ObjectName, 3600)
	if err != nil {
		url = ""
	}

	c.JSON(consts.StatusOK, AssetResponse{
		ID:               asset.ID.String(),
		FileName:         filepath.Base(asset.ObjectName),
		MimeType:         asset.MimeType,
		SizeBytes:        asset.SizeBytes,
		Caption:          asset.Caption,
		ProcessingStatus: asset.ProcessingStatus,
		URL:              url,
		Metadata:         asset.Metadata,
		CreatedAt:        asset.CreatedAt,
	})
}

// DeleteAsset deletes an asset
func DeleteAsset(ctx context.Context, c *app.RequestContext) {
	assetID := c.Param("id")

	var asset model.Asset
	if err := postgres.DB.Where("id = ?", assetID).First(&asset).Error; err != nil {
		c.JSON(consts.StatusNotFound, errno.AssetNotFound)
		return
	}

	// Delete from MinIO
	if err := minio.DeleteFile(ctx, asset.BucketName, asset.ObjectName); err != nil {
		c.JSON(consts.StatusInternalServerError, errno.MinIOErr)
		return
	}

	// Soft delete from database
	if err := postgres.DB.Delete(&asset).Error; err != nil {
		c.JSON(consts.StatusInternalServerError, errno.DBErr)
		return
	}

	c.JSON(consts.StatusOK, map[string]string{"message": "Asset deleted successfully"})
}

// Helper functions

func isValidFileType(contentType string) bool {
	validTypes := []string{
		"image/jpeg",
		"image/png",
		"image/gif",
		"image/webp",
		"application/pdf",
		"text/plain",
		"application/json",
		"text/markdown",
	}
	for _, t := range validTypes {
		if strings.HasPrefix(contentType, t) {
			return true
		}
	}
	return false
}

func parsePagination(pageRaw, perPageRaw string) (int, int) {
	page := parsePositiveInt(pageRaw, 1)
	perPage := parsePositiveInt(perPageRaw, 20)
	if perPage > 100 {
		perPage = 100
	}
	return page, perPage
}

func parsePositiveInt(raw string, fallback int) int {
	value, err := strconv.Atoi(raw)
	if err != nil || value <= 0 {
		return fallback
	}
	return value
}
