import { useEffect, useState } from 'react';
import { File, FileText, Image, Search, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  getAIHealth,
  getAssets,
  searchAssets,
  formatFileSize,
  type AIHealth,
  type Asset,
} from '@/lib/api';

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [assets, setAssets] = useState<Asset[]>([]);
  const [searchResults, setSearchResults] = useState<Asset[]>([]);
  const [aiHealth, setAIHealth] = useState<AIHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async (withLoading = false, keyword = '') => {
      try {
        if (withLoading) {
          setLoading(true);
        }
        setError(null);

        const trimmed = keyword.trim();
        const [healthResponse] = await Promise.all([getAIHealth().catch(() => null)]);

        if (cancelled) {
          return;
        }

        setAIHealth(healthResponse);
        if (trimmed) {
          const searchResp = await searchAssets(trimmed, 100, 0.05);
          if (cancelled) {
            return;
          }
          // Reuse Asset shape for rendering.
          setSearchResults(
            searchResp.results.map((item) => ({
              id: item.id,
              file_name: item.file_name,
              mime_type: item.mime_type,
              size_bytes: item.size_bytes,
              caption: item.caption,
              processing_status: item.processing_status,
              url: item.url,
              metadata: { score: item.score, content_preview: item.content_preview },
              created_at: item.created_at,
            }))
          );
        } else {
          const assetResponse = await getAssets(1, 100);
          if (cancelled) {
            return;
          }
          setAssets(assetResponse.assets);
          setSearchResults([]);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      } finally {
        if (withLoading && !cancelled) {
          setLoading(false);
        }
      }
    };

    void load(true, query);
    const timer = window.setInterval(() => {
      void load(false, query);
    }, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [query]);

  const filteredAssets = query.trim() ? searchResults : assets;

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return Image;
    if (mimeType === 'application/pdf') return FileText;
    return File;
  };

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Search</h1>
        <p className="text-muted-foreground">
          Find files by name, caption, or type. AI status is shown below.
        </p>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9"
              placeholder="Search by filename, caption, mime type..."
            />
          </div>
        </CardContent>
      </Card>

      <Card className={aiHealth?.available ? 'border-green-500/40' : 'border-yellow-500/40'}>
        <CardContent className="p-4 text-sm">
          {aiHealth?.available ? (
            <div className="space-y-1">
              <p>AI service is online ({aiHealth.host}:{aiHealth.port}).</p>
              {aiHealth.llm_available ? (
                <p>LLM service is online ({aiHealth.llm_url}).</p>
              ) : (
                <p className="text-yellow-700">LLM service is offline ({aiHealth.llm_message ?? 'unknown'}).</p>
              )}
            </div>
          ) : (
            <div className="space-y-1">
              <p>AI service is offline. Local file search still works; LLM features are unavailable.</p>
              {aiHealth?.llm_available === false && (
                <p className="text-yellow-700">LLM service is offline ({aiHealth.llm_message ?? 'unknown'}).</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {loading && (
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <Loader2 className="h-4 w-4 animate-spin" />
            <p>Loading assets...</p>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4 text-sm text-destructive">Error: {error}</CardContent>
        </Card>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filteredAssets.map((asset) => {
            const Icon = getFileIcon(asset.mime_type);
            const isImage = asset.mime_type.startsWith('image/');

            return (
              <Card key={asset.id} className="overflow-hidden">
                <CardContent className="p-0">
                  <div className="h-40 w-full bg-muted">
                    {isImage && asset.url ? (
                      <img src={asset.url} alt={asset.file_name} className="h-full w-full object-cover" />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <Icon className="h-10 w-10 text-muted-foreground/60" />
                      </div>
                    )}
                  </div>
                  <div className="space-y-1 p-3">
                    <p className="truncate text-sm font-medium">{asset.file_name}</p>
                    {asset.caption && <p className="line-clamp-2 text-xs text-muted-foreground">{asset.caption}</p>}
                    <p className="text-xs text-muted-foreground">{formatFileSize(asset.size_bytes)}</p>
                    <p className="text-xs text-muted-foreground">{asset.processing_status}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {!loading && !error && filteredAssets.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="p-8 text-center text-sm text-muted-foreground">
            No matching assets.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
