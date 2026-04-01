"use client"

import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

export type ConversionFormat = "original" | "png" | "webp" | "jpg"

export interface ResizeSettings {
  enabled: boolean
  width: number | null
  height: number | null
  keepAspect: boolean
}

export interface ConversionSettingsData {
  format: ConversionFormat
  quality: number
  resize: ResizeSettings
}

interface ConversionSettingsProps {
  settings: ConversionSettingsData
  onChange: (settings: ConversionSettingsData) => void
}

const FORMAT_OPTIONS: { value: ConversionFormat; label: string }[] = [
  { value: "original", label: "Original" },
  { value: "png", label: "PNG" },
  { value: "webp", label: "WebP" },
  { value: "jpg", label: "JPG" },
]

const DEFAULT_QUALITY: Partial<Record<ConversionFormat, number>> = {
  webp: 80,
  jpg: 85,
}

export function ConversionSettings({
  settings,
  onChange,
}: ConversionSettingsProps) {
  const showQuality = settings.format === "webp" || settings.format === "jpg"

  const handleFormatChange = (format: ConversionFormat) => {
    const quality = DEFAULT_QUALITY[format] ?? settings.quality
    onChange({ ...settings, format, quality })
  }

  return (
    <div className="space-y-6">
      {/* Format selector */}
      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">
          Formato de sa\u00edda
        </Label>
        <div className="flex overflow-hidden rounded-md border border-border">
          {FORMAT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleFormatChange(opt.value)}
              className={cn(
                "flex-1 px-3 py-2 text-sm transition-colors",
                settings.format === opt.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-card text-muted-foreground hover:text-foreground"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Quality slider */}
      {showQuality && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-muted-foreground">Qualidade</Label>
            <span className="text-xs tabular-nums text-muted-foreground">
              {settings.quality}
            </span>
          </div>
          <Slider
            value={[settings.quality]}
            onValueChange={(value) => {
              const v = Array.isArray(value) ? value[0] : value
              onChange({ ...settings, quality: v })
            }}
            min={1}
            max={100}
            step={1}
          />
        </div>
      )}

      {/* Resize settings */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Switch
            checked={settings.resize.enabled}
            onCheckedChange={(checked: boolean) =>
              onChange({
                ...settings,
                resize: { ...settings.resize, enabled: checked },
              })
            }
          />
          <Label className="text-xs text-muted-foreground">
            Redimensionamento
          </Label>
        </div>

        {settings.resize.enabled && (
          <div className="space-y-3 pl-1">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">
                  Largura (px)
                </Label>
                <Input
                  type="number"
                  placeholder="Auto"
                  min={1}
                  value={settings.resize.width ?? ""}
                  onChange={(e) => {
                    const width = e.target.value
                      ? parseInt(e.target.value, 10) || null
                      : null
                    onChange({
                      ...settings,
                      resize: { ...settings.resize, width },
                    })
                  }}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">
                  Altura (px)
                </Label>
                <Input
                  type="number"
                  placeholder="Auto"
                  min={1}
                  value={settings.resize.height ?? ""}
                  onChange={(e) => {
                    const height = e.target.value
                      ? parseInt(e.target.value, 10) || null
                      : null
                    onChange({
                      ...settings,
                      resize: { ...settings.resize, height },
                    })
                  }}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                checked={settings.resize.keepAspect}
                onCheckedChange={(checked: boolean) =>
                  onChange({
                    ...settings,
                    resize: { ...settings.resize, keepAspect: checked },
                  })
                }
              />
              <Label className="text-xs text-muted-foreground">
                Manter propor\u00e7\u00e3o
              </Label>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
