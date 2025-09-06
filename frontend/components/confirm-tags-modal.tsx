"use client"

import type React from "react"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, Tag, Plus, X, CheckCircle, Loader2, Sparkles } from "lucide-react"
import { Document } from "@/lib/api"

interface ConfirmTagsModalProps {
  document: Document
  onConfirm: (documentId: string, confirmedTags: string[], userAddedTags: string[]) => void
  onClose: () => void
}

export function ConfirmTagsModal({ document, onConfirm, onClose }: ConfirmTagsModalProps) {
  const [confirmedModelTags, setConfirmedModelTags] = useState<Set<string>>(
    new Set(document.modelGeneratedTags.filter(tag => tag.isConfirmed).map(tag => tag.tag))
  )
  const [userAddedTags, setUserAddedTags] = useState<string[]>(document.userAddedTags)
  const [newTag, setNewTag] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const addUserTag = () => {
    const trimmedTag = newTag.trim()
    if (trimmedTag && !userAddedTags.includes(trimmedTag) && !confirmedModelTags.has(trimmedTag)) {
      setUserAddedTags([...userAddedTags, trimmedTag])
      setNewTag("")
    }
  }

  const removeUserTag = (tagToRemove: string) => {
    setUserAddedTags(userAddedTags.filter((tag) => tag !== tagToRemove))
  }

  const toggleModelTag = (tag: string) => {
    const newConfirmedTags = new Set(confirmedModelTags)
    if (newConfirmedTags.has(tag)) {
      newConfirmedTags.delete(tag)
    } else {
      newConfirmedTags.add(tag)
    }
    setConfirmedModelTags(newConfirmedTags)
  }

  const handleConfirm = async () => {
    setIsLoading(true)
    try {
      // If no changes were made, auto-confirm all suggested tags
      const finalConfirmedTags = hasChanges 
        ? Array.from(confirmedModelTags)
        : document.modelGeneratedTags.map(tag => tag.tag) // Auto-confirm all suggested tags
      
      await onConfirm(document.id, finalConfirmedTags, userAddedTags)
      onClose()
    } catch (error) {
      console.error('Error confirming tags:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      addUserTag()
    }
  }

  const allTags = [...Array.from(confirmedModelTags), ...userAddedTags]
  const hasChanges = 
    confirmedModelTags.size !== document.modelGeneratedTags.filter(tag => tag.isConfirmed).length ||
    userAddedTags.length !== document.userAddedTags.length ||
    !Array.from(confirmedModelTags).every(tag => 
      document.modelGeneratedTags.some(mTag => mTag.tag === tag && mTag.isConfirmed)
    ) ||
    !userAddedTags.every(tag => document.userAddedTags.includes(tag))

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="shrink-0">
          <DialogTitle className="flex items-center gap-2 text-lg">
            <Tag className="w-5 h-5" />
            Edit Tags
          </DialogTitle>
          <div className="text-sm text-gray-600 truncate">
            {document.name} • {document.uploadDate} • {document.size}
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <div className="space-y-4 h-full overflow-y-auto pr-2">

            {/* AI Generated Tags */}
            {document.modelGeneratedTags.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-600" />
                    AI Generated Tags
                    <span className="text-xs font-normal text-gray-500">
                      (Click to toggle)
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-1.5">
                    {document.modelGeneratedTags.map((tagData, index) => {
                      const isConfirmed = confirmedModelTags.has(tagData.tag)
                      return (
                        <Badge
                          key={index}
                          variant={isConfirmed ? "default" : "outline"}
                          className={`cursor-pointer transition-all text-xs ${
                            isConfirmed
                              ? "bg-purple-100 text-purple-800 border-purple-300 hover:bg-purple-200"
                              : "border-purple-200 text-purple-700 hover:bg-purple-50"
                          }`}
                          onClick={() => toggleModelTag(tagData.tag)}
                        >
                          <span className="flex items-center gap-1">
                            {isConfirmed && <CheckCircle className="w-3 h-3" />}
                            {tagData.tag}
                            <span className="text-xs opacity-70">
                              ({Math.round(tagData.score * 100)}%)
                            </span>
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
                  {userAddedTags.map((tag, index) => (
                    <Badge
                      key={index}
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
                      >
                        <X className="w-2.5 h-2.5" />
                      </Button>
                    </Badge>
                  ))}
                  {userAddedTags.length === 0 && (
                    <p className="text-gray-500 italic text-sm">No custom tags</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Add custom tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={handleKeyPress}
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
            {hasChanges ? (
              `${allTags.length} tag${allTags.length !== 1 ? 's' : ''} selected`
            ) : (
              `Will confirm all ${document.modelGeneratedTags.length} AI tag${document.modelGeneratedTags.length !== 1 ? 's' : ''}`
            )}
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