/**
 * ThinkBank - Documents Page
 * Browse and manage document assets (PDFs, text files, etc.)
 */

import { useState, useEffect } from 'react';
import { FileText, File, Trash2, Eye, RefreshCw, Loader2, Download } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { getAssets, deleteAsset, formatFileSize, type Asset } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
    PENDING: 'bg-yellow-500',
    PROCESSING: 'bg-blue-500',
    COMPLETED: 'bg-green-500',
    FAILED: 'bg-red-500',
};

export function DocumentsPage() {
    const [assets, setAssets] = useState<Asset[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [hasMore, setHasMore] = useState(true);

    const fetchDocuments = async (pageNum = 1, append = false) => {
        try {
            setLoading(true);
            setError(null);

            // Fetch all assets and filter for non-image types on the client side
            // The backend filters by category, but we also want documents detected by mime_type
            const response = await getAssets(pageNum, 50);

            const docs = response.assets.filter(
                (a) =>
                    !a.mime_type.startsWith('image/') ||
                    a.category === 'Document' ||
                    a.category === 'Screenshot'
            );

            if (append) {
                setAssets((prev) => [...prev, ...docs]);
            } else {
                setAssets(docs);
            }

            setTotal(docs.length);
            setPage(pageNum);
            setHasMore(response.assets.length === response.per_page);
        } catch (err) {
            setError((err as Error).message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments(1);
    }, []);

    const handleRefresh = () => {
        fetchDocuments(1);
    };

    const handleLoadMore = () => {
        if (!loading && hasMore) {
            fetchDocuments(page + 1, true);
        }
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

    const getDocIcon = (mimeType: string) => {
        if (mimeType === 'application/pdf') return FileText;
        return File;
    };

    const getMimeLabel = (mimeType: string) => {
        if (mimeType === 'application/pdf') return 'PDF';
        if (mimeType === 'text/plain') return 'TXT';
        if (mimeType === 'text/markdown') return 'MD';
        if (mimeType === 'application/json') return 'JSON';
        return mimeType.split('/')[1]?.toUpperCase() || 'FILE';
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
                    <p className="text-muted-foreground">
                        {total} {total === 1 ? 'document' : 'documents'} in your ThinkBank
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
                            <FileText className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="mb-2 text-lg font-medium">No documents yet</h3>
                        <p className="text-muted-foreground mb-4">
                            Upload PDF, text, or markdown files to get started
                        </p>
                        <Button asChild>
                            <a href="/upload">Upload Files</a>
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Document List */}
            {assets.length > 0 && (
                <div className="space-y-3">
                    {assets.map((asset) => {
                        const Icon = getDocIcon(asset.mime_type);

                        return (
                            <Card
                                key={asset.id}
                                className="group hover:shadow-md transition-shadow cursor-pointer"
                                onClick={() => setSelectedAsset(asset)}
                            >
                                <CardContent className="flex items-center gap-4 p-4">
                                    {/* Icon */}
                                    <div className="flex-shrink-0 h-12 w-12 rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-500/10 flex items-center justify-center">
                                        <Icon className="h-6 w-6 text-blue-600" />
                                    </div>

                                    {/* Info */}
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium truncate">{asset.file_name}</p>
                                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                                            <span className="px-1.5 py-0.5 bg-muted rounded text-xs font-mono">
                                                {getMimeLabel(asset.mime_type)}
                                            </span>
                                            <span>{formatFileSize(asset.size_bytes)}</span>
                                            {asset.category && (
                                                <span className="px-1.5 py-0.5 bg-primary/10 text-primary rounded text-xs">
                                                    {asset.category}
                                                </span>
                                            )}
                                            <span>{new Date(asset.created_at).toLocaleDateString()}</span>
                                        </div>
                                        {asset.caption && (
                                            <p className="text-sm text-muted-foreground mt-1 truncate">
                                                {asset.caption}
                                            </p>
                                        )}
                                    </div>

                                    {/* Status */}
                                    <div className="flex items-center gap-2">
                                        <div
                                            className={`h-2.5 w-2.5 rounded-full ${STATUS_COLORS[asset.processing_status]}`}
                                            title={asset.processing_status}
                                        />
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-8 w-8"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedAsset(asset);
                                            }}
                                        >
                                            <Eye className="h-4 w-4" />
                                        </Button>
                                        {asset.url && (
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    window.open(asset.url, '_blank');
                                                }}
                                            >
                                                <Download className="h-4 w-4" />
                                            </Button>
                                        )}
                                        <Button
                                            variant="ghost"
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
                                </CardContent>
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

            {/* Document Detail Dialog */}
            <Dialog open={!!selectedAsset} onOpenChange={() => setSelectedAsset(null)}>
                <DialogContent className="max-w-3xl">
                    {selectedAsset && (
                        <>
                            <DialogHeader>
                                <DialogTitle>{selectedAsset.file_name}</DialogTitle>
                                <DialogDescription>
                                    {formatFileSize(selectedAsset.size_bytes)} • {selectedAsset.mime_type}
                                    {selectedAsset.category && ` • ${selectedAsset.category}`}
                                </DialogDescription>
                            </DialogHeader>

                            <div className="space-y-4">
                                {/* Caption / Summary */}
                                {selectedAsset.caption && (
                                    <div>
                                        <h4 className="text-sm font-medium mb-1">AI Summary</h4>
                                        <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                            {selectedAsset.caption}
                                        </p>
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

                                {/* Download Button */}
                                {selectedAsset.url && (
                                    <Button asChild variant="outline" className="w-full">
                                        <a href={selectedAsset.url} target="_blank" rel="noreferrer">
                                            <Download className="h-4 w-4 mr-2" />
                                            Download File
                                        </a>
                                    </Button>
                                )}
                            </div>
                        </>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
