'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiClient } from '@/lib/api'
import { formatDate, getStatusColor } from '@/lib/utils'
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
  XCircle
} from 'lucide-react'

export default function Sources() {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingSource, setEditingSource] = useState(null)
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
      setSources(response || [])
    } catch (error) {
      console.error('Failed to fetch sources:', error)
    } finally {
      setLoading(false)
    }
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
        await apiClient.deleteSource(sourceId)
        fetchSources()
      } catch (error) {
        console.error('Failed to delete source:', error)
      }
    }
  }

  const toggleSourceStatus = async (source) => {
    try {
      await apiClient.updateSource(source.id, {
        ...source,
        is_active: !source.is_active
      })
      fetchSources()
    } catch (error) {
      console.error('Failed to toggle source status:', error)
    }
  }

  const triggerScraping = async (source) => {
    try {
      await apiClient.triggerScraping({ source_id: source.id })
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to trigger scraping:', error)
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
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
    return `${Math.floor(seconds / 86400)}d`
  }

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
                <Database className="h-8 w-8 animate-pulse mx-auto mb-4" />
                <p className="text-gray-600">Loading sources...</p>
              </div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Last Scraped</TableHead>
                  <TableHead>Articles</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.map((source) => (
                  <TableRow key={source.id}>
                    <TableCell>
                      <div>
                        <h4 className="font-medium">{source.name}</h4>
                        {source.description && (
                          <p className="text-sm text-gray-500 line-clamp-1">
                            {source.description}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getSourceTypeColor(source.source_type)}>
                        {source.source_type.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {source.is_active ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600" />
                        )}
                        <Badge className={source.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {source.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-gray-500" />
                        <span className="text-sm">
                          {formatFrequency(source.scraping_frequency)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">
                        {formatDate(source.last_scraped)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-medium">
                        {source.article_count || 0}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleSourceStatus(source)}
                          title={source.is_active ? 'Pause' : 'Resume'}
                        >
                          {source.is_active ? (
                            <Pause className="h-3 w-3" />
                          ) : (
                            <Play className="h-3 w-3" />
                          )}
                        </Button>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => triggerScraping(source)}
                          title="Trigger scraping"
                        >
                          <Database className="h-3 w-3" />
                        </Button>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(source)}
                          title="Edit source"
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          asChild
                          title="Visit source"
                        >
                          <a href={source.url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </Button>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(source.id)}
                          title="Delete source"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
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
              <ExternalLink className="h-5 w-5 text-orange-600" />
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