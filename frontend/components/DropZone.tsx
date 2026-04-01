"use client"

import { useCallback, useRef, useState } from "react"
import { cn } from "@/lib/utils"

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"]
const ACCEPTED_EXTENSIONS = ".jpg,.jpeg,.png,.webp"

interface DropZoneProps {
  onFilesAdded: (files: File[]) => void
  disabled?: boolean
}

export function DropZone({ onFilesAdded, disabled = false }: DropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const filterValidFiles = (fileList: FileList): File[] => {
    return Array.from(fileList).filter((file) =>
      ACCEPTED_TYPES.includes(file.type)
    )
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      if (disabled) return
      const files = filterValidFiles(e.dataTransfer.files)
      if (files.length > 0) onFilesAdded(files)
    },
    [disabled, onFilesAdded]
  )

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      if (!disabled) setIsDragOver(true)
    },
    [disabled]
  )

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false)
  }, [])

  const handleClick = () => {
    if (!disabled) inputRef.current?.click()
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = filterValidFiles(e.target.files)
      if (files.length > 0) onFilesAdded(files)
    }
    e.target.value = ""
  }

  return (
    <div
      onClick={handleClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={cn(
        "relative flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-border bg-card px-6 py-10 transition-colors",
        isDragOver && !disabled && "border-ring bg-accent/5",
        disabled && "cursor-not-allowed opacity-50"
      )}
    >
      <p className="text-sm text-muted-foreground">
        Arraste imagens aqui ou clique para selecionar
      </p>
      <p className="mt-1 text-xs text-muted-foreground/60">JPG, PNG, WebP</p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        multiple
        onChange={handleInputChange}
        className="hidden"
        disabled={disabled}
      />
    </div>
  )
}
