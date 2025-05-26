'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiClient } from '@/lib/api'
import { formatDate, getSeverityColor } from '@/lib/utils'
import {
  FileText,
  Search,
  Filter,
  ExternalLink,
  Eye,
  Calendar,
  Tag
} from 'lucide-react'

export default function Articles() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0
  })

  useEffect(() => {
    fetchArticles()
  }, [pagination.page, pagination.limit])

  const fetchArticles = async () => {
    try {
      setLoading(true)
      const params = {
        page: pagination.page,
        limit: pagination.limit,
        ...(searchQuery && { search: searchQuery })
      }
      
      const response = await apiClient.getArticles(params)
      setArticles(response.items || [])
      setPagination(prev => ({
        ...prev,
        total: response.total || 0
      }))
    } catch (error) {
      console.error('Failed to fetch articles:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    fetchArticles()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const viewArticleDetails = async (articleId) => {
    try {
      const article = await apiClient.getArticle(articleId)
      setSelectedArticle(article)
    } catch (error) {
      console.error('Failed to fetch article details:', error)
    }
  }

  const totalPages = Math.ceil(pagination.total / pagination.limit)

  if (selectedArticle) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button 
            variant="outline" 
            onClick={() => setSelectedArticle(null)}
          >
            ← Back to Articles
          </Button>
          <div className="flex items-center gap-2">
            {selectedArticle.url && (
              <Button variant="outline" size="sm" asChild>
                <a href={selectedArticle.url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Original
                </a>
              </Button>
            )}
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-xl mb-2">
                  {selectedArticle.title}
                </CardTitle>
                <CardDescription className="flex items-center gap-4">
                  <span>{selectedArticle.source_name}</span>
                  <span>•</span>
                  <span>{formatDate(selectedArticle.published_date)}</span>
                  {selectedArticle.author && (
                    <>
                      <span>•</span>
                      <span>By {selectedArticle.author}</span>
                    </>
                  )}
                </CardDescription>
              </div>
              {selectedArticle.severity && (
                <Badge className={getSeverityColor(selectedArticle.severity)}>
                  {selectedArticle.severity}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {selectedArticle.summary && (
                <div>
                  <h3 className="font-semibold mb-2">Summary</h3>
                  <p className="text-gray-700 leading-relaxed">
                    {selectedArticle.summary}
                  </p>
                </div>
              )}

              {selectedArticle.content && (
                <div>
                  <h3 className="font-semibold mb-2">Content</h3>
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700">
                      {selectedArticle.content}
                    </div>
                  </div>
                </div>
              )}

              {selectedArticle.tags && selectedArticle.tags.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Tag className="h-4 w-4" />
                    Tags
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedArticle.tags.map((tag, index) => (
                      <Badge key={index} variant="outline">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedArticle.analysis_summary && (
                <div>
                  <h3 className="font-semibold mb-2">AI Analysis</h3>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-blue-900">
                      {selectedArticle.analysis_summary}
                    </p>
                  </div>
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
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search articles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-64"
            />
            <Button onClick={handleSearch} size="sm">
              <Search className="h-4 w-4" />
            </Button>
          </div>
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Security Articles
          </CardTitle>
          <CardDescription>
            {pagination.total} articles found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <FileText className="h-8 w-8 animate-pulse mx-auto mb-4" />
                <p className="text-gray-600">Loading articles...</p>
              </div>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Published</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {articles.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell>
                        <div className="max-w-md">
                          <h4 className="font-medium line-clamp-2">
                            {article.title}
                          </h4>
                          {article.summary && (
                            <p className="text-sm text-gray-500 line-clamp-1 mt-1">
                              {article.summary}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">{article.source_name}</span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm">
                          <Calendar className="h-3 w-3" />
                          {formatDate(article.published_date)}
                        </div>
                      </TableCell>
                      <TableCell>
                        {article.severity && (
                          <Badge className={getSeverityColor(article.severity)}>
                            {article.severity}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {article.analysis_status || 'pending'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => viewArticleDetails(article.id)}
                          >
                            <Eye className="h-3 w-3" />
                          </Button>
                          {article.url && (
                            <Button variant="outline" size="sm" asChild>
                              <a href={article.url} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-gray-600">
                    Showing {(pagination.page - 1) * pagination.limit + 1} to{' '}
                    {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                    {pagination.total} articles
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
    </div>
  )
}