import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Resolve a server-returned path (e.g. "/api/evaluation/uploads/…") to an absolute URL
// that works in both dev (Vite proxy) and prod (separate backend host).
export function resolveApiUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  if (/^https?:\/\//i.test(API_BASE_URL)) {
    // Strip any leading "/api" so we don't double it.
    const p = path.startsWith('/api/') ? path.slice(4) : path
    return API_BASE_URL.replace(/\/$/, '') + (p.startsWith('/') ? p : '/' + p)
  }
  return path
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.error || error.message || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

// Publications API
export const publicationsAPI = {
  getAll: (params) => api.get('/publications', { params }),
  getLatest: (limit = 50) => api.get('/publications/latest', { params: { limit } }),
  getById: (id) => api.get(`/publications/${id}`),
  getSimilar: (id, limit = 10) => api.get(`/publications/${id}/similar`, { params: { limit } }),
  getFilters: () => api.get('/publications/filters'),
}

// Authors API
export const authorsAPI = {
  search: (params) => api.get('/authors', { params }),
  getTop: (limit = 20, onlyFaculty = false) => 
    api.get('/authors/top', { params: { limit, only_faculty: onlyFaculty } }),
  getById: (id) => api.get(`/authors/${id}`),
  getCitations: (id) => api.get(`/authors/${id}/citations`),
  getSummary: (id) => api.get(`/authors/${id}/summary`),
  getAllFaculty: () => api.get('/authors/faculty/all'),
  getFacultyStats: () => api.get('/authors/faculty/stats'),
  getFacultyBySchool: (school) => api.get(`/authors/faculty/by-school/${school}`),
}

// Search API
export const searchAPI = {
  keywords: (keywords, useSemantic = true, maxResults = 100) =>
    api.get('/search/keywords', { params: { keywords, use_semantic: useSemantic, max_results: maxResults } }),
  semantic: (query, topK = 50) =>
    api.get('/search/semantic', { params: { query, top_k: topK } }),
  skills: (projectTitle, maxResults = 20) =>
    api.get('/search/skills', { params: { project_title: projectTitle, max_results: maxResults } }),
  autocomplete: (q, limit = 10) =>
    api.get('/search/autocomplete', { params: { q, limit } }),
}

// Thematic Areas API
export const thematicAPI = {
  getThemes: (onlyWithFaculty = true) =>
    api.get('/thematic/themes', { params: { only_with_faculty: onlyWithFaculty } }),
  getThemeDetails: (themeName) => api.get(`/thematic/themes/${themeName}`),
  getRankings: (theme, onlyFaculty = true, limit = 15) =>
    api.get('/thematic/rankings', { params: { theme, only_faculty: onlyFaculty, limit } }),
  getAllRankings: (onlyFaculty = true) =>
    api.get('/thematic/rankings/all', { params: { only_faculty: onlyFaculty } }),
  generateTeams: (themes, maxTeams = 5) =>
    api.post('/thematic/teams', { themes, max_teams: maxTeams }),
  getPopularCombinations: () => api.get('/thematic/teams/popular'),
  getStatistics: () => api.get('/thematic/statistics'),
  getAllDomains: () => api.get('/themes/all'),
}

// Analytics API
export const analyticsAPI = {
  getStats: () => api.get('/analytics/stats'),
  getTrends: () => api.get('/analytics/trends'),
  getDocumentTypes: () => api.get('/analytics/document-types'),
  getKeywords: (limit = 20) => api.get('/analytics/keywords', { params: { limit } }),
  getCollaborationNetwork: (minWeight = 2, maxNodes = 100) =>
    api.get('/analytics/collaboration/network', { params: { min_weight: minWeight, max_nodes: maxNodes } }),
  getGeographicCollaboration: () => api.get('/analytics/collaboration/geographic'),
  getSchoolComparison: () => api.get('/analytics/schools'),
  getJournalAnalytics: (limit = 20) => api.get('/analytics/journals', { params: { limit } }),
  getImpactMetrics: (entityType = 'institution', entityId = null) =>
    api.get('/analytics/impact', { params: { entity_type: entityType, entity_id: entityId } }),
  getThematicDistribution: () => api.get('/analytics/thematic-distribution'),
  getOpenAccess: () => api.get('/analytics/open-access'),
  getProductivity: () => api.get('/analytics/productivity'),
  getCitationDistribution: () => api.get('/analytics/citation-distribution'),
  getGrowthRate: () => api.get('/analytics/growth-rate'),
  getBenchmark: (schools = null) =>
    api.get('/analytics/benchmark', { params: { schools } }),
}

