import { useState } from 'react'
import { useQueryClient, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'
import {
  FileText, Users, Quote, GraduationCap, TrendingUp,
  Globe, ArrowRight, RotateCw
} from 'lucide-react'
import { analyticsAPI, publicationsAPI, authorsAPI } from '../services/api'
import {
  PageHeader, Card, StatCard, Loading, ErrorState, Badge, FacultyBadge
} from '../components/common'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'

const COLORS = ['#0056D6', '#FF4203', '#0C8930', '#8B5CF6', '#FF9900', '#6593DC']

export default function Dashboard() {
  const queryClient = useQueryClient()
  const [spinning, setSpinning] = useState(false)
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: analyticsAPI.getStats,
  })

  const handleRefresh = async () => {
    if (spinning) return
    setSpinning(true)
    try {
      await queryClient.invalidateQueries()
      toast.success('Refreshed', { id: 'page-refresh', duration: 1200 })
    } catch {
      toast.error('Refresh failed', { id: 'page-refresh' })
    } finally {
      setTimeout(() => setSpinning(false), 400)
    }
  }

  const { data: trends } = useQuery({
    queryKey: ['trends'],
    queryFn: analyticsAPI.getTrends,
  })

  const { data: latestPubs } = useQuery({
    queryKey: ['latestPubs'],
    queryFn: () => publicationsAPI.getLatest(5),
  })

  const { data: topAuthors } = useQuery({
    queryKey: ['topAuthors'],
    queryFn: () => authorsAPI.getTop(5, false),
  })

  const { data: docTypes } = useQuery({
    queryKey: ['docTypes'],
    queryFn: analyticsAPI.getDocumentTypes,
  })

  if (statsLoading) return <Loading message="Loading dashboard..." />
  if (statsError) return <ErrorState message={statsError.message} />

  // Prepare chart data
  const trendsData = trends ? trends.years.map((year, i) => ({
    year,
    publications: trends.publication_counts[i],
    citations: trends.citation_counts[i],
  })) : []

  const docTypeData = docTypes ? docTypes.types.map((type, i) => ({
    name: type,
    value: docTypes.counts[i],
  })) : []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="gradient-header rounded-2xl p-10 text-white text-center relative">
        <button
          onClick={handleRefresh}
          disabled={spinning}
          className="absolute top-4 right-4 inline-flex items-center justify-center w-9 h-9 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-60"
          title="Refresh dashboard"
        >
          <RotateCw size={18} className={clsx(spinning && 'animate-spin')} />
        </button>
        <img
          src="/sastra-logo.png"
          alt="SASTRA University Logo"
          className="h-full max-h-48 mx-auto object-contain"
        />
        <h1 className="text-3xl font-bold mt-5">SASTRA Research Finder</h1>
        <p className="text-primary-200 text-sm mt-1">SASTRA Deemed to be University</p>
        <p className="text-primary-100 text-lg mt-2">
          AI-powered research publication discovery platform
        </p>
        <div className="flex flex-wrap justify-center gap-4 mt-6">
          <Link to="/search" className="btn bg-white text-primary-700 hover:bg-primary-50">
            Start Searching
          </Link>
          <Link to="/analytics" className="btn bg-primary-500 text-white hover:bg-primary-400">
            View Analytics
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Total Publications"
          value={stats?.total_publications?.toLocaleString() || '0'}
          icon={FileText}
        />
        <StatCard
          label="Total Authors"
          value={stats?.total_authors?.toLocaleString() || '0'}
          icon={Users}
        />
        <StatCard
          label="Total Citations"
          value={stats?.total_citations?.toLocaleString() || '0'}
          icon={Quote}
        />
        <StatCard
          label="Current Faculty"
          value={stats?.total_current_faculty?.toLocaleString() || '0'}
          icon={GraduationCap}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Publication Trends */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Publication Trends</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#9ca3af" />
                <XAxis dataKey="year" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="publications"
                  stroke="#0056D6"
                  strokeWidth={2}
                  name="Publications"
                />
                <Line
                  type="monotone"
                  dataKey="citations"
                  stroke="#0C8930"
                  strokeWidth={2}
                  name="Citations"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Document Type Distribution */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Document Type Distribution</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={docTypeData}
                  cx="35%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  labelLine={false}
                  label={({ percent, cx, cy, midAngle, outerRadius }) => {
                    if (percent < 0.05) return null
                    const RADIAN = Math.PI / 180
                    const x = cx + (outerRadius + 14) * Math.cos(-midAngle * RADIAN)
                    const y = cy + (outerRadius + 14) * Math.sin(-midAngle * RADIAN)
                    return <text x={x} y={y} fill="#6b7280" fontSize={11} textAnchor="middle" dominantBaseline="central">{`${(percent * 100).toFixed(0)}%`}</text>
                  }}
                >
                  {docTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [value.toLocaleString(), name]} />
                <Legend
                  layout="vertical"
                  align="right"
                  verticalAlign="middle"
                  wrapperStyle={{ fontSize: '12px', lineHeight: '20px', paddingLeft: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Recent Publications & Top Authors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latest Publications */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Latest Publications</h3>
            <Link to="/publications" className="text-primary-600 hover:text-primary-700 text-sm flex items-center gap-1">
              View All <ArrowRight size={16} />
            </Link>
          </div>
          <div className="space-y-4">
            {latestPubs?.map((pub) => (
              <Link
                key={pub.pub_id}
                to={`/publications/${pub.pub_id}`}
                className="block p-4 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <h4 className="font-medium text-gray-900 line-clamp-2 mb-2">
                  {pub.title}
                </h4>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{pub.year}</span>
                  <span>{pub.citations} citations</span>
                  <Badge variant="gray">{pub.document_type}</Badge>
                </div>
              </Link>
            ))}
          </div>
        </Card>

        {/* Top Authors */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Top Authors</h3>
            <Link to="/authors" className="text-primary-600 hover:text-primary-700 text-sm flex items-center gap-1">
              View All <ArrowRight size={16} />
            </Link>
          </div>
          <div className="space-y-4">
            {topAuthors?.map((author, index) => (
              <Link
                key={author.author_id}
                to={`/authors/${author.author_id}`}
                className="flex items-center gap-4 p-4 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900 truncate">
                      {author.name}
                    </h4>
                    {author.is_current_faculty && <FacultyBadge />}
                  </div>
                  <p className="text-sm text-gray-500">
                    {author.pub_count} publications • {author.total_citations} citations
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </Card>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/teams" className="card p-6 hover:shadow-md transition-shadow">
          <Users className="text-primary-600 mb-4" size={32} />
          <h3 className="text-lg font-semibold mb-2">Team Builder</h3>
          <p className="text-gray-600 text-sm">
            Explore 100 research domains and build interdisciplinary faculty teams.
          </p>
        </Link>
        <Link to="/rag" className="card p-6 hover:shadow-md transition-shadow">
          <TrendingUp className="text-primary-600 mb-4" size={32} />
          <h3 className="text-lg font-semibold mb-2">AI Analysis</h3>
          <p className="text-gray-600 text-sm">
            Get AI-powered insights on research topics and experts.
          </p>
        </Link>
      </div>
    </div>
  )
}
