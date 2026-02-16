package handler

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/cloudwego/hertz/pkg/app"
	"github.com/cloudwego/hertz/pkg/protocol/consts"

	"thinkbank/backend/biz/dal/minio"
	"thinkbank/backend/biz/dal/postgres"
	"thinkbank/backend/biz/model"
)

type SearchResult struct {
	ID               string    `json:"id"`
	FileName         string    `json:"file_name"`
	MimeType         string    `json:"mime_type"`
	SizeBytes        int64     `json:"size_bytes"`
	Caption          string    `json:"caption,omitempty"`
	ContentPreview   string    `json:"content_preview,omitempty"`
	ProcessingStatus string    `json:"processing_status"`
	Score            float64   `json:"score"`
	URL              string    `json:"url,omitempty"`
	CreatedAt        time.Time `json:"created_at"`
}

type SearchResponse struct {
	Query   string         `json:"query"`
	Total   int            `json:"total"`
	Results []SearchResult `json:"results"`
}

type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatRequest struct {
	Query   string        `json:"query"`
	History []ChatMessage `json:"history"`
	TopK    int           `json:"top_k"`
}

type ChatResponse struct {
	Answer  string         `json:"answer"`
	Sources []SearchResult `json:"sources"`
}

type llmChatRequest struct {
	Model       string       `json:"model"`
	Messages    []llmChatMsg `json:"messages"`
	Temperature float64      `json:"temperature"`
	MaxTokens   int          `json:"max_tokens"`
	TopP        float64      `json:"top_p"`
	Stream      bool         `json:"stream"`
}

type llmChatMsg struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type llmChatResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

// Search provides hybrid vector + character retrieval over processed assets.
func Search(ctx context.Context, c *app.RequestContext) {
	query := strings.TrimSpace(c.Query("q"))
	limit := parseIntWithDefault(c.Query("limit"), 20)
	threshold := parseFloatWithDefault(c.Query("threshold"), 0.15)

	results, err := retrieveAssetsForQuery(ctx, query, limit, threshold)
	if err != nil {
		c.JSON(consts.StatusInternalServerError, map[string]string{"message": err.Error()})
		return
	}

	c.JSON(consts.StatusOK, SearchResponse{
		Query:   query,
		Total:   len(results),
		Results: results,
	})
}

// Chat performs RAG using hybrid retrieval and external LLM synthesis.
func Chat(ctx context.Context, c *app.RequestContext) {
	var req ChatRequest
	if err := c.BindAndValidate(&req); err != nil {
		c.JSON(consts.StatusBadRequest, map[string]string{"message": "invalid request"})
		return
	}

	req.Query = strings.TrimSpace(req.Query)
	if req.Query == "" {
		c.JSON(consts.StatusBadRequest, map[string]string{"message": "query is required"})
		return
	}

	topK := req.TopK
	if topK <= 0 {
		topK = 5
	}
	if topK > 12 {
		topK = 12
	}

	sources, err := retrieveAssetsForQuery(ctx, req.Query, topK, 0.05)
	if err != nil {
		c.JSON(consts.StatusInternalServerError, map[string]string{"message": err.Error()})
		return
	}

	answer, err := callLLMForRAG(req.Query, req.History, sources)
	if err != nil {
		c.JSON(consts.StatusBadGateway, map[string]string{"message": err.Error()})
		return
	}

	c.JSON(consts.StatusOK, ChatResponse{
		Answer:  answer,
		Sources: sources,
	})
}

