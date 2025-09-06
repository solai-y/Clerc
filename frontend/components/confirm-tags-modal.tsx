"use client"

import type React from "react"
import { useState, useMemo, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Tag, Plus, X, CheckCircle, Loader2, Sparkles } from "lucide-react"
import { Document } from "@/lib/api"

interface ConfirmTagsModalProps {
  document: Document
  onConfirm: (documentId: string, confirmedTags: string[], userAddedTags: string[]) => Promise<void> | void
  onClose: () => void
}

export function ConfirmTagsModal({ document, onConfirm, onClose }: ConfirmTagsModalProps) {
  // Defensive fallbacks — avoids undefined access on first render
  const modelGeneratedTags = useMemo(
    () => document.modelGeneratedTags ?? [],
    [document.modelGeneratedTags]
  )
  const initialConfirmed = useMemo(
    () => new Set(modelGeneratedTags.filter(t => t?.isConfirmed).map(t => t.tag)),
    [modelGeneratedTags]
  )
  const initialUserAdded = useMemo(
    () => document.userAddedTags ?? [],
    [document.userAddedTags]
  )

  const [confirmedModelTags, setConfirmedModelTags] = useState<Set<string>>(initialConfirmed)
  const [userAddedTags, setUserAddedTags] = useState<string[]>(initialUserAdded)
  const [newTag, setNewTag] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  // 🔄 Sync local state whenever the `document` prop changes
  useEffect(() => {
    setConfirmedModelTags(new Set(modelGeneratedTags.filter(t => t?.isConfirmed).map(t => t.tag)))
    setUserAddedTags(initialUserAdded)
  }, [modelGeneratedTags, initialUserAdded])

  const addUserTag = () => {
    const trimmedTag = newTag.trim()
    if (trimmedTag && !userAddedTags.includes(trimmedTag) && !confirmedModelTags.has(trimmedTag)) {
      setUserAddedTags(prev => [...prev, trimmedTag])
      setNewTag("")
    }
  }

  const removeUserTag = (tagToRemove: string) => {
    setUserAddedTags(prev => prev.filter(tag => tag !== tagToRemove))
  }

  const toggleModelTag = (tag: string) => {
    setConfirmedModelTags(prev => {
      const next = new Set(prev)
      next.has(tag) ? next.delete(tag) : next.add(tag)
      return next
    })
  }

  const hasChanges = useMemo(() => {
    const originallyConfirmed = new Set(modelGeneratedTags.filter(t => t?.isConfirmed).map(t => t.tag))
    if (confirmedModelTags.size !== originallyConfirmed.size) return true

    for (const tag of confirmedModelTags) {
      if (!originallyConfirmed.has(tag)) return true
    }
    for (const tag of originallyConfirmed) {
      if (!confirmedModelTags.has(tag)) return true
    }

    const originalUser = initialUserAdded
    if (userAddedTags.length !== originalUser.length) return true
    const a = [...userAddedTags].sort()
    const b = [...originalUser].sort()
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return true

    return false
  }, [confirmedModelTags, userAddedTags, modelGeneratedTags, initialUserAdded])

  const handleConfirm = async () => {
    setIsLoading(true)
    try {
      const finalConfirmedTags = hasChanges
        ? Array.from(confirmedModelTags)
        : modelGeneratedTags.map(t => t.tag) // auto-confirm all if no changes

      await onConfirm(document.id, finalConfirmedTags, userAddedTags)
      onClose()
    } catch (error) {
      console.error("Error confirming tags:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") addUserTag()
  }

  const allTags = useMemo(
    () => [...Array.from(confirmedModelTags), ...userAddedTags],
    [confirmedModelTags, userAddedTags]
  )

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent
        className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
        aria-describedby="confirm-tags-desc"
      >
        <DialogHeader className="shrink-0">
          <DialogTitle className="flex items-center gap-2 text-lg">
            <Tag className="w-5 h-5" />
            Edit Tags
          </DialogTitle>
          <DialogDescription id="confirm-tags-desc">
            Review AI-suggested tags, toggle the ones you want, or add your own custom tags.
          </DialogDescription>
          <div className="text-sm text-gray-600 truncate">
            {document.name} • {document.uploadDate} • {document.size}
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <div className="space-y-4 h-full overflow-y-auto pr-2">
            {/* AI Generated Tags */}
            {modelGeneratedTags.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-600" />
                    AI Generated Tags
                    <span className="text-xs font-normal text-gray-500">(Click to toggle)</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-1.5">
                    {modelGeneratedTags.map((tagData, index) => {
                      const tag = tagData?.tag ?? ""
                      const score = Math.round(((tagData?.score ?? 0) as number) * 100)
                      const isConfirmed = confirmedModelTags.has(tag)
                      return (
                        <Badge
                          key={`${tag}-${index}`}
                          variant={isConfirmed ? "default" : "outline"}
                          className={`cursor-pointer transition-all text-xs ${
                            isConfirmed
                              ? "bg-purple-100 text-purple-800 border-purple-300 hover:bg-purple-200"
                              : "border-purple-200 text-purple-700 hover:bg-purple-50"
                          }`}
                          onClick={() => tag && toggleModelTag(tag)}
                        >
                          <span className="flex items-center gap-1">
                            {isConfirmed && <CheckCircle className="w-3 h-3" />}
                            {tag}
                            <span className="text-xs opacity-70">({score}%)</span>
                          </span>
                        </Badge>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* User Added Tags */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Tag className="w-4 h-4 text-blue-600" />
                  Custom Tags
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 space-y-3">
                <div className="flex flex-wrap gap-1.5">
                  {userAddedTags.length > 0 ? (
                    userAddedTags.map((tag, index) => (
                      <Badge
                        key={`${tag}-${index}`}
                        variant="secondary"
                        className="bg-blue-50 text-blue-800 border-blue-200 text-xs"
                      >
                        <span>{tag}</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="ml-1 h-3 w-3 p-0 hover:bg-blue-200"
                          onClick={() => removeUserTag(tag)}
                          disabled={isLoading}
                          aria-label={`Remove ${tag}`}
                        >
                          <X className="w-2.5 h-2.5" />
                        </Button>
                      </Badge>
                    ))
                  ) : (
                    <p className="text-gray-500 italic text-sm">No custom tags</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Add custom tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 h-9"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={addUserTag}
                    size="sm"
                    disabled={!newTag.trim() || isLoading}
                    className="h-9"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator className="shrink-0" />

        <DialogFooter className="shrink-0 flex-row justify-between items-center">
          <div className="text-sm text-gray-600">
            {hasChanges
              ? `${allTags.length} tag${allTags.length !== 1 ? "s" : ""} selected`
              : `Will confirm all ${modelGeneratedTags.length} AI tag${modelGeneratedTags.length !== 1 ? "s" : ""}`}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirm}
              className="bg-red-600 hover:bg-red-700 text-white"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : hasChanges ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Update Tags
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Confirm All & Continue
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
