import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { FileText, Calendar, Quote, ExternalLink, Filter, X } from 'lucide-react'
import { publicationsAPI } from '../services/api'
import {
  PageHeader, Card, Loading, ErrorState, EmptyState,
  Badge, SearchInput, Select, Pagination
} from '../components/common'
import { useAppStore } from '../store'

export default function Publications() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = parseInt(searchParams.get('page') || '1', 10)
  const search = searchParams.get('q') || ''

  const setPage = useCallback((p) => {
    setSearchParams((prev) => { prev.set('page', p.toString()); return prev }, { replace: true })
  }, [setSearchParams])

  const setSearch = useCallback((v) => {
    setSearchParams((prev) => {
      if (v) prev.set('q', v); else prev.delete('q')
      prev.set('page', '1')
      return prev
    }, { replace: true })
  }, [setSearchParams])

  const { searchFilters, setSearchFilters, clearSearchFilters } = useAppStore()
  const pageSize = 20

  const { data: filters } = useQuery({
    queryKey: ['filters'],
    queryFn: publicationsAPI.getFilters,
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['publications', page, pageSize, searchFilters, search],
    queryFn: () => publicationsAPI.getAll({
      page,
      page_size: pageSize,
      year: searchFilters.year,
      school: searchFilters.school,
      document_type: searchFilters.documentType,
      thematic_area: searchFilters.thematicArea,
      is_international: searchFilters.isInternational,
      search,
    }),
  })

  const totalPages = Math.ceil((data?.total || 0) / pageSize)
  const hasFilters = Object.values(searchFilters).some(v => v !== null)

  const handleReset = () => {
    clearSearchFilters()
    setSearchParams({}, { replace: true })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Publications"
        subtitle={`${data?.total?.toLocaleString() || 0} publications found`}
        showBack
        showRefresh
        onRefresh={handleReset}
      />

      {/* Filters */}
      <Card>
        <div className="flex flex-col lg:flex-row gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search publications..."
            className="lg:w-64"
          />

          <div className="flex flex-wrap gap-3 flex-1">
            <Select
              options={filters?.years?.map(y => ({ value: y, label: y.toString() })) || []}
              value={searchFilters.year}
              onChange={(v) => setSearchFilters({ year: v ? parseInt(v) : null })}
              placeholder="All Years"
              className="w-32"
            />

            <Select
              options={filters?.schools?.map(s => ({ value: s, label: s })) || []}
              value={searchFilters.school}
              onChange={(v) => setSearchFilters({ school: v })}
              placeholder="All Schools"
              className="w-48"
            />

            <Select
              options={filters?.document_types?.map(d => ({ value: d, label: d })) || []}
              value={searchFilters.documentType}
              onChange={(v) => setSearchFilters({ documentType: v })}
              placeholder="All Types"
              className="w-40"
            />

            <Select
              options={[
                { value: 'true', label: 'International' },
                { value: 'false', label: 'National' },
              ]}
              value={searchFilters.isInternational?.toString()}
              onChange={(v) => setSearchFilters({ isInternational: v === '' ? null : v === 'true' })}
              placeholder="Collaboration"
              className="w-40"
            />
          </div>

          {hasFilters && (
            <button
              onClick={clearSearchFilters}
              className="btn btn-outline btn-sm flex items-center gap-1"
            >
              <X size={16} /> Clear
            </button>
          )}
        </div>
      </Card>

      {/* Results */}
      {isLoading ? (
        <Loading message="Loading publications..." />
      ) : error ? (
        <ErrorState message={error.message} />
      ) : data?.results?.length === 0 ? (
        <EmptyState
          title="No publications found"
          description="Try adjusting your filters or search query"
        />
      ) : (
        <>
          <div className="space-y-4">
            {data?.results?.map((pub) => (
              <PublicationCard key={pub.pub_id} publication={pub} />
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

function PublicationCard({ publication: pub }) {
  return (
    <Card hover className="border-l-4 border-l-primary-500">
      <div className="space-y-3">
        {/* Title */}
        <Link
          to={`/publications/${pub.pub_id}`}
          className="text-lg font-semibold text-gray-900 hover:text-primary-600 line-clamp-2 block"
        >
          {pub.title}
        </Link>

        {/* Meta Info */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Calendar size={14} />
            {pub.year}
          </span>
          <span className="flex items-center gap-1">
            <Quote size={14} />
            {pub.citations} citations
          </span>
          <Badge variant="gray">{pub.document_type || 'Article'}</Badge>
          {pub.open_access && <Badge variant="success">Open Access</Badge>}
          {pub.is_international_collab && <Badge variant="primary">International</Badge>}
        </div>

        {/* Authors */}
        <p className="text-sm text-gray-600">
          <span className="font-medium">Authors:</span>{' '}
          {pub.authors?.substring(0, 200)}{pub.authors?.length > 200 ? '...' : ''}
        </p>

        {/* Abstract Preview */}
        {pub.abstract && (
          <p className="text-sm text-gray-600 line-clamp-2">
            {pub.abstract}
          </p>
        )}

        {/* Keywords and Links */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap gap-2">
            {pub.author_keywords?.slice(0, 5).map((kw, i) => (
              <Badge key={i} variant="primary">{kw}</Badge>
            ))}
            {pub.thematic_areas?.slice(0, 2).map((area, i) => (
              <Badge key={i} variant="warning">{area}</Badge>
            ))}
          </div>

          {pub.doi && (
            <a
              href={`https://doi.org/${pub.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 text-sm flex items-center gap-1"
            >
              <ExternalLink size={14} />
              View Paper
            </a>
          )}
        </div>
      </div>
    </Card>
  )
}
