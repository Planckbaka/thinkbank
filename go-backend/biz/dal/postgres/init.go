// Package postgres provides PostgreSQL database connection using GORM
package postgres

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"thinkbank/backend/biz/model"
)

var DB *gorm.DB

type Config struct {
	Host     string
	Port     int
	User     string
	Password string
	DBName   string
	SSLMode  string
}

// DefaultConfig returns configuration from environment variables
func DefaultConfig() *Config {
	return &Config{
		Host:     getEnv("DB_HOST", "localhost"),
		Port:     getEnvInt("DB_PORT", 5432),
		User:     getEnv("DB_USER", "thinkbank"),
		Password: getEnv("DB_PASSWORD", "thinkbank123"),
		DBName:   getEnv("DB_NAME", "thinkbank"),
		SSLMode:  getEnv("DB_SSL_MODE", "disable"),
	}
}

func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	raw := os.Getenv(key)
	if raw == "" {
		return fallback
	}

	value, err := strconv.Atoi(raw)
	if err != nil || value <= 0 {
		return fallback
	}
	return value
}

func getEnvBool(key string, fallback bool) bool {
	raw := strings.TrimSpace(strings.ToLower(os.Getenv(key)))
	if raw == "" {
		return fallback
	}

	switch raw {
	case "1", "true", "yes", "y", "on":
		return true
	case "0", "false", "no", "n", "off":
		return false
	default:
		return fallback
	}
}

// Init initializes the database connection
func Init(cfg *Config) error {
	if cfg == nil {
		cfg = DefaultConfig()
	}

	dsn := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		cfg.Host, cfg.Port, cfg.User, cfg.Password, cfg.DBName, cfg.SSLMode,
	)

	var err error
	DB, err = gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Warn),
	})
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	sqlDB, err := DB.DB()
	if err != nil {
		return fmt.Errorf("failed to get underlying sql.DB: %w", err)
	}

	// Set connection pool settings
	sqlDB.SetMaxIdleConns(5)
	sqlDB.SetMaxOpenConns(20)

	// Test connection
	if err := sqlDB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	if getEnvBool("DB_AUTO_MIGRATE", true) {
		if err := migrateSchema(DB); err != nil {
			return fmt.Errorf("failed to migrate schema: %w", err)
		}
	} else {
		log.Println("DB_AUTO_MIGRATE is disabled, skipping schema migration")
	}

	log.Println("PostgreSQL connection established successfully")
	return nil
}

func migrateSchema(db *gorm.DB) error {
	statements := []string{
		`CREATE EXTENSION IF NOT EXISTS pgcrypto`,
		`CREATE EXTENSION IF NOT EXISTS vector`,
	}

	for _, stmt := range statements {
		if err := db.Exec(stmt).Error; err != nil {
			return err
		}
	}

	// Keep core tables in sync with model definitions (including deleted_at).
	if err := db.AutoMigrate(&model.Asset{}, &model.ProcessingTask{}); err != nil {
		return err
	}

	// Use raw SQL here to preserve pgvector column types.
	if err := db.Exec(`
		CREATE TABLE IF NOT EXISTS asset_embeddings (
			asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
			semantic_vector vector(1024),
			visual_vector vector(512),
			PRIMARY KEY (asset_id)
		)
	`).Error; err != nil {
		return err
	}

	// Ensure column dimensions match current embedding models.
	if err := db.Exec(`ALTER TABLE asset_embeddings ALTER COLUMN semantic_vector TYPE vector(1024)`).Error; err != nil {
		return err
	}
	if err := db.Exec(`ALTER TABLE asset_embeddings ALTER COLUMN visual_vector TYPE vector(512)`).Error; err != nil {
		log.Printf("warning: failed to alter visual_vector dimension, recreating asset_embeddings: %v", err)
		if err := db.Exec(`DROP TABLE IF EXISTS asset_embeddings`).Error; err != nil {
			return err
		}
		if err := db.Exec(`
			CREATE TABLE asset_embeddings (
				asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
				semantic_vector vector(1024),
				visual_vector vector(512),
				PRIMARY KEY (asset_id)
			)
		`).Error; err != nil {
			return err
		}
	}

	indexStatements := []string{
		`CREATE INDEX IF NOT EXISTS idx_semantic_vector ON asset_embeddings USING ivfflat (semantic_vector vector_cosine_ops) WITH (lists = 100)`,
		`CREATE INDEX IF NOT EXISTS idx_visual_vector ON asset_embeddings USING ivfflat (visual_vector vector_cosine_ops) WITH (lists = 100)`,
	}
	for _, stmt := range indexStatements {
		if err := db.Exec(stmt).Error; err != nil {
			return err
		}
	}

	return nil
}

// Close closes the database connection
func Close() error {
	sqlDB, err := DB.DB()
	if err != nil {
		return err
	}
	return sqlDB.Close()
}

// GetDB returns the database instance
func GetDB() *gorm.DB {
	return DB
}
