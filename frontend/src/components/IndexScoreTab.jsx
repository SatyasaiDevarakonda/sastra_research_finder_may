import { useState } from 'react'
import { evaluationAPI } from '../services/api'
import { Card } from '../components/common'

const IndexScoreTab = ({ authorId, indexScore, onRefresh }) => {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    scopus_h_index: 0,
    sci_paper_count: 0,
    q1_paper_count: 0,
    q2_paper_count: 0,
    web_of_science_count: 0,
  })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await evaluationAPI.updateIndexScore(authorId, formData)
      setShowForm(false)
      onRefresh()
    } catch (error) {
      console.error('Failed to update index score:', error)
    }
    setSaving(false)
  }

  const compositeScore = indexScore?.composite_index_score || 0

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Index Scores</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'Update Scores'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Scopus H-Index</label>
              <input
                type="number"
                value={formData.scopus_h_index}
                onChange={(e) => setFormData({ ...formData, scopus_h_index: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">SCI Paper Count</label>
              <input
                type="number"
                value={formData.sci_paper_count}
                onChange={(e) => setFormData({ ...formData, sci_paper_count: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Q1 Paper Count</label>
              <input
                type="number"
                value={formData.q1_paper_count}
                onChange={(e) => setFormData({ ...formData, q1_paper_count: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Q2 Paper Count</label>
              <input
                type="number"
                value={formData.q2_paper_count}
                onChange={(e) => setFormData({ ...formData, q2_paper_count: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Web of Science Count</label>
              <input
                type="number"
                value={formData.web_of_science_count}
                onChange={(e) => setFormData({ ...formData, web_of_science_count: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg"
                min="0"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Scores'}
          </button>
        </form>
      )}

      {indexScore ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{indexScore.scopus_h_index}</div>
            <div className="text-gray-600 text-sm mt-1">Scopus H-Index</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{indexScore.sci_paper_count}</div>
            <div className="text-gray-600 text-sm mt-1">SCI Papers</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">{indexScore.q1_paper_count}</div>
            <div className="text-gray-600 text-sm mt-1">Q1 Papers</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">{indexScore.q2_paper_count}</div>
            <div className="text-gray-600 text-sm mt-1">Q2 Papers</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-3xl font-bold text-teal-600">{indexScore.web_of_science_count}</div>
            <div className="text-gray-600 text-sm mt-1">WoS Papers</div>
          </Card>
          <Card className="p-4 text-center bg-gradient-to-br from-blue-50 to-purple-50">
            <div className="text-4xl font-bold text-indigo-600">{compositeScore}</div>
            <div className="text-gray-600 text-sm mt-1">Composite Index Score</div>
            <div className="text-xs text-gray-400 mt-2">
              (H×3 + SCI×2 + Q1×5 + Q2×2 + WoS×1)
            </div>
          </Card>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <p>No index scores recorded yet.</p>
          <p className="text-sm mt-1">Click "Update Scores" to add your first entry.</p>
        </div>
      )}
    </div>
  )
}

export default IndexScoreTab