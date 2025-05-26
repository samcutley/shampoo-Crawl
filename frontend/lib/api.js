const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://work-1-reytgktxuoazkkrw.prod-runtime.all-hands.dev/api/v1'

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Sources
  async getSources() {
    return this.request('/sources')
  }

  async createSource(sourceData) {
    return this.request('/sources', {
      method: 'POST',
      body: JSON.stringify(sourceData),
    })
  }

  async updateSource(sourceId, sourceData) {
    return this.request(`/sources/${sourceId}`, {
      method: 'PUT',
      body: JSON.stringify(sourceData),
    })
  }

  async deleteSource(sourceId) {
    return this.request(`/sources/${sourceId}`, {
      method: 'DELETE',
    })
  }

  // Articles
  async getArticles(params = {}) {
    const queryString = new URLSearchParams(params).toString()
    return this.request(`/articles?${queryString}`)
  }

  async getArticle(articleId) {
    return this.request(`/articles/${articleId}`)
  }

  // IOCs
  async getIocs(params = {}) {
    const queryString = new URLSearchParams(params).toString()
    return this.request(`/iocs?${queryString}`)
  }

  // Analysis
  async getAnalysisStats() {
    return this.request('/analysis/stats')
  }

  // Scraping
  async triggerScraping(sourceData) {
    return this.request('/scraping/trigger', {
      method: 'POST',
      body: JSON.stringify(sourceData),
    })
  }

  async getScrapingJobs(params = {}) {
    const queryString = new URLSearchParams(params).toString()
    return this.request(`/scraping/jobs?${queryString}`)
  }

  // System
  async getSystemStatus() {
    return this.request('/system/status')
  }

  async getHealth() {
    // Health endpoint is not under /api/v1, it's directly on the root
    const url = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'https://work-1-reytgktxuoazkkrw.prod-runtime.all-hands.dev'
    const response = await fetch(`${url}/health`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  }

  // Search
  async search(query, contentType = 'all', limit = 50) {
    const params = new URLSearchParams({
      q: query,
      content_type: contentType,
      limit: limit.toString(),
    })
    return this.request(`/search?${params}`)
  }
}

export const apiClient = new ApiClient()