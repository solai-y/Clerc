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
import { Select, SelectContent, SelectItem, SelectTrigger } from "@/components/ui/select"
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
  AlertCircle,
  RefreshCw,
  X,
  Plus
} from "lucide-react"
import { Document, apiClient } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface EnhancedTag {
  tag: string
  confidence: number
  source: 'ai' | 'llm' | 'human'
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

  // Stabilize explanations prop to prevent infinite re-renders
  const [propsExplanations] = useState(explanations)

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

        console.log("🗄️ Database - predictions:", documentResponse.confirmed_tags)
        console.log("🗄️ Database - explanations:", explanationsResponse)

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

  // Process prediction data into enhanced tags (from database OR props)
  const enhancedTags = useMemo<EnhancedTag[]>(() => {
    const tags: EnhancedTag[] = []
    const processedTags = new Set<string>()

    // Determine which explanations to use: database or props
    const explanationsToUse = dbExplanations.length > 0 ? dbExplanations : propsExplanations

    // First, process explanations to get the correct hierarchy levels and sources
    if (explanationsToUse && explanationsToUse.length > 0) {
      console.log("📊 Processing explanations for hierarchy:", explanationsToUse)

      for (const explanation of explanationsToUse) {
        // Handle both database format (predicted_tag, classification_level)
        // and props format (tag, level)
        const tagName = (explanation as any).predicted_tag || (explanation as any).tag
        const tagLevel = (explanation as any).classification_level || (explanation as any).level
        const tagSource = (explanation as any).source_service || (explanation as any).source
        const tagConfidence = explanation.confidence || 0

        console.log("🔍 Processing explanation:", {
          tagName,
          tagLevel,
          tagSource,
          tagConfidence
        })

        if (tagName && tagLevel && !processedTags.has(tagName)) {
          processedTags.add(tagName)

          // Use the actual classification level
          const level = tagLevel as 'primary' | 'secondary' | 'tertiary'

          const enhancedTag = {
            tag: tagName,
            confidence: tagConfidence,
            source: tagSource as 'ai' | 'llm' | 'human',
            level: level,
            reasoning: explanation.reasoning || `${tagSource?.toUpperCase()} prediction`,
            isConfirmed: true
          }

          console.log("✅ Adding enhanced tag:", enhancedTag)
          tags.push(enhancedTag)
        }
      }
    }

    // Also process confirmed_tags directly (not just as fallback)
    // This ensures we capture all tags even if explanations don't cover everything
    if (dbPredictions) {
      console.log("📊 Processing database confirmed_tags:", dbPredictions)

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

          const enhancedTag = {
            tag: confirmedTag.tag,
            confidence: confirmedTag.confidence || 1.0,
            source: (confirmedTag.source || 'human') as 'ai' | 'llm' | 'human',
            level: confirmedTag.level as 'primary' | 'secondary' | 'tertiary',
            reasoning: `${(confirmedTag.source || 'human').toUpperCase()} confirmed classification`,
            isConfirmed: true
          }

          console.log("✅ Adding confirmed tag:", enhancedTag)
          tags.push(enhancedTag)
        }
      }
    }

    console.log("✅ Enhanced tags result:", tags)
    return tags
  }, [dbPredictions, dbExplanations, propsExplanations])

  // State for multi-tag selection - arrays instead of single strings
  const [selectedPrimaryTags, setSelectedPrimaryTags] = useState<string[]>([])
  const [selectedSecondaryTags, setSelectedSecondaryTags] = useState<string[]>([])
  const [selectedTertiaryTags, setSelectedTertiaryTags] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("selection")

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false)

  // Initialize selections with all confirmed tags
  useEffect(() => {
    console.log("🎯 Initializing tags from enhancedTags:", enhancedTags)

    const primaryTagsFiltered = enhancedTags.filter(t => t.level === 'primary')
    const secondaryTagsFiltered = enhancedTags.filter(t => t.level === 'secondary')
    const tertiaryTagsFiltered = enhancedTags.filter(t => t.level === 'tertiary')

    console.log("🎯 Filtered tags:", {
      primary: primaryTagsFiltered,
      secondary: secondaryTagsFiltered,
      tertiary: tertiaryTagsFiltered
    })

    // Select all confirmed tags as default
    if (primaryTagsFiltered.length > 0) {
      const primaryTags = primaryTagsFiltered.map(t => t.tag)
      console.log("🎯 Setting primary tags:", primaryTags)
      setSelectedPrimaryTags(primaryTags)
    }
    if (secondaryTagsFiltered.length > 0) {
      const secondaryTags = secondaryTagsFiltered.map(t => t.tag)
      console.log("🎯 Setting secondary tags:", secondaryTags)
      setSelectedSecondaryTags(secondaryTags)
    }
    if (tertiaryTagsFiltered.length > 0) {
      const tertiaryTags = tertiaryTagsFiltered.map(t => t.tag)
      console.log("🎯 Setting tertiary tags:", tertiaryTags)
      setSelectedTertiaryTags(tertiaryTags)
    }
  }, [enhancedTags])

  // Get available options based on hierarchy
  const primaryOptions = useMemo(() => Object.keys(hierarchy), [hierarchy])

  const secondaryOptions = useMemo(() => {
    // Get all possible secondary tags across all selected primary tags
    const allSecondaryOptions = new Set<string>()
    selectedPrimaryTags.forEach(primary => {
      if (hierarchy[primary]) {
        Object.keys(hierarchy[primary]).forEach(secondary => allSecondaryOptions.add(secondary))
      }
    })
    return Array.from(allSecondaryOptions)
  }, [selectedPrimaryTags, hierarchy])

  const tertiaryOptions = useMemo(() => {
    // Get all possible tertiary tags across all selected primary and secondary combinations
    // Only include tertiaries where the secondary actually belongs to a selected primary
    const allTertiaryOptions = new Set<string>()

    selectedSecondaryTags.forEach(secondary => {
      // Find which primary this secondary belongs to
      selectedPrimaryTags.forEach(primary => {
        if (hierarchy[primary]?.[secondary]) {
          const tertiaries = hierarchy[primary][secondary]
          if (tertiaries.length > 0) {
            tertiaries.forEach(tertiary => allTertiaryOptions.add(tertiary))
          } else {
            // If no tertiary options, the secondary itself is the tertiary
            allTertiaryOptions.add(secondary)
          }
        }
      })
    })

    return Array.from(allTertiaryOptions)
  }, [selectedPrimaryTags, selectedSecondaryTags, hierarchy])

  // Functions to add/remove tags
  const addPrimaryTag = (tag: string) => {
    if (!selectedPrimaryTags.includes(tag)) {
      setSelectedPrimaryTags([...selectedPrimaryTags, tag])
    }
  }

  const removePrimaryTag = (tag: string) => {
    setSelectedPrimaryTags(selectedPrimaryTags.filter(t => t !== tag))
  }

  const addSecondaryTag = (tag: string) => {
    if (!selectedSecondaryTags.includes(tag)) {
      setSelectedSecondaryTags([...selectedSecondaryTags, tag])
    }
  }

  const removeSecondaryTag = (tag: string) => {
    setSelectedSecondaryTags(selectedSecondaryTags.filter(t => t !== tag))
  }

  const addTertiaryTag = (tag: string) => {
    if (!selectedTertiaryTags.includes(tag)) {
      setSelectedTertiaryTags([...selectedTertiaryTags, tag])
    }
  }

  const removeTertiaryTag = (tag: string) => {
    setSelectedTertiaryTags(selectedTertiaryTags.filter(t => t !== tag))
  }

  const handleConfirm = async () => {
    if (selectedPrimaryTags.length === 0 || selectedSecondaryTags.length === 0 || selectedTertiaryTags.length === 0) {
      toast({
        title: "Incomplete Selection",
        description: "Please select at least one tag for each level (primary, secondary, and tertiary).",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)
    try {
      // Create the data structure for the backend API with multiple tags per level
      const confirmedTags: any[] = []

      // Add all selected primary tags
      selectedPrimaryTags.forEach(tag => {
        const enhancedTag = enhancedTags.find(t => t.level === 'primary' && t.tag === tag)
        confirmedTags.push({
          tag,
          source: enhancedTag?.source || 'human',
          confidence: enhancedTag?.confidence || 1.0,
          confirmed: true,
          added_by: 'user',
          added_at: new Date().toISOString(),
          level: 'primary'
        })
      })

      // Add all selected secondary tags
      selectedSecondaryTags.forEach(tag => {
        const enhancedTag = enhancedTags.find(t => t.level === 'secondary' && t.tag === tag)
        confirmedTags.push({
          tag,
          source: enhancedTag?.source || 'human',
          confidence: enhancedTag?.confidence || 1.0,
          confirmed: true,
          added_by: 'user',
          added_at: new Date().toISOString(),
          level: 'secondary'
        })
      })

      // Add all selected tertiary tags
      selectedTertiaryTags.forEach(tag => {
        const enhancedTag = enhancedTags.find(t => t.level === 'tertiary' && t.tag === tag)
        confirmedTags.push({
          tag,
          source: enhancedTag?.source || 'human',
          confidence: enhancedTag?.confidence || 1.0,
          confirmed: true,
          added_by: 'user',
          added_at: new Date().toISOString(),
          level: 'tertiary'
        })
      })

      const confirmedTagsData = {
        confirmed_tags: {
          tags: confirmedTags
        }
      }

      await onConfirm(document.id, confirmedTagsData)

      toast({
        title: "Success!",
        description: `Document classification updated with ${confirmedTags.length} tags`,
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
    const primaryTagsFiltered = enhancedTags.filter(t => t.level === 'primary')
    const secondaryTagsFiltered = enhancedTags.filter(t => t.level === 'secondary')
    const tertiaryTagsFiltered = enhancedTags.filter(t => t.level === 'tertiary')

    // Reset to all confirmed tags
    setSelectedPrimaryTags(primaryTagsFiltered.map(t => t.tag))
    setSelectedSecondaryTags(secondaryTagsFiltered.map(t => t.tag))
    setSelectedTertiaryTags(tertiaryTagsFiltered.map(t => t.tag))
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
          <TabsList className="grid w-full grid-cols-3 shrink-0">
            <TabsTrigger value="selection" className="flex items-center gap-2">
              <Tag className="w-4 h-4" />
              Classifications
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
              <div className="space-y-4">
                {/* Reset Button */}
                {isEditMode && (
                  <div className="flex justify-end">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={resetToAIPredictions}
                    >
                      <RefreshCw className="w-4 h-4 mr-1" />
                      Reset to Current
                    </Button>
                  </div>
                )}

                {/* Primary Tags Container */}
                <Card className="border-l-4 border-l-blue-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center justify-between text-lg">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="bg-blue-50 text-blue-700">1</Badge>
                        <span>Primary Classification</span>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2 mb-3 min-h-[40px]">
                      {(() => {
                        console.log("🏷️ Rendering Primary Tags:", selectedPrimaryTags)
                        return null
                      })()}
                      {selectedPrimaryTags.length === 0 ? (
                        <p className="text-sm text-gray-500 italic">No primary tags selected. Use the dropdown below to add tags.</p>
                      ) : (
                        selectedPrimaryTags.map((tag) => {
                          const enhancedTag = enhancedTags.find(t => t.level === 'primary' && t.tag === tag)
                          const isAiGenerated = enhancedTag !== undefined && enhancedTag.source !== 'human'
                          return (
                            <Badge
                              key={tag}
                              className="bg-blue-100 text-blue-800 pr-1 flex items-center gap-1"
                            >
                              {isAiGenerated && (
                                <Bot className="w-3 h-3" />
                              )}
                              <span>{tag}</span>
                              {isAiGenerated && enhancedTag && (
                                <span className="text-xs opacity-75">
                                  ({Math.round(enhancedTag.confidence * 100)}%)
                                </span>
                              )}
                              <button
                                onClick={() => removePrimaryTag(tag)}
                                disabled={!isEditMode}
                                className="ml-1 hover:bg-blue-200 rounded-full p-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </Badge>
                          )
                        })
                      )}
                    </div>

                    {/* Add Primary Tag Dropdown */}
                    {isEditMode && (
                      <Select key={selectedPrimaryTags.join(',')} onValueChange={(value) => { addPrimaryTag(value) }}>
                        <SelectTrigger className="w-full">
                          <div className="flex items-center gap-2">
                            <Plus className="w-4 h-4" />
                            <span>Add primary tag</span>
                          </div>
                        </SelectTrigger>
                        <SelectContent>
                          {primaryOptions.filter(opt => !selectedPrimaryTags.includes(opt)).map((primary) => (
                            <SelectItem key={primary} value={primary}>
                              {primary}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </CardContent>
                </Card>

                {/* Secondary Tags Container */}
                <Card className="border-l-4 border-l-green-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center justify-between text-lg">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="bg-green-50 text-green-700">2</Badge>
                        <span>Secondary Classification</span>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2 mb-3 min-h-[40px]">
                      {selectedSecondaryTags.length === 0 ? (
                        <p className="text-sm text-gray-500 italic">No secondary tags selected. Use the dropdown below to add tags.</p>
                      ) : (
                        selectedSecondaryTags.map((tag) => {
                          const enhancedTag = enhancedTags.find(t => t.level === 'secondary' && t.tag === tag)
                          const isAiGenerated = enhancedTag !== undefined && enhancedTag.source !== 'human'
                          return (
                            <Badge
                              key={tag}
                              className="bg-green-100 text-green-800 pr-1 flex items-center gap-1"
                            >
                              {isAiGenerated && (
                                <Bot className="w-3 h-3" />
                              )}
                              <span>{tag}</span>
                              {isAiGenerated && enhancedTag && (
                                <span className="text-xs opacity-75">
                                  ({Math.round(enhancedTag.confidence * 100)}%)
                                </span>
                              )}
                              <button
                                onClick={() => removeSecondaryTag(tag)}
                                disabled={!isEditMode}
                                className="ml-1 hover:bg-green-200 rounded-full p-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </Badge>
                          )
                        })
                      )}
                    </div>

                    {/* Add Secondary Tag Dropdown */}
                    {isEditMode && (
                      <>
                        <Select
                          key={selectedSecondaryTags.join(',')}
                          onValueChange={(value) => { addSecondaryTag(value) }}
                          disabled={selectedPrimaryTags.length === 0}
                        >
                          <SelectTrigger className="w-full">
                            <div className="flex items-center gap-2">
                              <Plus className="w-4 h-4" />
                              <span>Add secondary tag</span>
                            </div>
                          </SelectTrigger>
                          <SelectContent>
                            {secondaryOptions.filter(opt => !selectedSecondaryTags.includes(opt)).map((secondary) => (
                              <SelectItem key={secondary} value={secondary}>
                                {secondary}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {selectedPrimaryTags.length === 0 && (
                          <p className="text-sm text-gray-500 mt-2">Select at least one primary tag first</p>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>

                {/* Tertiary Tags Container */}
                <Card className="border-l-4 border-l-orange-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center justify-between text-lg">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="bg-orange-50 text-orange-700">3</Badge>
                        <span>Tertiary Classification</span>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2 mb-3 min-h-[40px]">
                      {selectedTertiaryTags.length === 0 ? (
                        <p className="text-sm text-gray-500 italic">No tertiary tags selected. Use the dropdown below to add tags.</p>
                      ) : (
                        selectedTertiaryTags.map((tag) => {
                          const enhancedTag = enhancedTags.find(t => t.level === 'tertiary' && t.tag === tag)
                          const isAiGenerated = enhancedTag !== undefined && enhancedTag.source !== 'human'
                          return (
                            <Badge
                              key={tag}
                              className="bg-orange-100 text-orange-800 pr-1 flex items-center gap-1"
                            >
                              {isAiGenerated && (
                                <Bot className="w-3 h-3" />
                              )}
                              <span>{tag}</span>
                              {isAiGenerated && enhancedTag && (
                                <span className="text-xs opacity-75">
                                  ({Math.round(enhancedTag.confidence * 100)}%)
                                </span>
                              )}
                              <button
                                onClick={() => removeTertiaryTag(tag)}
                                disabled={!isEditMode}
                                className="ml-1 hover:bg-orange-200 rounded-full p-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </Badge>
                          )
                        })
                      )}
                    </div>

                    {/* Add Tertiary Tag Dropdown */}
                    {isEditMode && (
                      <>
                        <Select
                          key={selectedTertiaryTags.join(',')}
                          onValueChange={(value) => { addTertiaryTag(value) }}
                          disabled={selectedSecondaryTags.length === 0}
                        >
                          <SelectTrigger className="w-full">
                            <div className="flex items-center gap-2">
                              <Plus className="w-4 h-4" />
                              <span>Add tertiary tag</span>
                            </div>
                          </SelectTrigger>
                          <SelectContent>
                            {tertiaryOptions.filter(opt => !selectedTertiaryTags.includes(opt)).map((tertiary) => (
                              <SelectItem key={tertiary} value={tertiary}>
                                {tertiary}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {selectedSecondaryTags.length === 0 && (
                          <p className="text-sm text-gray-500 mt-2">Select at least one secondary tag first</p>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* AI Reasoning Tab */}
            <TabsContent value="explanations" className="h-full overflow-y-auto mt-4">
              {(() => {
                // Use database explanations if available, fallback to props explanations for SHAP data
                const explanationData = dbExplanations.length > 0 ? dbExplanations : propsExplanations

                console.log("🔍 Raw explanations data:", explanationData)
                console.log("🔍 Explanations length:", explanationData.length)
                console.log("🔍 DB explanations:", dbExplanations)
                console.log("🔍 Props explanations:", propsExplanations)

                // Debug each explanation's service_response
                explanationData.forEach((exp: any, idx: number) => {
                  console.log(`🔍 Explanation ${idx}:`, {
                    tag: exp.predicted_tag || exp.tag,
                    source: exp.source_service || exp.source,
                    service_response: exp.service_response,
                    has_shap_explainability: !!exp.service_response?.shap_explainability,
                    has_key_evidence: !!exp.service_response?.key_evidence,
                    shap_data: exp.shap_data,
                    full_response: exp.full_response
                  })
                })

                // Filter out AI explanations that were overridden by LLM
                const filteredExplanations = explanationData.filter((explanation: any) => {
                  return explanation.reasoning !== "AI model prediction (overridden by LLM)"
                })

                console.log("🔍 Filtered explanations:", filteredExplanations)

                // Enhanced explanations with SHAP data extracted from backend service_response
                const enhancedExplanations = filteredExplanations.map((explanation: any) => {
                  // Extract SHAP data from multiple possible locations
                  let shapData = null;

                  // Check service_response.shap_explainability (database format)
                  if (explanation.service_response?.shap_explainability) {
                    shapData = explanation.service_response.shap_explainability;
                  }
                  // Check service_response.key_evidence (alternative format)
                  else if (explanation.service_response?.key_evidence) {
                    shapData = explanation.service_response.key_evidence;
                  }
                  // Check direct shap_data property (props format from upload)
                  else if (explanation.shap_data) {
                    shapData = explanation.shap_data;
                  }
                  // Check full_response.key_evidence (another possible format)
                  else if (explanation.full_response?.key_evidence) {
                    shapData = explanation.full_response.key_evidence;
                  }

                  // Parse SHAP data if it's a string (from database)
                  if (shapData && typeof shapData === 'string') {
                    try {
                      // Replace single quotes with double quotes for valid JSON
                      const jsonString = shapData.replace(/'/g, '"');
                      shapData = JSON.parse(jsonString);
                      console.log('✅ Parsed SHAP data for', explanation.predicted_tag || explanation.tag, ':', shapData);
                    } catch (e) {
                      console.error('❌ Failed to parse SHAP data:', e, shapData);
                      shapData = null;
                    }
                  }

                  console.log('🧠 SHAP data for', explanation.predicted_tag || explanation.tag, ':', {
                    shapData,
                    service_response: explanation.service_response,
                    raw_explanation: explanation
                  });

                  return {
                    ...explanation,
                    shap_data: shapData
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
                {selectedPrimaryTags.length > 0 && selectedSecondaryTags.length > 0 && selectedTertiaryTags.length > 0 ? (
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
                  disabled={isLoading || selectedPrimaryTags.length === 0 || selectedSecondaryTags.length === 0 || selectedTertiaryTags.length === 0}
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