# Error Codes Reference

This document defines all error codes used in the ThinkBank API.

## Error Response Format

All API errors follow a consistent JSON structure:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error description",
  "details": {}  // Optional additional information
}
```

## HTTP Status Codes

| Status | Meaning | When Used |
|--------|---------|-----------|
| `200` | OK | Request succeeded |
| `400` | Bad Request | Invalid input, file type, or size |
| `404` | Not Found | Resource does not exist |
| `500` | Internal Server Error | Server-side error (DB, storage, etc.) |
| `503` | Service Unavailable | AI service not reachable |

---

## Error Codes by Category

### File Upload Errors

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `FILE_UPLOAD_ERROR` | 400 | No file provided in request | Ensure `multipart/form-data` with `file` field |
| `FILE_TOO_LARGE` | 400 | File exceeds 100MB limit | Compress file or split into smaller parts |
| `INVALID_FILE_TYPE` | 400 | MIME type not supported | Use supported types: JPEG, PNG, GIF, WebP, PDF, TXT, JSON, MD |

### Asset Errors

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `ASSET_NOT_FOUND` | 404 | Asset with given ID does not exist | Verify the asset ID is correct |
| `ASSET_DELETED` | 404 | Asset has been soft-deleted | Asset cannot be recovered |

### Processing Errors

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `PROCESSING_FAILED` | 500 | AI processing pipeline failed | Check logs, may retry processing |
| `EMBEDDING_FAILED` | 500 | Vector embedding generation failed | AI service may be overloaded |

### Infrastructure Errors

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `DB_ERROR` | 500 | Database operation failed | Check PostgreSQL status |
| `MINIO_ERROR` | 500 | Object storage operation failed | Check MinIO status |
| `REDIS_ERROR` | 500 | Redis queue operation failed | Check Redis status |
| `AI_SERVICE_UNAVAILABLE` | 503 | AI gRPC service not reachable | Check Python AI service status |

---

## Error Examples

### File Too Large

```json
// POST /api/v1/assets/upload
// HTTP 400
{
  "code": "FILE_TOO_LARGE",
  "message": "File size exceeds maximum allowed size of 100MB",
  "details": {
    "max_size_bytes": 104857600,
    "actual_size_bytes": 157286400
  }
}
```

### Invalid File Type

```json
// POST /api/v1/assets/upload
// HTTP 400
{
  "code": "INVALID_FILE_TYPE",
  "message": "File type 'video/mp4' is not supported",
  "details": {
    "content_type": "video/mp4",
    "supported_types": [
      "image/jpeg",
      "image/png",
      "image/gif",
      "image/webp",
      "application/pdf",
      "text/plain",
      "application/json",
      "text/markdown"
    ]
  }
}
```

### Asset Not Found

```json
// GET /api/v1/assets/invalid-uuid
// HTTP 404
{
  "code": "ASSET_NOT_FOUND",
  "message": "The requested asset was not found",
  "details": {
    "asset_id": "invalid-uuid"
  }
}
```

### AI Service Unavailable

```json
// GET /api/v1/ai/health
// HTTP 503
{
  "code": "AI_SERVICE_UNAVAILABLE",
  "message": "AI processing service is not available",
  "details": {
    "error": "grpc connection refused: localhost:50051"
  }
}
```

---

## Handling Errors in Client Code

### JavaScript/TypeScript Example

```typescript
async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/v1/assets/upload', {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    switch (data.code) {
      case 'FILE_TOO_LARGE':
        alert('File is too large. Maximum size is 100MB.');
        break;
      case 'INVALID_FILE_TYPE':
        alert('This file type is not supported.');
        break;
      default:
        alert(`Upload failed: ${data.message}`);
    }
    throw new Error(data.code);
  }

  return data; // { asset_id, message }
}
```

### Go Example

```go
func handleAPIError(err error, resp *http.Response) {
    var apiErr struct {
        Code    string `json:"code"`
        Message string `json:"message"`
    }
    json.NewDecoder(resp.Body).Decode(&apiErr)

    switch apiErr.Code {
    case "ASSET_NOT_FOUND":
        log.Printf("Asset not found: %s", apiErr.Message)
    case "FILE_TOO_LARGE":
        log.Printf("File too large: %s", apiErr.Message)
    default:
        log.Printf("API error [%s]: %s", apiErr.Code, apiErr.Message)
    }
}
```

---

## Processing Status Values

While not errors per se, processing statuses indicate the state of asset processing:

| Status | Description |
|--------|-------------|
| `PENDING` | Asset uploaded, waiting in queue |
| `PROCESSING` | AI pipeline actively processing |
| `COMPLETED` | All processing finished successfully |
| `FAILED` | Processing encountered an error |

When status is `FAILED`, check the `processing_tasks` table for error details.
