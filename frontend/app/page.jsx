'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import {
  Activity,
  FileText,
  Database,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Shield,
  Globe,
  Users,
  BarChart3,
  Loader2
} from 'lucide-react'

export default function Home() {
  const [stats, setStats] = useState({
    totalArticles: 0,
    activeSources: 0,
    pendingAnalysis: 0,
    totalIOCs: 0
  })
  const [recentArticles, setRecentArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch articles
      const articlesResponse = await apiClient.getArticles({ limit: 5 })
      setRecentArticles(articlesResponse.articles || [])
      
      // Fetch sources
      const sourcesResponse = await apiClient.getSources()
      const sources = sourcesResponse.sources || []
      
      // Calculate stats
      setStats({
        totalArticles: articlesResponse.pagination?.total || 0,
        activeSources: sources.filter(s => s.is_active).length,
        pendingAnalysis: articlesResponse.articles?.filter(a => a.analysis_status === 'pending').length || 0,
        totalIOCs: articlesResponse.articles?.reduce((sum, article) => sum + (article.ioc_count || 0), 0) || 0
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getAnalysisStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <Button onClick={fetchDashboardData} disabled={loading}>
          {loading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Activity className="h-4 w-4 mr-2" />
          )}
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Articles</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalArticles}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Sources</p>
                <p className="text-3xl font-bold text-gray-900">{stats.activeSources}</p>
              </div>
              <Database className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Analysis</p>
                <p className="text-3xl font-bold text-gray-900">{stats.pendingAnalysis}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total IOCs</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalIOCs}</p>
              </div>
              <Shield className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Articles */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Recent Articles
          </CardTitle>
          <CardDescription>
            Latest intelligence articles from your sources
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading articles...</p>
            </div>
          ) : recentArticles.length > 0 ? (
            <div className="space-y-4">
              {recentArticles.map((article) => (
                <div key={article.id} className="flex items-start justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 mb-1">
                      {article.title}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Globe className="h-4 w-4" />
                        {article.source_name || 'Unknown Source'}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {formatDate(article.published_date)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getAnalysisStatusColor(article.analysis_status)}>
                      {article.analysis_status || 'pending'}
                    </Badge>
                    {article.url && (
                      <Button variant="outline" size="sm" asChild>
                        <a href={article.url} target="_blank" rel="noopener noreferrer">
                          View
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No articles found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button className="h-20 flex-col gap-2" variant="outline" asChild>
              <a href="/sources">
                <Database className="h-6 w-6" />
                <span>Manage Sources</span>
              </a>
            </Button>
            <Button className="h-20 flex-col gap-2" variant="outline" asChild>
              <a href="/articles">
                <FileText className="h-6 w-6" />
                <span>View Articles</span>
              </a>
            </Button>
            <Button className="h-20 flex-col gap-2" variant="outline" asChild>
              <a href="/iocs">
                <Shield className="h-6 w-6" />
                <span>Review IOCs</span>
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}