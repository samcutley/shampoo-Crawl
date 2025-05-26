'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { apiClient } from '@/lib/api'
import { formatDate, getSeverityColor } from '@/lib/utils'
import {
  FileText,
  ExternalLink,
  Eye,
  Calendar,
  Tag,
  Clock,
  User,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react'

export default function Articles() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [stats, setStats] = useState({
    total: 0,
    analyzed: 0,
    pending: 0,
    failed: 0
  })

  useEffect(() => {
    fetchArticles()
    fetchStats()
  }, [])

  const fetchArticles = async () => {
    try {
      setLoading(true)
      const response = await apiClient.getArticles({ limit: 1000 }) // Get all articles for client-side pagination
      setArticles(response.articles || [])
    } catch (error) {
      console.error('Failed to fetch articles:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await apiClient.getAnalysisStats()
      if (response && Array.isArray(response)) {
        const statusCounts = response.reduce((acc, item) => {
          acc[item.analysis_status] = item.count
          return acc
        }, {})
        
        setStats({
          total: articles.length,
          analyzed: statusCounts.completed || 0,
          pending: statusCounts.pending || 0,
          failed: statusCounts.failed || 0
        })
      } else {
        // Fallback: calculate stats from articles data
        setStats({
          total: articles.length,
          analyzed: articles.filter(a => a.analysis_status === 'completed').length,
          pending: articles.filter(a => a.analysis_status === 'pending').length,
          failed: articles.filter(a => a.analysis_status === 'failed').length
        })
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      // Fallback: calculate stats from articles data
      setStats({
        total: articles.length,
        analyzed: articles.filter(a => a.analysis_status === 'completed').length,
        pending: articles.filter(a => a.analysis_status === 'pending').length,
        failed: articles.filter(a => a.analysis_status === 'failed').length
      })
    }
  }

  const getAnalysisStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return (
          <Badge className="bg-green-100 text-green-800 border-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            Analyzed
          </Badge>
        )
      case 'pending':
        return (
          <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        )
      case 'failed':
        return (
          <Badge className="bg-red-100 text-red-800 border-red-200">
            <XCircle className="h-3 w-3 mr-1" />
            Failed
          </Badge>
        )
      default:
        return (
          <Badge className="bg-gray-100 text-gray-800 border-gray-200">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Unknown
          </Badge>
        )
    }
  }

  const getSeverityBadge = (severity) => {
    if (!severity) return null
    
    const colors = getSeverityColor(severity)
    return (
      <Badge className={colors}>
        {severity.toUpperCase()}
      </Badge>
    )
  }

  const columns = useMemo(() => [
    {
      accessorKey: 'title',
      header: 'Title',
      cell: ({ row }) => {
        const article = row.original
        return (
          <div className="max-w-md">
            <h4 className="font-medium line-clamp-2 mb-1">
              {article.title}
            </h4>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <User className="h-3 w-3" />
              <span>{article.source_name || 'Unknown Source'}</span>
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'analysis_status',
      header: 'Analysis',
      cell: ({ row }) => {
        const status = row.getValue('analysis_status')
        return getAnalysisStatusBadge(status)
      },
    },
    {
      accessorKey: 'severity',
      header: 'Severity',
      cell: ({ row }) => {
        const severity = row.getValue('severity')
        return getSeverityBadge(severity)
      },
    },
    {
      accessorKey: 'published_date',
      header: 'Published',
      cell: ({ row }) => {
        const date = row.getValue('published_date')
        return (
          <div className="flex items-center gap-1 text-sm">
            <Calendar className="h-3 w-3 text-gray-500" />
            <span>{formatDate(date)}</span>
          </div>
        )
      },
    },
    {
      accessorKey: 'scraped_at',
      header: 'Scraped',
      cell: ({ row }) => {
        const date = row.getValue('scraped_at')
        return (
          <div className="flex items-center gap-1 text-sm">
            <Clock className="h-3 w-3 text-gray-500" />
            <span>{formatDate(date)}</span>
          </div>
        )
      },
    },
    {
      accessorKey: 'ioc_count',
      header: 'IOCs',
      cell: ({ row }) => {
        const count = row.getValue('ioc_count') || 0
        return (
          <div className="flex items-center gap-1">
            <Tag className="h-3 w-3 text-gray-500" />
            <span className="text-sm font-medium">{count}</span>
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const article = row.original
        return (
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedArticle(article)}
              className="h-8 w-8 p-0"
            >
              <Eye className="h-3 w-3" />
            </Button>
            
            {article.url && (
              <Button
                variant="outline"
                size="sm"
                asChild
                className="h-8 w-8 p-0"
              >
                <a href={article.url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-3 w-3" />
                </a>
              </Button>
            )}
          </div>
        )
      },
    },
  ], [])

  const filterOptions = [
    {
      column: 'analysis_status',
      placeholder: 'Analysis Status',
      options: [
        { value: 'completed', label: 'Analyzed' },
        { value: 'pending', label: 'Pending' },
        { value: 'failed', label: 'Failed' },
      ],
    },
    {
      column: 'severity',
      placeholder: 'Severity',
      options: [
        { value: 'critical', label: 'Critical' },
        { value: 'high', label: 'High' },
        { value: 'medium', label: 'Medium' },
        { value: 'low', label: 'Low' },
      ],
    },
  ]

  if (selectedArticle) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Article Details</h1>
          <Button variant="outline" onClick={() => setSelectedArticle(null)}>
            Back to Articles
          </Button>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <CardTitle className="text-xl">{selectedArticle.title}</CardTitle>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    <span>{selectedArticle.source_name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDate(selectedArticle.published_date)}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {getAnalysisStatusBadge(selectedArticle.analysis_status)}
                {getSeverityBadge(selectedArticle.severity)}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {selectedArticle.summary && (
                <div>
                  <h3 className="font-medium mb-2">Summary</h3>
                  <p className="text-gray-700">{selectedArticle.summary}</p>
                </div>
              )}
              
              {selectedArticle.content && (
                <div>
                  <h3 className="font-medium mb-2">Content</h3>
                  <div className="prose max-w-none">
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {selectedArticle.content.substring(0, 1000)}
                      {selectedArticle.content.length > 1000 && '...'}
                    </p>
                  </div>
                </div>
              )}

              {selectedArticle.url && (
                <div className="pt-4 border-t">
                  <Button asChild>
                    <a href={selectedArticle.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Read Full Article
                    </a>
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Articles</h1>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium">Total Articles</p>
                <p className="text-2xl font-bold">{articles.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">Analyzed</p>
                <p className="text-2xl font-bold">{stats.analyzed}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-600" />
              <div>
                <p className="text-sm font-medium">Pending</p>
                <p className="text-2xl font-bold">{stats.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium">IOCs Found</p>
                <p className="text-2xl font-bold">
                  {articles.reduce((sum, article) => sum + (article.ioc_count || 0), 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Intelligence Articles
          </CardTitle>
          <CardDescription>
            Browse and analyze cybersecurity intelligence articles
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading articles...</p>
              </div>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={articles}
              searchKey="title"
              searchPlaceholder="Search articles..."
              showFilter={true}
              filterOptions={filterOptions}
              pageSize={20}
              onRowClick={(article) => setSelectedArticle(article)}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}