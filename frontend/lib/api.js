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
    // Transform frontend data to backend format
    const backendData = {
      name: sourceData.name,
      base_url: sourceData.url,
      source_type: sourceData.source_type,
      is_active: sourceData.is_active,
      scraping_config: {
        scraping_frequency: sourceData.scraping_frequency,
        description: sourceData.description || '',
        ...sourceData.scraping_config
      }
    }
    
    return this.request('/sources', {
      method: 'POST',
      body: JSON.stringify(backendData),
    })
  }

  async updateSource(sourceId, sourceData) {
    // Transform frontend data to backend format
    const backendData = {
      name: sourceData.name,
      base_url: sourceData.url,
      source_type: sourceData.source_type,
      is_active: sourceData.is_active,
      scraping_config: {
        scraping_frequency: sourceData.scraping_frequency,
        description: sourceData.description || '',
        ...sourceData.scraping_config
      }
    }
    
    return this.request(`/sources/${sourceId}`, {
      method: 'PUT',
      body: JSON.stringify(backendData),
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
    // Backend expects source_name, not source_id
    const payload = {
      source_name: sourceData.source_name || sourceData.name,
      job_type: 'manual'
    }
    
    return this.request('/scraping/trigger', {
      method: 'POST',
      body: JSON.stringify(payload),
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