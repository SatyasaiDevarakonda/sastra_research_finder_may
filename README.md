# SASTRA Research Finder v4.0

A professional, AI-powered research publication discovery platform for SASTRA Deemed University. Built with React + FastAPI, featuring SciVal-like analytics, semantic search, and interdisciplinary team formation.

![Version](https://img.shields.io/badge/version-4.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![React](https://img.shields.io/badge/react-18.2-blue)

## 🌟 Features

### Core Features
- **5,159+ Publications** - Comprehensive publication database
- **735 Faculty Members** - Current SASTRA faculty integration
- **50 Thematic Areas** - Research domain classification
- **FAISS Semantic Search** - AI-powered similarity matching

### Search Capabilities
- Keyword-based search with relevance scoring
- Semantic search using sentence-transformers
- Skill-based expert finder
- Real-time autocomplete

### Author & Faculty Management
- Complete author profiles with metrics (h-index, g-index, i10-index)
- Current faculty identification with department info
- Publication history and citation analysis
- International collaboration tracking

### Team Builder
- **Faculty-only teams** from current SASTRA staff
- Interdisciplinary team formation
- Popular combination templates
- Contact information integration

### Analytics (SciVal-like)
- Publication trends over time
- Citation distribution analysis
- School-wise comparisons
- International collaboration maps
- Journal analytics with quartile distribution
- Impact metrics (h-index, top percentile papers)

### AI-Powered Analysis (RAG)
- Skill extraction from project titles
- Research gap identification
- Expert recommendations
- Powered by Mistral AI

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│   Vercel Deployment • Vite • TailwindCSS • Recharts        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│   Railway/Render • Python 3.10+ • FAISS • Sentence-Trans   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                            │
│   SASTRA_Publications_2024-25.xlsx • Faculty-List.xlsx     │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
sastra-research-finder/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── core/          # Configuration
│   │   ├── models/        # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   ├── data/              # Excel data files
│   ├── main.py            # FastAPI entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── store/         # Zustand state
│   │   └── styles/        # TailwindCSS
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY (optional)

# Place data files in backend/data/
# - SASTRA_Publications_2024-25.xlsx
# - Faculty-List.xlsx

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Access the application at:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 📊 API Endpoints

### Publications
- `GET /api/publications` - List with filters
- `GET /api/publications/latest` - Recent publications
- `GET /api/publications/{id}` - Single publication
- `GET /api/publications/{id}/similar` - Similar papers

### Authors
- `GET /api/authors` - Search authors
- `GET /api/authors/top` - Top authors
- `GET /api/authors/{id}` - Author profile
- `GET /api/authors/faculty/all` - Current faculty

### Search
- `GET /api/search/keywords` - Keyword search
- `GET /api/search/semantic` - Semantic search
- `GET /api/search/skills` - Skill-based search

### Thematic Areas
- `GET /api/thematic/themes` - Available themes
- `GET /api/thematic/rankings` - Theme rankings
- `POST /api/thematic/teams` - Generate teams

### Analytics
- `GET /api/analytics/stats` - Summary stats
- `GET /api/analytics/trends` - Publication trends
- `GET /api/analytics/impact` - Impact metrics

### RAG Analysis
- `POST /api/rag/analyze` - AI analysis
- `POST /api/rag/extract-skills` - Skill extraction

## 🔧 Configuration

### Environment Variables

```env
# Backend (.env)
DEBUG=true
MISTRAL_API_KEY=your_api_key_here
PORT=8000

# Frontend (.env)
VITE_API_URL=/api
```

### Data Files

Place the following Excel files in `backend/data/`:

1. **SASTRA_Publications_2024-25.xlsx**
   - Required columns: Title, Authors, Author(s) ID, Year, Cited by, etc.

2. **Faculty-List.xlsx**
   - Required columns: Name, Email, Department, School

## 🚢 Deployment

### Backend (Railway/Render)

1. Connect your GitHub repository
2. Set environment variables
3. Deploy with:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Frontend (Vercel)

1. Connect your GitHub repository
2. Set build settings:
   - Build Command: `npm run build`
   - Output Directory: `dist`
3. Add environment variable:
   - `VITE_API_URL`: Your backend URL

## 🔒 Key Design Principles

1. **Faculty-Only Teams**: Team formation uses ONLY current SASTRA faculty
2. **Data Integrity**: Read-only from Excel, no manual modifications
3. **No Web Scraping**: All data from verified institutional datasets
4. **Performance**: FAISS indexing, pickle caching, lazy loading

## 📈 Features Roadmap

- [ ] MongoDB integration for persistent storage
- [ ] Real-time collaboration networks (D3.js)
- [ ] Geographic visualization (Mapbox)
- [ ] PDF export for reports
- [ ] Email notifications for collaboration requests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- SASTRA Deemed University for publication data
- Anthropic Claude for development assistance
- Mistral AI for RAG capabilities