func retrieveAssetsForQuery(ctx context.Context, query string, limit int, threshold float64) ([]SearchResult, error) {
	if limit <= 0 {
		limit = 20
	}
	if limit > 100 {
		limit = 100
	}

	var assets []model.Asset
	db := postgres.DB.WithContext(ctx).Where("processing_status = ?", model.StatusCompleted).Order("created_at DESC").Limit(500)
	if err := db.Find(&assets).Error; err != nil {
		return nil, err
	}

	normalizedQuery := normalizeSearchText(query)
	queryRunes := uniqueRunes(normalizedQuery)
	hasQuery := normalizedQuery != ""

	// ---------- Vector search (best-effort) ----------
	vectorScores := make(map[string]float64) // asset_id → cosine similarity
	if hasQuery {
		queryVector := embedQueryText(query)
		if queryVector != nil {
			vectorScores = pgvectorSearch(ctx, queryVector, 100)
		}
	}
	hasVectorScores := len(vectorScores) > 0

	// ---------- Character + Vector hybrid ----------
	results := make([]SearchResult, 0, len(assets))
	for _, asset := range assets {
		fileName := filepath.Base(asset.ObjectName)
		searchText := normalizeSearchText(strings.Join([]string{
			fileName,
			asset.MimeType,
			asset.Caption,
			asset.ContentText,
		}, " "))

		// Character score (0–3 range, normalized to 0–1)
		charScore := 0.0
		if !hasQuery {
			charScore = 0.1
		} else {
			if strings.Contains(searchText, normalizedQuery) {
				charScore += 2.0
			}
			if strings.Contains(normalizeSearchText(asset.Caption), normalizedQuery) {
				charScore += 1.0
			}
			if len(queryRunes) > 0 {
				matchCount := 0
				for _, r := range queryRunes {
					if strings.ContainsRune(searchText, r) {
						matchCount++
					}
				}
				charScore += float64(matchCount) / float64(len(queryRunes))
			}
		}
		charScoreNorm := math.Min(charScore/3.0, 1.0)

		// Vector score (already 0–1 cosine similarity)
		vecScore := vectorScores[asset.ID.String()]

		// Hybrid score
		var finalScore float64
		if hasVectorScores {
			finalScore = 0.7*vecScore + 0.3*charScoreNorm
		} else {
			finalScore = charScoreNorm
		}

		// Recency tie-break
		finalScore += 0.001 * float64(time.Since(asset.CreatedAt).Hours()) * -1.0
		finalScore = math.Round(finalScore*1000) / 1000

		if hasQuery && finalScore < threshold {
			continue
		}

		url := ""
		if signedURL, err := minio.GetFileURL(ctx, asset.BucketName, asset.ObjectName, 3600); err == nil {
			url = signedURL
		}

		results = append(results, SearchResult{
			ID:               asset.ID.String(),
			FileName:         fileName,
			MimeType:         asset.MimeType,
			SizeBytes:        asset.SizeBytes,
			Caption:          asset.Caption,
			ContentPreview:   previewText(asset.ContentText, 240),
			ProcessingStatus: asset.ProcessingStatus,
			Score:            finalScore,
			URL:              url,
			CreatedAt:        asset.CreatedAt,
		})
	}

	sort.Slice(results, func(i, j int) bool {
		if results[i].Score == results[j].Score {
			return results[i].CreatedAt.After(results[j].CreatedAt)
		}
		return results[i].Score > results[j].Score
	})

	if len(results) > limit {
		results = results[:limit]
	}
	return results, nil
}

