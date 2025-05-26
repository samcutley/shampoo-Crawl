'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api'
import { Bell, RefreshCw, Activity } from 'lucide-react'

export function Header() {
  const [systemStatus, setSystemStatus] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchSystemStatus = async () => {
    try {
      setIsRefreshing(true)
      const status = await apiClient.getSystemStatus()
      setSystemStatus(status)
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Cybersecurity Intelligence Platform
          </h2>
        </div>
        
        <div className="flex items-center space-x-4">
          {systemStatus && (
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-gray-500" />
              <Badge className={getStatusColor(systemStatus.status)}>
                {systemStatus.status}
              </Badge>
              <span className="text-sm text-gray-500">
                {systemStatus.active_workers} workers
              </span>
            </div>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={fetchSystemStatus}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
          
          <Button variant="outline" size="sm">
            <Bell className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}