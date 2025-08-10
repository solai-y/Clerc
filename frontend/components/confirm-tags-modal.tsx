"use client"

import type React from "react"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Tag, Plus, X, Brain, CheckCircle } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  size: string
  subtags: { [tagId: string]: string[] }
}

interface ConfirmTagsModalProps {
  document: Document
  onConfirm: (documentId: string, tags: string[], subtags: { [tagId: string]: string[] }) => void
  onClose: () => void
}

export function ConfirmTagsModal({ document, onConfirm, onClose }: ConfirmTagsModalProps) {
  const [tags, setTags] = useState<string[]>(document.tags)
  const [subtags, setSubtags] = useState<{ [tagId: string]: string[] }>(document.subtags)
  const [newTag, setNewTag] = useState("")
  const [newSubtag, setNewSubtag] = useState("")
  const [selectedTagForSubtag, setSelectedTagForSubtag] = useState<string>("")
  const [isConfirming, setIsConfirming] = useState(false)
  const [previewMode, setPreviewMode] = useState<"ai-context" | "full-document">("ai-context")

  // Mock AI analysis data
  const aiAnalysis = {
    confidence: 92,
    keyPhrases: [
      { phrase: "financial performance", relevance: 95, position: "Page 1, Line 3" },
      { phrase: "quarterly results", relevance: 88, position: "Page 1, Line 8" },
      { phrase: "revenue growth", relevance: 85, position: "Page 2, Line 15" },
      { phrase: "risk assessment", relevance: 78, position: "Page 3, Line 22" },
    ],
    suggestedTags: ["Financial Report", "Quarterly", "Revenue", "Performance Analysis"],
    suggestedSubtags: {
      "Financial Report": ["Income Statement", "Balance Sheet", "Cash Flow"],
      Quarterly: ["Q3 2024", "Current Quarter"],
      Revenue: ["Operating Revenue", "Investment Income"],
      "Performance Analysis": ["YoY Comparison", "Trend Analysis"],
    },
  }

  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      const trimmedTag = newTag.trim()
      setTags([...tags, trimmedTag])
      if (!subtags[trimmedTag]) {
        setSubtags({ ...subtags, [trimmedTag]: [] })
      }
      setNewTag("")
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove))
    const newSubtags = { ...subtags }
    delete newSubtags[tagToRemove]
    setSubtags(newSubtags)
  }

  const addSubtag = () => {
    if (newSubtag.trim() && selectedTagForSubtag && !subtags[selectedTagForSubtag]?.includes(newSubtag.trim())) {
      setSubtags({
        ...subtags,
        [selectedTagForSubtag]: [...(subtags[selectedTagForSubtag] || []), newSubtag.trim()],
      })
      setNewSubtag("")
      setSelectedTagForSubtag("")
    }
  }

  const removeSubtag = (tag: string, subtagToRemove: string) => {
    setSubtags({
      ...subtags,
      [tag]: subtags[tag].filter((subtag) => subtag !== subtagToRemove),
    })
  }

  const addSuggestedSubtag = (tag: string, subtag: string) => {
    if (!subtags[tag]?.includes(subtag)) {
      setSubtags({
        ...subtags,
        [tag]: [...(subtags[tag] || []), subtag],
      })
    }
  }

  const handleConfirm = async () => {
    setIsConfirming(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))
    onConfirm(document.id, tags, subtags)
    setIsConfirming(false)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      addTag()
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-red-600" />
            <span>Edit Document Tags</span>
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Document Info & Tags */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <FileText className="w-5 h-5" />
                  <span>Document Details</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="font-medium text-gray-900">{document.name}</p>
                  <p className="text-sm text-gray-500">Size: {document.size}</p>
                </div>

                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-green-600 font-medium">
                    AI Analysis Complete ({aiAnalysis.confidence}% confidence)
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Tag className="w-5 h-5" />
                  <span>Document Tags</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Document Tags:</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {tags.map((tag, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="bg-red-50 text-red-700 hover:bg-red-100 flex items-center space-x-1"
                      >
                        <span>{tag}</span>
                        <button onClick={() => removeTag(tag)} className="ml-1 hover:bg-red-200 rounded-full p-0.5">
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Subtags by Category:</p>
                  <div className="space-y-2 mb-3">
                    {tags.map((tag) => (
                      <div key={tag} className="bg-gray-50 p-2 rounded-lg">
                        <p className="text-xs font-medium text-gray-600 mb-1">{tag}:</p>
                        <div className="flex flex-wrap gap-1">
                          {(subtags[tag] || []).map((subtag, index) => (
                            <Badge
                              key={index}
                              variant="outline"
                              className="text-xs border-red-200 text-red-600 flex items-center space-x-1"
                            >
                              <span>{subtag}</span>
                              <button
                                onClick={() => removeSubtag(tag, subtag)}
                                className="ml-1 hover:bg-red-100 rounded-full p-0.5"
                              >
                                <X className="w-2 h-2" />
                              </button>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Input
                    placeholder="Add new tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="flex-1"
                  />
                  <Button
                    onClick={addTag}
                    size="sm"
                    variant="outline"
                    className="border-red-200 text-red-700 hover:bg-red-50 bg-transparent"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>

                <div className="flex space-x-2">
                  <Select
                    value={selectedTagForSubtag || "select-tag"}
                    onValueChange={(value: string) => {
                      const newValue = value === "select-tag" ? "" : value
                      setSelectedTagForSubtag(newValue)
                    }}
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select tag for subtag" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="select-tag" disabled>
                        Select tag for subtag
                      </SelectItem>
                      {tags.map((tag) => (
                        <SelectItem key={tag} value={tag}>
                          {tag}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    placeholder="Add subtag..."
                    value={newSubtag}
                    onChange={(e) => setNewSubtag(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && addSubtag()}
                    className="flex-1"
                    disabled={!selectedTagForSubtag}
                  />
                  <Button
                    onClick={addSubtag}
                    size="sm"
                    variant="outline"
                    className="border-red-200 text-red-700 hover:bg-red-50 bg-transparent"
                    disabled={!selectedTagForSubtag}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">AI Suggested Tags:</p>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {aiAnalysis.suggestedTags
                      .filter((tag) => !tags.includes(tag))
                      .map((tag, index) => (
                        <Button
                          key={index}
                          variant="outline"
                          size="sm"
                          onClick={() => setTags([...tags, tag])}
                          className="text-xs border-gray-300 hover:border-red-300 hover:bg-red-50"
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          {tag}
                        </Button>
                      ))}
                  </div>

                  <p className="text-sm font-medium text-gray-700 mb-2">AI Suggested Subtags:</p>
                  <div className="space-y-2">
                    {Object.entries(aiAnalysis.suggestedSubtags).map(
                      ([tag, suggestedSubtags]) =>
                        tags.includes(tag) && (
                          <div key={tag} className="bg-gray-50 p-2 rounded-lg">
                            <p className="text-xs font-medium text-gray-600 mb-1">{tag}:</p>
                            <div className="flex flex-wrap gap-1">
                              {suggestedSubtags
                                .filter((subtag) => !subtags[tag]?.includes(subtag))
                                .map((subtag, index) => (
                                  <Button
                                    key={index}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => addSuggestedSubtag(tag, subtag)}
                                    className="text-xs border-gray-300 hover:border-red-300 hover:bg-red-50"
                                  >
                                    <Plus className="w-2 h-2 mr-1" />
                                    {subtag}
                                  </Button>
                                ))}
                            </div>
                          </div>
                        ),
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* AI Analysis */}
          {/* AI Analysis and Document Preview */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Brain className="w-5 h-5" />
                  <span>AI Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-green-50 p-3 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">High Confidence Analysis</span>
                  </div>
                  <p className="text-sm text-green-700">
                    AI model is {aiAnalysis.confidence}% confident in the tag suggestions based on document content
                    analysis.
                  </p>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Key Phrases Identified:</h4>
                  <div className="space-y-2">
                    {aiAnalysis.keyPhrases.map((phrase, index) => (
                      <div key={index} className="bg-gray-50 p-3 rounded-lg">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-medium text-gray-900">"{phrase.phrase}"</span>
                          <Badge variant="outline" className="text-xs">
                            {phrase.relevance}% relevance
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-500">{phrase.position}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Document Preview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                    <button
                      onClick={() => setPreviewMode("ai-context")}
                      className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        previewMode === "ai-context"
                          ? "bg-white text-red-600 shadow-sm"
                          : "text-gray-600 hover:text-gray-900"
                      }`}
                    >
                      AI Context
                    </button>
                    <button
                      onClick={() => setPreviewMode("full-document")}
                      className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        previewMode === "full-document"
                          ? "bg-white text-red-600 shadow-sm"
                          : "text-gray-600 hover:text-gray-900"
                      }`}
                    >
                      Full Document
                    </button>
                  </div>
                </div>

                {previewMode === "ai-context" ? (
                  <div>
                    <div className="bg-gray-50 p-4 rounded-lg h-48 overflow-y-auto">
                      <p className="text-sm text-gray-700 leading-relaxed">
                        <strong>QUARTERLY FINANCIAL REPORT</strong>
                        <br />
                        <br />
                        This document presents the financial performance of our organization for Q3 2024. The quarterly
                        results show significant revenue growth compared to the previous period.
                        <br />
                        <br />
                        <span className="bg-yellow-200">Key financial metrics indicate strong performance</span> across
                        all business segments. Revenue growth has exceeded expectations by 12%, driven primarily by
                        increased market penetration and strategic partnerships.
                        <br />
                        <br />
                        <span className="bg-yellow-200">Risk assessment procedures</span> have been updated to reflect
                        current market conditions and regulatory requirements...
                      </p>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Highlighted sections contributed to AI tag suggestions</p>
                  </div>
                ) : (
                  <div>
                    <div className="bg-gray-50 p-4 rounded-lg h-96 overflow-y-auto">
                      <div className="text-sm text-gray-700 leading-relaxed space-y-4">
                        <div className="text-center mb-6">
                          <h1 className="text-xl font-bold text-gray-900 mb-2">QUARTERLY FINANCIAL REPORT</h1>
                          <p className="text-gray-600">Q3 2024 Financial Performance Summary</p>
                          <hr className="my-4 border-gray-300" />
                        </div>

                        <section className="mb-6">
                          <h2 className="text-lg font-semibold text-gray-900 mb-3">Executive Summary</h2>
                          <p className="mb-3">
                            This document presents the financial performance of our organization for Q3 2024. The
                            quarterly results show significant revenue growth compared to the previous period, with
                            strong performance across all business segments.
                          </p>
                          <p className="mb-3">
                            Key financial metrics indicate strong performance across all business segments. Revenue
                            growth has exceeded expectations by 12%, driven primarily by increased market penetration
                            and strategic partnerships established during the quarter.
                          </p>
                        </section>

                        <section className="mb-6">
                          <h2 className="text-lg font-semibold text-gray-900 mb-3">Financial Highlights</h2>
                          <ul className="list-disc list-inside space-y-2 ml-4">
                            <li>Total Revenue: $2.4B (↑12% YoY)</li>
                            <li>Net Income: $340M (↑8% YoY)</li>
                            <li>Operating Margin: 14.2% (↑1.1% YoY)</li>
                            <li>Return on Equity: 15.8% (↑0.9% YoY)</li>
                          </ul>
                        </section>

                        <section className="mb-6">
                          <h2 className="text-lg font-semibold text-gray-900 mb-3">Business Segment Performance</h2>
                          <div className="space-y-3">
                            <div>
                              <h3 className="font-medium text-gray-800">Investment Banking</h3>
                              <p className="text-sm text-gray-600">
                                Revenue increased by 15% driven by strong M&A activity and equity underwriting.
                              </p>
                            </div>
                            <div>
                              <h3 className="font-medium text-gray-800">Asset Management</h3>
                              <p className="text-sm text-gray-600">
                                Assets under management grew to $180B, with net inflows of $12B during the quarter.
                              </p>
                            </div>
                            <div>
                              <h3 className="font-medium text-gray-800">Retail Banking</h3>
                              <p className="text-sm text-gray-600">
                                Steady performance with 8% growth in deposits and improved net interest margin.
                              </p>
                            </div>
                          </div>
                        </section>

                        <section className="mb-6">
                          <h2 className="text-lg font-semibold text-gray-900 mb-3">Risk Management</h2>
                          <p className="mb-3">
                            Risk assessment procedures have been updated to reflect current market conditions and
                            regulatory requirements. Our comprehensive risk management framework continues to
                            effectively identify, measure, and mitigate various risk exposures.
                          </p>
                          <p className="mb-3">
                            Credit risk remains well-controlled with a provision coverage ratio of 1.8%. Market risk
                            exposure is within established limits, and operational risk management has been strengthened
                            through enhanced controls and monitoring systems.
                          </p>
                        </section>

                        <section className="mb-6">
                          <h2 className="text-lg font-semibold text-gray-900 mb-3">Outlook</h2>
                          <p className="mb-3">
                            Looking ahead to Q4 2024, we remain optimistic about our growth prospects. Market conditions
                            continue to be favorable, and our strategic initiatives are expected to drive continued
                            revenue growth and operational efficiency improvements.
                          </p>
                          <p>
                            We anticipate maintaining our strong capital position while continuing to invest in
                            technology and talent to support long-term sustainable growth.
                          </p>
                        </section>

                        <div className="text-center mt-8 pt-4 border-t border-gray-300">
                          <p className="text-xs text-gray-500">
                            This report contains forward-looking statements. Actual results may differ materially.
                          </p>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Complete document content - {document.size}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        <DialogFooter className="flex justify-between">
          <Button variant="outline" onClick={onClose} disabled={isConfirming}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={isConfirming} className="bg-red-600 hover:bg-red-700">
            {isConfirming ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
