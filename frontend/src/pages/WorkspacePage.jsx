// ==========================================
// WorkspacePage — Document upload & NER analysis
// ==========================================
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import FileUpload from '../components/ui/FileUpload'
import NerHighlighter from '../components/ui/NerHighlighter'
import client from '../api/client'
import GaugeChart from '../components/ui/GaugeChart'

export default function WorkspacePage() {
  const { projectId } = useParams()
  const [uploaded, setUploaded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // State for real NLP results
  const [documentText, setDocumentText] = useState('')
  const [entities, setEntities] = useState([])
  const [summary, setSummary] = useState('')
  const [scores, setScores] = useState({ risk: 0, profitability: 0, relevance: 0 })

  async function handleUpload(file) {
    if (!projectId) {
      setError('Ошибка: отсутствует ID проекта (projectId в URL).')
      return
    }

    setLoading(true)
    setError('')
    setUploaded(false)

    try {
      // 1. Upload Document
      const formData = new FormData()
      formData.append('file', file)
      formData.append('doc_type', 'OTHER')

      const docRes = await client.post(`/projects/${projectId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      setDocumentText(docRes.content || '')

      // 2. Generate Prediction
      const predRes = await client.post(`/projects/${projectId}/predictions/generate`)
      
      setSummary(predRes.summary || '')
      setScores({
        risk: predRes.risk_score || 0,
        profitability: predRes.profitability_score || 0,
        relevance: predRes.relevance_score || 0,
      })
      
      // Parse entities JSON string if necessary
      let parsedEntities = []
      if (typeof predRes.entities === 'string') {
        try { parsedEntities = JSON.parse(predRes.entities) } catch(e) {}
      } else if (Array.isArray(predRes.entities)) {
        parsedEntities = predRes.entities
      }
      setEntities(parsedEntities)

      setUploaded(true)
    } catch (err) {
      console.error(err)
      setError(err.message || 'Ошибка обработки документа.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-5xl mx-auto">
        {/* --- Header --- */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight">Document Analysis Workspace</h1>
          <p className="text-gray-400 mt-2">Upload IT documentation for automated NLP analysis and risk assessment.</p>
        </div>

        {/* --- Error message --- */}
        {error && (
          <div className="mb-6 bg-crimson/10 border border-crimson/30 text-crimson p-4 rounded-xl">
            {error}
          </div>
        )}

        {/* --- Upload Zone --- */}
        <div className="mb-12">
          <FileUpload onUpload={handleUpload} />
          {loading && <p className="text-center text-gray-400 mt-4 animate-pulse">Анализ документа нейросетью...</p>}
        </div>

        {/* --- Results Panel (shown after upload) --- */}
        {uploaded && (
          <div className="space-y-8 animate-fade-in">
            {/* Score gauges */}
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-surface border border-white/5 rounded-2xl p-6 flex flex-col items-center">
                <GaugeChart value={scores.risk} label="Risk Level" color="#FF3366" />
              </div>
              <div className="bg-surface border border-white/5 rounded-2xl p-6 flex flex-col items-center">
                <GaugeChart value={scores.profitability} label="Profitability" color="#00FF66" />
              </div>
              <div className="bg-surface border border-white/5 rounded-2xl p-6 flex flex-col items-center">
                <GaugeChart value={scores.relevance} label="Relevance" color="#00F0FF" />
              </div>
            </div>

            {/* Summary */}
            <div className="bg-surface border border-white/5 rounded-2xl p-8">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-4">
                📋 Document Summary
              </h3>
              <p className="text-gray-300 leading-relaxed">{summary}</p>
            </div>

            {/* NER Highlighted Text */}
            <div className="bg-surface border border-white/5 rounded-2xl p-8">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-4">
                🏷️ Named Entity Recognition
              </h3>
              <div className="bg-navy rounded-xl p-6 border border-white/5 h-96 overflow-y-auto whitespace-pre-wrap">
                <NerHighlighter text={documentText} entities={entities} />
              </div>
              {/* Entity legend */}
              <div className="flex flex-wrap gap-3 mt-5">
                {[
                  { label: 'Technology', color: 'bg-electric/15 text-electric border-electric/30' },
                  { label: 'Budget', color: 'bg-emerald/15 text-emerald border-emerald/30' },
                  { label: 'Deadline', color: 'bg-crimson/15 text-crimson border-crimson/30' },
                  { label: 'Organization', color: 'bg-purple-400/15 text-purple-400 border-purple-400/30' },
                ].map(({ label, color }) => (
                  <span key={label} className={`text-[11px] px-2.5 py-1 rounded-md border font-medium ${color}`}>
                    {label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
