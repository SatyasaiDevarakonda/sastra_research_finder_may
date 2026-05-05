import { useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useSearchParams, Link } from 'react-router-dom'
import { Users2, X, Mail, Building, Sparkles, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { thematicAPI } from '../services/api'
import {
  PageHeader, Card, Loading, EmptyState,
  Badge, FacultyBadge
} from '../components/common'
import { useAppStore } from '../store'
import toast from 'react-hot-toast'

export default function TeamBuilder() {
  const [searchParams] = useSearchParams()
  const teamBuilderState = useAppStore((s) => s.teamBuilderState)
  const updateTeamBuilderState = useAppStore((s) => s.updateTeamBuilderState)
  const resetTeamBuilderState = useAppStore((s) => s.resetTeamBuilderState)

  const { selectedThemes, themeSearch, expandedDomains, generatedTeams } = teamBuilderState
  const setSelectedThemes = (v) => updateTeamBuilderState({
    selectedThemes: typeof v === 'function' ? v(selectedThemes) : v
  })
  const setThemeSearch = (v) => updateTeamBuilderState({ themeSearch: v })
  const setExpandedDomains = (v) => updateTeamBuilderState({
    expandedDomains: typeof v === 'function' ? v(expandedDomains) : v
  })

  // Fetch domains with themes (grouped)
  const { data: domainsData } = useQuery({
    queryKey: ['domains'],
    queryFn: () => thematicAPI.getAllDomains(),
  })

  // Fallback to legacy themes if no domains
  const { data: themes } = useQuery({
    queryKey: ['themesLegacy'],
    queryFn: () => thematicAPI.getThemes(true),
    enabled: !domainsData || domainsData?.length === 0,
  })

  const { data: statistics } = useQuery({
    queryKey: ['thematicStats'],
    queryFn: thematicAPI.getStatistics,
  })

  const { data: popular } = useQuery({
    queryKey: ['popularCombinations'],
    queryFn: thematicAPI.getPopularCombinations,
  })

  const { isLoading: teamsLoading, mutate: generateTeams, reset: resetTeams } = useMutation({
    mutationFn: (themes) => thematicAPI.generateTeams(themes, 5),
    onSuccess: (data) => {
      updateTeamBuilderState({ generatedTeams: data })
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate teams')
    },
  })

  const teams = generatedTeams

  const handleReset = () => {
    resetTeams()
    resetTeamBuilderState()
  }

  const handleNewTeam = handleReset

  useEffect(() => {
    const theme = searchParams.get('theme')
    if (theme && !selectedThemes.includes(theme)) {
      setSelectedThemes([theme])
    }
  }, [searchParams])

  const addTheme = (theme) => {
    if (!selectedThemes.includes(theme) && selectedThemes.length < 3) {
      setSelectedThemes([...selectedThemes, theme])
    }
  }

  const removeTheme = (theme) => {
    setSelectedThemes(selectedThemes.filter(t => t !== theme))
  }

  const handleGenerate = () => {
    if (selectedThemes.length >= 2) {
      generateTeams(selectedThemes)
    } else {
      toast.error('Please select at least 2 themes')
    }
  }

  const selectPopularCombination = (combo) => {
    setSelectedThemes(combo.themes)
    generateTeams(combo.themes)
  }

  const getThemeStats = (themeName) => {
    if (!statistics) return null
    return statistics.find(s => s.theme_name === themeName)
  }

  const toggleDomain = (domainName) => {
    setExpandedDomains(prev => ({
      ...prev,
      [domainName]: !prev[domainName]
    }))
  }

  // Use domains if available, otherwise use legacy themes
  const hasDomains = domainsData && domainsData.length > 0

  // Get all themes for search
  const allThemeNames = hasDomains
    ? domainsData.flatMap(d => d.themes.map(t => t.name))
    : (themes?.themes || [])

  // Filter themes by search
  const filteredThemeNames = allThemeNames.filter(t =>
    t.toLowerCase().includes(themeSearch.toLowerCase())
  )

  // Get filtered domains
  const filteredDomains = hasDomains
    ? domainsData.map(domain => ({
        ...domain,
        themes: domain.themes.filter(t => 
          t.name.toLowerCase().includes(themeSearch.toLowerCase())
        )
      })).filter(d => d.themes.length > 0)
    : []

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interdisciplinary Team Builder"
        subtitle="Build teams from current SASTRA faculty across research domains"
        showBack
        showRefresh
        onRefresh={handleReset}
      />

      {/* Selected Themes + Generate Bar */}
      <Card className="bg-primary-50 border-primary-200">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <Users2 className="text-primary-600 flex-shrink-0 hidden sm:block" size={24} />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-2">
              Selected Themes ({selectedThemes.length}/3)
            </h3>
            {selectedThemes.length === 0 ? (
              <p className="text-sm text-gray-600">
                Select 2-3 themes from the domains below to build teams.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {selectedThemes.map((theme) => (
                  <span key={theme} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-full text-sm font-medium text-primary-700 border border-primary-200">
                    {theme}
                    <button onClick={() => removeTheme(theme)} className="text-primary-400 hover:text-primary-700">
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={handleGenerate}
            disabled={selectedThemes.length < 2 || teamsLoading}
            className="btn btn-primary whitespace-nowrap disabled:opacity-50"
          >
            {teamsLoading ? 'Generating...' : 'Generate Teams'}
          </button>
        </div>
      </Card>

      {/* Generated Teams */}
      {teamsLoading ? (
        <Loading message="Generating teams..." />
      ) : teams && teams.teams?.length === 0 ? (
        <EmptyState title="No teams could be formed" description="Not enough faculty in selected themes" />
      ) : teams ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Generated Teams ({teams.teams.length})</h3>
              <p className="text-sm text-gray-500">Themes: {teams.themes.join(' + ')}</p>
            </div>
            <button onClick={handleNewTeam} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50">
              <RefreshCw size={15} /> New Team
            </button>
          </div>

          {teams.teams.map((team, index) => (
            <Card key={index} className="border-l-4 border-l-primary-500">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-lg">Team {team.team_number}</h4>
                <div className="flex gap-2">
                  {team.members[0]?.unified_score !== undefined && (
                    <Badge variant="purple">
                      Avg Score: {(team.members.reduce((sum, m) => sum + (m.unified_score || 0), 0) / team.members.length * 100).toFixed(1)}%
                    </Badge>
                  )}
                  <Badge variant="primary">{team.total_cite_score.toLocaleString()} citations</Badge>
                </div>
              </div>

              <div className="space-y-4">
                {team.members.map((member, i) => (
                  <div key={i} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                    <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold flex-shrink-0">
                      {member.name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Link to={`/authors/${member.author_id}`} className="font-semibold text-gray-900 hover:text-primary-600">
                          {member.name}
                        </Link>
                        <FacultyBadge />
                      </div>
                      <Badge variant="warning" className="mb-2">{member.theme}</Badge>
                      <p className="text-sm text-gray-500">{member.paper_count} papers • {member.cite_score.toLocaleString()} citations</p>
                      
                      {member.unified_score !== undefined && (
                        <div className="mt-2 flex items-center gap-2">
                          <span className="text-xs text-gray-500">Score:</span>
                          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500" style={{ width: `${Math.min(member.unified_score * 100, 100)}%` }} />
                          </div>
                          <span className="text-xs font-medium text-gray-700">{(member.unified_score * 100).toFixed(1)}%</span>
                        </div>
                      )}

                      {member.faculty_info && (
                        <div className="mt-2 text-sm text-gray-600">
                          <p className="flex items-center gap-1"><Building size={14} />{member.faculty_info.department} • {member.faculty_info.school}</p>
                          {member.faculty_info.email && (
                            <a href={`mailto:${member.faculty_info.email}`} className="flex items-center gap-1 text-primary-600 hover:text-primary-700">
                              <Mail size={14} />{member.faculty_info.email}
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      ) : null}

      {/* Domain/Theme Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Popular Combinations */}
        <div className="lg:col-span-2">
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">
              <Sparkles className="inline mr-2 text-warning-500" size={18} />
              Popular Combinations
            </h3>
            <div className="space-y-2">
              {popular?.combinations?.map((combo, i) => (
                <button
                  key={i}
                  onClick={() => selectPopularCombination(combo)}
                  className="w-full text-left p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xl">{combo.icon}</span>
                    <span className="font-medium text-gray-900">{combo.name}</span>
                  </div>
                  <p className="text-xs text-gray-500">{combo.themes.join(' + ')}</p>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Available Themes by Domain */}
        <div className="lg:col-span-3">
          <Card>
            <div className="mb-4">
              <input
                type="text"
                value={themeSearch}
                onChange={(e) => setThemeSearch(e.target.value)}
                placeholder="Search themes..."
                className="input w-full"
              />
            </div>

            <div className="max-h-[500px] overflow-y-auto custom-scrollbar space-y-2">
              {hasDomains ? (
                // Show grouped by domain
                filteredDomains.map((domain) => (
                  <div key={domain.id || domain.name} className="border rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleDomain(domain.name)}
                      className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100"
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: domain.color }} />
                        <span className="font-medium">{domain.name}</span>
                        <span className="text-xs text-gray-500">({domain.themes.length})</span>
                      </div>
                      {expandedDomains[domain.name] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    {expandedDomains[domain.name] && (
                      <div className="p-2 bg-white">
                        <div className="flex flex-wrap gap-2">
                          {domain.themes.map((theme) => {
                            const stats = getThemeStats(theme.name)
                            const isSelected = selectedThemes.includes(theme.name)
                            return (
                              <button
                                key={theme.id}
                                onClick={() => addTheme(theme.name)}
                                disabled={isSelected || selectedThemes.length >= 3}
                                className={`px-3 py-1.5 rounded-lg text-sm text-left transition-colors ${
                                  isSelected
                                    ? 'bg-primary-100 text-primary-700 border border-primary-300'
                                    : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                                }`}
                              >
                                {theme.name}
                                {stats && <span className="ml-1 text-xs text-gray-400">({stats.current_faculty_count})</span>}
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                // Legacy flat list
                <div className="flex flex-wrap gap-2">
                  {filteredThemeNames.slice(0, 50).map((theme) => {
                    const stats = getThemeStats(theme)
                    const isSelected = selectedThemes.includes(theme)
                    return (
                      <button
                        key={theme}
                        onClick={() => addTheme(theme)}
                        disabled={isSelected || selectedThemes.length >= 3}
                        className={`px-3 py-1.5 rounded-lg text-sm ${
                          isSelected ? 'bg-primary-100 text-primary-700' : 'bg-gray-50 hover:bg-gray-100'
                        }`}
                      >
                        {theme}
                        {stats && <span className="ml-1 text-xs text-gray-400">({stats.current_faculty_count})</span>}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}