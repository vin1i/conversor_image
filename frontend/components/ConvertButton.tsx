"use client"

import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

interface ConvertButtonProps {
  disabled: boolean
  processing: boolean
  progress: { current: number; total: number }
  onClick: () => void
}

export function ConvertButton({
  disabled,
  processing,
  progress,
  onClick,
}: ConvertButtonProps) {
  return (
    <div className="space-y-3">
      <Button
        className="h-11 w-full text-sm"
        disabled={disabled || processing}
        onClick={onClick}
      >
        {processing
          ? `Convertendo ${progress.current} de ${progress.total}...`
          : "Converter"}
      </Button>
      {processing && progress.total > 0 && (
        <Progress value={(progress.current / progress.total) * 100} />
      )}
    </div>
  )
}
