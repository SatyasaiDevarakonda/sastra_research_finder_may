import { useCallback, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { Search as SearchIcon, Sparkles, Users } from 'lucide-react'
import { searchAPI } from '../services/api'
import {
  PageHeader, Card, Loading, ErrorState, EmptyState,
  Badge, FacultyBadge
} from '../components/common'
import { useAppStore } from '../store'

function AuthorAvatar({ author }) {
  return (
    <div className="w-12 h-12 rounded-full overflow-hidden bg-primary-100 flex items-center justify-center flex-shrink-0 relative">
      <span className="text-primary-700 font-bold text-lg select-none">
        {author.name?.charAt(0) || '?'}
      </span>
      {author.photo_url && (
        <img
          src={author.photo_url}
          alt={author.name}
          className="absolute inset-0 w-full h-full object-cover"
          onError={(e) => { e.currentTarget.style.display = 'none' }}
        />
      )}
    </div>
  )
}

function AuthorList({ authors }) {
  if (!authors?.length) return <EmptyState title="No results" description="Try a different query" />
  return (
    <div className="space-y-3">
      {authors.slice(0, 30).map((author) => (
        <Link
          key={author.author_id}
          to={`/authors/${author.author_id}`}
          className="flex items-center gap-4 p-4 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
        >
          <AuthorAvatar author={author} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-gray-900">{author.name}</span>
              {author.is_current_faculty && <FacultyBadge />}
            </div>
            <p className="text-sm text-gray-500 mt-0.5">
              {author.matching_papers} matching papers &bull; {author.total_citations?.toLocaleString()} citations
            </p>
            {author.top_keywords?.length > 0 && (
              <div className="flex gap-1 mt-1 flex-wrap">
                {author.top_keywords.slice(0, 3).map((kw, i) => (
                  <Badge key={i} variant="gray">{kw}</Badge>
                ))}
              </div>
            )}
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-lg font-bold text-primary-600">
              {author.total_score?.toFixed(1)}
            </p>
            <p className="text-xs text-gray-500">relevance</p>
          </div>
        </Link>
      ))}
    </div>
  )
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = useAppStore((s) => s.searchPageState.query)
  const submittedQuery = useAppStore((s) => s.searchPageState.submittedQuery)
  const activeTab = useAppStore((s) => s.searchPageState.activeTab)
  const updateSearchPageState = useAppStore((s) => s.updateSearchPageState)
  const setQuery = (v) => updateSearchPageState({ query: v })

  const setActiveTab = useCallback((tab) => {
    updateSearchPageState({ activeTab: tab })
    setSearchParams((prev) => { prev.set('tab', tab); return prev }, { replace: true })
  }, [setSearchParams, updateSearchPageState])

  // If the URL has ?q= / ?tab= (deep link / refresh), hydrate the store from it once.
  useEffect(() => {
    const urlQuery = searchParams.get('q')
    const urlTab = searchParams.get('tab')
    const patch = {}
    if (urlQuery) {
      patch.query = urlQuery
      patch.submittedQuery = urlQuery
    }
    if (urlTab) patch.activeTab = urlTab
    if (Object.keys(patch).length) updateSearchPageState(patch)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['search', activeTab, submittedQuery],
    queryFn: () => {
      if (!submittedQuery.trim()) return null
      return searchAPI.keywords(submittedQuery, activeTab === 'ai')
    },
    enabled: !!submittedQuery.trim(),
  })

  const handleSearch = () => {
    if (query.trim()) {
      updateSearchPageState({ submittedQuery: query })
      setSearchParams((prev) => { prev.set('q', query); return prev }, { replace: true })
    }
  }

  const handleReset = () => {
    updateSearchPageState({ query: '', submittedQuery: '', activeTab: 'keyword' })
    setSearchParams({}, { replace: true })
  }

  const tabs = [
    { id: 'keyword', label: 'Keyword Search', icon: SearchIcon },
    { id: 'ai', label: 'AI-Powered Search', icon: Sparkles },
  ]

  const authors = data?.results || []

  return (
    <div className="space-y-6">
      <PageHeader
        title="Search"
        subtitle="Find publications, authors, and experts"
        showBack
        showRefresh
        onRefresh={handleReset}
      />

      {/* Search Card */}
      <Card>
        {/* Tabs */}
        <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit mb-6">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-white text-primary-700 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Input */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder={
                activeTab === 'ai'
                  ? 'Enter keywords or project title for AI-powered matching...'
                  : 'Enter keywords to search titles, abstracts, and keywords...'
              }
              className="input pl-10 pr-4"
            />
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          </div>
          <button onClick={handleSearch} className="btn btn-primary px-6">
            Search
          </button>
        </div>

        {/* Description */}
        <p className="mt-3 text-sm text-gray-500">
          {activeTab === 'keyword'
            ? 'Matches papers by exact and partial keywords in titles, abstracts, and author keywords.'
            : 'Uses AI semantic similarity matching to find conceptually related papers — even without exact keyword matches.'}
        </p>
      </Card>

      {/* Results */}
      {isLoading && <Loading message="Searching..." />}
      {error && <ErrorState message={error.message} />}

      {data && (
        <div className="space-y-4">
          {/* Summary bar */}
          <Card className="bg-primary-50 border-primary-200 py-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                <Users className="text-primary-600" size={20} />
              </div>
              <div>
                <p className="font-semibold text-gray-900">
                  {data.total || authors.length} researchers found
                </p>
                {data.keywords_used?.length > 0 && (
                  <p className="text-sm text-gray-600">
                    Keywords: {data.keywords_used.join(', ')}
                  </p>
                )}
              </div>
              {activeTab === 'ai' && (
                <span className="ml-auto flex items-center gap-1 text-xs text-primary-600 font-medium bg-primary-100 px-2 py-1 rounded-full">
                  <Sparkles size={12} />
                  AI-enhanced
                </span>
              )}
            </div>
          </Card>

          {/* Author list */}
          <Card>
            <h3 className="text-lg font-semibold mb-4">
              <Users className="inline mr-2" size={20} />
              Matching Researchers
            </h3>
            <AuthorList authors={authors} />
          </Card>
        </div>
      )}

      {!data && !isLoading && !error && (
        <Card className="text-center py-12">
          <SearchIcon className="mx-auto text-gray-300 mb-4" size={48} />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Start Searching</h3>
          <p className="text-gray-500">Enter a query above to find researchers and experts</p>
        </Card>
      )}
    </div>
  )
}
