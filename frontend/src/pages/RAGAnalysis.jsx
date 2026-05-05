import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Brain, Sparkles, AlertCircle, CheckCircle, ExternalLink, FileText, Users, Globe, File, Loader2, Check } from 'lucide-react'
import { ragAPI } from '../services/api'
import { PageHeader, Card, ErrorState, Badge } from '../components/common'
import { useAppStore } from '../store'
import toast from 'react-hot-toast'

export default function RAGAnalysis() {
  const ragState = useAppStore((s) => s.ragState)
  const updateRagState = useAppStore((s) => s.updateRagState)
  const resetRagState = useAppStore((s) => s.resetRagState)

  const { projectTitle, skills, searchOnline, analysisResult } = ragState

  const setProjectTitle = (v) => updateRagState({ projectTitle: v })
  const setSkills = (v) => updateRagState({ skills: v })
  const setSearchOnline = (v) => updateRagState({ searchOnline: v })

  const { data: status } = useQuery({
    queryKey: ['ragStatus'],
    queryFn: ragAPI.getStatus,
  })

  const extractMutation = useMutation({
    mutationFn: (title) => ragAPI.extractSkills(title),
    onSuccess: (data) => {
      updateRagState({ skills: data.skills?.join(', ') || '' })
      toast.success('Skills extracted successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to extract skills')
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: ({ skills, searchOnline, maxGlobalPapers }) => {
      const skillArray = Array.isArray(skills) ? skills : (skills || '').split(',').filter(s => s.trim())
      return ragAPI.analyze(skillArray, 20, true, searchOnline, maxGlobalPapers)
    },
    onSuccess: (data) => {
      updateRagState({ analysisResult: data })
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to analyze')
    },
  })

  const handleExtract = () => {
    if (projectTitle.trim()) {
      extractMutation.mutate(projectTitle)
    }
  }

  const handleAnalyze = () => {
    const skillList = (skills || '').split(',').filter(s => s.trim())
    if (skillList.length === 0) {
      toast.error('Please enter skills first')
      return
    }
    analyzeMutation.mutate({
      skills: skillList,
      searchOnline,
      maxGlobalPapers: 10,
    })
  }

  const removeSkill = (index) => {
    const skillList = skills.split(',').filter(s => s.trim())
    skillList.splice(index, 1)
    updateRagState({ skills: skillList.join(', ') })
  }

  const handleReset = () => {
    extractMutation.reset()
    analyzeMutation.reset()
    resetRagState()
  }

  const skillList = skills.split(',').filter(s => s.trim())
  // Prefer the persisted result from the store; fall back to the live mutation result
  // (covers the initial render after a successful mutation before the store roundtrip).
  const result = analysisResult || analyzeMutation.data
  const hasResult = !!(result && (result.sastra_papers?.length || result.global_papers?.length || result.structured_analysis || result.analysis))

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI-Powered Research Analysis"
        subtitle="Use Mistral AI to analyze research topics and find experts"
        showBack
        showRefresh
        onRefresh={handleReset}
      />

      <Card className={status?.available
        ? 'bg-success-50 border-success-200'
        : 'bg-warning-50 border-warning-200'
      }>
        <div className="flex items-center gap-4">
          {status?.available ? (
            <CheckCircle className="text-success-600" size={24} />
          ) : (
            <AlertCircle className="text-warning-600" size={24} />
          )}
          <div>
            <h3 className="font-semibold text-gray-900">
              {status?.available ? 'Mistral AI Connected' : 'Mistral AI Not Configured'}
            </h3>
            <p className="text-sm text-gray-600">
              {status?.available
                ? `Model: ${status.model}`
                : 'Add MISTRAL_API_KEY to environment variables to enable AI analysis'}
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Section */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">
              <Brain className="inline mr-2" size={20} />
              Step 1: Enter Project Title
            </h3>
            <textarea
              value={projectTitle}
              onChange={(e) => setProjectTitle(e.target.value)}
              placeholder="e.g., Deep learning for medical image segmentation"
              className="input min-h-24"
            />
            <button
              onClick={handleExtract}
              disabled={!projectTitle.trim() || extractMutation.isPending}
              className="btn btn-primary mt-3 w-full"
            >
              {extractMutation.isPending ? 'Extracting...' : 'Auto-Extract Skills'}
            </button>
          </Card>

          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">
              <Sparkles className="inline mr-2 text-warning-500" size={20} />
              Step 2: Skills (comma-separated)
            </h3>
            <textarea
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="machine learning, deep learning, cnn..."
              className="input min-h-24"
            />
            {skillList.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-3">
                {skillList.map((skill, i) => (
                  <Badge key={i} variant="primary" className="text-xs flex items-center gap-1">
                    {skill.trim()}
                    <button onClick={() => removeSkill(i)} className="ml-1 hover:text-red-500">×</button>
                  </Badge>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">Step 3: Generate Analysis</h3>
            <div className="flex items-center gap-2 mb-3">
              <input
                type="checkbox"
                id="searchOnline"
                checked={searchOnline}
                onChange={(e) => setSearchOnline(e.target.checked)}
                className="w-4 h-4 text-primary-600"
              />
              <label htmlFor="searchOnline" className="text-sm text-gray-700 flex items-center gap-1">
                <Globe size={14} /> Also search global web for related papers
              </label>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={skillList.length === 0 || analyzeMutation.isPending || !status?.available}
              className="btn btn-primary w-full disabled:opacity-50"
            >
              {analyzeMutation.isPending ? 'Generating Analysis...' : 'Generate Analysis'}
            </button>
            <p className="text-xs text-gray-500 mt-2">
              Returns key methods, research gaps, trends, SASTRA papers and global references in one report.
            </p>
          </Card>
        </div>

        {/* Results Section */}
        <div className="lg:col-span-2">
          {analyzeMutation.isPending ? (
            <AnalysisProgress searchOnline={searchOnline} />
          ) : result?.error && !hasResult ? (
            <Card className="h-full"><ErrorState message={result.error} /></Card>
          ) : hasResult ? (
            <UnifiedResults data={result} />
          ) : (
            <Card className="h-full flex items-center justify-center text-center p-8 min-h-96">
              <div>
                <Brain className="mx-auto text-gray-300 mb-4" size={64} />
                <h3 className="text-lg font-medium text-gray-900 mb-2">AI Research Analysis</h3>
                <p className="text-gray-500 max-w-md">
                  Enter a project title, extract skills, and generate analysis to get AI-powered insights.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

function UnifiedResults({ data }) {
  const papers = data.sastra_papers || []
  const globalPapers = data.global_papers || []
  const analysis = data.structured_analysis
  const hasInsights = !!(analysis && (
    (analysis.key_methods?.length || 0) +
    (analysis.research_gaps?.length || 0) +
    (analysis.emerging_trends?.length || 0) +
    (analysis.collaboration_insights?.length || 0) > 0
  ))

  return (
    <div className="space-y-6">
      {/* 1) Detailed Analysis Report (top) */}
      {data.analysis && (
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4 pb-2 border-b">
            Detailed Analysis Report
          </h3>
          <div
            className="prose prose-sm max-w-none text-gray-700 space-y-2"
            dangerouslySetInnerHTML={{ __html: formatAnalysis(data.analysis) }}
          />
          {data.context_count > 0 && (
            <div className="mt-4 pt-4 border-t text-sm text-gray-500">
              Based on {data.context_count} publications from SASTRA database
            </div>
          )}
        </Card>
      )}

      {/* 2) Research Insights highlight (compact summary cards) */}
      {hasInsights && (
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">Research Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysis.key_methods?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-primary-600 mb-2 flex items-center gap-1">
                  <Sparkles size={14} /> Key Methods
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {analysis.key_methods.slice(0, 5).map((m, i) => <li key={i}>• {m}</li>)}
                </ul>
              </div>
            )}
            {analysis.research_gaps?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-warning-600 mb-2 flex items-center gap-1">
                  <AlertCircle size={14} /> Research Gaps
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {analysis.research_gaps.slice(0, 5).map((g, i) => <li key={i}>• {g}</li>)}
                </ul>
              </div>
            )}
            {analysis.emerging_trends?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-success-600 mb-2 flex items-center gap-1">
                  <Brain size={14} /> Emerging Trends
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {analysis.emerging_trends.slice(0, 5).map((t, i) => <li key={i}>• {t}</li>)}
                </ul>
              </div>
            )}
            {analysis.collaboration_insights?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-info-600 mb-2 flex items-center gap-1">
                  <Users size={14} /> Collaboration Insights
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {analysis.collaboration_insights.slice(0, 5).map((c, i) => <li key={i}>• {c}</li>)}
                </ul>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* 3) SASTRA papers — numbered */}
      <Card>
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText size={20} />
          SASTRA Papers ({papers.length})
        </h3>
        <div className="space-y-3">
          {papers.map((paper, i) => (
            <PaperCard key={`sastra-${i}`} index={i + 1} paper={paper} />
          ))}
          {papers.length === 0 && (
            <p className="text-gray-500 text-center py-4">No SASTRA papers matched these skills.</p>
          )}
        </div>
      </Card>

      {/* 4) Global research papers — numbered */}
      {globalPapers.length > 0 && (
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Globe size={20} />
            Global Research Papers ({globalPapers.length})
          </h3>
          <div className="space-y-3">
            {globalPapers.map((paper, i) => (
              <PaperCard key={`global-${i}`} index={i + 1} paper={paper} />
            ))}
          </div>
        </Card>
      )}

      {data.error && (
        <Card className="bg-warning-50 border-warning-200">
          <p className="text-sm text-warning-700">{data.error}</p>
        </Card>
      )}
    </div>
  )
}

function PaperCard({ paper, index }) {
  // Prefer the canonical paper page; fall back to PDF link only if nothing else is available.
  const primaryHref = paper.link || paper.pdf_link || ''
  const isPdf = primaryHref && primaryHref.toLowerCase().endsWith('.pdf')

  return (
    <div className="p-3 border rounded-lg hover:bg-gray-50 transition-colors flex gap-3">
      {typeof index === 'number' && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary-50 text-primary-700 text-xs font-semibold flex items-center justify-center">
          {index}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start gap-2">
          <h4 className="font-medium text-gray-900 text-sm line-clamp-2 flex-1">{paper.title}</h4>
          {primaryHref && (
            <a
              href={primaryHref}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 flex-shrink-0"
              title={isPdf ? 'Open PDF' : 'Open paper'}
            >
              {isPdf ? <File size={16} /> : <ExternalLink size={16} />}
            </a>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">{paper.authors}</p>
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <Badge variant="gray" className="text-xs">{paper.year || 'N/A'}</Badge>
          {paper.citations > 0 && (
            <Badge variant="info" className="text-xs">{paper.citations} citations</Badge>
          )}
          {paper.venue && (
            <Badge variant="gray" className="text-xs">{paper.venue}</Badge>
          )}
          <Badge variant={paper.source === 'SASTRA' ? 'primary' : 'info'} className="text-xs">
            {paper.source || 'SASTRA'}
          </Badge>
        </div>
      </div>
    </div>
  )
}

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

// Step-based progress for the RAG analysis call. The backend is synchronous
// so we can't receive real progress events — instead we simulate a ramp that
// mirrors the actual phases and caps at 95% while waiting. If the request
// comes back sooner, we jump to Done. If it runs longer, the bar idles at 95%.
function AnalysisProgress({ searchOnline }) {
  const steps = [
    { key: 'sastra',  label: 'Searching SASTRA publications',     target: 18 },
    ...(searchOnline ? [{ key: 'global', label: 'Fetching global research papers', target: 38 }] : []),
    { key: 'llm',     label: 'Analyzing with Mistral AI',          target: 85 },
    { key: 'format',  label: 'Formatting results',                 target: 95 },
  ]
  const [progress, setProgress] = useState(0)
  const [stepIdx, setStepIdx] = useState(0)
  const maxCap = 95
  // Typical total latency: ~12–25s depending on Mistral + global search.
  // Ramp at ~3.3% / sec so a healthy run reaches ~90% at ~27s.
  const tickMs = 120
  const perTick = 0.4

  useEffect(() => {
    const id = setInterval(() => {
      setProgress(p => {
        const next = Math.min(p + perTick, maxCap)
        // Advance step when we pass its target threshold
        setStepIdx(idx => {
          if (idx < steps.length - 1 && next >= steps[idx].target) return idx + 1
          return idx
        })
        return next
      })
    }, tickMs)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <Card className="h-full flex items-center justify-center min-h-96">
      <div className="w-full max-w-md px-6">
        <div className="flex items-center justify-center mb-5">
          <div className="relative">
            <Brain className="text-primary-500 animate-pulse" size={44} />
            <div className="absolute -bottom-1 -right-1 bg-white rounded-full p-0.5">
              <Loader2 className="text-primary-600 animate-spin" size={14} />
            </div>
          </div>
        </div>

        {/* Bar */}
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full transition-[width] duration-200 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-500">
          <span>{Math.round(progress)}%</span>
          <span>Please wait</span>
        </div>

        {/* Step list */}
        <ul className="mt-5 space-y-2">
          {steps.map((s, i) => {
            const status = i < stepIdx ? 'done' : i === stepIdx ? 'active' : 'pending'
            return (
              <li key={s.key} className="flex items-center gap-2 text-sm">
                {status === 'done' && (
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-success-100 text-success-600">
                    <Check size={12} />
                  </span>
                )}
                {status === 'active' && (
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-100 text-primary-600">
                    <Loader2 className="animate-spin" size={12} />
                  </span>
                )}
                {status === 'pending' && (
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded-full border border-gray-300 text-gray-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />
                  </span>
                )}
                <span className={
                  status === 'done' ? 'text-gray-500 line-through' :
                  status === 'active' ? 'text-gray-900 font-medium' :
                  'text-gray-400'
                }>
                  {s.label}
                </span>
              </li>
            )
          })}
        </ul>

        <p className="mt-5 text-center text-xs text-gray-500">
          Mistral responses can take 10–30 seconds depending on the topic.
        </p>
      </div>
    </Card>
  )
}

// Strip trailing punctuation/brackets that the LLM often glues onto a URL.
function cleanUrl(url) {
  let u = url
  // Strip trailing characters that are never part of a real URL path
  u = u.replace(/[.,;:!?\]\)]+$/, '')
  // Fix HTML-entity-escaped ampersands inside query strings (already escaped earlier)
  return u
}

function formatInline(s) {
  // Escape first, then apply inline formatting so we don't double-encode entities.
  let out = escapeHtml(s)

  // 1. Linked quoted paper title:  "Title" [LINK: https://...]
  out = out.replace(
    /&quot;([^&]+?)&quot;\s*\[LINK:\s*(https?:\/\/[^\]\s]+?)\]/g,
    (_m, title, url) => {
      const clean = cleanUrl(url)
      return `<a href="${clean}" target="_blank" rel="noopener noreferrer" class="text-primary-600 hover:underline font-medium">"${title}"</a>`
    }
  )
  // Strip "[LINK: N/A]"
  out = out.replace(/\s*\[LINK:\s*N\/A\]/g, '')
  // Strip dangling trailing ids: "Title 12345678"
  out = out.replace(/&quot;([^&]+?)\s+\d{8,}&quot;/g, '&quot;$1&quot;')

  // 2. Markdown links [text](url)
  out = out.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    (_m, text, url) => {
      const clean = cleanUrl(url)
      return `<a href="${clean}" target="_blank" rel="noopener noreferrer" class="text-primary-600 hover:underline">${text}</a>`
    }
  )

  // 3. Plain URLs → links (stop at whitespace, <, ), ], common trailing punctuation).
  //    Character-class is tight so two back-to-back URLs don't merge.
  out = out.replace(
    /(https?:\/\/[^\s<>\[\]()]+)(?![^<]*<\/a>)/g,
    (_m, url) => {
      const clean = cleanUrl(url)
      return `<a href="${clean}" target="_blank" rel="noopener noreferrer" class="text-primary-600 hover:underline break-all">${clean}</a>`
    }
  )

  // 4. "owner/repo" GitHub shorthand → real link. Only fire when the segment
  //    looks like a repo path (short, ASCII, single slash, no dots in final
  //    segment except . _ -). Skip if already inside an <a>.
  out = out.replace(
    /(^|[\s(])([A-Za-z0-9][A-Za-z0-9_.-]{0,38})\/([A-Za-z0-9][A-Za-z0-9_.-]{0,99})(?=[\s,.;)\]]|$)(?![^<]*<\/a>)/g,
    (m, pre, owner, repo) => {
      // Filter common false positives
      const lower = `${owner}/${repo}`.toLowerCase()
      if (/\.(com|org|net|io|ai|co|edu|gov)$/.test(lower)) return m
      if (/^\d+\/\d+$/.test(`${owner}/${repo}`)) return m // dates/fractions
      const url = `https://github.com/${owner}/${repo}`
      return `${pre}<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-primary-600 hover:underline">${owner}/${repo}</a>`
    }
  )

  // Bold **x** and italic *x*
  out = out.replace(/\*\*([^*]+?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
  out = out.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, '$1<em>$2</em>')

  // Inline code `x`
  out = out.replace(/`([^`]+?)`/g, '<code class="bg-gray-100 px-1 rounded text-xs">$1</code>')

  // Highlight Author IDs
  out = out.replace(/AUTHOR_ID:\s*([A-Za-z0-9_-]+)/g,
    '<code class="bg-primary-50 text-primary-700 px-1 rounded text-xs">$1</code>')

  return out
}

function formatAnalysis(text) {
  if (!text) return ''

  const lines = text.split(/\r?\n/)
  const out = []
  let listType = null // 'ul' | 'ol' | null

  const closeList = () => {
    if (listType) {
      out.push(`</${listType}>`)
      listType = null
    }
  }
  const openList = (type) => {
    if (listType !== type) {
      closeList()
      const cls = type === 'ul'
        ? 'list-disc pl-6 space-y-1 text-gray-700'
        : 'list-decimal pl-6 space-y-1 text-gray-700'
      out.push(`<${type} class="${cls}">`)
      listType = type
    }
  }

  for (let rawLine of lines) {
    const line = rawLine.trimEnd()
    const trimmed = line.trim()

    // Blank line → close lists, add spacer
    if (!trimmed) {
      closeList()
      continue
    }

    // Horizontal rule
    if (/^-{3,}$|^_{3,}$|^\*{3,}$/.test(trimmed)) {
      closeList()
      out.push('<hr class="my-4 border-gray-200" />')
      continue
    }

    // Headings: ##, ###, #
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.*)$/)
    if (headingMatch) {
      closeList()
      const level = headingMatch[1].length
      const body = formatInline(headingMatch[2])
      const cls = level === 1
        ? 'text-xl font-bold mt-5 mb-3 text-gray-900'
        : level === 2
        ? 'text-lg font-bold mt-5 mb-2 text-primary-600'
        : 'text-base font-semibold mt-4 mb-2 text-gray-800'
      const tag = `h${Math.min(level + 1, 6)}`
      out.push(`<${tag} class="${cls}">${body}</${tag}>`)
      continue
    }

    // Ordered list: "1. text"
    const olMatch = trimmed.match(/^(\d+)[.)]\s+(.*)$/)
    if (olMatch) {
      openList('ol')
      out.push(`<li>${formatInline(olMatch[2])}</li>`)
      continue
    }

    // Unordered list: "- text", "* text", "• text"
    const ulMatch = trimmed.match(/^[-*•]\s+(.*)$/)
    if (ulMatch) {
      openList('ul')
      out.push(`<li>${formatInline(ulMatch[1])}</li>`)
      continue
    }

    // Paragraph
    closeList()
    out.push(`<p class="leading-relaxed text-gray-700">${formatInline(trimmed)}</p>`)
  }

  closeList()
  return out.join('\n')
}
