import JSZip from "jszip"

export async function downloadAsZip(
  files: { blob: Blob; filename: string }[]
): Promise<void> {
  const zip = new JSZip()

  for (const file of files) {
    zip.file(file.filename, file.blob)
  }

  const zipBlob = await zip.generateAsync({ type: "blob" })

  const url = URL.createObjectURL(zipBlob)
  const a = document.createElement("a")
  a.href = url
  a.download = "imagens-convertidas.zip"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
