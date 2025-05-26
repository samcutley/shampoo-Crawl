'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/ui/data-table'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { apiClient } from '@/lib/api'
import { formatDate, getStatusColor } from '@/lib/utils'
import { toast } from 'sonner'
import {
  Database,
  Plus,
  Edit,
  Trash2,
  Play,
  Pause,
  ExternalLink,
  Globe,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  FileText
} from 'lucide-react'

export default function Sources() {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingSource, setEditingSource] = useState(null)
  const [actionLoading, setActionLoading] = useState({})
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    source_type: 'rss',
    is_active: true,
    scraping_frequency: 3600,
    description: ''
  })

  useEffect(() => {
    fetchSources()
  }, [])

  const fetchSources = async () => {
    try {
      setLoading(true)
      const response = await apiClient.getSources()
      
      // Transform backend data to frontend format
      const transformedSources = (response.sources || []).map(source => ({
        ...source,
        url: source.base_url,
        scraping_frequency: source.scraping_config?.scraping_frequency || 3600,
        description: source.scraping_config?.description || ''
      }))
      
      // Check for duplicates and remove oldest entries
      const uniqueSources = removeDuplicates(transformedSources)
      setSources(uniqueSources)
    } catch (error) {
      console.error('Failed to fetch sources:', error)
    } finally {
      setLoading(false)
    }
  }

  const removeDuplicates = (sources) => {
    const seen = new Map()
    const duplicates = []
    
    // Group by title and URL
    sources.forEach(source => {
      const key = `${source.name}-${source.url}`
      if (seen.has(key)) {
        const existing = seen.get(key)
        // Keep the newer one (higher ID or more recent created_at)
        if (source.id > existing.id || new Date(source.created_at) > new Date(existing.created_at)) {
          duplicates.push(existing.id)
          seen.set(key, source)
        } else {
          duplicates.push(source.id)
        }
      } else {
        seen.set(key, source)
      }
    })
    
    // Remove duplicates from backend if any found
    if (duplicates.length > 0) {
      duplicates.forEach(async (id) => {
        try {
          await apiClient.deleteSource(id)
        } catch (error) {
          console.error(`Failed to remove duplicate source ${id}:`, error)
        }
      })
    }
    
    return Array.from(seen.values())
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingSource) {
        await apiClient.updateSource(editingSource.id, formData)
      } else {
        await apiClient.createSource(formData)
      }
      
      setShowAddForm(false)
      setEditingSource(null)
      setFormData({
        name: '',
        url: '',
        source_type: 'rss',
        is_active: true,
        scraping_frequency: 3600,
        description: ''
      })
      fetchSources()
    } catch (error) {
      console.error('Failed to save source:', error)
      alert('Failed to save source. Please check the console for details.')
    }
  }

  const handleEdit = (source) => {
    setEditingSource(source)
    setFormData({
      name: source.name,
      url: source.url,
      source_type: source.source_type,
      is_active: source.is_active,
      scraping_frequency: source.scraping_frequency,
      description: source.description || ''
    })
    setShowAddForm(true)
  }

  const handleDelete = async (sourceId) => {
    if (confirm('Are you sure you want to delete this source?')) {
      try {
        setActionLoading(prev => ({ ...prev, [`delete-${sourceId}`]: true }))
        await apiClient.deleteSource(sourceId)
        fetchSources()
      } catch (error) {
        console.error('Failed to delete source:', error)
        alert('Failed to delete source. Please check the console for details.')
      } finally {
        setActionLoading(prev => ({ ...prev, [`delete-${sourceId}`]: false }))
      }
    }
  }

  const toggleSourceStatus = async (source) => {
    try {
      setActionLoading(prev => ({ ...prev, [`toggle-${source.id}`]: true }))
      await apiClient.updateSource(source.id, {
        ...source,
        is_active: !source.is_active
      })
      fetchSources()
      toast.success(`Source ${source.name} ${source.is_active ? 'paused' : 'activated'} successfully!`)
    } catch (error) {
      console.error('Failed to toggle source status:', error)
      toast.error(`Failed to toggle source status for ${source.name}: ${error.message || 'Unknown error'}`)
    } finally {
      setActionLoading(prev => ({ ...prev, [`toggle-${source.id}`]: false }))
    }
  }

  const triggerScraping = async (source) => {
    try {
      setActionLoading(prev => ({ ...prev, [`scrape-${source.id}`]: true }))
      await apiClient.triggerScraping({ 
        source_name: source.name,
        job_type: 'manual'
      })
      toast.success(`Scraping triggered successfully for ${source.name}`)
      // Refresh sources to get updated status
      fetchSources()
    } catch (error) {
      console.error('Failed to trigger scraping:', error)
      toast.error(`Failed to trigger scraping for ${source.name}: ${error.message || 'Unknown error'}`)
    } finally {
      setActionLoading(prev => ({ ...prev, [`scrape-${source.id}`]: false }))
    }
  }

  const getSourceTypeColor = (type) => {
    switch (type) {
      case 'rss':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'web':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'api':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatFrequency = (seconds) => {
    if (!seconds || isNaN(seconds)) return 'Auto'
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
    return `${Math.floor(seconds / 86400)}d`
  }

  const columns = useMemo(() => [
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => {
        const source = row.original
        return (
          <div>
            <h4 className="font-medium">{source.name}</h4>
            {source.description && (
              <p className="text-sm text-gray-500 line-clamp-1">
                {source.description}
              </p>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'source_type',
      header: 'Type',
      cell: ({ row }) => {
        const type = row.getValue('source_type')
        return (
          <Badge className={getSourceTypeColor(type)}>
            {type.toUpperCase()}
          </Badge>
        )
      },
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => {
        const isActive = row.getValue('is_active')
        return (
          <div className="flex items-center gap-2">
            {isActive ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <XCircle className="h-4 w-4 text-red-600" />
            )}
            <Badge className={isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
              {isActive ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        )
      },
    },
    {
      accessorKey: 'scraping_frequency',
      header: 'Frequency',
      cell: ({ row }) => {
        const frequency = row.getValue('scraping_frequency')
        return (
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-gray-500" />
            <span className="text-sm">
              {formatFrequency(frequency)}
            </span>
          </div>
        )
      },
    },
    {
      accessorKey: 'last_scraped',
      header: 'Last Scraped',
      cell: ({ row }) => {
        const lastScraped = row.getValue('last_scraped')
        return (
          <span className="text-sm">
            {formatDate(lastScraped)}
          </span>
        )
      },
    },
    {
      accessorKey: 'article_count',
      header: 'Articles',
      cell: ({ row }) => {
        const count = row.getValue('article_count')
        return (
          <span className="text-sm font-medium">
            {count || 0}
          </span>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const source = row.original
        return (
          <div className="flex items-center gap-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleSourceStatus(source)}
                    disabled={actionLoading[`toggle-${source.id}`]}
                    className="h-8 w-8 p-0"
                  >
                    {actionLoading[`toggle-${source.id}`] ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : source.is_active ? (
                      <Pause className="h-3 w-3" />
                    ) : (
                      <Play className="h-3 w-3" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{source.is_active ? 'Pause' : 'Resume'}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => triggerScraping(source)}
                    disabled={actionLoading[`scrape-${source.id}`]}
                    className="h-8 w-8 p-0"
                  >
                    {actionLoading[`scrape-${source.id}`] ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Database className="h-3 w-3" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Trigger scraping</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(source)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Edit source</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                    className="h-8 w-8 p-0"
                  >
                    <a href={source.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Visit source</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(source.id)}
                    disabled={actionLoading[`delete-${source.id}`]}
                    className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                  >
                    {actionLoading[`delete-${source.id}`] ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Delete source</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )
      },
    },
  ], [actionLoading])

  const filterOptions = [
    {
      column: 'source_type',
      placeholder: 'Type',
      options: [
        { value: 'rss', label: 'RSS' },
        { value: 'web', label: 'Web' },
        { value: 'api', label: 'API' },
      ],
    },
    {
      column: 'is_active',
      placeholder: 'Status',
      options: [
        { value: 'true', label: 'Active' },
        { value: 'false', label: 'Inactive' },
      ],
    },
  ]

  if (showAddForm) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">
            {editingSource ? 'Edit Source' : 'Add New Source'}
          </h1>
          <Button 
            variant="outline" 
            onClick={() => {
              setShowAddForm(false)
              setEditingSource(null)
              setFormData({
                name: '',
                url: '',
                source_type: 'rss',
                is_active: true,
                scraping_frequency: 3600,
                description: ''
              })
            }}
          >
            Cancel
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Source Configuration</CardTitle>
            <CardDescription>
              Configure the source details and scraping parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Source Name *
                  </label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., KrebsOnSecurity"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Source Type *
                  </label>
                  <select
                    value={formData.source_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, source_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  >
                    <option value="rss">RSS Feed</option>
                    <option value="web">Web Scraping</option>
                    <option value="api">API</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  URL *
                </label>
                <Input
                  value={formData.url}
                  onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                  placeholder="https://example.com/feed.xml"
                  type="url"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Brief description of the source"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Scraping Frequency (seconds)
                  </label>
                  <Input
                    value={formData.scraping_frequency}
                    onChange={(e) => setFormData(prev => ({ ...prev, scraping_frequency: parseInt(e.target.value) }))}
                    type="number"
                    min="60"
                    placeholder="3600"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Minimum 60 seconds. Default is 3600 (1 hour)
                  </p>
                </div>

                <div className="flex items-center space-x-2 pt-6">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded"
                  />
                  <label htmlFor="is_active" className="text-sm font-medium">
                    Active Source
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button type="submit">
                  {editingSource ? 'Update Source' : 'Add Source'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Sources</h1>
        <Button onClick={() => setShowAddForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Source
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Configured Sources
          </CardTitle>
          <CardDescription>
            Manage your intelligence sources and scraping configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading sources...</p>
              </div>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={sources}
              searchKey="name"
              searchPlaceholder="Search sources..."
              showFilter={true}
              filterOptions={filterOptions}
              pageSize={10}
            />
          )}
        </CardContent>
      </Card>

      {/* Source Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">Active Sources</p>
                <p className="text-2xl font-bold">
                  {sources.filter(s => s.is_active).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium">RSS Feeds</p>
                <p className="text-2xl font-bold">
                  {sources.filter(s => s.source_type === 'rss').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium">Web Sources</p>
                <p className="text-2xl font-bold">
                  {sources.filter(s => s.source_type === 'web').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-sm font-medium">Total Articles</p>
                <p className="text-2xl font-bold">
                  {sources.reduce((sum, s) => sum + (s.article_count || 0), 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}