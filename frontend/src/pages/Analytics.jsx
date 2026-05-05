import { useQuery } from '@tanstack/react-query'
import { BarChart3, Globe, BookOpen, TrendingUp, Users, Building } from 'lucide-react'
import { analyticsAPI } from '../services/api'
import { PageHeader, Card, Loading, ErrorState, StatCard } from '../components/common'
import { useState } from 'react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'

const COLORS = ['#0056D6', '#FF4203', '#0C8930', '#8B5CF6', '#FF9900', '#6593DC', '#ec4899', '#14b8a6']

export default function Analytics() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: analyticsAPI.getStats,
  })

  const { data: trends } = useQuery({
    queryKey: ['trends'],
    queryFn: analyticsAPI.getTrends,
  })

  const { data: docTypes } = useQuery({
    queryKey: ['docTypes'],
    queryFn: analyticsAPI.getDocumentTypes,
  })

  const { data: schoolComparison } = useQuery({
    queryKey: ['schoolComparison'],
    queryFn: analyticsAPI.getSchoolComparison,
  })

  const { data: geographic } = useQuery({
    queryKey: ['geographic'],
    queryFn: analyticsAPI.getGeographicCollaboration,
  })

  const { data: journals } = useQuery({
    queryKey: ['journals'],
    queryFn: () => analyticsAPI.getJournalAnalytics(15),
  })

  const { data: impact } = useQuery({
    queryKey: ['impact'],
    queryFn: () => analyticsAPI.getImpactMetrics('institution'),
  })

  const { data: citationDist } = useQuery({
    queryKey: ['citationDist'],
    queryFn: analyticsAPI.getCitationDistribution,
  })

  if (statsLoading) return <Loading message="Loading analytics..." />

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

  const schoolData = schoolComparison ? schoolComparison.schools.map((school, i) => ({
    name: school.length > 20 ? school.substring(0, 20) + '...' : school,
    publications: schoolComparison.publication_counts[i],
    citations: schoolComparison.citation_counts[i],
    faculty: schoolComparison.faculty_counts[i],
  })) : []

  const geoData = geographic ? geographic.countries.slice(0, 15).map((country, i) => ({
    name: country,
    collaborations: geographic.collaboration_counts[i],
  })) : []

  const journalData = journals ? journals.journals.slice(0, 10).map((journal, i) => ({
    name: journal.length > 30 ? journal.substring(0, 30) + '...' : journal,
    count: journals.counts[i],
  })) : []

  const citationData = citationDist ? citationDist.bins.map((bin, i) => ({
    range: bin,
    count: citationDist.counts[i],
  })) : []

  return (
    <div className="space-y-6">
      <PageHeader
        title="Research Analytics"
        subtitle="Metrics and visualizations"
        showBack
        showRefresh
      />

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Publications"
          value={stats?.total_publications?.toLocaleString() || '0'}
          icon={BookOpen}
        />
        <StatCard
          label="Total Citations"
          value={stats?.total_citations?.toLocaleString() || '0'}
          icon={TrendingUp}
        />
        <StatCard
          label="H-Index"
          value={impact?.h_index || '0'}
          icon={BarChart3}
        />
        <StatCard
          label="International %"
          value={`${geographic?.international_percentage?.toFixed(1) || '0'}%`}
          icon={Globe}
        />
      </div>

      {/* Impact Metrics */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Impact Metrics </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-primary-50 rounded-lg">
            <p className="text-2xl font-bold text-primary-600">{impact?.h_index || 0}</p>
            <p className="text-sm text-gray-600">H-Index</p>
          </div>
          <div className="text-center p-4 bg-success-50 rounded-lg">
            <p className="text-2xl font-bold text-success-600">{impact?.papers_in_top_10_percent || 0}</p>
            <p className="text-sm text-gray-600">Top 10% Papers</p>
          </div>
          <div className="text-center p-4 bg-warning-50 rounded-lg">
            <p className="text-2xl font-bold text-warning-600">{impact?.avg_citations_per_paper || 0}</p>
            <p className="text-sm text-gray-600">Avg. Citations per Paper</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-2xl font-bold text-purple-600">{impact?.papers_in_top_1_percent || 0}</p>
            <p className="text-sm text-gray-600">Top 1% Papers</p>
          </div>
        </div>
      </Card>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Publication Trends */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Publication Trends</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" stroke="#6b7280" tick={{ fontSize: 12 }} />
                <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="publications" stackId="1" stroke="#0056D6" fill="#0056D6" fillOpacity={0.6} name="Publications" />
                <Area type="monotone" dataKey="citations" stackId="2" stroke="#0C8930" fill="#0C8930" fillOpacity={0.6} name="Citations" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Document Types */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Document Type Distribution</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={docTypeData}
                  cx="35%"
                  cy="50%"
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  labelLine={false}
                  label={({ percent, cx, cy, midAngle, outerRadius }) => {
                    if (percent < 0.05) return null
                    const RADIAN = Math.PI / 180
                    const x = cx + (outerRadius + 16) * Math.cos(-midAngle * RADIAN)
                    const y = cy + (outerRadius + 16) * Math.sin(-midAngle * RADIAN)
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
                  wrapperStyle={{ fontSize: '12px', lineHeight: '22px', paddingLeft: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* School Comparison */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Publications by School</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={schoolData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="publications" fill="#0056D6" name="Publications" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* International Collaborations */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">International Collaborations</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={geoData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="collaborations" fill="#0C8930" name="Collaborations" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Charts Row 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Citation Distribution */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Citation Distribution</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={citationData} margin={{ bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} height={50} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8B5CF6" name="Papers" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {citationDist && (
            <div className="mt-4 flex justify-around text-sm">
              <div className="text-center">
                <p className="font-bold text-danger-500">{citationDist.uncited_count}</p>
                <p className="text-gray-500">Uncited Papers</p>
              </div>
              <div className="text-center">
                <p className="font-bold text-success-500">{citationDist.highly_cited_count}</p>
                <p className="text-gray-500">Highly Cited (100+)</p>
              </div>
            </div>
          )}
        </Card>

        {/* Top Journals */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Top Publication Venues</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={journalData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={180} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#FF9900" name="Publications" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Summary Stats Table */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Summary Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Year Range</p>
            <p className="font-semibold text-gray-900">{stats?.year_range || 'N/A'}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Total Authors</p>
            <p className="font-semibold text-gray-900">{stats?.total_authors?.toLocaleString() || 0}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Current Faculty</p>
            <p className="font-semibold text-gray-900">{stats?.total_current_faculty || 0}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Unique Keywords</p>
            <p className="font-semibold text-gray-900">{stats?.unique_keywords?.toLocaleString() || 0}</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
