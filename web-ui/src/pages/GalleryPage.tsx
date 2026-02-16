/**
 * ThinkBank - Gallery Page
 * Bento Grid layout for displaying assets
 */

import { useState, useEffect } from 'react';
import { Image, FileText, File, Trash2, Eye, RefreshCw, Loader2 } from 'lucide-react';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { getAssets, deleteAsset, formatFileSize, type Asset } from '@/lib/api';

const CATEGORIES = ['All', 'Landscape', 'Portrait', 'Document', 'Screenshot', 'Food', 'Animal', 'Graphic Design', 'Other'];

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-yellow-500',
  PROCESSING: 'bg-blue-500',
  COMPLETED: 'bg-green-500',
  FAILED: 'bg-red-500',
};

export function GalleryPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [activeCategory, setActiveCategory] = useState('All');

  const fetchAssets = async (pageNum = 1, append = false, category?: string) => {
    try {
      setLoading(true);
      setError(null);

      const catFilter = category && category !== 'All' ? category : undefined;
      const response = await getAssets(pageNum, 20, undefined, catFilter);

      if (append) {
        setAssets((prev) => [...prev, ...response.assets]);
      } else {
        setAssets(response.assets);
      }

      setTotal(response.total);
      setPage(pageNum);
      setHasMore(response.assets.length === response.per_page);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets(1, false, activeCategory);
  }, [activeCategory]);

  const handleRefresh = () => {
    fetchAssets(1, false, activeCategory);
  };

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      fetchAssets(page + 1, true, activeCategory);
    }
  };

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    setPage(1);
  };

  const handleDelete = async (asset: Asset) => {
    if (!confirm(`Delete "${asset.file_name}"?`)) return;

    try {
      await deleteAsset(asset.id);
      setAssets((prev) => prev.filter((a) => a.id !== asset.id));
      setTotal((prev) => prev - 1);
    } catch (err) {
      alert(`Failed to delete: ${(err as Error).message}`);
    }
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return Image;
    if (mimeType === 'application/pdf') return FileText;
    return File;
  };

  // Bento Grid layout with varied sizes
  const getGridClass = (index: number) => {
    // Every 5th item is larger (featured)
    if (index % 5 === 0) {
      return 'md:col-span-2 md:row-span-2';
    }
    return '';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Gallery</h1>
          <p className="text-muted-foreground">
            {total} {total === 1 ? 'asset' : 'assets'} in your ThinkBank
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <Button
            key={cat}
            variant={activeCategory === cat ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleCategoryChange(cat)}
          >
            {cat}
          </Button>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 p-4 text-destructive">
            <p>Error: {error}</p>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && assets.length === 0 && !error && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-4 rounded-full bg-muted p-4">
              <Image className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="mb-2 text-lg font-medium">No assets yet</h3>
            <p className="text-muted-foreground mb-4">
              Upload some files to get started
            </p>
            <Button asChild>
              <a href="/upload">Upload Files</a>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Bento Grid */}
      {assets.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 auto-rows-[200px]">
          {assets.map((asset, index) => {
            const Icon = getFileIcon(asset.mime_type);
            const isImage = asset.mime_type.startsWith('image/');

            return (
              <Card
                key={asset.id}
                className={`group relative overflow-hidden transition-all hover:shadow-lg ${getGridClass(index)}`}
              >
                {/* Image Preview or Icon */}
                <div
                  className="absolute inset-0 cursor-pointer"
                  onClick={() => setSelectedAsset(asset)}
                >
                  {isImage && asset.url ? (
                    <img
                      src={asset.url}
                      alt={asset.caption || asset.file_name}
                      className="h-full w-full object-cover transition-transform group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-muted to-muted/50">
                      <Icon className="h-12 w-12 text-muted-foreground/50" />
                    </div>
                  )}
                </div>

                {/* Overlay Gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                {/* Status Badge + Category */}
                <div className="absolute top-2 right-2 flex items-center gap-1.5">
                  {asset.category && asset.category !== 'Other' && (
                    <span className="px-1.5 py-0.5 bg-black/50 backdrop-blur-sm text-white text-[10px] font-medium rounded">
                      {asset.category}
                    </span>
                  )}
                  <div
                    className={`h-2.5 w-2.5 rounded-full ${STATUS_COLORS[asset.processing_status]}`}
                    title={asset.processing_status}
                  />
                </div>

                {/* Footer Info */}
                <CardFooter className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {asset.file_name}
                    </p>
                    <p className="text-xs text-white/70">
                      {formatFileSize(asset.size_bytes)}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="secondary"
                      size="icon"
                      className="h-8 w-8"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAsset(asset);
                      }}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="secondary"
                      size="icon"
                      className="h-8 w-8 hover:bg-destructive hover:text-destructive-foreground"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(asset);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

      {/* Load More */}
      {hasMore && assets.length > 0 && (
        <div className="flex justify-center pt-4">
          <Button variant="outline" onClick={handleLoadMore} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              'Load More'
            )}
          </Button>
        </div>
      )}

      {/* Asset Detail Dialog */}
      <Dialog open={!!selectedAsset} onOpenChange={() => setSelectedAsset(null)}>
        <DialogContent className="max-w-3xl">
          {selectedAsset && (
            <>
              <DialogHeader>
                <DialogTitle>{selectedAsset.file_name}</DialogTitle>
                <DialogDescription>
                  {formatFileSize(selectedAsset.size_bytes)} • {selectedAsset.mime_type}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                {/* Preview */}
                {selectedAsset.mime_type.startsWith('image/') && selectedAsset.url && (
                  <img
                    src={selectedAsset.url}
                    alt={selectedAsset.caption || selectedAsset.file_name}
                    className="w-full rounded-lg"
                  />
                )}

                {/* Caption */}
                {selectedAsset.caption && (
                  <div>
                    <h4 className="text-sm font-medium mb-1">AI Caption</h4>
                    <p className="text-sm text-muted-foreground">{selectedAsset.caption}</p>
                  </div>
                )}

                <Separator />

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Status: </span>
                    <span className="font-medium">{selectedAsset.processing_status}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Created: </span>
                    <span className="font-medium">
                      {new Date(selectedAsset.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {selectedAsset.category && (
                    <div>
                      <span className="text-muted-foreground">Category: </span>
                      <span className="font-medium">{selectedAsset.category}</span>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
