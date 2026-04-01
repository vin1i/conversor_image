"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"

interface FileListProps {
  files: File[]
  onRemove: (index: number) => void
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function FilePreview({ file }: { file: File }) {
  const [src, setSrc] = useState<string | null>(null)

  useEffect(() => {
    const url = URL.createObjectURL(file)
    setSrc(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  if (!src) return <div className="size-8 shrink-0 rounded-sm bg-muted" />

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt=""
      className="size-8 shrink-0 rounded-sm object-cover"
    />
  )
}

export function FileList({ files, onRemove }: FileListProps) {
  if (files.length === 0) return null

  return (
    <div className="space-y-1">
      {files.map((file, index) => (
        <div
          key={`${file.name}-${file.size}-${index}`}
          className="flex items-center justify-between rounded-sm bg-card px-3 py-2"
        >
          <div className="flex items-center gap-3 overflow-hidden">
            <FilePreview file={file} />
            <span className="truncate text-sm text-foreground">
              {file.name}
            </span>
            <span className="shrink-0 text-xs text-muted-foreground">
              {formatFileSize(file.size)}
            </span>
          </div>
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => onRemove(index)}
            className="shrink-0"
          >
            <X className="size-3.5" />
          </Button>
        </div>
      ))}
    </div>
  )
}
