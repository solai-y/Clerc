"use client"

import type React from "react"
import { useState, useMemo, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { 
  Tag, 
  Plus, 
  X, 
  CheckCircle, 
  Loader2, 
  Brain, 
  Bot, 
  FileText, 
  Info,
  AlertCircle,
  TrendingUp,
  Eye,
  MessageSquare,
  Settings
} from "lucide-react"
import { Document } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface EnhancedTag {
  tag: string
  confidence: number
  source: 'ai' | 'llm'
  level: 'primary' | 'secondary' | 'tertiary'
  reasoning?: string
  isConfirmed: boolean
}

interface EnhancedConfirmTagsModalProps {
  document: Document
  predictions?: any // Raw prediction response from orchestrator
  explanations?: any[] // Explanation data
  onConfirm: (documentId: string, confirmedTags: string[], userAddedTags: string[]) => Promise<void> | void
  onClose: () => void
}

export function EnhancedConfirmTagsModal({ 
  document, 
  predictions, 
  explanations = [], 
  onConfirm, 
  onClose 
}: EnhancedConfirmTagsModalProps) {
  const { toast } = useToast()

  // Debug logging
  useEffect(() => {
    console.log("🏷️ Enhanced Confirm Tags Modal - explanations:", explanations)
    explanations.forEach((exp, idx) => {
      console.log(`🔍 Explanation ${idx}:`, {
        tag: exp.tag,
        level: exp.level,
        source: exp.source,
        shap_data: exp.shap_data
      })
    })
  }, [explanations])

  // Process prediction data into enhanced tags
  const enhancedTags = useMemo<EnhancedTag[]>(() => {
    const tags: EnhancedTag[] = []
    const processedTags = new Set<string>()

    if (predictions?.prediction) {
      for (const level of ['primary', 'secondary', 'tertiary'] as const) {
        const levelPred = predictions.prediction[level]
        if (levelPred && !processedTags.has(levelPred.pred)) {
          processedTags.add(levelPred.pred)
          tags.push({
            tag: levelPred.pred,
            confidence: levelPred.confidence,
            source: levelPred.source,
            level: level,
            reasoning: levelPred.reasoning,
            isConfirmed: true
          })
        }
      }
    }

    return tags
  }, [predictions])

  const [confirmedTags, setConfirmedTags] = useState<Set<string>>(
    new Set(enhancedTags.map(t => t.tag))
  )
  const [userAddedTags, setUserAddedTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("tags")

  // Reset state when enhancedTags changes
  useEffect(() => {
    setConfirmedTags(new Set(enhancedTags.map(t => t.tag)))
  }, [enhancedTags])

  const addUserTag = () => {
    const trimmedTag = newTag.trim()
    if (trimmedTag && !userAddedTags.includes(trimmedTag) && !confirmedTags.has(trimmedTag)) {
      setUserAddedTags(prev => [...prev, trimmedTag])
      setNewTag("")
    }
  }

  const removeUserTag = (tagToRemove: string) => {
    setUserAddedTags(prev => prev.filter(tag => tag !== tagToRemove))
  }

  const toggleTag = (tag: string) => {
    setConfirmedTags(prev => {
      const next = new Set(prev)
      next.has(tag) ? next.delete(tag) : next.add(tag)
      return next
    })
  }

  const handleConfirm = async () => {
    setIsLoading(true)
    try {
      await onConfirm(document.id, Array.from(confirmedTags), userAddedTags)
      
      toast({
        title: "Success!",
        description: `Document tags have been updated successfully. ${confirmedTags.size + userAddedTags.length} tags applied.`,
        variant: "default",
      })
      
      onClose()
    } catch (error) {
      console.error("Error confirming tags:", error)
      
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

  const aiTags = enhancedTags.filter(t => t.source === 'ai')
  const llmTags = enhancedTags.filter(t => t.source === 'llm')
  const primaryTag = enhancedTags.find(t => t.level === 'primary')
  const secondaryTag = enhancedTags.find(t => t.level === 'secondary')
  const tertiaryTag = enhancedTags.find(t => t.level === 'tertiary')

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="shrink-0 pb-4">
          <DialogTitle className="flex items-center gap-2 text-xl font-semibold">
            <Brain className="w-6 h-6 text-purple-600" />
            Review & Confirm Document Tags
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-4 shrink-0">
            <TabsTrigger value="tags" className="flex items-center gap-2">
              <Tag className="w-4 h-4" />
              Tags
            </TabsTrigger>
            <TabsTrigger value="hierarchy" className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Hierarchy
            </TabsTrigger>
            <TabsTrigger value="explanations" className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Explanations
            </TabsTrigger>
            <TabsTrigger value="document" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Document
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-hidden">
            {/* Tags Tab */}
            <TabsContent value="tags" className="h-full overflow-y-auto space-y-4 mt-4 data-[state=active]:flex data-[state=active]:flex-col">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* AI Generated Tags */}
                <Card className="border-l-4 border-l-blue-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Bot className="w-5 h-5 text-blue-600" />
                      AI Generated Tags
                      <Badge variant="secondary" className="ml-auto">
                        {aiTags.length} tags
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {aiTags.map((tagData, index) => {
                        const isConfirmed = confirmedTags.has(tagData.tag)
                        return (
                          <div key={`ai-${index}`} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                            <div className="flex items-center gap-3 flex-1">
                              <input
                                type="checkbox"
                                checked={isConfirmed}
                                onChange={() => toggleTag(tagData.tag)}
                                className="w-4 h-4"
                              />
                              <div className="flex-1">
                                <div className="font-medium">{tagData.tag}</div>
                                <div className="text-sm text-gray-500">
                                  Level: {tagData.level} • Confidence: {Math.round(tagData.confidence * 100)}%
                                </div>
                              </div>
                            </div>
                            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                              <Bot className="w-3 h-3 mr-1" />
                              AI
                            </Badge>
                          </div>
                        )
                      })}
                      {aiTags.length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p>No AI-generated tags available</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* LLM Generated Tags */}
                <Card className="border-l-4 border-l-purple-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Brain className="w-5 h-5 text-purple-600" />
                      LLM Generated Tags
                      <Badge variant="secondary" className="ml-auto">
                        {llmTags.length} tags
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {llmTags.map((tagData, index) => {
                        const isConfirmed = confirmedTags.has(tagData.tag)
                        return (
                          <div key={`llm-${index}`} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                            <div className="flex items-center gap-3 flex-1">
                              <input
                                type="checkbox"
                                checked={isConfirmed}
                                onChange={() => toggleTag(tagData.tag)}
                                className="w-4 h-4"
                              />
                              <div className="flex-1">
                                <div className="font-medium">{tagData.tag}</div>
                                <div className="text-sm text-gray-500">
                                  Level: {tagData.level} • Confidence: {Math.round(tagData.confidence * 100)}%
                                </div>
                              </div>
                            </div>
                            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                              <Brain className="w-3 h-3 mr-1" />
                              LLM
                            </Badge>
                          </div>
                        )
                      })}
                      {llmTags.length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          <Brain className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p>No LLM-generated tags available</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Custom Tags */}
              <Card className="border-l-4 border-l-green-500">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Plus className="w-5 h-5 text-green-600" />
                    Custom Tags
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {userAddedTags.length > 0 ? (
                      userAddedTags.map((tag, index) => (
                        <Badge
                          key={`custom-${index}`}
                          variant="secondary"
                          className="bg-green-50 text-green-800 border-green-200"
                        >
                          <span>{tag}</span>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="ml-1 h-3 w-3 p-0 hover:bg-green-200"
                            onClick={() => removeUserTag(tag)}
                            disabled={isLoading}
                          >
                            <X className="w-2.5 h-2.5" />
                          </Button>
                        </Badge>
                      ))
                    ) : (
                      <p className="text-gray-500 italic text-sm">No custom tags added</p>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <Input
                      placeholder="Add custom tag..."
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyDown={handleKeyDown}
                      className="flex-1"
                      disabled={isLoading}
                    />
                    <Button
                      onClick={addUserTag}
                      disabled={!newTag.trim() || isLoading}
                      variant="outline"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Hierarchy Tab */}
            <TabsContent value="hierarchy" className="h-full overflow-y-auto space-y-4 mt-4 data-[state=active]:flex data-[state=active]:flex-col">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                    Classification Hierarchy
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Primary Level */}
                    {primaryTag && (
                      <div className="flex items-center gap-4 p-4 border-2 border-blue-200 rounded-lg bg-blue-50">
                        <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm">
                          1
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-lg">{primaryTag.tag}</div>
                          <div className="text-sm text-gray-600">
                            Primary Classification • {Math.round(primaryTag.confidence * 100)}% confidence
                          </div>
                        </div>
                        <Badge className={primaryTag.source === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}>
                          {primaryTag.source === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                          {primaryTag.source.toUpperCase()}
                        </Badge>
                      </div>
                    )}

                    {/* Arrow */}
                    {primaryTag && secondaryTag && (
                      <div className="flex justify-center">
                        <div className="w-0 h-0 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent border-t-gray-400"></div>
                      </div>
                    )}

                    {/* Secondary Level */}
                    {secondaryTag && (
                      <div className="flex items-center gap-4 p-4 border-2 border-green-200 rounded-lg bg-green-50">
                        <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold text-sm">
                          2
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-lg">{secondaryTag.tag}</div>
                          <div className="text-sm text-gray-600">
                            Secondary Classification • {Math.round(secondaryTag.confidence * 100)}% confidence
                          </div>
                        </div>
                        <Badge className={secondaryTag.source === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}>
                          {secondaryTag.source === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                          {secondaryTag.source.toUpperCase()}
                        </Badge>
                      </div>
                    )}

                    {/* Arrow */}
                    {secondaryTag && tertiaryTag && (
                      <div className="flex justify-center">
                        <div className="w-0 h-0 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent border-t-gray-400"></div>
                      </div>
                    )}

                    {/* Tertiary Level */}
                    {tertiaryTag && (
                      <div className="flex items-center gap-4 p-4 border-2 border-orange-200 rounded-lg bg-orange-50">
                        <div className="w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold text-sm">
                          3
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-lg">{tertiaryTag.tag}</div>
                          <div className="text-sm text-gray-600">
                            Tertiary Classification • {Math.round(tertiaryTag.confidence * 100)}% confidence
                          </div>
                        </div>
                        <Badge className={tertiaryTag.source === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}>
                          {tertiaryTag.source === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                          {tertiaryTag.source.toUpperCase()}
                        </Badge>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Explanations Tab */}
            <TabsContent value="explanations" className="h-full flex flex-col mt-4 data-[state=active]:flex">
              {(() => {
                // Filter explanations to show only the correct ones:
                // - If LLM overrode AI for a level, show only LLM explanation
                // - Otherwise show AI explanation with SHAP
                const filteredExplanations = explanations.filter(exp => {
                  // Check if there's an LLM explanation for the same tag and level
                  const hasLLMForSameLevel = explanations.some(other =>
                    other.tag === exp.tag &&
                    other.level === exp.level &&
                    other.source === 'llm'
                  );

                  // If LLM exists for this tag/level, only show LLM explanation
                  if (hasLLMForSameLevel) {
                    return exp.source === 'llm';
                  }

                  // Otherwise show AI explanation
                  return exp.source === 'ai';
                });

                return filteredExplanations.length > 0 ? (
                  <div className="space-y-2 overflow-y-auto flex-1">
                    {filteredExplanations.map((explanation, index) => (
                      <div key={`explanation-${index}`} className="border border-indigo-200 rounded-lg p-3 bg-gradient-to-r from-indigo-50 to-purple-50">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <MessageSquare className="w-4 h-4 text-indigo-600" />
                            <span className="font-semibold text-sm">{explanation.tag}</span>
                            <Badge variant="outline" className="text-xs px-1 py-0">
                              {explanation.level}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className={`text-xs px-2 py-0 ${explanation.source === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}>
                              {explanation.source === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                              {explanation.source.toUpperCase()}
                            </Badge>
                            <div className="text-xs font-medium text-gray-600">
                              {Math.round(explanation.confidence * 100)}%
                            </div>
                          </div>
                        </div>

                        {/* Confidence Bar */}
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                          <div
                            className="bg-indigo-600 h-1.5 rounded-full"
                            style={{ width: `${explanation.confidence * 100}%` }}
                          ></div>
                        </div>

                        {/* Reasoning */}
                        <div className="text-xs leading-normal text-gray-700 bg-white/70 rounded p-2 border max-h-20 overflow-y-auto">
                          {explanation.reasoning}
                        </div>

                        {/* SHAP Explainability for AI predictions */}
                        {explanation.source === 'ai' && explanation.shap_data && (
                            <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                              <div className="text-xs font-semibold text-blue-800 mb-1 flex items-center">
                                <Brain className="w-3 h-3 mr-1" />
                                SHAP Feature Importance
                              </div>
                              <div className="space-y-1">
                                {/* Supporting Evidence */}
                                {explanation.shap_data.supporting?.length > 0 && (
                                  <div>
                                    <div className="text-xs font-medium text-green-700">Supporting:</div>
                                    <div className="flex flex-wrap gap-1">
                                      {explanation.shap_data.supporting.map((item: any, idx: number) => (
                                        <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-green-100 text-green-800 border border-green-300">
                                          <span className="font-mono mr-1">{item.token?.trim() || item}</span>
                                          <span className="text-green-600 font-semibold">{item.impact || ''}</span>
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Opposing Evidence */}
                                {explanation.shap_data.opposing?.length > 0 && (
                                  <div>
                                    <div className="text-xs font-medium text-red-700">Opposing:</div>
                                    <div className="flex flex-wrap gap-1">
                                      {explanation.shap_data.opposing.map((item: any, idx: number) => (
                                        <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-red-100 text-red-800 border border-red-300">
                                          <span className="font-mono mr-1">{item.token?.trim() || item}</span>
                                          <span className="text-red-600 font-semibold">{item.impact || ''}</span>
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500 flex-1 flex flex-col justify-center">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p className="text-base font-medium">No explanations available</p>
                    <p className="text-sm">Explanations will appear here when provided by the AI models</p>
                  </div>
                );
              })()}
            </TabsContent>

            {/* Document Tab */}
            <TabsContent value="document" className="h-full overflow-y-auto space-y-4 mt-4 data-[state=active]:flex data-[state=active]:flex-col">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    Document Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm font-medium text-gray-600">Name</div>
                      <div className="font-medium">{document.name}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-600">Upload Date</div>
                      <div>{document.uploadDate}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-600">File Size</div>
                      <div>{document.size}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-600">Status</div>
                      <div>{document.status}</div>
                    </div>
                  </div>
                  
                  {document.link && (
                    <div className="mt-6">
                      <div className="text-sm font-medium text-gray-600 mb-2">Document Preview</div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(document.link, '_blank')}
                        className="w-full"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        Open Document
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </div>
        </Tabs>

        <Separator className="shrink-0 my-4" />

        <DialogFooter className="shrink-0 flex-row justify-between items-center">
          <div className="text-sm text-gray-600">
            {confirmedTags.size + userAddedTags.length} tag{confirmedTags.size + userAddedTags.length !== 1 ? "s" : ""} will be applied
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
                  Applying...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Confirm Tags
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}