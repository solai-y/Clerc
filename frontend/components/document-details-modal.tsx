"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Progress } from "@/components/ui/progress"
import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api"
import {
  FileText,
  Calendar,
  Tag,
  Building,
  User,
  Download,
  ExternalLink,
  Clock,
  CheckCircle,
  AlertCircle,
  Info,
  Bot,
  UserPlus,
  Check,
  X,
  MessageSquare,
  Brain,
  Cpu,
  TrendingUp,
  Eye,
  Settings
} from "lucide-react"

interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  size: string
  type: string
  link: string
  company: number | null
  companyName: string | null
  uploaded_by: number | null
  status: string
  modelGeneratedTags: Array<{
    tag: string
    score: number
    isConfirmed: boolean
  }>
  userAddedTags: string[]
}

interface DocumentDetailsModalProps {
  document: Document
  onClose: () => void
}

export function DocumentDetailsModal({ document, onClose }: DocumentDetailsModalProps) {
  const [explanations, setExplanations] = useState<Array<{
    explanation_id: number;
    classification_level: string;
    predicted_tag: string;
    confidence: number;
    reasoning: string;
    source_service: string;
    created_at: string;
    service_response?: {
      shap_explainability?: {
        supporting_tokens?: Array<{ token: string; impact: number }>;
        opposing_tokens?: Array<{ token: string; impact: number }>;
      };
    };
  }>>([])
  const [loadingExplanations, setLoadingExplanations] = useState(false)
  const [activeTab, setActiveTab] = useState("tags")

  useEffect(() => {
    const fetchExplanations = async () => {
      setLoadingExplanations(true)
      try {
        console.log("🔍 Fetching explanations for document:", document.id)

        // TEMPORARY: For testing SHAP display, use hardcoded data for document 1374
        if (document.id === "1374") {
          console.log("🧪 Using test SHAP data for document 1374")
          const testExplanations = [
            {
              explanation_id: 24,
              classification_level: "primary",
              predicted_tag: "News",
              confidence: 0.85,
              reasoning: "This document contains news-related content about digital regulations",
              source_service: "ai",
              created_at: "2025-09-23T04:27:48.348857+00:00",
              service_response: {
                shap_explainability: {
                  supporting_tokens: [
                    { token: "EU", impact: 0.15 },
                    { token: "regulation", impact: 0.12 }
                  ],
                  opposing_tokens: [
                    { token: "technology", impact: -0.05 }
                  ]
                }
              }
            },
            {
              explanation_id: 25,
              classification_level: "secondary",
              predicted_tag: "Industry",
              confidence: 0.75,
              reasoning: "Content discusses industry implications",
              source_service: "ai",
              created_at: "2025-09-23T04:27:48.348857+00:00",
              service_response: {
                shap_explainability: {
                  supporting_tokens: [
                    { token: "digital", impact: 0.08 },
                    { token: "laws", impact: 0.06 }
                  ],
                  opposing_tokens: [
                    { token: "Brussels", impact: -0.03 }
                  ]
                }
              }
            },
            {
              explanation_id: 26,
              classification_level: "tertiary",
              predicted_tag: "Regulation",
              confidence: 0.9,
              reasoning: "Document discusses regulatory frameworks",
              source_service: "llm",
              created_at: "2025-09-23T04:27:48.348857+00:00",
              service_response: {}
            }
          ]
          setExplanations(testExplanations)
          setLoadingExplanations(false)
          return
        }

        const explanationData = await apiClient.getDocumentExplanations(parseInt(document.id))
        console.log("📊 Explanation data received:", explanationData)
        console.log("📊 Explanation data length:", explanationData?.length)
        console.log("📊 First explanation:", explanationData?.[0])
        if (explanationData?.[0]?.service_response?.shap_explainability) {
          console.log("🧠 SHAP data found:", explanationData[0].service_response.shap_explainability)
        }
        setExplanations(explanationData || [])
      } catch (error) {
        console.error("❌ Error fetching explanations:", error)
        console.error("❌ Error details:", {
          message: error instanceof Error ? error.message : 'Unknown error',
          stack: error instanceof Error ? error.stack : undefined,
          documentId: document.id
        })

        // Create mock explanations from document data as fallback
        console.warn("⚠️ Using fallback explanations due to API error")
        const mockExplanations = document.modelGeneratedTags?.map(tag => ({
          explanation_id: Math.random(),
          classification_level: tag.hierarchy_level || 'unknown',
          predicted_tag: tag.tag,
          confidence: tag.score,
          reasoning: `${tag.source?.toUpperCase() || 'AI'} prediction with ${Math.round(tag.score * 100)}% confidence`,
          source_service: tag.source || 'ai',
          created_at: new Date().toISOString(),
          service_response: null
        })) || []
        setExplanations(mockExplanations)
      } finally {
        setLoadingExplanations(false)
      }
    }

    if (document.id) {
      fetchExplanations()
    }
  }, [document.id])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed':
      case 'completed':
      case 'user_confirmed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'failed':
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Info className="w-4 h-4 text-blue-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed':
      case 'completed':
      case 'user_confirmed':
        return 'bg-green-50 text-green-700 border-green-200'
      case 'processing':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200'
      case 'failed':
      case 'error':
        return 'bg-red-50 text-red-700 border-red-200'
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200'
    }
  }

  const handleDownload = () => {
    if (document.link) {
      window.open(document.link, '_blank')
    }
  }

  const handleOpenExternal = () => {
    if (document.link) {
      window.open(document.link, '_blank')
    }
  }

  // Process tags for hierarchy display
  // If we have explanations, use them to separate AI vs LLM tags
  // Otherwise, show all model tags as a fallback
  const aiTags = explanations.length > 0
    ? document.modelGeneratedTags.filter(tag =>
        tag.tag && explanations.some(exp => exp.predicted_tag === tag.tag && exp.source_service === 'ai')
      )
    : document.modelGeneratedTags // Fallback: show all as "AI" if no explanations

  const llmTags = explanations.length > 0
    ? document.modelGeneratedTags.filter(tag =>
        tag.tag && explanations.some(exp => exp.predicted_tag === tag.tag && exp.source_service === 'llm')
      )
    : [] // Only show LLM tags if we have explanation data

  const primaryTag = explanations.find(exp => exp.classification_level === 'primary')
  const secondaryTag = explanations.find(exp => exp.classification_level === 'secondary')
  const tertiaryTag = explanations.find(exp => exp.classification_level === 'tertiary')

  // Debug info
  console.log("🏷️ Document data:", {
    id: document.id,
    modelGeneratedTags: document.modelGeneratedTags,
    userAddedTags: document.userAddedTags,
    explanationsCount: explanations.length,
    aiTagsCount: aiTags.length,
    llmTagsCount: llmTags.length
  })

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="shrink-0 pb-4">
          <DialogTitle className="flex items-center gap-2 text-xl font-semibold">
            <FileText className="w-6 h-6 text-blue-600" />
            Document Details - {document.name}
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
                      {aiTags.map((tagData, index) => (
                        <div key={`ai-${index}`} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                          <div className="flex items-center gap-3 flex-1">
                            <div className="flex items-center gap-1">
                              {tagData.isConfirmed ? (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                              ) : (
                                <X className="w-4 h-4 text-gray-400" />
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <div className="font-medium">{tagData.tag}</div>
                                {tagData.hierarchy_level && (
                                  <Badge variant="outline" className="text-xs px-1 py-0">
                                    {tagData.hierarchy_level}
                                  </Badge>
                                )}
                              </div>
                              <div className="text-sm text-gray-500">
                                Confidence: {Math.round(tagData.score * 100)}%
                                {tagData.source && (
                                  <span className="ml-2">• Source: {tagData.source.toUpperCase()}</span>
                                )}
                              </div>
                            </div>
                          </div>
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                            <Bot className="w-3 h-3 mr-1" />
                            AI
                          </Badge>
                        </div>
                      ))}
                      {aiTags.length === 0 && !loadingExplanations && (
                        <div className="text-center py-8 text-gray-500">
                          <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p>No AI-generated tags available</p>
                        </div>
                      )}
                      {aiTags.length === 0 && loadingExplanations && (
                        <div className="text-center py-8 text-gray-500">
                          <div className="animate-pulse">
                            <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>Loading tag information...</p>
                          </div>
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
                      {llmTags.map((tagData, index) => (
                        <div key={`llm-${index}`} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                          <div className="flex items-center gap-3 flex-1">
                            <div className="flex items-center gap-1">
                              {tagData.isConfirmed ? (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                              ) : (
                                <X className="w-4 h-4 text-gray-400" />
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <div className="font-medium">{tagData.tag}</div>
                                {tagData.hierarchy_level && (
                                  <Badge variant="outline" className="text-xs px-1 py-0">
                                    {tagData.hierarchy_level}
                                  </Badge>
                                )}
                              </div>
                              <div className="text-sm text-gray-500">
                                Confidence: {Math.round(tagData.score * 100)}%
                                {tagData.source && (
                                  <span className="ml-2">• Source: {tagData.source.toUpperCase()}</span>
                                )}
                              </div>
                            </div>
                          </div>
                          <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                            <Brain className="w-3 h-3 mr-1" />
                            LLM
                          </Badge>
                        </div>
                      ))}
                      {llmTags.length === 0 && !loadingExplanations && (
                        <div className="text-center py-8 text-gray-500">
                          <Brain className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p>No LLM-generated tags available</p>
                        </div>
                      )}
                      {llmTags.length === 0 && loadingExplanations && (
                        <div className="text-center py-8 text-gray-500">
                          <div className="animate-pulse">
                            <Brain className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>Loading tag information...</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* User Added Tags */}
              <Card className="border-l-4 border-l-green-500">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <UserPlus className="w-5 h-5 text-green-600" />
                    User Added Tags
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {document.userAddedTags.length > 0 ? (
                      document.userAddedTags.map((tag, index) => (
                        <Badge
                          key={`custom-${index}`}
                          variant="secondary"
                          className="bg-green-50 text-green-800 border-green-200"
                        >
                          <span>{tag}</span>
                        </Badge>
                      ))
                    ) : (
                      <p className="text-gray-500 italic text-sm">No user-added tags</p>
                    )}
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
                          <div className="font-semibold text-lg">{primaryTag.predicted_tag}</div>
                          <div className="text-sm text-gray-600">
                            Primary Classification • {Math.round(primaryTag.confidence * 100)}% confidence
                          </div>
                        </div>
                        <Badge className={primaryTag.source_service === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}>
                          {primaryTag.source_service === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                          {primaryTag.source_service.toUpperCase()}
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
                          <div className="font-semibold text-lg">{secondaryTag.predicted_tag}</div>
                          <div className="text-sm text-gray-600">
                            Secondary Classification • {Math.round(secondaryTag.confidence * 100)}% confidence
                          </div>
                        </div>
                        <Badge className={secondaryTag.source_service === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}>
                          {secondaryTag.source_service === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                          {secondaryTag.source_service.toUpperCase()}
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
                          <div className="font-semibold text-lg">{tertiaryTag.predicted_tag}</div>
                          <div className="text-sm text-gray-600">
                            Tertiary Classification • {Math.round(tertiaryTag.confidence * 100)}% confidence
                          </div>
                        </div>
                        <Badge className={tertiaryTag.source_service === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}>
                          {tertiaryTag.source_service === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                          {tertiaryTag.source_service.toUpperCase()}
                        </Badge>
                      </div>
                    )}

                    {!primaryTag && !secondaryTag && !tertiaryTag && (
                      <div className="text-center py-12 text-gray-500">
                        <TrendingUp className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p className="text-lg">No hierarchy data available</p>
                        <p className="text-sm">The classification hierarchy will appear here when available</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Explanations Tab */}
            <TabsContent value="explanations" className="h-full flex flex-col mt-4 data-[state=active]:flex">
              {loadingExplanations ? (
                <div className="text-center py-12 text-gray-500 flex-1 flex flex-col justify-center">
                  <div className="animate-pulse">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p className="text-base font-medium">Loading explanations...</p>
                    <p className="text-sm">Please wait while we fetch the reasoning data</p>
                  </div>
                </div>
              ) : explanations.length > 0 ? (
                <div className="space-y-2 overflow-y-auto flex-1">
                  {explanations.map((explanation, index) => (
                    <div key={`explanation-${index}`} className="border border-indigo-200 rounded-lg p-3 bg-gradient-to-r from-indigo-50 to-purple-50">
                      {/* Header */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 text-indigo-600" />
                          <span className="font-semibold text-sm">{explanation.predicted_tag}</span>
                          <Badge variant="outline" className="text-xs px-1 py-0">
                            {explanation.classification_level}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={`text-xs px-2 py-0 ${explanation.source_service === 'ai' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}>
                            {explanation.source_service === 'ai' ? <Bot className="w-3 h-3 mr-1" /> : <Brain className="w-3 h-3 mr-1" />}
                            {explanation.source_service.toUpperCase()}
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
                      {explanation.source_service === 'ai' && explanation.service_response?.shap_explainability && (
                        <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                          <div className="text-xs font-semibold text-blue-800 mb-1 flex items-center">
                            <Brain className="w-3 h-3 mr-1" />
                            SHAP Feature Importance
                          </div>
                          <div className="space-y-1">
                            {/* Supporting Evidence */}
                            {explanation.service_response.shap_explainability.supporting_tokens?.length > 0 && (
                              <div>
                                <div className="text-xs font-medium text-green-700">Supporting:</div>
                                <div className="flex flex-wrap gap-1">
                                  {explanation.service_response.shap_explainability.supporting_tokens.map((item: any, idx: number) => (
                                    <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-green-100 text-green-800 border border-green-300">
                                      <span className="font-mono mr-1">{item.token.trim()}</span>
                                      <span className="text-green-600 font-semibold">{Math.round(item.impact * 100)}%</span>
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Opposing Evidence */}
                            {explanation.service_response.shap_explainability.opposing_tokens?.length > 0 && (
                              <div>
                                <div className="text-xs font-medium text-red-700">Opposing:</div>
                                <div className="flex flex-wrap gap-1">
                                  {explanation.service_response.shap_explainability.opposing_tokens.map((item: any, idx: number) => (
                                    <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-red-100 text-red-800 border border-red-300">
                                      <span className="font-mono mr-1">{item.token.trim()}</span>
                                      <span className="text-red-600 font-semibold">{Math.round(item.impact * 100)}%</span>
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
              )}
            </TabsContent>

            {/* Document Tab */}
            <TabsContent value="document" className="h-full overflow-y-auto space-y-4 mt-4 data-[state=active]:flex data-[state=active]:flex-col">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Basic Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-blue-600" />
                      Document Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <div className="text-sm font-medium text-gray-600">Name</div>
                        <div className="font-medium">{document.name}</div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm font-medium text-gray-600">Upload Date</div>
                          <div>{formatDate(document.uploadDate + 'T00:00:00')}</div>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-600">File Size</div>
                          <div>{document.size}</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm font-medium text-gray-600">Status</div>
                          <Badge className={`text-sm ${getStatusColor(document.status)}`}>
                            {document.status.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-600">Type</div>
                          <div>{document.type || 'Unknown'}</div>
                        </div>
                      </div>
                      {document.companyName && (
                        <div>
                          <div className="text-sm font-medium text-gray-600">Company</div>
                          <div>{document.companyName}</div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Document Access */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Eye className="w-5 h-5 text-green-600" />
                      Document Access
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {document.link ? (
                      <div className="space-y-4">
                        <div>
                          <div className="text-sm font-medium text-gray-600 mb-2">Actions</div>
                          <div className="flex gap-2">
                            <Button
                              onClick={handleDownload}
                              size="sm"
                              className="bg-red-600 hover:bg-red-700"
                            >
                              <Download className="w-4 h-4 mr-2" />
                              Download
                            </Button>
                            <Button
                              onClick={handleOpenExternal}
                              variant="outline"
                              size="sm"
                            >
                              <ExternalLink className="w-4 h-4 mr-2" />
                              Open
                            </Button>
                          </div>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-600 mb-2">Document URL</div>
                          <div className="bg-gray-50 p-2 rounded border text-xs font-mono break-all">
                            {document.link}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <ExternalLink className="w-12 h-12 mx-auto mb-2 opacity-50" />
                        <p>No download link available</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </div>
        </Tabs>

        <Separator className="shrink-0 my-4" />

        <div className="flex justify-end shrink-0">
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
