import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { Users, GraduationCap, FileText, Quote } from 'lucide-react'
import { authorsAPI, analyticsAPI } from '../services/api'
import {
  PageHeader, Card, Loading, ErrorState, EmptyState,
  SearchInput, Badge, FacultyBadge, Tabs, Pagination
} from '../components/common'

export default function Authors() {
  const [searchParams, setSearchParams] = useSearchParams()
  const search = searchParams.get('q') || ''
  const onlyFaculty = searchParams.get('faculty') === 'true'
  const page = parseInt(searchParams.get('page') || '1', 10)

  const setSearch = useCallback((v) => {
    setSearchParams((prev) => {
      if (v) prev.set('q', v); else prev.delete('q')
      prev.set('page', '1')
      return prev
    }, { replace: true })
  }, [setSearchParams])

  const setOnlyFaculty = useCallback((v) => {
    setSearchParams((prev) => {
      if (v) prev.set('faculty', 'true'); else prev.delete('faculty')
      prev.set('page', '1')
      return prev
    }, { replace: true })
  }, [setSearchParams])

  const setPage = useCallback((p) => {
    setSearchParams((prev) => { prev.set('page', p.toString()); return prev }, { replace: true })
  }, [setSearchParams])
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['authors', search, onlyFaculty],
    queryFn: () => {
      const isAuthorId = /^\d[\d.]*$/.test(search)
      return authorsAPI.search({
        ...(search ? (isAuthorId ? { author_id: search } : { name: search }) : {}),
        only_faculty: onlyFaculty,
        // Faculty tab needs all 735 faculty (Scopus-matched + file-only).
        // Name search also benefits from a higher cap.
        limit: onlyFaculty ? 2000 : 400,
      })
    },
  })

  const { data: facultyStats } = useQuery({
    queryKey: ['facultyStats'],
    queryFn: authorsAPI.getFacultyStats,
  })

  const { data: globalStats } = useQuery({
    queryKey: ['analyticsStats'],
    queryFn: analyticsAPI.getStats,
  })

  // Paginate results
  const startIndex = (page - 1) * pageSize
  const paginatedResults = data?.slice(startIndex, startIndex + pageSize) || []
  const totalPages = Math.ceil((data?.length || 0) / pageSize)

  const totalResearchers = globalStats?.total_authors || data?.length || 0

  const tabs = [
    { id: 'all', label: 'All Researchers', count: totalResearchers },
    { id: 'faculty', label: 'Current Faculty', count: facultyStats?.total_faculty },
  ]

  const handleReset = () => {
    setSearchParams({}, { replace: true })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Authors & Faculty"
        subtitle="Discover researchers and their publications"
        showBack
        showRefresh
        onRefresh={handleReset}
      />

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-gradient-to-br from-primary-50 to-white">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center">
              <Users className="text-primary-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{totalResearchers}</p>
              <p className="text-sm text-gray-500">Total Researchers</p>
            </div>
          </div>
        </Card>
        <Card className="bg-gradient-to-br from-success-50 to-white">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-success-50 flex items-center justify-center">
              <GraduationCap className="text-success-600" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{facultyStats?.total_faculty || 0}</p>
              <p className="text-sm text-gray-500">Current Faculty</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search by Author Id or Name"
            className="sm:w-96"
          />
          <Tabs
            tabs={tabs}
            activeTab={onlyFaculty ? 'faculty' : 'all'}
            onChange={(id) => setOnlyFaculty(id === 'faculty')}
          />
        </div>
      </Card>

      {/* Results */}
      {isLoading ? (
        <Loading message="Loading authors..." />
      ) : error ? (
        <ErrorState message={error.message} />
      ) : paginatedResults.length === 0 ? (
        <EmptyState
          title="No authors found"
          description="Try adjusting your search query"
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {paginatedResults.map((author) => (
              <AuthorCard key={author.author_id} author={author} />
            ))}
          </div>
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  )
}

function AuthorCard({ author }) {
  const [imgError, setImgError] = useState(false)

  return (
    <Link to={`/authors/${author.author_id}`}>
      <Card hover>
        <div className="flex items-start gap-4">
          {author.photo_url && !imgError ? (
            <img
              src={author.photo_url}
              alt={author.name}
              className="w-16 h-16 rounded-full object-cover flex-shrink-0 bg-primary-50"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold text-xl flex-shrink-0">
              {author.name?.charAt(0) || '?'}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-gray-900 truncate">{author.name}</h3>
              {author.is_current_faculty && <FacultyBadge />}
            </div>
            <p className="text-sm text-gray-500 mb-2">ID: {author.author_id}</p>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <FileText size={14} />
                {author.matching_papers || author.pub_count || 0} papers
              </span>
              <span className="flex items-center gap-1">
                <Quote size={14} />
                {author.total_citations || 0} citations
              </span>
            </div>
            {author.top_keywords?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {author.top_keywords.slice(0, 3).map((kw, i) => (
                  <Badge key={i} variant="gray">{kw}</Badge>
                ))}
              </div>
            )}
          </div>
        </div>
      </Card>
    </Link>
  )
}