// embedQueryText calls the python-ai embed HTTP endpoint to get a 1024-dim vector.
func embedQueryText(query string) []float64 {
	embedURL := getEnv("AI_EMBED_URL", "http://127.0.0.1:50052") + "/api/embed"

	payload, _ := json.Marshal(map[string]string{"text": query})
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Post(embedURL, "application/json", bytes.NewReader(payload))
	if err != nil {
		return nil // fail silently, fallback to character search
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil
	}

	var result struct {
		Vector []float64 `json:"vector"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil
	}
	return result.Vector
}

// pgvectorSearch runs a cosine similarity query against asset_embeddings using pgvector.
func pgvectorSearch(ctx context.Context, queryVector []float64, limit int) map[string]float64 {
	scores := make(map[string]float64)

	// Format vector as pgvector-compatible string: [0.1,0.2,...]
	vecParts := make([]string, len(queryVector))
	for i, v := range queryVector {
		vecParts[i] = strconv.FormatFloat(v, 'f', 8, 64)
	}
	vecStr := "[" + strings.Join(vecParts, ",") + "]"

	type vectorResult struct {
		AssetID  string  `gorm:"column:asset_id"`
		Distance float64 `gorm:"column:distance"`
	}

	var results []vectorResult
	err := postgres.DB.WithContext(ctx).Raw(
		`SELECT asset_id::text, (semantic_vector <=> ?::vector) as distance
		 FROM asset_embeddings
		 WHERE semantic_vector IS NOT NULL
		 ORDER BY distance ASC
		 LIMIT ?`,
		vecStr, limit,
	).Scan(&results).Error

	if err != nil {
		return scores
	}

	for _, r := range results {
		// Convert cosine distance to similarity (0–1, higher is better)
		similarity := 1.0 - r.Distance
		if similarity < 0 {
			similarity = 0
		}
		scores[r.AssetID] = similarity
	}
	return scores
}

func callLLMForRAG(query string, history []ChatMessage, sources []SearchResult) (string, error) {
	baseURL := strings.TrimRight(getEnv("LLM_API_URL", "http://127.0.0.1:8000/v1"), "/")
	apiKey := getEnv("LLM_API_KEY", "sk-local")
	modelName := getEnv("LLM_MODEL", "Qwen/Qwen3-VL-8B-Instruct-GPTQ-Int4")

	var contextBuilder strings.Builder
	for idx, src := range sources {
		contextBuilder.WriteString("[" + strconv.Itoa(idx+1) + "] ")
		contextBuilder.WriteString("id=" + src.ID + ", file=" + src.FileName + ", mime=" + src.MimeType + "\n")
		if strings.TrimSpace(src.Caption) != "" {
			contextBuilder.WriteString("caption: " + src.Caption + "\n")
		}
		if strings.TrimSpace(src.ContentPreview) != "" {
			contextBuilder.WriteString("text: " + src.ContentPreview + "\n")
		}
		contextBuilder.WriteString("\n")
	}

	systemPrompt := "You are ThinkBank assistant. Answer based on provided context. If uncertain, say what is missing."
	userPrompt := "User query:\n" + query + "\n\nRetrieved context:\n" + contextBuilder.String()

	messages := []llmChatMsg{{Role: "system", Content: systemPrompt}}
	for _, h := range history {
		role := strings.ToLower(strings.TrimSpace(h.Role))
		if role != "assistant" && role != "system" {
			role = "user"
		}
		content := strings.TrimSpace(h.Content)
		if content == "" {
			continue
		}
		messages = append(messages, llmChatMsg{Role: role, Content: content})
	}
	messages = append(messages, llmChatMsg{Role: "user", Content: userPrompt})

	payload := llmChatRequest{
		Model:       modelName,
		Messages:    messages,
		Temperature: 0.2,
		MaxTokens:   800,
		TopP:        0.9,
		Stream:      false,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequest(http.MethodPost, baseURL+"/chat/completions", bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	client := &http.Client{Timeout: 90 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		errBody := strings.TrimSpace(string(respBody))
		if errBody == "" {
			errBody = http.StatusText(resp.StatusCode)
		}
		return "", fmt.Errorf("llm request failed: status=%d body=%s", resp.StatusCode, errBody)
	}

	var parsed llmChatResponse
	if err := json.Unmarshal(respBody, &parsed); err != nil {
		return "", err
	}
	if len(parsed.Choices) == 0 {
		return "", fmt.Errorf("llm response has no choices")
	}

	answer := strings.TrimSpace(parsed.Choices[0].Message.Content)
	if answer == "" {
		answer = "No response generated."
	}
	return answer, nil
}

func normalizeSearchText(input string) string {
	s := strings.TrimSpace(strings.ToLower(input))
	s = strings.NewReplacer("\n", " ", "\t", " ", "\r", " ").Replace(s)
	return strings.Join(strings.Fields(s), " ")
}

func uniqueRunes(input string) []rune {
	seen := make(map[rune]struct{})
	out := make([]rune, 0, len(input))
	for _, r := range input {
		if r == ' ' {
			continue
		}
		if _, ok := seen[r]; ok {
			continue
		}
		seen[r] = struct{}{}
		out = append(out, r)
	}
	return out
}

func previewText(input string, maxLen int) string {
	input = strings.TrimSpace(input)
	if input == "" || maxLen <= 0 {
		return ""
	}
	runes := []rune(input)
	if len(runes) <= maxLen {
		return input
	}
	return string(runes[:maxLen]) + "..."
}

func parseIntWithDefault(raw string, fallback int) int {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return fallback
	}
	v, err := strconv.Atoi(raw)
	if err != nil {
		return fallback
	}
	return v
}

func parseFloatWithDefault(raw string, fallback float64) float64 {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return fallback
	}
	v, err := strconv.ParseFloat(raw, 64)
	if err != nil {
		return fallback
	}
	return v
}

func getEnv(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}
