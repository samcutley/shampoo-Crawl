'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api'
import { formatDate, formatNumber, getSeverityColor, getStatusColor } from '@/lib/utils'
import {
  Activity,
  FileText,
  Shield,
  Database,
  TrendingUp,
  AlertTriangle,
  Clock,
  CheckCircle
} from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recentArticles, setRecentArticles] = useState([])
  const [recentIocs, setRecentIocs] = useState([])
  const [sources, setSources] = useState([])
  const [systemStatus, setSystemStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch all dashboard data in parallel
      const [
        analysisStats,
        sourcesResponse,
        articlesResponse,
        iocsResponse
      ] = await Promise.all([
        apiClient.getAnalysisStats(),
        apiClient.getSources(),
        apiClient.getArticles({ limit: 5 }).catch(() => ({ items: [] })),
        apiClient.getIocs({ limit: 5 }).catch(() => ({ items: [] }))
      ])

      setStats(analysisStats)
      setSources(sourcesResponse.sources || [])
      setRecentArticles(articlesResponse.items || [])
      setRecentIocs(iocsResponse.items || [])
      
      // Create a mock system status since the endpoint doesn't exist
      setSystemStatus({
        status: 'healthy',
        active_workers: 1,
        last_update: new Date().toISOString()
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const statCards = [
    {
      title: 'Total Articles',
      value: stats?.recent_activity?.[0]?.articles_scraped || 0,
      icon: FileText,
      description: 'Analyzed articles',
      color: 'text-blue-600'
    },
    {
      title: 'IOCs Extracted',
      value: stats?.top_ioc_types?.length || 0,
      icon: Shield,
      description: 'Indicators of compromise',
      color: 'text-red-600'
    },
    {
      title: 'Active Sources',
      value: sources.filter(source => source.is_active).length,
      icon: Database,
      description: 'Monitored sources',
      color: 'text-green-600'
    },
    {
      title: 'Analysis Jobs',
      value: stats?.overall_stats?.pending || 0,
      icon: Activity,
      description: 'Pending analysis',
      color: 'text-orange-600'
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <Button onClick={fetchDashboardData} variant="outline">
          <Activity className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stat.value)}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* System Status */}
      {systemStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <Badge className={getStatusColor(systemStatus.status)}>
                  {systemStatus.status}
                </Badge>
                <span className="text-sm text-gray-600">Overall Status</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm">{systemStatus.active_workers} Active Workers</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-blue-600" />
                <span className="text-sm">Last Update: {formatDate(systemStatus.last_update)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Articles */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Recent Articles
            </CardTitle>
            <CardDescription>
              Latest analyzed security articles
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentArticles.length > 0 ? (
                recentArticles.map((article) => (
                  <div key={article.id} className="border-b border-gray-200 pb-3 last:border-b-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm line-clamp-2">
                          {article.title}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">
                          {article.source_name} • {formatDate(article.published_date)}
                        </p>
                      </div>
                      {article.severity && (
                        <Badge className={getSeverityColor(article.severity)}>
                          {article.severity}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-sm">No articles found</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent IOCs */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Recent IOCs
            </CardTitle>
            <CardDescription>
              Latest indicators of compromise
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentIocs.length > 0 ? (
                recentIocs.map((ioc) => (
                  <div key={ioc.id} className="border-b border-gray-200 pb-3 last:border-b-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm font-mono">
                          {ioc.value}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">
                          {ioc.ioc_type} • {formatDate(ioc.first_seen)}
                        </p>
                      </div>
                      {ioc.confidence && (
                        <Badge variant="outline">
                          {ioc.confidence}% confidence
                        </Badge>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-sm">No IOCs found</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and operations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-20 flex-col" asChild>      
      <Link href="#">
              <TrendingUp className="h-6 w-6 mb-2" />
              Trigger Analysis
      </Link>
            </Button>
            <Button variant="outline" className="h-20 flex-col" asChild>
      <Link href="/sources">
              <Database className="h-6 w-6 mb-2" />
              Manage Sources
              </Link>
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <AlertTriangle className="h-6 w-6 mb-2" />
              View Alerts
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}