// RAG API
export const ragAPI = {
  analyze: (skills, maxContext = 20, structured = false, searchOnline = false, maxGlobalPapers = 10) =>
    api.post('/rag/analyze', { 
      skills, 
      max_context: maxContext, 
      structured,
      search_online: searchOnline,
      max_global_papers: maxGlobalPapers
    }),
  analyzeGet: (skills, maxContext = 20) =>
    api.get('/rag/analyze', { params: { skills: skills.join(','), max_context: maxContext } }),
  summarizeAuthor: (authorId) =>
    api.post('/rag/summarize-author', { author_id: authorId }),
  extractSkills: (projectTitle) =>
    api.post('/rag/extract-skills', null, { params: { project_title: projectTitle } }),
  getStatus: () => api.get('/rag/status'),
}

// Evaluation API
export const evaluationAPI = {
  // POC Projects
  getPocProjects: (authorId) => api.get(`/evaluation/poc/${authorId}`),
  addPocProject: (data) => api.post('/evaluation/poc', data),
  updatePocProject: (id, data) => api.put(`/evaluation/poc/${id}`, data),
  deletePocProject: (id) => api.delete(`/evaluation/poc/${id}`),
  
  // Funded Projects
  getFundedProjects: (authorId) => api.get(`/evaluation/funded/${authorId}`),
  addFundedProject: (data) => api.post('/evaluation/funded', data),
  updateFundedProject: (id, data) => api.put(`/evaluation/funded/${id}`, data),
  deleteFundedProject: (id) => api.delete(`/evaluation/funded/${id}`),
  
  // Index Score
  getIndexScore: (authorId) => api.get(`/evaluation/index/${authorId}`),
  updateIndexScore: (authorId, data) => api.post(`/evaluation/index/${authorId}`, data),
  
  // Extract Metadata
  extractMetadata: (title, description) =>
    api.post('/evaluation/extract-metadata', { title, description }),

  // Upload Project Document
  uploadDocument: (authorId, file, onUploadProgress) => {
    const formData = new FormData()
    formData.append('faculty_author_id', authorId)
    formData.append('file', file)
    return api.post('/evaluation/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    })
  },

  // Summary
  getSummary: (authorId) => api.get(`/evaluation/summary/${authorId}`),
}

// GitHub API
export const githubAPI = {
  connect: (authorId, accessToken) =>
    api.post('/github/connect', { access_token: accessToken }, { params: { faculty_author_id: authorId } }),
  connectByUsername: (authorId, username) =>
    api.post('/github/connect-public', { username }, { params: { faculty_author_id: authorId } }),
  suggest: (authorId) =>
    api.get('/github/suggest', { params: { faculty_author_id: authorId } }),
  disconnect: (authorId) =>
    api.post('/github/disconnect', null, { params: { faculty_author_id: authorId } }),
  getStatus: (authorId) =>
    api.get('/github/status', { params: { faculty_author_id: authorId } }),
  getRepositories: (authorId) =>
    api.get('/github/repositories', { params: { faculty_author_id: authorId } }),
  createProject: (authorId, repoId) =>
    api.post('/github/projects', { repo_id: repoId }, { params: { faculty_author_id: authorId } }),
  syncProject: (projectId) =>
    api.post(`/github/projects/${projectId}/sync`),
}

// Domains API
export const domainsAPI = {
  getAll: () => api.get('/domains/all'),
  getDynamic: () => api.get('/domains/dynamic'),
  detect: (text) => api.post('/domains/detect', { text }),
  createDynamic: (data) => api.post('/domains/dynamic', data),
  approveDynamic: (id) => api.post(`/domains/dynamic/${id}/approve`),
  deleteDynamic: (id) => api.delete(`/domains/dynamic/${id}`),
}

// Health API
export const healthAPI = {
  check: () => api.get('/health'),
}

export default api
