// Package minio provides MinIO client for object storage
package minio

import (
	"context"
	"fmt"
	"io"
	"mime/multipart"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

var Client *minio.Client
var defaultBucket = "thinkbank-assets"

type Config struct {
	Endpoint string
	User     string
	Password string
	Bucket   string
	Secure   bool
}

// DefaultConfig returns configuration from environment variables
func DefaultConfig() *Config {
	return &Config{
		Endpoint: getEnv("MINIO_ENDPOINT", "localhost:9000"),
		User:     getEnv("MINIO_USER", "minioadmin"),
		Password: getEnv("MINIO_PASSWORD", "minioadmin123"),
		Bucket:   getEnv("MINIO_BUCKET", "thinkbank-assets"),
		Secure:   false,
	}
}

func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

// Init initializes the MinIO client
func Init(cfg *Config) error {
	if cfg == nil {
		cfg = DefaultConfig()
	}
	defaultBucket = cfg.Bucket

	var err error
	Client, err = minio.New(cfg.Endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.User, cfg.Password, ""),
		Secure: cfg.Secure,
	})
	if err != nil {
		return fmt.Errorf("failed to create MinIO client: %w", err)
	}

	ctx := context.Background()

	// Check if bucket exists, create if not
	exists, err := Client.BucketExists(ctx, cfg.Bucket)
	if err != nil {
		return fmt.Errorf("failed to check bucket existence: %w", err)
	}

	if !exists {
		if err := Client.MakeBucket(ctx, cfg.Bucket, minio.MakeBucketOptions{}); err != nil {
			return fmt.Errorf("failed to create bucket: %w", err)
		}
		// Set public read policy for thumbnails (optional)
		policy := `{
			"Version": "2012-10-17",
			"Statement": [
				{
					"Effect": "Allow",
					"Principal": {"AWS": ["*"]},
					"Action": ["s3:GetObject"],
					"Resource": ["arn:aws:s3:::` + cfg.Bucket + `/thumbnails/*"]
				}
			]
		}`
		if err := Client.SetBucketPolicy(ctx, cfg.Bucket, policy); err != nil {
			// Log warning but don't fail
			fmt.Printf("Warning: failed to set bucket policy: %v\n", err)
		}
	}

	return nil
}

// UploadFile uploads a file to MinIO
func UploadFile(ctx context.Context, bucket, objectName string, file *multipart.FileHeader) (string, error) {
	src, err := file.Open()
	if err != nil {
		return "", fmt.Errorf("failed to open file: %w", err)
	}
	defer src.Close()

	// Generate object path with extension
	ext := filepath.Ext(file.Filename)
	objectPath := objectName
	if filepath.Ext(objectName) == "" {
		if ext == "" {
			ext = ".bin"
		}
		objectPath = fmt.Sprintf("%s%s", objectName, ext)
	}

	_, err = Client.PutObject(ctx, bucket, objectPath, src, file.Size, minio.PutObjectOptions{
		ContentType: file.Header.Get("Content-Type"),
	})
	if err != nil {
		return "", fmt.Errorf("failed to upload file: %w", err)
	}

	return objectPath, nil
}

// UploadFromReader uploads data from an io.Reader
func UploadFromReader(ctx context.Context, bucket, objectName string, reader io.Reader, size int64, contentType string) error {
	_, err := Client.PutObject(ctx, bucket, objectName, reader, size, minio.PutObjectOptions{
		ContentType: contentType,
	})
	return err
}

// DownloadFile downloads a file from MinIO
func DownloadFile(ctx context.Context, bucket, objectName string) (*minio.Object, error) {
	return Client.GetObject(ctx, bucket, objectName, minio.GetObjectOptions{})
}

// GetFileURL returns a presigned URL for file access
func GetFileURL(ctx context.Context, bucket, objectName string, expirySeconds int) (string, error) {
	url, err := Client.PresignedGetObject(ctx, bucket, objectName, time.Duration(expirySeconds)*time.Second, nil)
	if err != nil {
		return "", err
	}
	return url.String(), nil
}

// DeleteFile deletes a file from MinIO
func DeleteFile(ctx context.Context, bucket, objectName string) error {
	return Client.RemoveObject(ctx, bucket, objectName, minio.RemoveObjectOptions{})
}

// GetClient returns the MinIO client
func GetClient() *minio.Client {
	return Client
}

// GetBucket returns the default bucket name
func GetBucket() string {
	if strings.TrimSpace(defaultBucket) == "" {
		defaultBucket = DefaultConfig().Bucket
	}
	return defaultBucket
}
