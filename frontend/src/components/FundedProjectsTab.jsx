import { useState, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { evaluationAPI, githubAPI, resolveApiUrl } from '../services/api'
import { Card, Badge } from '../components/common'
import {
  Plus, Upload, X, Loader, Wand2, DollarSign, Calendar, Building2,
  Trash2, ExternalLink, File as FileIcon, Github, Folder, GitBranch, Star,
  Check, Unplug, ChevronDown, ChevronUp,
} from 'lucide-react'
import toast from 'react-hot-toast'

const emptyForm = () => ({
  title: '',
  description: '',
  funding_agency: '',
  amount: '',
  currency: 'INR',
  start_year: new Date().getFullYear(),
  end_year: '',
  document_url: '',
  extracted_domains: [],
  keywords: [],
})

export default function FundedProjectsTab({ authorId, projects, onRefresh }) {
  const [mode, setMode] = useState(null) // 'manual' | 'upload' | 'github' | null
  const [formData, setFormData] = useState(emptyForm())
  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [githubUsername, setGithubUsername] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [prefilling, setPrefilling] = useState(false)
  const fileInputRef = useRef(null)

  const { data: githubStatus, refetch: refetchGithubStatus } = useQuery({
    queryKey: ['githubStatus', authorId],
    queryFn: () => githubAPI.getStatus(authorId),
    enabled: !!authorId,
  })

  const { data: repoResp, isLoading: reposLoading } = useQuery({
    queryKey: ['githubRepos', authorId],
    queryFn: () => githubAPI.getRepositories(authorId),
    enabled: githubStatus?.connected && mode === 'github',
  })
  const repos = repoResp?.repositories || []

  const { data: suggestResp, isFetching: suggestLoading } = useQuery({
    queryKey: ['githubSuggest', authorId],
    queryFn: () => githubAPI.suggest(authorId),
    enabled: mode === 'github' && !githubStatus?.connected,
  })
  const suggestions = suggestResp?.suggestions || []

  const connectMutation = useMutation({
    mutationFn: ({ token }) => githubAPI.connect(authorId, token),
    onSuccess: (data) => {
      toast.success(`Connected as @${data.github_username}`)
      refetchGithubStatus()
      setGithubToken('')
    },
    onError: (error) => toast.error(error.message || 'Failed to connect GitHub'),
  })

  const connectByUsernameMutation = useMutation({
    mutationFn: ({ username }) => githubAPI.connectByUsername(authorId, username),
    onSuccess: (data) => {
      toast.success(`Connected @${data.github_username} (${data.repositories_count} public repos)`)
      refetchGithubStatus()
      setGithubUsername('')
    },
    onError: (error) => toast.error(error.message || 'GitHub profile not found'),
  })

  const disconnectMutation = useMutation({
    mutationFn: () => githubAPI.disconnect(authorId),
    onSuccess: () => {
      toast.success('GitHub disconnected')
      refetchGithubStatus()
    },
    onError: (error) => toast.error(error.message || 'Failed to disconnect'),
  })

  const resetForm = () => {
    setFormData(emptyForm())
    setUploadedFile(null)
    setMode(null)
  }

  const handleConnect = () => {
    if (githubToken.trim()) connectMutation.mutate({ token: githubToken.trim() })
  }

  const handleConnectByUsername = (username) => {
    const value = (username || githubUsername || '')
      .trim()
      .replace(/^@/, '')
      .replace(/^https?:\/\/github\.com\//, '')
      .replace(/\/$/, '')
    if (!value) return toast.error('Enter a GitHub username')
    connectByUsernameMutation.mutate({ username: value })
  }

  // Selecting a repo pre-fills the Funded form with repo title, description,
  // GitHub link, and LLM-extracted metadata. Faculty then fills in funding
  // agency / amount / years and hits Save.
  const handlePickRepo = async (repo) => {
    setPrefilling(true)
    try {
      let title = repo.name || ''
      let description = repo.description || ''
      let domains = []
      let keywords = Array.isArray(repo.topics) ? repo.topics.slice(0, 5) : []

      // Reuse the same metadata endpoint manual uploads call so domains/keywords
      // are LLM-derived, not just raw GitHub topics.
      try {
        const seed = [description, Array.isArray(repo.topics) ? `Topics: ${repo.topics.join(', ')}` : '']
          .filter(Boolean).join('\n\n') || title
        const meta = await evaluationAPI.extractMetadata(title, seed)
        domains = meta.domains || []
        if (meta.keywords?.length) keywords = meta.keywords.slice(0, 10)
      } catch (e) {
        // metadata enrichment is best-effort
      }

      setFormData(prev => ({
        ...prev,
        title,
        description,
        document_url: repo.html_url || '',
        extracted_domains: domains.length ? domains : (repo.topics || []),
        keywords,
      }))
      setMode('manual')
      toast.success('Repo loaded — fill in funding details and save')
    } catch (err) {
      toast.error('Failed to import repo')
    } finally {
      setPrefilling(false)
    }
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const resp = await evaluationAPI.uploadDocument(authorId, file)
      const meta = resp.metadata || {}
      setUploadedFile({
        filename: resp.filename,
        url: resp.file_url,
        size: resp.size_bytes,
        files_listed: resp.files_listed || [],
      })
      setFormData(prev => ({
        ...prev,
        title: meta.suggested_title || prev.title || file.name,
        description: meta.suggested_description || prev.description,
        document_url: resp.file_url,
        extracted_domains: meta.domains || [],
        keywords: meta.keywords || [],
      }))
      toast.success('File analysed — review and save')
    } catch (err) {
      toast.error(err.message || 'Failed to process file')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleExtractMetadata = async () => {
    if (!formData.title || !formData.description) return
    setExtracting(true)
    try {
      const result = await evaluationAPI.extractMetadata(formData.title, formData.description)
      setFormData(prev => ({
        ...prev,
        extracted_domains: result.domains || [],
        keywords: result.keywords || [],
      }))
      toast.success('Metadata extracted')
    } catch (err) {
      toast.error(err.message || 'Metadata extraction failed')
    }
    setExtracting(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.title.trim()) return toast.error('Title is required')
    setSaving(true)
    try {
      await evaluationAPI.addFundedProject({
        faculty_author_id: authorId,
        title: formData.title,
        description: formData.description,
        funding_agency: formData.funding_agency,
        amount: formData.amount ? parseFloat(formData.amount) : null,
        currency: formData.currency,
        start_year: parseInt(formData.start_year) || new Date().getFullYear(),
        end_year: formData.end_year ? parseInt(formData.end_year) : null,
        document_url: formData.document_url || null,
        extracted_domains: formData.extracted_domains,
        keywords: formData.keywords,
      })
      toast.success('Project saved')
      resetForm()
      onRefresh()
    } catch (err) {
      toast.error(err.message || 'Failed to save project')
    }
    setSaving(false)
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this funded project?')) return
    try {
      await evaluationAPI.deleteFundedProject(id)
      toast.success('Project deleted')
      onRefresh()
    } catch (err) {
      toast.error(err.message || 'Failed to delete')
    }
  }

  const totalProjects = projects?.length || 0
  const totalAmount = (projects || [])
    .filter(p => p.amount && p.currency === 'INR')
    .reduce((sum, p) => sum + (p.amount || 0), 0)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Funded Projects</h3>
          <p className="text-sm text-gray-500">
            {totalProjects} project{totalProjects === 1 ? '' : 's'}
            {totalAmount > 0 && ` · Total funding ${formatAmount(totalAmount, 'INR')}`}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton
            active={mode === 'manual'}
            icon={<Plus size={16} />}
            label="Add Manually"
            onClick={() => setMode(mode === 'manual' ? null : 'manual')}
          />
          <ActionButton
            active={mode === 'upload'}
            icon={<Upload size={16} />}
            label="Upload File / Folder"
            onClick={() => setMode(mode === 'upload' ? null : 'upload')}
          />
          <ActionButton
            active={mode === 'github'}
            icon={<Github size={16} />}
            label={githubStatus?.connected ? `@${githubStatus.github_username}` : 'Connect GitHub'}
            onClick={() => setMode(mode === 'github' ? null : 'github')}
            highlighted={githubStatus?.connected}
          />
        </div>
      </div>

      {/* GitHub panel — picking a repo pre-fills the funded form */}
      {mode === 'github' && (
        <Card className="border-primary-200 bg-primary-50/30">
          <div className="flex justify-between items-start mb-4">
            <h4 className="font-semibold text-gray-900 flex items-center gap-2">
              <Github size={18} /> Import from GitHub
            </h4>
            <div className="flex items-center gap-3">
              {githubStatus?.connected && (
                <button
                  onClick={() => disconnectMutation.mutate()}
                  className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
                >
                  <Unplug size={14} /> Disconnect
                </button>
              )}
              <button onClick={() => setMode(null)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
          </div>

          {!githubStatus?.connected ? (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Pick a repo to pre-fill the funded-project form with title, description, and auto-extracted metadata.
                You complete the funding agency / amount / years.
              </p>

              {(suggestLoading || suggestions.length > 0) && (
                <div>
                  <div className="flex items-center gap-2 text-xs font-medium text-gray-700 mb-2">
                    <Wand2 size={14} className="text-primary-500" />
                    Suggested from your SASTRA profile{suggestResp?.source ? ` (${suggestResp.source})` : ''}
                  </div>
                  {suggestLoading ? (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Loader className="animate-spin" size={12} /> Searching GitHub…
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {suggestions.map((s) => (
                        <button
                          key={s.username}
                          onClick={() => handleConnectByUsername(s.username)}
                          disabled={connectByUsernameMutation.isPending}
                          className="flex items-center gap-2 px-3 py-1.5 bg-white border border-primary-200 rounded-lg hover:bg-primary-50 text-sm disabled:opacity-50"
                          title={`Matched by ${s.match_reason}`}
                        >
                          {s.avatar_url && <img src={s.avatar_url} alt={s.username} className="w-5 h-5 rounded-full" />}
                          <span className="font-medium">@{s.username}</span>
                          {s.name && <span className="text-xs text-gray-500">· {s.name}</span>}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div>
                <label className="text-xs font-medium text-gray-700 block mb-1">Or enter GitHub username</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={githubUsername}
                    onChange={(e) => setGithubUsername(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleConnectByUsername() } }}
                    placeholder="e.g. octocat or https://github.com/octocat"
                    className="input flex-1"
                  />
                  <button
                    onClick={() => handleConnectByUsername()}
                    disabled={!githubUsername.trim() || connectByUsernameMutation.isPending}
                    className="btn btn-primary"
                  >
                    {connectByUsernameMutation.isPending ? <Loader className="animate-spin" size={16} /> : 'Connect'}
                  </button>
                </div>
              </div>

              <div className="border-t pt-3">
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900"
                >
                  {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  Advanced: connect with Personal Access Token (for private repos)
                </button>
                {showAdvanced && (
                  <div className="mt-3 space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="password"
                        value={githubToken}
                        onChange={(e) => setGithubToken(e.target.value)}
                        placeholder="Paste GitHub Personal Access Token"
                        className="input flex-1"
                      />
                      <button
                        onClick={handleConnect}
                        disabled={!githubToken.trim() || connectMutation.isPending}
                        className="btn btn-secondary"
                      >
                        {connectMutation.isPending ? <Loader className="animate-spin" size={16} /> : 'Connect with Token'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-green-700">
                <Check size={16} />
                Connected as <strong>@{githubStatus.github_username}</strong>
              </div>

              {reposLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader className="animate-spin text-primary-500" size={24} />
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium mb-2">
                    Pick a repository — its metadata will pre-fill the form:
                  </p>
                  <div className="max-h-72 overflow-y-auto border rounded-lg bg-white">
                    {repos.length === 0 && (
                      <p className="text-sm text-gray-500 text-center py-6">
                        No public repositories found on this profile.
                      </p>
                    )}
                    {repos.map((repo) => (
                      <button
                        key={repo.repo_id}
                        type="button"
                        onClick={() => handlePickRepo(repo)}
                        disabled={prefilling}
                        className="w-full text-left p-3 border-b last:border-b-0 hover:bg-primary-50 disabled:opacity-50 flex items-start gap-2"
                      >
                        <Folder size={14} className="text-gray-500 flex-shrink-0 mt-1" />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{repo.name}</div>
                          <p className="text-xs text-gray-500 line-clamp-1">{repo.description || 'No description'}</p>
                          <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                            {repo.language && <span className="flex items-center gap-1"><GitBranch size={12} /> {repo.language}</span>}
                            <span className="flex items-center gap-1"><Star size={12} /> {repo.stargazers_count}</span>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                  {prefilling && (
                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-2">
                      <Loader className="animate-spin" size={12} /> Analysing repo metadata…
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {(mode === 'manual' || mode === 'upload') && (
        <Card className="border-primary-200">
          <div className="flex justify-between items-start mb-4">
            <h4 className="font-semibold text-gray-900 flex items-center gap-2">
              {mode === 'upload' ? <Upload size={18} /> : <Plus size={18} />}
              {mode === 'upload' ? 'Upload Funded Project Document' : 'New Funded Project'}
            </h4>
            <button onClick={resetForm} className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </button>
          </div>

          {mode === 'upload' && (
            <div className="mb-4">
              <label
                htmlFor="funded-file"
                className={`block border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                  uploading ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-400 hover:bg-primary-50/30'
                }`}
              >
                {uploading ? (
                  <div className="flex flex-col items-center gap-2">
                    <Loader className="animate-spin text-primary-500" size={28} />
                    <p className="text-sm text-gray-600">Analysing document…</p>
                  </div>
                ) : uploadedFile ? (
                  <div className="flex flex-col items-center gap-1">
                    <FileIcon className="text-primary-500" size={28} />
                    <p className="text-sm font-medium text-gray-900">{uploadedFile.filename}</p>
                    <p className="text-xs text-gray-500">{formatBytes(uploadedFile.size)}</p>
                    <p className="text-xs text-primary-600 underline">Click to replace</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-1">
                    <Upload className="text-gray-400" size={32} />
                    <p className="text-sm font-medium text-gray-900">Click to upload or drag a file here</p>
                    <p className="text-xs text-gray-500">PDF, DOCX, TXT, MD, Jupyter <strong>.ipynb</strong>, code files, or a <strong>.zip</strong> of a folder (max 20 MB)</p>
                  </div>
                )}
                <input
                  id="funded-file"
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md,.ipynb,.py,.js,.ts,.tsx,.jsx,.java,.c,.cpp,.h,.go,.rs,.json,.yml,.yaml,.zip"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
              {uploadedFile?.files_listed?.length > 1 && (
                <details className="mt-2 text-xs text-gray-500">
                  <summary className="cursor-pointer">Files in archive ({uploadedFile.files_listed.length})</summary>
                  <ul className="mt-1 max-h-32 overflow-y-auto pl-4 list-disc">
                    {uploadedFile.files_listed.slice(0, 50).map((f) => <li key={f}>{f}</li>)}
                  </ul>
                </details>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="input"
                required
                placeholder="e.g., Smart Grid Load Forecasting"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="input"
                rows={3}
                placeholder="Scope and objectives of the funded work"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Funding Agency</label>
              <input
                type="text"
                value={formData.funding_agency}
                onChange={(e) => setFormData({ ...formData, funding_agency: e.target.value })}
                className="input"
                placeholder="e.g., DST, DBT, AICTE, SERB"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">Amount</label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="input"
                  placeholder="e.g., 2500000"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Currency</label>
                <select
                  value={formData.currency}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  className="input"
                >
                  <option value="INR">INR</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Start Year</label>
                <input
                  type="number"
                  value={formData.start_year}
                  onChange={(e) => setFormData({ ...formData, start_year: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">End Year</label>
                <input
                  type="number"
                  value={formData.end_year}
                  onChange={(e) => setFormData({ ...formData, end_year: e.target.value })}
                  className="input"
                  placeholder="Ongoing if empty"
                />
              </div>
            </div>

            {(formData.extracted_domains?.length > 0 || formData.keywords?.length > 0) && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="text-xs font-medium text-gray-700 mb-2">Extracted metadata</div>
                <div className="flex flex-wrap gap-1.5">
                  {formData.extracted_domains?.map((d) => <Badge key={d} variant="primary">{d}</Badge>)}
                  {formData.keywords?.slice(0, 10).map((k) => <Badge key={k} variant="gray">{k}</Badge>)}
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-2">
              <button
                type="button"
                onClick={handleExtractMetadata}
                disabled={extracting || !formData.title || !formData.description}
                className="btn btn-secondary"
              >
                {extracting ? <><Loader className="animate-spin inline mr-1" size={14} />Extracting…</> : <><Wand2 className="inline mr-1" size={14} />Extract metadata</>}
              </button>
              <button type="submit" disabled={saving} className="btn btn-primary">
                {saving ? 'Saving…' : 'Save Project'}
              </button>
            </div>
          </form>
        </Card>
      )}

      {totalProjects === 0 ? (
        <Card>
          <div className="text-center py-8">
            <DollarSign className="mx-auto text-gray-300 mb-3" size={48} />
            <p className="text-gray-600 font-medium">No funded projects yet</p>
            <p className="text-sm text-gray-500 mt-1">Add manually or upload a sanction letter to get started.</p>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((p) => <FundedProjectCard key={p.id} project={p} onDelete={handleDelete} />)}
        </div>
      )}
    </div>
  )
}

function FundedProjectCard({ project, onDelete }) {
  const status = project.end_year ? 'Completed' : 'Ongoing'
  const statusColor = project.end_year ? 'bg-gray-100 text-gray-700' : 'bg-success-100 text-success-700'

  return (
    <div className="group bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-primary-200 transition-all flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${statusColor}`}>
          {status}
        </span>
        <button
          onClick={() => onDelete(project.id)}
          className="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
          title="Delete"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <h4 className="font-semibold text-gray-900 line-clamp-2 mb-1">{project.title}</h4>
      <p className="text-sm text-gray-600 line-clamp-3 mb-3 flex-1">
        {project.description || 'No description'}
      </p>

      <div className="space-y-1.5 mb-3 text-sm">
        {project.funding_agency && (
          <div className="flex items-center gap-2 text-gray-600">
            <Building2 size={14} className="text-gray-400 flex-shrink-0" />
            <span className="truncate">{project.funding_agency}</span>
          </div>
        )}
        <div className="flex items-center gap-2 text-gray-600">
          <Calendar size={14} className="text-gray-400 flex-shrink-0" />
          <span>{project.start_year}{project.end_year ? ` – ${project.end_year}` : ' – Ongoing'}</span>
        </div>
        {project.amount && (
          <div className="flex items-center gap-2 font-semibold text-success-700">
            <DollarSign size={14} className="flex-shrink-0" />
            <span>{formatAmount(project.amount, project.currency)}</span>
          </div>
        )}
      </div>

      {(project.extracted_domains?.length > 0 || project.keywords?.length > 0) && (
        <div className="flex flex-wrap gap-1 mb-3">
          {project.extracted_domains?.slice(0, 3).map((d) => <Badge key={d} variant="primary">{d}</Badge>)}
          {project.keywords?.slice(0, 2).map((k) => <Badge key={k} variant="gray">{k}</Badge>)}
        </div>
      )}

      {project.document_url && (
        <div className="pt-2 border-t border-gray-100">
          <a
            href={resolveApiUrl(project.document_url)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary-600 hover:underline flex items-center gap-1"
          >
            <FileIcon size={12} /> View document
            <ExternalLink size={10} />
          </a>
        </div>
      )}
    </div>
  )
}

function ActionButton({ active, icon, label, onClick, highlighted }) {
  const base = 'inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors'
  const cls = active
    ? 'bg-primary-600 text-white border border-primary-600'
    : highlighted
    ? 'bg-success-50 text-success-700 border border-success-200 hover:bg-success-100'
    : 'bg-white text-gray-700 border border-gray-300 hover:border-primary-300 hover:bg-primary-50'
  return (
    <button onClick={onClick} className={`${base} ${cls}`}>
      {icon}
      {label}
    </button>
  )
}

function formatAmount(amount, currency) {
  if (!amount) return 'N/A'
  return new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-US', {
    style: 'currency',
    currency: currency || 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

function formatBytes(n) {
  if (!n) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++ }
  return `${n.toFixed(1)} ${units[i]}`
}
