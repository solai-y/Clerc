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
import { Tag, Plus, X, CheckCircle, Loader2, Brain, Eye, EyeOff, FileText } from "lucide-react"
import { Document } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface ConfirmTagsModalProps {
  document: Document
  onConfirm: (documentId: string, confirmedTags: string[], userAddedTags: string[]) => Promise<void> | void
  onClose: () => void
}

export function ConfirmTagsModal({ document, onConfirm, onClose }: ConfirmTagsModalProps) {
  const { toast } = useToast()
  const modelGeneratedTags = useMemo(
    () => document.modelGeneratedTags ?? [],
    [document.modelGeneratedTags]
  )
  const initialConfirmed = useMemo(
    () => new Set(modelGeneratedTags.map(t => t.tag)),
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
  const [showDocumentPreview, setShowDocumentPreview] = useState(false)

  useEffect(() => {
    setConfirmedModelTags(new Set(modelGeneratedTags.map(t => t.tag)))
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
    const originallyConfirmed = new Set(modelGeneratedTags.map(t => t.tag))
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
        : modelGeneratedTags.map(t => t.tag)

      await onConfirm(document.id, finalConfirmedTags, userAddedTags)
      
      // Show success notification
      toast({
        title: "Success!",
        description: `Document tags have been updated successfully. ${finalConfirmedTags.length + userAddedTags.length} tags applied.`,
        variant: "default",
      })
      
      onClose()
    } catch (error) {
      console.error("Error confirming tags:", error)
      
      // Show error notification
      toast({
        title: "Error",
        description: "Failed to update document tags. Please try again.",
        variant: "destructive",
      })
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
      <DialogContent className="max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
        <DialogHeader className="shrink-0 pb-4">
          <DialogTitle className="flex items-center gap-2 text-xl font-semibold">
            <Brain className="w-6 h-6 text-purple-600" />
            Edit Document Tags
          </DialogTitle>
          <DialogDescription>
            Review and edit AI/LLM-generated tags, or add your own custom tags to organize this document.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Document Information */}
            <div className="space-y-4">
              <Card className="border-l-4 border-l-blue-500">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <FileText className="w-5 h-5 text-blue-600" />
                    Document Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Name</label>
                    <p className="text-sm font-medium">{document.name}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Upload Date</label>
                      <p className="text-sm">{document.uploadDate}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">File Size</label>
                      <p className="text-sm">{document.size}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-l-4 border-l-purple-500">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <FileText className="w-5 h-5 text-purple-600" />
                    Document Preview
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label className="text-sm font-medium text-gray-600">View Document</label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowDocumentPreview(!showDocumentPreview)}
                        className="h-7 px-2"
                      >
                        {showDocumentPreview ? (
                          <>
                            <EyeOff className="w-3 h-3 mr-1" />
                            Hide Preview
                          </>
                        ) : (
                          <>
                            <Eye className="w-3 h-3 mr-1" />
                            Show Preview
                          </>
                        )}
                      </Button>
                    </div>
                    
                    {showDocumentPreview && (
                      <div className="bg-gray-50 rounded-lg p-3 min-h-64 max-h-96 border">
                        {document.link ? (
                          <iframe
                            src={document.link}
                            className="w-full h-64 rounded border-0"
                            title={`Preview of ${document.name}`}
                            onError={() => console.error('Failed to load document preview')}
                          />
                        ) : (
                          <div className="flex items-center justify-center h-64 text-gray-500">
                            <div className="text-center">
                              <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                              <p className="text-sm">Document preview not available</p>
                              <p className="text-xs">No link provided for this document</p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {document.link && (
                      <div className="mt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(document.link, '_blank')}
                          className="w-full"
                        >
                          <FileText className="w-4 h-4 mr-2" />
                          Open in New Tab
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column - Tag Management */}
            <div className="space-y-4">
              {modelGeneratedTags.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Brain className="w-5 h-5 text-purple-600" />
                      AI/LLM Suggested Tags
                      <span className="text-xs font-normal text-gray-500 ml-auto">(Click to toggle)</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {modelGeneratedTags.map((tagData, index) => {
                        const tag = tagData?.tag ?? ""
                        const score = Math.round(((tagData?.score ?? 0) as number) * 100)
                        const isConfirmed = confirmedModelTags.has(tag)
                        return (
                          <Badge
                            key={`${tag}-${index}`}
                            variant={isConfirmed ? "default" : "outline"}
                            className={`cursor-pointer transition-all ${
                              isConfirmed
                                ? "bg-purple-100 text-purple-800 border-purple-300 hover:bg-purple-200"
                                : "border-purple-200 text-purple-700 hover:bg-purple-50"
                            }`}
                            onClick={() => tag && toggleModelTag(tag)}
                          >
                            <div className="flex items-center gap-1">
                              {isConfirmed && <CheckCircle className="w-3 h-3" />}
                              <span>{tag}</span>
                              <span className="text-xs opacity-70">({score}%)</span>
                            </div>
                          </Badge>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Tag className="w-5 h-5 text-blue-600" />
                    Custom Tags
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {userAddedTags.length > 0 ? (
                      userAddedTags.map((tag, index) => (
                        <Badge
                          key={`${tag}-${index}`}
                          variant="secondary"
                          className="bg-blue-50 text-blue-800 border-blue-200"
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
                      <p className="text-gray-500 italic text-sm">No custom tags added</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Add New Tag</label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Enter tag name..."
                        value={newTag}
                        onChange={(e) => setNewTag(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="flex-1"
                        disabled={isLoading}
                      />
                      <Button
                        onClick={addUserTag}
                        disabled={!newTag.trim() || isLoading}
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Tag Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>AI Confirmed Tags:</span>
                      <span className="font-medium">{confirmedModelTags.size}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Custom Tags:</span>
                      <span className="font-medium">{userAddedTags.length}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between font-medium">
                      <span>Total Tags:</span>
                      <span>{allTags.length}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        <Separator className="shrink-0 my-4" />

        <DialogFooter className="shrink-0 flex-row justify-between items-center">
          <div className="text-sm text-gray-600">
            {hasChanges
              ? `${allTags.length} tag${allTags.length !== 1 ? "s" : ""} will be applied`
              : `Will confirm all ${modelGeneratedTags.length} suggested tag${modelGeneratedTags.length !== 1 ? "s" : ""}`}
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={isLoading}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Applying Changes...
                </>
              ) : hasChanges ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Apply Changes
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Confirm All Tags
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
