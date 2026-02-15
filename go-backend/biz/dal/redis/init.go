// Package redis provides Redis client for task queue
package redis

import (
	"context"
	"fmt"
	"os"
	"strconv"

	"github.com/redis/go-redis/v9"
)

var Client *redis.Client
var queueName string

type Config struct {
	Host      string
	Port      int
	DB        int
	QueueName string
}

// DefaultConfig returns configuration from environment variables
func DefaultConfig() *Config {
	return &Config{
		Host:      getEnv("REDIS_HOST", "localhost"),
		Port:      getEnvInt("REDIS_PORT", 6379),
		DB:        0,
		QueueName: getEnv("REDIS_QUEUE_NAME", "thinkbank:tasks"),
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

// Init initializes the Redis client
func Init(cfg *Config) error {
	if cfg == nil {
		cfg = DefaultConfig()
	}

	queueName = cfg.QueueName

	Client = redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
		DB:   cfg.DB,
	})

	ctx := context.Background()
	if err := Client.Ping(ctx).Err(); err != nil {
		return fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return nil
}

// Close closes the Redis connection
func Close() error {
	if Client != nil {
		return Client.Close()
	}
	return nil
}

// PushTask pushes an asset ID to the processing queue
func PushTask(ctx context.Context, assetID string) error {
	return Client.LPush(ctx, getQueueName(), assetID).Err()
}

// PopTask pops an asset ID from the processing queue (blocking)
func PopTask(ctx context.Context) (string, error) {
	result, err := Client.BRPop(ctx, 0, getQueueName()).Result()
	if err != nil {
		return "", err
	}
	if len(result) < 2 {
		return "", fmt.Errorf("no task received")
	}
	return result[1], nil
}

// GetClient returns the Redis client
func GetClient() *redis.Client {
	return Client
}

func getQueueName() string {
	if queueName == "" {
		queueName = DefaultConfig().QueueName
	}
	return queueName
}
