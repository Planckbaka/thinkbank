/**
 * ThinkBank - Upload Page
 * Drag & drop file upload with Bento Grid style
 */

import { useState, useCallback } from 'react';
import { Upload, File, Image, FileText, X, CheckCircle2, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { uploadFile, formatFileSize } from '@/lib/api';

interface UploadingFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  assetId?: string;
}

const ACCEPTED_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'application/pdf',
  'text/plain',
  'text/markdown',
];

export function UploadPage() {
  const [files, setFiles] = useState<UploadingFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files));
    }
  }, []);

  const addFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter((file) =>
      ACCEPTED_TYPES.includes(file.type) || file.type.startsWith('image/')
    );

    const uploadingFiles: UploadingFile[] = validFiles.map((file) => ({
      file,
      progress: 0,
      status: 'pending' as const,
    }));

    setFiles((prev) => [...prev, ...uploadingFiles]);

    // Start uploading each file
    uploadingFiles.forEach((uf) => uploadSingleFile(uf.file));
  };

  const uploadSingleFile = async (file: File) => {
    // Update status to uploading
    setFiles((prev) =>
      prev.map((f) =>
        f.file === file ? { ...f, status: 'uploading', progress: 25 } : f
      )
    );

    try {
      const result = await uploadFile(file);

      setFiles((prev) =>
        prev.map((f) =>
          f.file === file
            ? { ...f, status: 'success', progress: 100, assetId: result.asset_id }
            : f
        )
      );
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          f.file === file
            ? { ...f, status: 'error', error: (error as Error).message }
            : f
        )
      );
    }
  };

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return Image;
    if (type === 'application/pdf') return FileText;
    return File;
  };

  const pendingCount = files.filter((f) => f.status === 'pending' || f.status === 'uploading').length;
  const successCount = files.filter((f) => f.status === 'success').length;

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Upload Files</h1>
        <p className="text-muted-foreground">
          Drag and drop files or click to browse. Supports images, PDFs, and text files.
        </p>
      </div>

      {/* Drop Zone - Bento Grid Item 1 */}
      <Card
        className={`mx-auto w-full border-2 border-dashed transition-colors cursor-pointer ${
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <input
            type="file"
            multiple
            accept={ACCEPTED_TYPES.join(',')}
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="flex w-full cursor-pointer flex-col items-center justify-center text-center">
            <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
              <Upload className="h-8 w-8 text-primary" />
            </div>
            <p className="mb-2 text-lg font-medium">
              {isDragging ? 'Drop files here' : 'Drag files here or click to upload'}
            </p>
            <p className="text-sm text-muted-foreground">
              Images (JPG, PNG, GIF, WebP), PDFs, and text files up to 100MB
            </p>
          </label>
        </CardContent>
      </Card>

      {/* File Queue - Bento Grid Item 2 */}
      {files.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium">Upload Queue</h2>
            <p className="text-sm text-muted-foreground">
              {successCount} of {files.length} uploaded
              {pendingCount > 0 && ` (${pendingCount} in progress)`}
            </p>
          </div>

          <div className="grid gap-3">
            {files.map((uf, index) => {
              const Icon = getFileIcon(uf.file.type);

              return (
                <Card key={index} className="overflow-hidden">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="flex-shrink-0">
                      {uf.file.type.startsWith('image/') ? (
                        <img
                          src={URL.createObjectURL(uf.file)}
                          alt={uf.file.name}
                          className="h-12 w-12 rounded-lg object-cover"
                        />
                      ) : (
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
                          <Icon className="h-6 w-6 text-muted-foreground" />
                        </div>
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{uf.file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(uf.file.size)}
                      </p>

                      {/* Progress Bar */}
                      {uf.status === 'uploading' && (
                        <div className="mt-2 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${uf.progress}%` }}
                          />
                        </div>
                      )}

                      {uf.status === 'error' && (
                        <p className="mt-1 text-sm text-destructive">{uf.error}</p>
                      )}
                    </div>

                    <div className="flex-shrink-0">
                      {uf.status === 'uploading' && (
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      )}
                      {uf.status === 'success' && (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      )}
                      {(uf.status === 'pending' || uf.status === 'error') && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeFile(uf.file)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
