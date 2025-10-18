'use client'

import { useState } from 'react'
import { ChevronDown, Filter, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import TierFilterSection from './tier-filter-section'

export interface TagFilters {
  primary: string[]
  secondary: string[]
  tertiary: string[]
}

interface FilterPanelProps {
  availableTags: {
    primary: string[]
    secondary: string[]
    tertiary: string[]
  }
  selectedFilters: TagFilters
  onFilterChange: (filters: TagFilters) => void
  filteredCount?: number
  totalCount?: number
}

export default function FilterPanel({
  availableTags,
  selectedFilters,
  onFilterChange,
  filteredCount,
  totalCount,
}: FilterPanelProps) {
  // Count total active filters
  const activeFilterCount =
    selectedFilters.primary.length +
    selectedFilters.secondary.length +
    selectedFilters.tertiary.length

  // Handle adding/removing tags
  const handleToggleTag = (tier: 'primary' | 'secondary' | 'tertiary', tag: string) => {
    const currentTierTags = selectedFilters[tier]
    const newTierTags = currentTierTags.includes(tag)
      ? currentTierTags.filter((t) => t !== tag)
      : [...currentTierTags, tag]

    onFilterChange({
      ...selectedFilters,
      [tier]: newTierTags,
    })
  }

  // Clear all filters
  const handleClearAll = () => {
    onFilterChange({
      primary: [],
      secondary: [],
      tertiary: [],
    })
  }

  // Clear specific tier
  const handleClearTier = (tier: 'primary' | 'secondary' | 'tertiary') => {
    onFilterChange({
      ...selectedFilters,
      [tier]: [],
    })
  }

  return (
    <div className="w-full bg-white border rounded-lg shadow-sm">
      <Accordion type="single" collapsible defaultValue="">
        <AccordionItem value="filters" className="border-none">
          <AccordionTrigger className="px-4 py-3 hover:no-underline">
            <div className="flex items-center gap-3 w-full">
              <Filter className="h-4 w-4 text-gray-500" />
              <span className="font-medium text-gray-700">Filter by Tags</span>
              {activeFilterCount > 0 && (
                <>
                  <Badge variant="secondary" className="ml-auto mr-2">
                    {activeFilterCount} active
                  </Badge>
                  <span
                    onClick={(e) => {
                      e.stopPropagation()
                      handleClearAll()
                    }}
                    className="inline-flex items-center h-6 px-2 text-xs rounded-md cursor-pointer hover:bg-red-50 hover:text-red-600 transition-colors"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Clear All
                  </span>
                </>
              )}
            </div>
          </AccordionTrigger>

          <AccordionContent className="px-4 pb-4 space-y-4">
            {/* Filtered count display */}
            {filteredCount !== undefined && totalCount !== undefined && (
              <div className="text-sm text-gray-600 border-b pb-3">
                Showing <span className="font-semibold text-gray-900">{filteredCount}</span> of{' '}
                <span className="font-semibold text-gray-900">{totalCount}</span> documents
              </div>
            )}

            {/* Primary Tags */}
            <TierFilterSection
              title="Primary Tags"
              tierLevel="primary"
              availableTags={availableTags.primary}
              selectedTags={selectedFilters.primary}
              onToggleTag={(tag) => handleToggleTag('primary', tag)}
              onClearTier={() => handleClearTier('primary')}
              color="blue"
            />

            {/* Secondary Tags */}
            <TierFilterSection
              title="Secondary Tags"
              tierLevel="secondary"
              availableTags={availableTags.secondary}
              selectedTags={selectedFilters.secondary}
              onToggleTag={(tag) => handleToggleTag('secondary', tag)}
              onClearTier={() => handleClearTier('secondary')}
              color="green"
            />

            {/* Tertiary Tags */}
            <TierFilterSection
              title="Tertiary Tags"
              tierLevel="tertiary"
              availableTags={availableTags.tertiary}
              selectedTags={selectedFilters.tertiary}
              onToggleTag={(tag) => handleToggleTag('tertiary', tag)}
              onClearTier={() => handleClearTier('tertiary')}
              color="orange"
            />
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  )
}
