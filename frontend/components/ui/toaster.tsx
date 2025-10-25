"use client"

import { useToast } from "@/hooks/use-toast"
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"

/**
 * High z-index toaster pinned to the top-right of the viewport.
 * - Default 5s duration if caller doesn't specify one
 * - Sits above any overlays (modals, drawers, etc.)
 */
export function Toaster() {
  const { toasts } = useToast()

  return (
    <ToastProvider swipeDirection="right">
      {toasts.map(function ({ id, title, description, action, duration, ...props }) {
        return (
          <Toast key={id} {...props} duration={duration ?? 5000}>
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && <ToastDescription>{description}</ToastDescription>}
            </div>
            {action}
            <ToastClose />
          </Toast>
        )
      })}

      {/* Position + stacking context */}
      <ToastViewport
        className="
          fixed top-4 right-4 z-[2147483647]
          flex max-h-screen w-full flex-col gap-2 p-4
          md:max-w-[420px]
        "
      />
    </ToastProvider>
  )
}

/* Export default too so either `import { Toaster }` or `import Toaster` works */
export default Toaster
