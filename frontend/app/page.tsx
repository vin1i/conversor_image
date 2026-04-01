"use client"

import { useState, useCallback } from "react"
import { DropZone } from "@/components/DropZone"
import { FileList } from "@/components/FileList"
import {
  ConversionSettings,
  type ConversionSettingsData,
} from "@/components/ConversionSettings"
import { ConvertButton } from "@/components/ConvertButton"
import { Footer } from "@/components/Footer"
import { processImage } from "@/lib/imageProcessor"
import { downloadAsZip } from "@/lib/zipper"

type AppStatus = "idle" | "processing" | "done" | "error"

interface ProcessingResult {
  filename: string
  blob: Blob
  error?: string
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function Home() {
  const [files, setFiles] = useState<File[]>([])
  const [settings, setSettings] = useState<ConversionSettingsData>({
    format: "original",
    quality: 80,
    resize: {
      enabled: false,
      width: null,
      height: null,
      keepAspect: true,
    },
  })
  const [status, setStatus] = useState<AppStatus>("idle")
  const [progress, setProgress] = useState({ current: 0, total: 0 })
  const [results, setResults] = useState<ProcessingResult[]>([])

  const handleFilesAdded = useCallback((newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles])
    setStatus("idle")
    setResults([])
  }, [])

  const handleRemoveFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleConvert = async () => {
    if (files.length === 0) return

    setStatus("processing")
    setProgress({ current: 0, total: files.length })
    const processed: ProcessingResult[] = []

    for (let i = 0; i < files.length; i++) {
      setProgress({ current: i + 1, total: files.length })
      try {
        const result = await processImage(files[i], {
          format: settings.format,
          quality: settings.quality / 100,
          resize: settings.resize,
        })
        processed.push(result)
      } catch {
        processed.push({
          filename: files[i].name,
          blob: new Blob(),
          error: `N\u00e3o foi poss\u00edvel processar ${files[i].name}`,
        })
      }
    }

    setResults(processed)

    const successful = processed.filter((r) => !r.error)

    if (successful.length === 1) {
      downloadBlob(successful[0].blob, successful[0].filename)
    } else if (successful.length > 1) {
      await downloadAsZip(successful)
    }

    const hasErrors = processed.some((r) => r.error)
    setStatus(hasErrors ? "error" : "done")
  }

  const handleReset = () => {
    setFiles([])
    setResults([])
    setStatus("idle")
    setProgress({ current: 0, total: 0 })
  }

  return (
    <div className="mx-auto flex w-full max-w-[720px] flex-1 flex-col px-4 py-8">
      <header className="mb-8">
        <h1 className="text-lg font-light text-foreground">Image Converter</h1>
      </header>

      <main className="flex flex-1 flex-col gap-6">
        <DropZone
          onFilesAdded={handleFilesAdded}
          disabled={status === "processing"}
        />

        <FileList files={files} onRemove={handleRemoveFile} />

        {files.length > 0 && (
          <>
            <ConversionSettings settings={settings} onChange={setSettings} />
            <ConvertButton
              disabled={files.length === 0}
              processing={status === "processing"}
              progress={progress}
              onClick={handleConvert}
            />
          </>
        )}

        {status === "done" && (
          <div className="space-y-2 text-center">
            <p className="text-sm text-foreground">Download pronto</p>
            <button
              onClick={handleReset}
              className="text-sm text-muted-foreground underline-offset-4 hover:underline"
            >
              Converter mais arquivos
            </button>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-2">
            {results
              .filter((r) => r.error)
              .map((r, i) => (
                <p key={i} className="text-sm text-destructive">
                  {r.error}
                </p>
              ))}
            <div className="text-center">
              <button
                onClick={handleReset}
                className="text-sm text-muted-foreground underline-offset-4 hover:underline"
              >
                Tentar novamente
              </button>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}
