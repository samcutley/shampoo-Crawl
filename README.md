# Cybersecurity Intelligence Platform

A comprehensive threat intelligence platform that scrapes security blogs and DFIR reports, analyzes content with AI, and provides market intelligence for playbook updates.

## Features

### Backend (FastAPI)
- **SQLite Database**: Normalized schema with 9 tables for articles, IOCs, CVEs, threat actors, and more
- **AI Analysis**: OpenAI-compatible LLaMA integration for content analysis and IOC extraction
- **Parallel Scraping**: Multi-threaded scraping with error handling and retry logic
- **Background Workers**: Asynchronous processing for AI analysis tasks
- **Scheduler**: Automated scraping and maintenance tasks
- **REST API**: Comprehensive endpoints with pagination, search, and filtering
- **Configuration Management**: Pydantic models for type-safe configuration
- **Structured Logging**: JSON-formatted logs with context awareness

### Frontend (NextJS)
- **Dashboard**: Real-time system status, statistics, and quick actions
- **Articles Management**: Browse, search, and view detailed analysis of security articles
- **IOC Database**: Comprehensive indicators of compromise with filtering and export
- **Source Management**: CRUD operations for intelligence sources with scheduling
- **Modern UI**: Responsive design with Tailwind CSS and shadcn/ui components
- **Real-time Updates**: Live system status and data refresh capabilities

## Architecture

```
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes and endpoints
│   │   ├── core/              # Configuration and logging
│   │   ├── db/                # Database models and connection
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic services
│   │   ├── utils/             # Utility functions
│   │   └── workers/           # Background workers
│   ├── enhanced_crawler.py    # Main crawler script
│   └── requirements.txt       # Python dependencies
├── frontend/                  # NextJS frontend
│   ├── app/                   # App router pages
│   ├── components/            # Reusable UI components
│   ├── lib/                   # Utilities and API client
│   └── package.json           # Node.js dependencies
└── README.md                  # This file
```

## Database Schema

### Core Tables
- **sources**: Intelligence sources (RSS feeds, websites, APIs)
- **articles**: Scraped security articles and reports
- **iocs**: Indicators of compromise extracted from articles
- **cves**: CVE information and references
- **threat_actors**: Known threat actor profiles
- **campaigns**: Threat campaigns and operations
- **analysis_jobs**: AI analysis task tracking
- **tags**: Categorization and labeling system
- **article_tags**: Many-to-many relationship for article categorization

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- Local LLaMA server running on http://127.0.0.1:8081

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Initialize database
python -c "from app.db.database import init_db; init_db()"

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 12000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install

# Start the development server
npm run dev
```

### Running the Crawler
```bash
cd backend

# One-time scraping
python enhanced_crawler.py --mode scrape

# Start background workers
python enhanced_crawler.py --mode worker

# Start scheduler
python enhanced_crawler.py --mode scheduler

# Full system startup
python enhanced_crawler.py --mode all
```

## API Endpoints

### Articles
- `GET /api/articles` - List articles with pagination and search
- `GET /api/articles/{id}` - Get article details
- `POST /api/articles` - Create new article
- `PUT /api/articles/{id}` - Update article
- `DELETE /api/articles/{id}` - Delete article

### IOCs
- `GET /api/iocs` - List IOCs with filtering
- `GET /api/iocs/{id}` - Get IOC details
- `POST /api/iocs` - Create new IOC
- `PUT /api/iocs/{id}` - Update IOC
- `DELETE /api/iocs/{id}` - Delete IOC

### Sources
- `GET /api/sources` - List all sources
- `GET /api/sources/{id}` - Get source details
- `POST /api/sources` - Create new source
- `PUT /api/sources/{id}` - Update source
- `DELETE /api/sources/{id}` - Delete source

### Analysis
- `POST /api/analysis/trigger` - Trigger AI analysis
- `GET /api/analysis/stats` - Get analysis statistics
- `GET /api/analysis/jobs` - List analysis jobs

### System
- `GET /api/health` - Health check
- `GET /api/system/status` - System status and metrics

## Configuration

### Backend Configuration (app/core/config.py)
```python
DATABASE_URL = "sqlite:///./threat_intelligence.db"
LLAMA_SERVER_URL = "http://127.0.0.1:8081"
MAX_WORKERS = 4
SCRAPING_FREQUENCY = 3600  # seconds
LOG_LEVEL = "INFO"
```

### Frontend Configuration
- API base URL: `http://localhost:12000`
- Development server: `http://localhost:12001`

## Usage Examples

### Adding a New Source
```python
import requests

source_data = {
    "name": "KrebsOnSecurity",
    "url": "https://krebsonsecurity.com/feed/",
    "source_type": "rss",
    "is_active": True,
    "scraping_frequency": 3600,
    "description": "Security news and investigation"
}

response = requests.post("http://localhost:12000/api/sources", json=source_data)
```

### Triggering Analysis
```python
import requests

analysis_request = {
    "article_ids": [1, 2, 3],
    "analysis_type": "full"
}

response = requests.post("http://localhost:12000/api/analysis/trigger", json=analysis_request)
```

### Searching Articles
```python
import requests

params = {
    "search": "ransomware",
    "severity": "high",
    "page": 1,
    "limit": 20
}

response = requests.get("http://localhost:12000/api/articles", params=params)
```

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend linting
cd backend
flake8 app/
black app/

# Frontend linting
cd frontend
npm run lint
```

## Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Production Configuration
- Set environment variables for production
- Configure reverse proxy (nginx)
- Set up SSL certificates
- Configure log rotation
- Set up monitoring and alerting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `/docs` folder
- Review the API documentation at `/docs` when the server is running

## Roadmap

- [ ] Machine learning models for threat classification
- [ ] Integration with external threat intelligence feeds
- [ ] Advanced visualization and reporting
- [ ] Mobile application
- [ ] Multi-tenant support
- [ ] Advanced search with Elasticsearch
- [ ] Real-time notifications and alerts
- [ ] Export to STIX/TAXII formats