"use client"

import type React from "react"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Tag, Plus, X } from "lucide-react"
import { Document } from "@/lib/api"

interface ConfirmTagsModalProps {
  document: Document
  onConfirm: (documentId: string, tags: string[]) => void
  onClose: () => void
}

export function ConfirmTagsModal({ document, onConfirm, onClose }: ConfirmTagsModalProps) {
  const [tags, setTags] = useState<string[]>(document.tags)
  const [newTag, setNewTag] = useState("")

  const addTag = () => {
    const trimmedTag = newTag.trim()
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag])
      setNewTag("")
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove))
  }

  const handleConfirm = () => {
    onConfirm(document.id, tags)
    onClose()
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      addTag()
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Confirm Tags for {document.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Document Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Document Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Name:</span> {document.name}
                </div>
                <div>
                  <span className="font-medium">Upload Date:</span> {document.uploadDate}
                </div>
                <div>
                  <span className="font-medium">Size:</span> {document.size}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Current Tags */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Tag className="w-5 h-5" />
                Current Tags
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="bg-red-50 text-red-700 hover:bg-red-100"
                    >
                      <span>{tag}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="ml-1 h-4 w-4 p-0 hover:bg-red-200"
                        onClick={() => removeTag(tag)}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </Badge>
                  ))}
                  {tags.length === 0 && (
                    <p className="text-gray-500 italic">No tags assigned</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Add new tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="flex-1"
                  />
                  <Button onClick={addTag} size="sm">
                    <Plus className="w-4 h-4 mr-1" />
                    Add Tag
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            Confirm Tags
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}