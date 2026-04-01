export interface ProcessImageOptions {
  format: "original" | "png" | "webp" | "jpg"
  quality: number
  resize: {
    enabled: boolean
    width: number | null
    height: number | null
    keepAspect: boolean
  }
}

export interface ProcessImageResult {
  blob: Blob
  filename: string
}

const MIME_MAP: Record<string, string> = {
  png: "image/png",
  webp: "image/webp",
  jpg: "image/jpeg",
}

const EXT_MAP: Record<string, string> = {
  png: ".png",
  webp: ".webp",
  jpg: ".jpg",
}

function getOutputMimeType(format: string, originalType: string): string {
  if (format === "original") return originalType
  return MIME_MAP[format] || originalType
}

function getOutputFilename(format: string, originalName: string): string {
  if (format === "original") return originalName
  const baseName = originalName.replace(/\.[^.]+$/, "")
  return baseName + (EXT_MAP[format] || "")
}

function calculateDimensions(
  srcW: number,
  srcH: number,
  targetW: number | null,
  targetH: number | null,
  keepAspect: boolean
): { width: number; height: number } {
  if (!targetW && !targetH) return { width: srcW, height: srcH }

  if (keepAspect) {
    if (targetW && !targetH) {
      return { width: targetW, height: Math.round((targetW / srcW) * srcH) }
    }
    if (!targetW && targetH) {
      return { width: Math.round((targetH / srcH) * srcW), height: targetH }
    }
    if (targetW && targetH) {
      const ratio = Math.min(targetW / srcW, targetH / srcH)
      return {
        width: Math.round(srcW * ratio),
        height: Math.round(srcH * ratio),
      }
    }
  }

  return {
    width: targetW || srcW,
    height: targetH || srcH,
  }
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error("Failed to load image"))
    img.src = src
  })
}

export async function processImage(
  file: File,
  options: ProcessImageOptions
): Promise<ProcessImageResult> {
  const url = URL.createObjectURL(file)

  try {
    const img = await loadImage(url)

    let width = img.naturalWidth
    let height = img.naturalHeight

    if (options.resize.enabled) {
      const dims = calculateDimensions(
        width,
        height,
        options.resize.width,
        options.resize.height,
        options.resize.keepAspect
      )
      width = dims.width
      height = dims.height
    }

    const canvas = document.createElement("canvas")
    canvas.width = width
    canvas.height = height

    const ctx = canvas.getContext("2d")!
    ctx.drawImage(img, 0, 0, width, height)

    const mimeType = getOutputMimeType(options.format, file.type)
    const quality = mimeType === "image/png" ? undefined : options.quality

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (b) => {
          if (b) resolve(b)
          else reject(new Error("Failed to create blob"))
        },
        mimeType,
        quality
      )
    })

    const filename = getOutputFilename(options.format, file.name)

    return { blob, filename }
  } finally {
    URL.revokeObjectURL(url)
  }
}
