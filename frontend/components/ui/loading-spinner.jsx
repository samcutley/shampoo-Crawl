'use client'

import { cn } from '@/lib/utils'
import { useLoading } from '@/contexts/LoadingContext'

export function LoadingSpinner({ className, size = 'default' }) {
  const { isLoading } = useLoading()
  
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  }

  if (!isLoading) return null

  return (
    <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 shadow-lg flex flex-col items-center space-y-4">
        <div
          className={cn(
            'animate-spin rounded-full border-2 border-gray-300 border-t-blue-600',
            sizeClasses[size],
            className
          )}
        />
        <p className="text-sm text-gray-600">Loading...</p>
      </div>
    </div>
  )
}