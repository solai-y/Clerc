'use client'

import { X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/utils'

interface TierFilterSectionProps {
  title: string
  tierLevel: 'primary' | 'secondary' | 'tertiary'
  availableTags: string[]
  selectedTags: string[]
  onToggleTag: (tag: string) => void
  onClearTier: () => void
  color: 'blue' | 'green' | 'orange'
}

const colorStyles = {
  blue: {
    badge: 'bg-blue-100 text-blue-800 border-blue-300',
    checkbox: 'data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600',
    dot: 'bg-blue-500',
    clearButton: 'hover:bg-blue-50 hover:text-blue-600',
  },
  green: {
    badge: 'bg-green-100 text-green-800 border-green-300',
    checkbox: 'data-[state=checked]:bg-green-600 data-[state=checked]:border-green-600',
    dot: 'bg-green-500',
    clearButton: 'hover:bg-green-50 hover:text-green-600',
  },
  orange: {
    badge: 'bg-orange-100 text-orange-800 border-orange-300',
    checkbox: 'data-[state=checked]:bg-orange-600 data-[state=checked]:border-orange-600',
    dot: 'bg-orange-500',
    clearButton: 'hover:bg-orange-50 hover:text-orange-600',
  },
}

export default function TierFilterSection({
  title,
  tierLevel,
  availableTags,
  selectedTags,
  onToggleTag,
  onClearTier,
  color,
}: TierFilterSectionProps) {
  const styles = colorStyles[color]

  if (availableTags.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={cn('h-2 w-2 rounded-full', styles.dot)} />
          <h3 className="text-sm font-medium text-gray-700">{title}</h3>
          {selectedTags.length > 0 && (
            <Badge variant="outline" className="h-5 px-1.5 text-xs">
              {selectedTags.length}
            </Badge>
          )}
        </div>
        {selectedTags.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearTier}
            className={cn('h-6 px-2 text-xs', styles.clearButton)}
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {availableTags.map((tag) => {
          const isSelected = selectedTags.includes(tag)
          return (
            <label
              key={tag}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md border cursor-pointer transition-all',
                isSelected
                  ? cn('border-current', styles.badge)
                  : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              )}
            >
              <Checkbox
                checked={isSelected}
                onCheckedChange={() => onToggleTag(tag)}
                className={cn('h-4 w-4', isSelected && styles.checkbox)}
              />
              <span className="text-sm font-medium">
                {tag.replace(/_/g, ' ')}
              </span>
            </label>
          )
        })}
      </div>
    </div>
  )
}
