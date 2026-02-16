// Package model defines database models
package model

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// Asset represents a digital asset (image or document)
type Asset struct {
	ID               uuid.UUID      `gorm:"type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	BucketName       string         `gorm:"type:varchar(64);not null" json:"bucket_name"`
	ObjectName       string         `gorm:"type:varchar(255);not null" json:"object_name"`
	MimeType         string         `gorm:"type:varchar(127);not null" json:"mime_type"`
	SizeBytes        int64          `gorm:"not null" json:"size_bytes"`
	Caption          string         `gorm:"type:text" json:"caption"`
	ContentText      string         `gorm:"type:text" json:"content_text"`
	Metadata         JSONB          `gorm:"type:jsonb;default:'{}'" json:"metadata"`
	ProcessingStatus string         `gorm:"type:varchar(32);default:'PENDING'" json:"processing_status"`
	CreatedAt        time.Time      `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt        time.Time      `gorm:"autoUpdateTime" json:"updated_at"`
	DeletedAt        gorm.DeletedAt `gorm:"index" json:"-"`
}

// AssetEmbedding stores vector embeddings for an asset
type AssetEmbedding struct {
	AssetID        uuid.UUID `gorm:"type:uuid;primaryKey" json:"asset_id"`
	SemanticVector []float64 `gorm:"type:vector(1024)" json:"semantic_vector"` // BGE-M3
	VisualVector   []float64 `gorm:"type:vector(512)" json:"visual_vector"`    // CLIP ViT-B/32
}

// ProcessingTask tracks async processing status
type ProcessingTask struct {
	ID           uuid.UUID  `gorm:"type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	AssetID      uuid.UUID  `gorm:"type:uuid;not null" json:"asset_id"`
	Status       string     `gorm:"type:varchar(32);default:'PENDING'" json:"status"`
	Stage        string     `gorm:"type:varchar(32);default:'QUEUED'" json:"stage"`
	Progress     float64    `gorm:"default:0" json:"progress"`
	ErrorMessage string     `gorm:"type:text" json:"error_message"`
	CreatedAt    time.Time  `gorm:"autoCreateTime" json:"created_at"`
	StartedAt    *time.Time `json:"started_at"`
	CompletedAt  *time.Time `json:"completed_at"`
}

// JSONB type for PostgreSQL JSONB
type JSONB map[string]interface{}

// Value implements driver.Valuer for PostgreSQL JSONB serialization.
func (j JSONB) Value() (driver.Value, error) {
	if j == nil {
		return "{}", nil
	}

	data, err := json.Marshal(j)
	if err != nil {
		return nil, err
	}
	return string(data), nil
}

// Scan implements sql.Scanner for PostgreSQL JSONB deserialization.
func (j *JSONB) Scan(value interface{}) error {
	if j == nil {
		return fmt.Errorf("JSONB scan target is nil")
	}

	switch v := value.(type) {
	case nil:
		*j = JSONB{}
		return nil
	case []byte:
		if len(v) == 0 {
			*j = JSONB{}
			return nil
		}
		return json.Unmarshal(v, j)
	case string:
		if v == "" {
			*j = JSONB{}
			return nil
		}
		return json.Unmarshal([]byte(v), j)
	default:
		return fmt.Errorf("unsupported JSONB Scan type: %T", value)
	}
}

// TableName overrides
func (Asset) TableName() string {
	return "assets"
}

func (AssetEmbedding) TableName() string {
	return "asset_embeddings"
}

func (ProcessingTask) TableName() string {
	return "processing_tasks"
}

// BeforeCreate sets UUID before creating
func (a *Asset) BeforeCreate(tx *gorm.DB) error {
	if a.ID == uuid.Nil {
		a.ID = uuid.New()
	}
	return nil
}

// Processing status constants
const (
	StatusPending    = "PENDING"
	StatusProcessing = "PROCESSING"
	StatusCompleted  = "COMPLETED"
	StatusFailed     = "FAILED"
)

// Processing stage constants
const (
	StageQueued      = "QUEUED"
	StageDownloading = "DOWNLOADING"
	StageProcessing  = "PROCESSING"
	StageEmbedding   = "EMBEDDING"
	StageCompleted   = "COMPLETED"
	StageFailed      = "FAILED"
)
