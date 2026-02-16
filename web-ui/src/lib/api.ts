/**
 * ThinkBank API Client
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export interface Asset {
  id: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  caption?: string;
  processing_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  url?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface AssetListResponse {
  assets: Asset[];
  total: number;
  page: number;
  per_page: number;
}

export interface UploadResponse {
  asset_id: string;
  message: string;
}

export interface AIHealth {
  available: boolean;
  host: string;
  port: string;
  message: string;
  llm_available?: boolean;
  llm_url?: string;
  llm_message?: string;
}

export interface SearchResultItem {
  id: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  caption?: string;
  content_preview?: string;
  processing_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  score: number;
  url?: string;
  created_at: string;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResultItem[];
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  answer: string;
  sources: SearchResultItem[];
}

/**
 * Upload a file to the server
 */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/api/v1/assets/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Upload failed' }));
    throw new Error(error.message || 'Upload failed');
  }

  return response.json();
}

/**
 * Get list of assets
 */
export async function getAssets(page = 1, perPage = 20, status?: string): Promise<AssetListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });

  if (status) {
    params.append('status', status);
  }

  const response = await fetch(`${API_BASE}/api/v1/assets?${params}`);

  if (!response.ok) {
    throw new Error('Failed to fetch assets');
  }

  return response.json();
}

/**
 * Get a single asset
 */
export async function getAsset(id: string): Promise<Asset> {
  const response = await fetch(`${API_BASE}/api/v1/assets/${id}`);

  if (!response.ok) {
    throw new Error('Failed to fetch asset');
  }

  return response.json();
}

/**
 * Check AI service availability
 */
export async function getAIHealth(): Promise<AIHealth> {
  const response = await fetch(`${API_BASE}/api/v1/ai/health`);

  if (!response.ok) {
    throw new Error('Failed to check AI service');
  }

  return response.json();
}

export async function searchAssets(query: string, limit = 20, threshold = 0.15): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
    threshold: String(threshold),
  });

  const response = await fetch(`${API_BASE}/api/v1/search?${params}`);
  if (!response.ok) {
    throw new Error('Failed to search assets');
  }
  return response.json();
}

export async function chatWithAssets(query: string, history: ChatMessage[] = [], topK = 5): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history, top_k: topK }),
  });

  if (!response.ok) {
    throw new Error('Failed to chat with assets');
  }
  return response.json();
}

/**
 * Delete an asset
 */
export async function deleteAsset(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/assets/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete asset');
  }
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

/**
 * Get file icon based on mime type
 */
export function getFileIcon(mimeType: string): string {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType === 'application/pdf') return 'pdf';
  if (mimeType.startsWith('text/')) return 'text';
  return 'file';
}
