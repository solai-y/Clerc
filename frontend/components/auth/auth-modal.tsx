'use client'

import { useState } from 'react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { LoginForm } from './login-form'
import { SignupForm } from './signup-form'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  defaultMode?: 'login' | 'signup'
  redirectTo?: string
}

export function AuthModal({
  isOpen,
  onClose,
  defaultMode = 'login',
  redirectTo = '/'
}: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'signup'>(defaultMode)

  const toggleMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login')
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md p-0 border-0">
        {mode === 'login' ? (
          <LoginForm
            onToggleMode={toggleMode}
            redirectTo={redirectTo}
          />
        ) : (
          <SignupForm onToggleMode={toggleMode} />
        )}
      </DialogContent>
    </Dialog>
  )
}