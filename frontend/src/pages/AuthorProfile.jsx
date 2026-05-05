import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Mail, Building, ClipboardList } from 'lucide-react'
import { authorsAPI } from '../services/api'
import { PageHeader, Card, Loading, ErrorState, Badge } from '../components/common'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'

const COLORS = ['#0056D6', '#FF4203', '#0C8930', '#8B5CF6', '#FF9900']

export default function AuthorProfile() {
  const { id } = useParams()
  const [imgError, setImgError] = useState(false)

  const { data: author, isLoading, error } = useQuery({
    queryKey: ['author', id],
    queryFn: () => authorsAPI.getById(id),
  })

  const { data: citations } = useQuery({
    queryKey: ['authorCitations', id],
    queryFn: () => authorsAPI.getCitations(id),
    enabled: !!id,
  })

  if (isLoading) return <Loading />
  if (error) return <ErrorState message={error.message} />
  if (!author) return <ErrorState message="Author not found" />

  // Prepare chart data
  const yearlyData = Object.entries(author.yearly_publications || {})
    .map(([year, count]) => ({
      year: parseInt(year),
      publications: count,
      citations: author.yearly_citations?.[year] || 0,
    }))
    .sort((a, b) => a.year - b.year)

  const citationData = citations?.bins?.map((bin, i) => ({
    name: bin,
    count: citations.counts[i],
  })) || []

  const countryData = Object.entries(author.country_collabs || {})
    .filter(([country]) => country.toLowerCase() !== 'india')
    .map(([country, count]) => ({ name: country, value: count }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)

  return (
    <div className="space-y-6">
      <PageHeader
        title={author.name || 'Author Profile'}
        subtitle={`Author ID: ${author.author_id}`}
        showBack
        showRefresh
      />

      {/* Profile Header */}
      <Card className="gradient-header text-white">
        <div className="flex flex-col md:flex-row gap-6">
          {author.faculty_info?.photo_url && !imgError ? (
            <img
              src={author.faculty_info.photo_url}
              alt={author.name}
              className="w-36 h-36 rounded-full object-cover border-4 border-white/30 bg-white/10"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="w-36 h-36 rounded-full bg-white/20 flex items-center justify-center text-5xl font-bold">
              {author.name?.charAt(0) || '?'}
            </div>
          )}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold">{author.name}</h1>
              {author.is_current_faculty && (
                <Badge className="bg-white/20 text-white">🎓 Current Faculty</Badge>
              )}
            </div>
            <p className="text-primary-100 mb-4">Author ID: {author.author_id}</p>

            {/* Faculty Info */}
            {author.faculty_info && (
              <div className="flex flex-wrap gap-4 text-sm text-primary-100">
                {author.faculty_info.department && (
                  <span className="flex items-center gap-1">
                    <Building size={14} />
                    {author.faculty_info.department}
                  </span>
                )}
                {author.faculty_info.school && (
                  <span>{author.faculty_info.school}</span>
                )}
                {author.faculty_info.email && (
                  <a href={`mailto:${author.faculty_info.email}`} className="flex items-center gap-1 hover:text-white">
                    <Mail size={14} />
                    {author.faculty_info.email}
                  </a>
                )}
                {author.is_current_faculty && (
                  <Link
                    to={`/faculty/${author.author_id}/evaluation`}
                    className="flex items-center gap-1 text-white hover:underline"
                  >
                    <ClipboardList size={14} />
                    Evaluation
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="text-center">
          <p className="text-3xl font-bold text-primary-600">{author.pub_count}</p>
          <p className="text-sm text-gray-500">Publications</p>
        </Card>
        <Card className="text-center">
          <p className="text-3xl font-bold text-primary-600">{author.total_citations}</p>
          <p className="text-sm text-gray-500">Citations</p>
        </Card>
        <Card className="text-center">
          <p className="text-3xl font-bold text-primary-600">{author.h_index}</p>
          <p className="text-sm text-gray-500">h-index</p>
        </Card>
        <Card className="text-center">
          <p className="text-3xl font-bold text-primary-600">{author.g_index}</p>
          <p className="text-sm text-gray-500">g-index</p>
        </Card>
        <Card className="text-center">
          <p className="text-3xl font-bold text-primary-600">{author.i10_index}</p>
          <p className="text-sm text-gray-500">i10-index</p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Publication Trends */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Publication Trends</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={yearlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="publications" stroke="#0056D6" strokeWidth={2} name="Publications" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Citation Distribution */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Citation Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={citationData} margin={{ bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} height={50} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#0056D6" name="Papers" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* International Collaborations */}
      {countryData.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">International Collaborations</h3>
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="h-64 flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={countryData}
                    cx="40%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    labelLine={false}
                  >
                    {countryData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value, name) => [`${value} papers`, name]} />
                  <Legend
                    layout="vertical"
                    align="right"
                    verticalAlign="middle"
                    wrapperStyle={{ fontSize: '12px', lineHeight: '20px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="lg:w-64">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-primary-50 rounded-lg">
                  <p className="text-2xl font-bold text-primary-600">{author.international_collabs}</p>
                  <p className="text-sm text-gray-600">International</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-600">{author.national_collabs}</p>
                  <p className="text-sm text-gray-600">National</p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Top Keywords */}
      {author.top_keywords?.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Research Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {author.top_keywords.map((kw, i) => (
              <Badge key={i} variant="primary" className="text-sm">
                {kw.keyword} ({kw.count})
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {/* Publications */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Publications ({author.publications?.length || 0})</h3>
        <div className="space-y-4 max-h-96 overflow-y-auto custom-scrollbar">
          {author.publications?.map((pub) => (
            <Link
              key={pub.pub_id}
              to={`/publications/${pub.pub_id}`}
              className="block p-4 rounded-lg border border-gray-100 hover:bg-gray-50"
            >
              <h4 className="font-medium text-gray-900 line-clamp-2">{pub.title}</h4>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span>{pub.year}</span>
                <span>{pub.citations} citations</span>
                <Badge variant="gray">{pub.author_position}</Badge>
              </div>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  )
}
