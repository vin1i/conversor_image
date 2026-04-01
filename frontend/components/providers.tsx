"use client"

import { CSPProvider } from "@base-ui/react/csp-provider"

export function Providers({ children }: { children: React.ReactNode }) {
  return <CSPProvider nonce="">{children}</CSPProvider>
}
