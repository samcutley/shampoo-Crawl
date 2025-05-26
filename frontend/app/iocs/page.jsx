'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiClient } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import {
  Shield,
  Search,
  Filter,
  Copy,
  ExternalLink,
  AlertTriangle,
  Hash,
  Globe,
  Mail
} from 'lucide-react'

const IOC_TYPE_ICONS = {
  'ip': Globe,
  'domain': Globe,
  'url': ExternalLink,
  'hash': Hash,
  'email': Mail,
  'file': Hash,
  'registry': Hash,
  'default': AlertTriangle
}

export default function IOCs() {
  const [iocs, setIocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState('all')
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
    total: 0
  })

  useEffect(() => {
    fetchIOCs()
  }, [pagination.page, pagination.limit])

  const fetchIOCs = async () => {
    try {
      setLoading(true)
      const params = {
        page: pagination.page,
        limit: pagination.limit,
        ...(searchQuery && { search: searchQuery }),
        ...(selectedType !== 'all' && { ioc_type: selectedType })
      }
      
      const response = await apiClient.getIocs(params)
      setIocs(response.items || [])
      setPagination(prev => ({
        ...prev,
        total: response.total || 0
      }))
    } catch (error) {
      console.error('Failed to fetch IOCs:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    fetchIOCs()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
    }
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'bg-green-100 text-green-800 border-green-200'
    if (confidence >= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    if (confidence >= 40) return 'bg-orange-100 text-orange-800 border-orange-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  const getTypeIcon = (type) => {
    const IconComponent = IOC_TYPE_ICONS[type?.toLowerCase()] || IOC_TYPE_ICONS.default
    return IconComponent
  }

  const totalPages = Math.ceil(pagination.total / pagination.limit)

  const iocTypes = ['all', 'ip', 'domain', 'url', 'hash', 'email', 'file', 'registry']

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Indicators of Compromise</h1>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search IOCs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-64"
            />
            <Button onClick={handleSearch} size="sm">
              <Search className="h-4 w-4" />
            </Button>
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {iocTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            IOC Database
          </CardTitle>
          <CardDescription>
            {pagination.total} indicators found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <Shield className="h-8 w-8 animate-pulse mx-auto mb-4" />
                <p className="text-gray-600">Loading IOCs...</p>
              </div>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>First Seen</TableHead>
                    <TableHead>Last Seen</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {iocs.map((ioc) => {
                    const TypeIcon = getTypeIcon(ioc.ioc_type)
                    return (
                      <TableRow key={ioc.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <TypeIcon className="h-4 w-4 text-gray-500" />
                            <Badge variant="outline">
                              {ioc.ioc_type}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="font-mono text-sm max-w-xs">
                            <span className="break-all">{ioc.value}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {ioc.confidence && (
                            <Badge className={getConfidenceColor(ioc.confidence)}>
                              {ioc.confidence}%
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {formatDate(ioc.first_seen)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {formatDate(ioc.last_seen)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {ioc.source_article_id ? 'Article' : 'Manual'}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copyToClipboard(ioc.value)}
                              title="Copy to clipboard"
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                            {(ioc.ioc_type === 'url' || ioc.ioc_type === 'domain') && (
                              <Button
                                variant="outline"
                                size="sm"
                                asChild
                                title="Open in new tab"
                              >
                                <a 
                                  href={ioc.ioc_type === 'url' ? ioc.value : `http://${ioc.value}`}
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                >
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-gray-600">
                    Showing {(pagination.page - 1) * pagination.limit + 1} to{' '}
                    {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                    {pagination.total} IOCs
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                      disabled={pagination.page === 1}
                    >
                      Previous
                    </Button>
                    <span className="text-sm">
                      Page {pagination.page} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                      disabled={pagination.page === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* IOC Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium">IP Addresses</p>
                <p className="text-2xl font-bold">
                  {iocs.filter(ioc => ioc.ioc_type === 'ip').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">Domains</p>
                <p className="text-2xl font-bold">
                  {iocs.filter(ioc => ioc.ioc_type === 'domain').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Hash className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium">Hashes</p>
                <p className="text-2xl font-bold">
                  {iocs.filter(ioc => ioc.ioc_type === 'hash').length}
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
                <p className="text-sm font-medium">URLs</p>
                <p className="text-2xl font-bold">
                  {iocs.filter(ioc => ioc.ioc_type === 'url').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}