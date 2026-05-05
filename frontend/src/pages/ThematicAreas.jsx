import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Layers, Users, FileText, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react'
import { thematicAPI } from '../services/api'
import {
  PageHeader, Card, Loading, EmptyState,
  Badge, FacultyBadge, SearchInput
} from '../components/common'
import { useAppStore } from '../store'

export default function ThematicAreas() {
  const thematicState = useAppStore((s) => s.thematicState)
  const updateThematicState = useAppStore((s) => s.updateThematicState)
  const resetThematicState = useAppStore((s) => s.resetThematicState)

  const { search, selectedTheme, expandedDomains } = thematicState
  const setSearch = (v) => updateThematicState({ search: v })
  const setSelectedTheme = (v) => updateThematicState({ selectedTheme: v })
  const setExpandedDomains = (v) => updateThematicState({
    expandedDomains: typeof v === 'function' ? v(expandedDomains) : v
  })

  // Fetch domains with themes (grouped)
  const { data: domainsData, isLoading: domainsLoading } = useQuery({
    queryKey: ['domains'],
    queryFn: () => thematicAPI.getAllDomains(),
  })

  // Fallback to legacy themes if no domains
  const { data: themes, isLoading: themesLoading } = useQuery({
    queryKey: ['themesLegacy'],
    queryFn: () => thematicAPI.getThemes(true),
    enabled: !domainsData || domainsData?.length === 0,
  })

  const { data: statistics } = useQuery({
    queryKey: ['thematicStats'],
    queryFn: thematicAPI.getStatistics,
  })

  const { data: rankings, isLoading: rankingsLoading } = useQuery({
    queryKey: ['thematicRankings', selectedTheme],
    queryFn: () => thematicAPI.getRankings(selectedTheme, true, 15),
    enabled: !!selectedTheme,
  })

  const isLoading = domainsLoading || (themesLoading && !domainsData)

  const toggleDomain = (domainName) => {
    setExpandedDomains(prev => ({
      ...prev,
      [domainName]: !prev[domainName]
    }))
  }

  // Use domains if available
  const hasDomains = domainsData && domainsData.length > 0

  // Filter domains/themes by search
  const filteredDomains = hasDomains
    ? domainsData.map(domain => ({
        ...domain,
        themes: domain.themes.filter(t => 
          t.name.toLowerCase().includes(search.toLowerCase())
        )
      })).filter(d => d.themes.length > 0)
    : []

  const filteredThemes = themes?.themes?.filter(theme =>
    theme.toLowerCase().includes(search.toLowerCase())
  ) || []

  const themeStats = statistics?.find(s => s.theme_name === selectedTheme)

  if (isLoading) return <Loading message="Loading thematic areas..." />

  return (
    <div className="space-y-6">
      <PageHeader
        title="Thematic Areas"
        subtitle="Explore research domains and find experts"
        showBack
        showRefresh
        onRefresh={resetThematicState}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Theme List */}
        <div className="lg:col-span-1 space-y-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search themes..."
          />

          <Card className="max-h-[600px] overflow-y-auto custom-scrollbar">
            {hasDomains ? (
              // Grouped by domain
              <div className="space-y-2">
                {filteredDomains.map((domain) => (
                  <div key={domain.id || domain.name} className="border rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleDomain(domain.name)}
                      className="w-full flex items-center justify-between p-2 hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: domain.color }} />
                        <span className="font-medium text-sm">{domain.name}</span>
                      </div>
                      {expandedDomains[domain.name] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                    {expandedDomains[domain.name] && (
                      <div className="pl-4 pb-2">
                        {domain.themes.map((theme) => {
                          const stats = statistics?.find(s => s.theme_name === theme.name)
                          return (
                            <button
                              key={theme.id}
                              onClick={() => setSelectedTheme(theme.name)}
                              className={`w-full text-left p-2 rounded flex items-center justify-between ${
                                selectedTheme === theme.name ? 'bg-primary-50' : 'hover:bg-gray-50'
                              }`}
                            >
                              <span className="text-sm">{theme.name}</span>
                              {stats && <span className="text-xs text-gray-400">{stats.current_faculty_count}</span>}
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              // Legacy flat list
              <div className="space-y-1">
                {filteredThemes.map((theme) => {
                  const stats = statistics?.find(s => s.theme_name === theme)
                  return (
                    <button
                      key={theme}
                      onClick={() => setSelectedTheme(theme)}
                      className={`w-full text-left p-3 rounded-lg transition-colors flex items-center justify-between ${
                        selectedTheme === theme
                          ? 'bg-primary-50 text-primary-700'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div>
                        <span className="font-medium">{theme}</span>
                        {stats && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {stats.paper_count} papers • {stats.current_faculty_count} faculty
                          </p>
                        )}
                      </div>
                      <ChevronRight size={16} className="text-gray-400" />
                    </button>
                  )
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Theme Details */}
        <div className="lg:col-span-2">
          {selectedTheme ? (
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">{selectedTheme}</h3>
                <Link to={`/teams?theme=${encodeURIComponent(selectedTheme)}`} className="btn btn-secondary btn-sm">
                  Build Team
                </Link>
              </div>

              {themeStats && (
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-primary-600">{themeStats.paper_count}</p>
                    <p className="text-xs text-gray-500">Papers</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-primary-600">{themeStats.total_citations}</p>
                    <p className="text-xs text-gray-500">Citations</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-primary-600">{themeStats.author_count}</p>
                    <p className="text-xs text-gray-500">Authors</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-primary-600">{themeStats.current_faculty_count}</p>
                    <p className="text-xs text-gray-500">Faculty</p>
                  </div>
                </div>
              )}

              {/* Top Faculty */}
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Users size={18} /> Top Researchers
              </h4>
              
              {rankingsLoading ? (
                <Loading />
              ) : rankings?.authors?.length > 0 ? (
                <div className="space-y-3">
                  {rankings.authors.map((author, idx) => (
                    <Link
                      key={author.author_id}
                      to={`/authors/${author.author_id}`}
                      className="flex items-center gap-4 p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{author.primary_name}</p>
                        <p className="text-sm text-gray-500">{author.paper_count} papers • {author.total_cite_score.toLocaleString()} citations</p>
                      </div>
                      <FacultyBadge />
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No faculty found for this theme</p>
              )}
            </Card>
          ) : (
            <Card className="h-full flex items-center justify-center">
              <div className="text-center">
                <Layers className="mx-auto text-gray-300 mb-4" size={64} />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Theme</h3>
                <p className="text-gray-500">Choose a research theme from the list to view details and top researchers.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}