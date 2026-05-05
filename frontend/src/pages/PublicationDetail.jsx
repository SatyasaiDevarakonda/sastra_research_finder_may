// Publication Detail Page
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Calendar, Quote, ExternalLink, Users } from 'lucide-react'
import { publicationsAPI } from '../services/api'
import { PageHeader, Card, Loading, ErrorState, Badge, FacultyBadge } from '../components/common'

export default function PublicationDetail() {
  const { id } = useParams()

  const { data: pub, isLoading, error } = useQuery({
    queryKey: ['publication', id],
    queryFn: () => publicationsAPI.getById(id),
  })

  const { data: similar } = useQuery({
    queryKey: ['similar', id],
    queryFn: () => publicationsAPI.getSimilar(id, 5),
    enabled: !!id,
  })

  if (isLoading) return <Loading />
  if (error) return <ErrorState message={error.message} />
  if (!pub) return <ErrorState message="Publication not found" />

  return (
    <div className="space-y-6">
      <PageHeader
        title="Publication Detail"
        showBack
        showRefresh
      />

      <Card>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">{pub.title}</h1>

        <div className="flex flex-wrap gap-4 mb-6 text-sm text-gray-600">
          <span className="flex items-center gap-1">
            <Calendar size={16} /> {pub.year}
          </span>
          <span className="flex items-center gap-1">
            <Quote size={16} /> {pub.citations} citations
          </span>
          <Badge variant="gray">{pub.document_type}</Badge>
          {pub.open_access && <Badge variant="success">Open Access</Badge>}
          {pub.is_international_collab && <Badge variant="primary">International Collaboration</Badge>}
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Authors</h3>
            <p className="text-gray-700">{pub.authors}</p>
          </div>

          {pub.abstract && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Abstract</h3>
              <p className="text-gray-700 leading-relaxed">{pub.abstract}</p>
            </div>
          )}

          {pub.author_keywords?.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Keywords</h3>
              <div className="flex flex-wrap gap-2">
                {pub.author_keywords.map((kw, i) => (
                  <Badge key={i} variant="primary">{kw}</Badge>
                ))}
              </div>
            </div>
          )}

          {pub.thematic_areas?.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Research Areas</h3>
              <div className="flex flex-wrap gap-2">
                {pub.thematic_areas.map((area, i) => (
                  <Badge key={i} variant="warning">{area}</Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-4 pt-4">
            {pub.doi && (
              <a
                href={`https://doi.org/${pub.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                <ExternalLink size={16} className="mr-2" />
                View Full Paper
              </a>
            )}
          </div>
        </div>
      </Card>

      {similar?.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Similar Publications</h3>
          <div className="space-y-3">
            {similar.map((s) => (
              <Link
                key={s.pub_id}
                to={`/publications/${s.pub_id}`}
                className="block p-3 rounded-lg border border-gray-100 hover:bg-gray-50"
              >
                <h4 className="font-medium text-gray-900 line-clamp-2">{s.title}</h4>
                <p className="text-sm text-gray-500 mt-1">
                  {s.year} • {s.citations} citations
                </p>
              </Link>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
