import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { evaluationAPI, authorsAPI } from '../services/api'
import { PageHeader, Card, Loading, Tabs } from '../components/common'
import PocProjectsTab from '../components/PocProjectsTab'
import FundedProjectsTab from '../components/FundedProjectsTab'
import { useAppStore } from '../store'

const FacultyEvaluation = () => {
  const { id: authorId } = useParams()
  const activeTab = useAppStore((s) => s.facultyEvalTabById[authorId] || 'poc')
  const setFacultyEvalTab = useAppStore((s) => s.setFacultyEvalTab)
  const setActiveTab = (tab) => setFacultyEvalTab(authorId, tab)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [authorInfo, setAuthorInfo] = useState(null)

  useEffect(() => {
    loadData()
  }, [authorId])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [summaryData, authorData] = await Promise.all([
        evaluationAPI.getSummary(authorId).catch(() => null),
        authorsAPI.getById(authorId).catch(() => null),
      ])
      setSummary(summaryData)
      setAuthorInfo(authorData)
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  const tabs = [
    { id: 'poc', label: 'POC Projects' },
    { id: 'funded', label: 'Funded Projects' },
  ]

  const handleReset = async () => {
    setActiveTab('poc')
    await loadData()
  }

  if (loading) {
    return <Loading message="Loading evaluation data..." />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={authorInfo?.name_variants?.[0] ? `${authorInfo.name_variants[0]} - Evaluation` : 'Faculty Evaluation'}
        subtitle={authorInfo ? `${authorInfo.pub_count} publications • ${authorInfo.total_citations} citations • H-index: ${authorInfo.h_index}` : ''}
        showBack
        showRefresh
        onRefresh={handleReset}
      />

      {error && (
        <Card className="bg-red-50 border-red-200">
          <p className="text-red-700">{error}</p>
        </Card>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6">
        {activeTab === 'poc' && (
          <PocProjectsTab
            authorId={authorId}
            projects={summary?.poc_projects || []}
            onRefresh={loadData}
          />
        )}
        {activeTab === 'funded' && (
          <FundedProjectsTab
            authorId={authorId}
            projects={summary?.funded_projects || []}
            onRefresh={loadData}
          />
        )}
      </div>
    </div>
  )
}

export default FacultyEvaluation