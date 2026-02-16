package handler

import (
	"context"
	"io"
	"net/http"
	"net"
	"os"
	"strings"
	"time"

	"github.com/cloudwego/hertz/pkg/app"
	"github.com/cloudwego/hertz/pkg/protocol/consts"
)

type AIHealthResponse struct {
	Available    bool   `json:"available"`
	Host         string `json:"host"`
	Port         string `json:"port"`
	Message      string `json:"message"`
	LLMAvailable bool   `json:"llm_available"`
	LLMURL       string `json:"llm_url"`
	LLMMessage   string `json:"llm_message"`
}

// AIHealth checks whether the external AI gRPC service is reachable.
func AIHealth(ctx context.Context, c *app.RequestContext) {
	host := getEnvOrDefault("AI_SERVICE_HOST", "127.0.0.1")
	port := getEnvOrDefault("AI_SERVICE_PORT", getEnvOrDefault("AI_GRPC_PORT", "50051"))
	address := net.JoinHostPort(host, port)
	llmURL := getEnvOrDefault("LLM_API_URL", "http://127.0.0.1:8000/v1")
	llmAPIKey := getEnvOrDefault("LLM_API_KEY", "sk-local")
	llmOK, llmMsg := checkLLMHealth(llmURL, llmAPIKey)

	conn, err := net.DialTimeout("tcp", address, 1500*time.Millisecond)
	if err != nil {
		c.JSON(consts.StatusOK, AIHealthResponse{
			Available:    false,
			Host:         host,
			Port:         port,
			Message:      "AI service unreachable",
			LLMAvailable: llmOK,
			LLMURL:       llmURL,
			LLMMessage:   llmMsg,
		})
		return
	}
	_ = conn.Close()

	c.JSON(consts.StatusOK, AIHealthResponse{
		Available:    true,
		Host:         host,
		Port:         port,
		Message:      "AI service reachable",
		LLMAvailable: llmOK,
		LLMURL:       llmURL,
		LLMMessage:   llmMsg,
	})
}

func checkLLMHealth(baseURL, apiKey string) (bool, string) {
	url := strings.TrimRight(baseURL, "/") + "/models"

	client := &http.Client{Timeout: 2 * time.Second}
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return false, "invalid LLM URL"
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := client.Do(req)
	if err != nil {
		return false, "LLM endpoint unreachable"
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return true, "LLM endpoint reachable"
	}
	if resp.StatusCode == http.StatusUnauthorized {
		return false, "LLM reachable but API key rejected"
	}
	return false, "LLM endpoint responded with non-2xx"
}

func getEnvOrDefault(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}
