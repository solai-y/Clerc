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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Tag,
  CheckCircle,
  Loader2,
  Brain,
  Bot,
  FileText,
  TrendingUp,
  Eye,
  MessageSquare,
  ArrowRight,
  AlertCircle,
  RefreshCw
} from "lucide-react"
import { Document, apiClient } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface EnhancedTag {
  tag: string
  confidence: number
  source: 'ai' | 'llm'
  level: 'primary' | 'secondary' | 'tertiary'
  reasoning?: string
  isConfirmed: boolean
}

interface TagHierarchy {
  [primary: string]: {
    [secondary: string]: string[]
  }
}

interface DocumentDetailsModalProps {
  document: Document
  onConfirm: (documentId: string, confirmedTagsData: any) => Promise<void> | void
  onClose: () => void
  // TEMPORARY: Keep explanations prop for SHAP data until orchestrator is fixed
  explanations?: any[]
}

export function DocumentDetailsModal({
  document,
  onConfirm,
  onClose,
  explanations = []
}: DocumentDetailsModalProps) {
  const { toast } = useToast()


  // Load hierarchy from JSON file
  const [hierarchy, setHierarchy] = useState<TagHierarchy>({})
  const [hierarchyLoading, setHierarchyLoading] = useState(true)

  // Database-fetched data
  const [dbPredictions, setDbPredictions] = useState<any>(null)
  const [dbExplanations, setDbExplanations] = useState<any[]>([])
  const [dataLoading, setDataLoading] = useState(true)

  useEffect(() => {
    const loadHierarchy = async () => {
      try {
        const response = await fetch('/hierarchy.json')
        const data = await response.json()
        setHierarchy(data)
      } catch (error) {
        console.error('Failed to load hierarchy:', error)
        toast({
          title: "Warning",
          description: "Failed to load tag hierarchy. Using fallback structure.",
          variant: "destructive",
        })
      } finally {
        setHierarchyLoading(false)
      }
    }
    loadHierarchy()
  }, [toast])

  // Fetch prediction and explanation data from database
  useEffect(() => {
    const fetchDatabaseData = async () => {
      try {
        setDataLoading(true)

        // Fetch complete document details (includes confirmed_tags from processed_documents)
        const documentResponse = await apiClient.getCompleteDocument(parseInt(document.id))

        console.log("🗄️ confirmed_tags field:", documentResponse.confirmed_tags)

        setDbPredictions(documentResponse.confirmed_tags)

        // Fetch explanations from database
        const explanationsResponse = await apiClient.getDocumentExplanations(parseInt(document.id))
        setDbExplanations(explanationsResponse)


      } catch (error) {
        console.error('Failed to fetch database data:', error)
        toast({
          title: "Warning",
          description: "Failed to load prediction data from database. Using props if available.",
          variant: "destructive",
        })
      } finally {
        setDataLoading(false)
      }
    }

    if (document.id) {
      fetchDatabaseData()
    }
  }, [document.id, toast])

  // Process prediction data into enhanced tags (using database data only)
  const enhancedTags = useMemo<EnhancedTag[]>(() => {
    const tags: EnhancedTag[] = []
    const processedTags = new Set<string>()

    // First, process confirmed_tags with JSONB structure (priority for view details)
    if (dbPredictions) {

      // Handle JSONB confirmed_tags structure: {confirmed_tags: {tags: [...]}}
      let confirmedTagsArray = [];

      if (dbPredictions?.confirmed_tags?.tags && Array.isArray(dbPredictions.confirmed_tags.tags)) {
        confirmedTagsArray = dbPredictions.confirmed_tags.tags;
      } else if (Array.isArray(dbPredictions)) {
        // Legacy format - array of tags
        confirmedTagsArray = dbPredictions;
      }

      for (const confirmedTag of confirmedTagsArray) {
        if (confirmedTag.tag && !processedTags.has(confirmedTag.tag)) {
          processedTags.add(confirmedTag.tag)

          tags.push({
            tag: confirmedTag.tag,
            confidence: confirmedTag.confidence || 1.0,
            source: (confirmedTag.source || 'human') as 'ai' | 'llm',
            level: confirmedTag.level as 'primary' | 'secondary' | 'tertiary',
            reasoning: `${(confirmedTag.source || 'human').toUpperCase()} confirmed classification`,
            isConfirmed: true
          })
        }
      }
    }

    // Fallback: if no confirmed tags, use explanations
    if (tags.length === 0 && dbExplanations && dbExplanations.length > 0) {
      for (const explanation of dbExplanations) {
        if (explanation.predicted_tag && explanation.classification_level && !processedTags.has(explanation.predicted_tag)) {
          processedTags.add(explanation.predicted_tag)

          const level = explanation.classification_level as 'primary' | 'secondary' | 'tertiary'
          const confidence = explanation.confidence || 0

          const enhancedTag = {
            tag: explanation.predicted_tag,
            confidence: confidence,
            source: explanation.source_service as 'ai' | 'llm',
            level: level,
            reasoning: explanation.reasoning || `${explanation.source_service?.toUpperCase()} prediction`,
            isConfirmed: false
          }

          tags.push(enhancedTag)
        }
      }
    }

    return tags
  }, [dbPredictions, dbExplanations])

  // State for hierarchy-based selection
  const [selectedPrimary, setSelectedPrimary] = useState<string>("")
  const [selectedSecondary, setSelectedSecondary] = useState<string>("")
  const [selectedTertiary, setSelectedTertiary] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("selection")

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false)

  // Initialize selections with AI/LLM predictions
  useEffect(() => {
    const primaryTag = enhancedTags.find(t => t.level === 'primary')
    const secondaryTag = enhancedTags.find(t => t.level === 'secondary')
    const tertiaryTag = enhancedTags.find(t => t.level === 'tertiary')

    if (primaryTag) setSelectedPrimary(primaryTag.tag)
    if (secondaryTag) setSelectedSecondary(secondaryTag.tag)
    if (tertiaryTag) setSelectedTertiary(tertiaryTag.tag)
  }, [enhancedTags])

  // Get available options based on current selection
  const primaryOptions = useMemo(() => Object.keys(hierarchy), [hierarchy])

  const secondaryOptions = useMemo(() => {
    if (!selectedPrimary || !hierarchy[selectedPrimary]) return []
    return Object.keys(hierarchy[selectedPrimary])
  }, [selectedPrimary, hierarchy])

  const tertiaryOptions = useMemo(() => {
    if (!selectedPrimary || !selectedSecondary || !hierarchy[selectedPrimary]?.[selectedSecondary]) return []
    const tertiaries = hierarchy[selectedPrimary][selectedSecondary]
    return tertiaries.length > 0 ? tertiaries : [selectedSecondary]
  }, [selectedPrimary, selectedSecondary, hierarchy])

  // Handle hierarchy changes
  const handlePrimaryChange = (value: string) => {
    setSelectedPrimary(value)
    setSelectedSecondary("")
    setSelectedTertiary("")
  }

  const handleSecondaryChange = (value: string) => {
    setSelectedSecondary(value)
    setSelectedTertiary("")
  }

  const handleTertiaryChange = (value: string) => {
    setSelectedTertiary(value)
  }

  // Auto-select when only one option is available
  useEffect(() => {
    if (secondaryOptions.length === 1 && !selectedSecondary) {
      setSelectedSecondary(secondaryOptions[0])
    }
  }, [secondaryOptions, selectedSecondary])

  useEffect(() => {
    if (tertiaryOptions.length === 1 && !selectedTertiary) {
      setSelectedTertiary(tertiaryOptions[0])
    }
  }, [tertiaryOptions, selectedTertiary])

  const handleConfirm = async () => {
    if (!selectedPrimary || !selectedSecondary || !selectedTertiary) {
      toast({
        title: "Incomplete Selection",
        description: "Please select primary, secondary, and tertiary tags.",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)
    try {
      // Create the data structure for the backend API
      const confirmedTagsData = {
        confirmed_tags: {
          tags: [
            {
              tag: selectedPrimary,
              source: enhancedTags.find(t => t.level === 'primary')?.source || 'human',
              confidence: enhancedTags.find(t => t.level === 'primary')?.confidence || 1.0,
              confirmed: true,
              added_by: 'user',
              added_at: new Date().toISOString(),
              level: 'primary'
            },
            {
              tag: selectedSecondary,
              source: enhancedTags.find(t => t.level === 'secondary')?.source || 'human',
              confidence: enhancedTags.find(t => t.level === 'secondary')?.confidence || 1.0,
              confirmed: true,
              added_by: 'user',
              added_at: new Date().toISOString(),
              level: 'secondary'
            },
            {
              tag: selectedTertiary,
              source: enhancedTags.find(t => t.level === 'tertiary')?.source || 'human',
              confidence: enhancedTags.find(t => t.level === 'tertiary')?.confidence || 1.0,
              confirmed: true,
              added_by: 'user',
              added_at: new Date().toISOString(),
              level: 'tertiary'
            }
          ]
        }
      }

      await onConfirm(document.id, confirmedTagsData)

      toast({
        title: "Success!",
        description: `Document classification updated: ${selectedPrimary} → ${selectedSecondary} → ${selectedTertiary}`,
        variant: "default",
      })

      onClose()
    } catch (error) {
      console.error("Error confirming tags:", error)

      toast({
        title: "Error",
        description: "Failed to update document classification. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const resetToAIPredictions = () => {
    const primaryTag = enhancedTags.find(t => t.level === 'primary')
    const secondaryTag = enhancedTags.find(t => t.level === 'secondary')
    const tertiaryTag = enhancedTags.find(t => t.level === 'tertiary')

    setSelectedPrimary(primaryTag?.tag || "")
    setSelectedSecondary(secondaryTag?.tag || "")
    setSelectedTertiary(tertiaryTag?.tag || "")
  }

  const primaryTag = enhancedTags.find(t => t.level === 'primary')
  const secondaryTag = enhancedTags.find(t => t.level === 'secondary')
  const tertiaryTag = enhancedTags.find(t => t.level === 'tertiary')

  // Helper function to get the source for displayed tags
  const getTagSource = (selectedTag: string, originalTag: EnhancedTag | undefined) => {
    if (!originalTag) return 'human'; // If no AI/LLM prediction, it's human selected
    if (selectedTag === originalTag.tag) return originalTag.source; // Same as prediction
    return 'human'; // User changed the selection
  }

  if (hierarchyLoading || dataLoading) {
    return (
      <Dialog open onOpenChange={onClose}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Loading Document Classification</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin" />
            <span className="ml-2">
              {hierarchyLoading && dataLoading
                ? "Loading data..."
                : hierarchyLoading
                ? "Loading hierarchy..."
                : "Loading predictions..."}
            </span>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="shrink-0 pb-4 relative">
          <DialogTitle className="flex items-center gap-2 text-xl font-semibold">
            <TrendingUp className="w-6 h-6 text-blue-600" />
            {isEditMode ? "Edit Document Classification" : "View Document Details"}: {document.name}
          </DialogTitle>

          {/* Edit button in header - only show in view mode */}
          {!isEditMode && (
            <Button
              onClick={() => setIsEditMode(true)}
              className="absolute top-0 right-12 h-8 px-3 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium shadow-md border border-amber-600"
              size="sm"
            >
              <TrendingUp className="w-3 h-3 mr-1" />
              Edit
            </Button>
          )}
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-4 shrink-0">
            <TabsTrigger value="selection" className="flex items-center gap-2">
              <Tag className="w-4 h-4" />
              Classification
            </TabsTrigger>
            <TabsTrigger value="hierarchy" className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Current Path
            </TabsTrigger>
            <TabsTrigger value="explanations" className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              AI Reasoning
            </TabsTrigger>
            <TabsTrigger value="document" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Document
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-hidden">
            {/* Classification Selection Tab */}
            <TabsContent value="selection" className="h-full overflow-y-auto mt-4">
              <div className="space-y-6">
                {/* Current Classification Summary */}
                {enhancedTags.length > 0 && (
                  <Card className="border-l-4 border-l-green-500 bg-green-50">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        Current Classification
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={resetToAIPredictions}
                          disabled={!isEditMode}
                          className="ml-auto"
                        >
                          <RefreshCw className="w-4 h-4 mr-1" />
                          Reset to Current
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-2 text-sm">
                        {primaryTag && (
                          <Badge variant="outline" className="bg-blue-100 text-blue-800">
                            {primaryTag.tag}
                          </Badge>
                        )}
                        {primaryTag && secondaryTag && <ArrowRight className="w-4 h-4 text-gray-400" />}
                        {secondaryTag && (
                          <Badge variant="outline" className="bg-green-100 text-green-800">
                            {secondaryTag.tag}
                          </Badge>
                        )}
                        {secondaryTag && tertiaryTag && <ArrowRight className="w-4 h-4 text-gray-400" />}
                        {tertiaryTag && (
                          <Badge variant="outline" className="bg-orange-100 text-orange-800">
                            {tertiaryTag.tag}
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Hierarchy Selection */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Tag className="w-5 h-5 text-blue-600" />
                      Select Classification Path
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Primary Selection */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700">Primary Classification</label>
                      <Select value={selectedPrimary} onValueChange={handlePrimaryChange} disabled={!isEditMode}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select primary classification..." />
                        </SelectTrigger>
                        <SelectContent>
                          {primaryOptions.map((primary) => (
                            <SelectItem key={primary} value={primary}>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="bg-blue-50 text-blue-700">1</Badge>
                                {primary}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Secondary Selection */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700">Secondary Classification</label>
                      <Select
                        value={selectedSecondary}
                        onValueChange={handleSecondaryChange}
                        disabled={!isEditMode || !selectedPrimary}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select secondary classification..." />
                        </SelectTrigger>
                        <SelectContent>
                          {secondaryOptions.map((secondary) => (
                            <SelectItem key={secondary} value={secondary}>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="bg-green-50 text-green-700">2</Badge>
                                {secondary}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Tertiary Selection */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700">Tertiary Classification</label>
                      <Select
                        value={selectedTertiary}
                        onValueChange={handleTertiaryChange}
                        disabled={!isEditMode || !selectedSecondary}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select tertiary classification..." />
                        </SelectTrigger>
                        <SelectContent>
                          {tertiaryOptions.map((tertiary) => (
                            <SelectItem key={tertiary} value={tertiary}>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="bg-orange-50 text-orange-700">3</Badge>
                                {tertiary}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Current Selection Preview */}
                    {selectedPrimary && selectedSecondary && selectedTertiary && (
                      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                        <div className="text-sm font-medium text-gray-600 mb-2">Selected Classification Path:</div>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-blue-100 text-blue-800">{selectedPrimary}</Badge>
                          <ArrowRight className="w-4 h-4 text-gray-400" />
                          <Badge className="bg-green-100 text-green-800">{selectedSecondary}</Badge>
                          <ArrowRight className="w-4 h-4 text-gray-400" />
                          <Badge className="bg-orange-100 text-orange-800">{selectedTertiary}</Badge>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Current Path Tab */}
            <TabsContent value="hierarchy" className="h-full overflow-y-auto mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                    Classification Hierarchy
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Selected Path */}
                    {selectedPrimary && (
                      <div className="flex items-center gap-4 p-4 border-2 border-blue-200 rounded-lg bg-blue-50">
                        <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm">
                          1
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-lg">{selectedPrimary}</div>
                          <div className="text-sm text-gray-600">Primary Classification</div>
                        </div>
                        {(() => {
                          const source = getTagSource(selectedPrimary, primaryTag);
                          return (
                            <Badge className={source === 'ai' ? 'bg-blue-100 text-blue-800' : source === 'llm' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}>
                              {source === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : source === 'llm' ? <Brain className="w-3 h-3 mr-1" /> : <Tag className="w-3 h-3 mr-1" />}
                              {source === 'ai' ? 'AI' : source === 'llm' ? 'LLM' : 'HUMAN'}
                            </Badge>
                          );
                        })()}
                      </div>
                    )}

                    {selectedPrimary && selectedSecondary && (
                      <>
                        <div className="flex justify-center">
                          <div className="w-0 h-0 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent border-t-gray-400"></div>
                        </div>
                        <div className="flex items-center gap-4 p-4 border-2 border-green-200 rounded-lg bg-green-50">
                          <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold text-sm">
                            2
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold text-lg">{selectedSecondary}</div>
                            <div className="text-sm text-gray-600">Secondary Classification</div>
                          </div>
                          {(() => {
                            const source = getTagSource(selectedSecondary, secondaryTag);
                            return (
                              <Badge className={source === 'ai' ? 'bg-blue-100 text-blue-800' : source === 'llm' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}>
                                {source === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : source === 'llm' ? <Brain className="w-3 h-3 mr-1" /> : <Tag className="w-3 h-3 mr-1" />}
                                {source === 'ai' ? 'AI' : source === 'llm' ? 'LLM' : 'HUMAN'}
                              </Badge>
                            );
                          })()}
                        </div>
                      </>
                    )}

                    {selectedSecondary && selectedTertiary && (
                      <>
                        <div className="flex justify-center">
                          <div className="w-0 h-0 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent border-t-gray-400"></div>
                        </div>
                        <div className="flex items-center gap-4 p-4 border-2 border-orange-200 rounded-lg bg-orange-50">
                          <div className="w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold text-sm">
                            3
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold text-lg">{selectedTertiary}</div>
                            <div className="text-sm text-gray-600">Tertiary Classification</div>
                          </div>
                          {(() => {
                            const source = getTagSource(selectedTertiary, tertiaryTag);
                            return (
                              <Badge className={source === 'ai' ? 'bg-blue-100 text-blue-800' : source === 'llm' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}>
                                {source === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : source === 'llm' ? <Brain className="w-3 h-3 mr-1" /> : <Tag className="w-3 h-3 mr-1" />}
                                {source === 'ai' ? 'AI' : source === 'llm' ? 'LLM' : 'HUMAN'}
                              </Badge>
                            );
                          })()}
                        </div>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* AI Reasoning Tab */}
            <TabsContent value="explanations" className="h-full overflow-y-auto mt-4">
              {(() => {
                // Use database explanations if available, fallback to props explanations for SHAP data
                const explanationData = dbExplanations.length > 0 ? dbExplanations : explanations

                // Filter out AI explanations that were overridden by LLM
                const filteredExplanations = explanationData.filter((explanation: any) => {
                  return explanation.reasoning !== "AI model prediction (overridden by LLM)"
                })

                // Enhanced explanations with SHAP data extracted from backend service_response
                const enhancedExplanations = filteredExplanations.map((explanation: any) => {
                  // Extract SHAP data from service_response.shap_explainability (backend data)
                  let shapData = null;

                  if (explanation.service_response?.shap_explainability) {
                    shapData = explanation.service_response.shap_explainability;
                  }


                  return {
                    ...explanation,
                    shap_data: shapData || explanation.shap_data
                  };
                });

                return enhancedExplanations.length > 0 ? (
                  <div className="space-y-2 p-4">
                    {enhancedExplanations.map((explanation: any, index: number) => (
                    <div key={`explanation-${index}`} className="border border-indigo-200 rounded-lg p-3 bg-gradient-to-r from-indigo-50 to-purple-50">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 text-indigo-600" />
                          <span className="font-semibold text-sm">{explanation.predicted_tag || explanation.tag}</span>
                          <Badge variant="outline" className="text-xs px-1 py-0">
                            {explanation.classification_level || explanation.level}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={`text-xs px-2 py-0 ${(explanation.source_service || explanation.source) === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}>
                            {(explanation.source_service || explanation.source) === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                            {(explanation.source_service || explanation.source)?.toUpperCase()}
                          </Badge>
                          <div className="text-xs font-medium text-gray-600">
                            {Math.round((explanation.confidence || 0) * 100)}%
                          </div>
                        </div>
                      </div>
                      <div className="text-xs leading-normal text-gray-700 bg-white/70 rounded p-2 border max-h-20 overflow-y-auto">
                        {explanation.reasoning}
                      </div>

                      {/* SHAP Explainability for AI predictions (enhanced with props data) */}
                      {(explanation.source_service || explanation.source) === 'ai' && explanation.shap_data && (
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
                  <div className="text-center py-12 text-gray-500 p-4">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p className="text-base font-medium">No explanations available</p>
                    <p className="text-sm">AI reasoning will appear here when available</p>
                  </div>
                );
              })()}
            </TabsContent>

            {/* Document Tab */}
            <TabsContent value="document" className="h-full overflow-y-auto mt-4">
              <div className="space-y-6 p-4">
                {/* Document Header */}
                <div className="text-center border-b pb-4">
                  <h3 className="text-xl font-bold text-gray-800 mb-2">{document.name}</h3>
                  <p className="text-sm text-gray-600">Document ID: {document.id}</p>
                </div>

                {/* Document Details */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-800 mb-3 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    Document Details
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Upload Date:</span>
                      <span className="font-medium">{document.uploadDate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">File Size:</span>
                      <span className="font-medium">{document.size}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Document Type:</span>
                      <span className="font-medium">{document.type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        document.status === 'processed' ? 'bg-green-100 text-green-800' :
                        document.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                        document.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {document.status}
                      </span>
                    </div>
                    {document.companyName && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Company:</span>
                        <span className="font-medium">{document.companyName}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Open Document Button */}
                {document.link ? (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                    <h4 className="font-semibold text-purple-800 mb-3 flex items-center justify-center">
                      <Eye className="w-4 h-4 mr-2" />
                      View Full Document
                    </h4>
                    <p className="text-sm text-gray-600 mb-4">
                      Open the original document in a new tab to view the full content.
                    </p>
                    <Button
                      onClick={() => window.open(document.link, '_blank')}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Open Document
                    </Button>
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
                    <p className="text-sm text-gray-500">No document link available</p>
                  </div>
                )}

                {/* Tags Section */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-semibold text-green-800 mb-3 flex items-center">
                    <Tag className="w-4 h-4 mr-2" />
                    Document Tags ({document.tags?.length || 0})
                  </h4>
                  {document.tags && document.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {document.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium border border-green-300"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 italic">No tags assigned to this document</p>
                  )}
                </div>
              </div>
            </TabsContent>
          </div>
        </Tabs>

        <Separator className="shrink-0 my-4" />

        <DialogFooter className="shrink-0 flex-row justify-between items-center">
          {isEditMode ? (
            <>
              <div className="text-sm text-gray-600">
                {selectedPrimary && selectedSecondary && selectedTertiary ? (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    Ready to update classification
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    Please complete all three levels
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setIsEditMode(false)} disabled={isLoading}>
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirm}
                  disabled={isLoading || !selectedPrimary || !selectedSecondary || !selectedTertiary}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-blue-600" />
                  View mode - Click Edit button in header to make changes
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={onClose}>
                  Close
                </Button>
              </div>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}