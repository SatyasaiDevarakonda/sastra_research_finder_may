import { useState, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { evaluationAPI, githubAPI, resolveApiUrl } from '../services/api'
import { Card, Badge } from '../components/common'
import {
  Github, Folder, GitBranch, Star, Check, Loader, ExternalLink, Unplug,
  Wand2, ChevronDown, ChevronUp, Plus, Upload, FileText, X, File as FileIcon,
  Trash2, Edit3, Link as LinkIcon, RefreshCw,
} from 'lucide-react'
import toast from 'react-hot-toast'

const emptyForm = () => ({
  title: '',
  description: '',
  github_link: '',
  document_url: '',
  year: new Date().getFullYear(),
  source: 'manual',
  extracted_domains: [],
  keywords: [],
  // complexity_score: 0,
  // impact_score: 0,
})

export default function PocProjectsTab({ authorId, projects, onRefresh }) {
  const [mode, setMode] = useState(null) // 'manual' | 'upload' | 'github' | null
  const [formData, setFormData] = useState(emptyForm())
  const [githubUsername, setGithubUsername] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [selectedRepos, setSelectedRepos] = useState([])
  const [extracting, setExtracting] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [saving, setSaving] = useState(false)
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
      setSelectedRepos([])
    },
    onError: (error) => toast.error(error.message || 'Failed to disconnect'),
  })

  const createFromGithubMutation = useMutation({
    mutationFn: ({ repoId }) => githubAPI.createProject(authorId, repoId),
    onSuccess: () => {
      toast.success('Project created from GitHub!')
      setSelectedRepos([])
      onRefresh()
    },
    onError: (error) => toast.error(error.message || 'Failed to create project'),
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

  const toggleRepoSelection = (repo) => {
    setSelectedRepos(prev => prev.some(r => r.repo_id === repo.repo_id)
      ? prev.filter(r => r.repo_id !== repo.repo_id)
      : [...prev, repo])
  }

  const handleCreateFromGithub = () => {
    selectedRepos.forEach(repo => createFromGithubMutation.mutate({ repoId: repo.repo_id }))
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
        // complexity_score: meta.complexity || 0,
        // impact_score: meta.impact_score || 0,
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
        // complexity_score: result.complexity || 0,
        // impact_score: result.impact_score || 0,
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
      await evaluationAPI.addPocProject({
        faculty_author_id: authorId,
        title: formData.title,
        description: formData.description,
        github_link: formData.github_link || null,
        document_url: formData.document_url || null,
        year: parseInt(formData.year) || new Date().getFullYear(),
        source: 'manual',
        extracted_domains: formData.extracted_domains,
        keywords: formData.keywords,
        // complexity_score: formData.complexity_score,
        // impact_score: formData.impact_score,
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
    if (!confirm('Delete this project?')) return
    try {
      await evaluationAPI.deletePocProject(id)
      toast.success('Project deleted')
      onRefresh()
    } catch (err) {
      toast.error(err.message || 'Failed to delete')
    }
  }

  const handleSyncGithub = async (id) => {
    const tId = toast.loading('Re-analysing repo…')
    try {
      await githubAPI.syncProject(id)
      toast.success('Metadata refreshed', { id: tId })
      onRefresh()
    } catch (err) {
      toast.error(err.message || 'Re-analyse failed', { id: tId })
    }
  }

  const totalProjects = projects?.length || 0
  const githubCount = projects?.filter(p => p.source === 'github').length || 0

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">POC Projects</h3>
          <p className="text-sm text-gray-500">
            {totalProjects} total · {githubCount} from GitHub · {totalProjects - githubCount} manual/uploaded
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

      {/* Upload / Manual form */}
      {(mode === 'manual' || mode === 'upload') && (
        <Card className="border-primary-200">
          <div className="flex justify-between items-start mb-4">
            <h4 className="font-semibold text-gray-900 flex items-center gap-2">
              {mode === 'upload' ? <Upload size={18} /> : <Plus size={18} />}
              {mode === 'upload' ? 'Upload Project Document' : 'New POC Project'}
            </h4>
            <button onClick={resetForm} className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </button>
          </div>

          {mode === 'upload' && (
            <div className="mb-4">
              <label
                htmlFor="poc-file"
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
                  id="poc-file"
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
                placeholder="e.g., Deep Learning for Retinal Image Segmentation"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="input"
                rows={3}
                placeholder="Brief description of the project, its objective and approach"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">GitHub / Project Link (optional)</label>
                <input
                  type="url"
                  value={formData.github_link}
                  onChange={(e) => setFormData({ ...formData, github_link: e.target.value })}
                  className="input"
                  placeholder="https://github.com/you/project"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Year</label>
                <input
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                  className="input"
                />
              </div>
            </div>

            {/* Metadata preview */}
            {(formData.extracted_domains?.length > 0 || formData.keywords?.length > 0) && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="text-xs font-medium text-gray-700 mb-2">Extracted metadata (auto-filled, editable after save)</div>
                <div className="flex flex-wrap gap-1.5">
                  {formData.extracted_domains?.map((d) => <Badge key={d} variant="primary">{d}</Badge>)}
                  {formData.keywords?.slice(0, 10).map((k) => <Badge key={k} variant="gray">{k}</Badge>)}
                </div>
                {/* Complexity / Impact display disabled (commented out)
                <div className="flex gap-3 mt-2 text-xs text-gray-600">
                  {formData.complexity_score > 0 && <span>Complexity: <strong>{formData.complexity_score}/10</strong></span>}
                  {formData.impact_score > 0 && <span>Impact: <strong>{formData.impact_score}/10</strong></span>}
                </div>
                */}
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-2">
              <button
                type="button"
                onClick={handleExtractMetadata}
                disabled={extracting || !formData.title || !formData.description}
                className="btn btn-secondary"
              >
                {extracting ? <><Loader className="animate-spin inline mr-1" size={14} />Extracting…</> : <><Wand2 className="inline mr-1" size={14} />Re-extract metadata</>}
              </button>
              <button type="submit" disabled={saving} className="btn btn-primary">
                {saving ? 'Saving…' : 'Save Project'}
              </button>
            </div>
          </form>
        </Card>
      )}

      {/* GitHub panel */}
      {mode === 'github' && (
        <Card className="border-primary-200 bg-primary-50/30">
          <div className="flex justify-between items-start mb-4">
            <h4 className="font-semibold text-gray-900 flex items-center gap-2">
              <Github size={18} /> GitHub Integration
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
                Link your GitHub profile to auto-import public repositories. No token required.
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
                    <p className="text-xs text-gray-500">
                      Generate at GitHub → Settings → Developer settings → Personal access tokens (classic, scope <code>repo</code>).
                    </p>
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
                    Select repositories ({repos.length}):
                  </p>
                  <div className="max-h-72 overflow-y-auto border rounded-lg bg-white">
                    {repos.length === 0 && (
                      <p className="text-sm text-gray-500 text-center py-6">
                        No public repositories found on this profile.
                      </p>
                    )}
                    {repos.map((repo) => {
                      const isSelected = selectedRepos.some(r => r.repo_id === repo.repo_id)
                      return (
                        <label
                          key={repo.repo_id}
                          className={`flex items-start gap-2 p-3 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 ${
                            isSelected ? 'bg-primary-50 border-l-4 border-l-primary-500' : ''
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleRepoSelection(repo)}
                            className="mt-1"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <Folder size={14} className="text-gray-500 flex-shrink-0" />
                              <span className="font-medium text-sm truncate">{repo.name}</span>
                            </div>
                            <p className="text-xs text-gray-500 line-clamp-1">{repo.description || 'No description'}</p>
                            <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                              {repo.language && <span className="flex items-center gap-1"><GitBranch size={12} /> {repo.language}</span>}
                              <span className="flex items-center gap-1"><Star size={12} /> {repo.stargazers_count}</span>
                            </div>
                          </div>
                        </label>
                      )
                    })}
                  </div>

                  {selectedRepos.length > 0 && (
                    <button
                      onClick={handleCreateFromGithub}
                      disabled={createFromGithubMutation.isPending}
                      className="btn btn-primary w-full mt-3"
                    >
                      {createFromGithubMutation.isPending
                        ? <Loader className="animate-spin" size={16} />
                        : `Add ${selectedRepos.length} Selected as POC Projects`}
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Projects grid */}
      {totalProjects === 0 ? (
        <Card>
          <div className="text-center py-8">
            <Folder className="mx-auto text-gray-300 mb-3" size={48} />
            <p className="text-gray-600 font-medium">No POC projects yet</p>
            <p className="text-sm text-gray-500 mt-1">Add manually, upload a file, or connect GitHub to import repos.</p>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => (
            <PocProjectCard
              key={project.id}
              project={project}
              onDelete={handleDelete}
              onSync={handleSyncGithub}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function PocProjectCard({ project, onDelete, onSync }) {
  const isGithub = project.source === 'github'
  const fileName = project.document_url ? project.document_url.split('/').pop() : null

  return (
    <div className="group bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-primary-200 transition-all flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          {isGithub ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-900 text-white text-[10px] font-medium">
              <Github size={10} /> GitHub
            </span>
          ) : project.document_url ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary-100 text-primary-700 text-[10px] font-medium">
              <FileIcon size={10} /> Uploaded
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-[10px] font-medium">
              <Edit3 size={10} /> Manual
            </span>
          )}
          <span className="text-xs text-gray-500">{project.year}</span>
        </div>
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {isGithub && onSync && (
            <button
              onClick={() => onSync(project.id)}
              className="text-gray-400 hover:text-primary-600"
              title="Re-analyse repo (pull latest README + re-extract metadata)"
            >
              <RefreshCw size={14} />
            </button>
          )}
          <button
            onClick={() => onDelete(project.id)}
            className="text-gray-300 hover:text-red-500"
            title="Delete"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <h4 className="font-semibold text-gray-900 line-clamp-2 mb-1">{project.title}</h4>
      <p className="text-sm text-gray-600 line-clamp-3 mb-3 flex-1">
        {project.description || 'No description'}
      </p>

      {isGithub && (project.tech_stack?.length > 0 || project.stars > 0) && (
        <div className="flex items-center gap-3 mb-2 text-xs text-gray-500">
          {project.tech_stack?.length > 0 && (
            <span className="flex items-center gap-1">
              <GitBranch size={12} /> {project.tech_stack.slice(0, 2).join(', ')}
            </span>
          )}
          {project.stars > 0 && <span className="flex items-center gap-1"><Star size={12} /> {project.stars}</span>}
        </div>
      )}

      {(project.extracted_domains?.length > 0 || project.keywords?.length > 0) && (
        <div className="flex flex-wrap gap-1 mb-3">
          {project.extracted_domains?.slice(0, 3).map((d) => <Badge key={d} variant="primary">{d}</Badge>)}
          {project.keywords?.slice(0, 2).map((k) => <Badge key={k} variant="gray">{k}</Badge>)}
        </div>
      )}

      {/* Complexity / Impact bars disabled (commented out)
      {(project.complexity_score > 0 || project.impact_score > 0) && (
        <div className="flex gap-3 text-xs text-gray-600 mb-3">
          {project.complexity_score > 0 && (
            <div className="flex items-center gap-1">
              <span>Complexity</span>
              <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-warning-500" style={{ width: `${project.complexity_score * 10}%` }} />
              </div>
              <span className="font-medium">{project.complexity_score}</span>
            </div>
          )}
          {project.impact_score > 0 && (
            <div className="flex items-center gap-1">
              <span>Impact</span>
              <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-success-500" style={{ width: `${project.impact_score * 10}%` }} />
              </div>
              <span className="font-medium">{project.impact_score}</span>
            </div>
          )}
        </div>
      )}
      */}

      <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
        {(project.github_link || project.github_repo_name) && (
          <a
            href={project.github_link || `https://github.com/${project.github_repo_name}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary-600 hover:underline flex items-center gap-1"
          >
            <Github size={12} /> GitHub
            <ExternalLink size={10} />
          </a>
        )}
        {project.document_url && (
          <a
            href={resolveApiUrl(project.document_url)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary-600 hover:underline flex items-center gap-1"
            title={fileName}
          >
            <FileIcon size={12} /> Document
            <ExternalLink size={10} />
          </a>
        )}
      </div>
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

function formatBytes(n) {
  if (!n) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++ }
  return `${n.toFixed(1)} ${units[i]}`
}
