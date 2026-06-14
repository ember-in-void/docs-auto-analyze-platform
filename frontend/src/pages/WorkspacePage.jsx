// ==========================================
// WorkspacePage — Document upload & NER analysis
// ==========================================
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import FileUpload from '../components/ui/FileUpload'
import NerHighlighter from '../components/ui/NerHighlighter'
import client from '../api/client'


export default function WorkspacePage() {
  const { projectId } = useParams()
  const [uploaded, setUploaded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // State for real NLP results
  const [documentText, setDocumentText] = useState('')
  const [entities, setEntities] = useState([])
  const [analysisResult, setAnalysisResult] = useState(null)

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
      
      setAnalysisResult(predRes)
      
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
        {uploaded && analysisResult && (
          <div className="space-y-8 animate-fade-in text-left">
            {/* 1. Meta Bar */}
            <div className="flex flex-wrap items-center gap-6 py-4 px-6 bg-surface border border-white/5 rounded-2xl text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-500 font-medium">Бюджет:</span>
                <span className="px-3 py-1 rounded bg-emerald/10 text-emerald font-semibold border border-emerald/20">
                  {analysisResult.meta_info?.budget || 'Не указано'}
                </span>
              </div>
              <div className="h-4 w-px bg-white/10 hidden sm:block" />
              <div className="flex items-center gap-2">
                <span className="text-gray-500 font-medium">Сроки:</span>
                <span className="px-3 py-1 rounded bg-blue-500/10 text-blue-400 font-semibold border border-blue-500/20">
                  {analysisResult.meta_info?.timeline || 'Не указано'}
                </span>
              </div>
              <div className="h-4 w-px bg-white/10 hidden sm:block" />
              <div className="flex items-center gap-2">
                <span className="text-gray-500 font-medium">Доменная область:</span>
                <span className="px-3 py-1 rounded bg-purple-500/10 text-purple-400 font-semibold border border-purple-500/20">
                  {analysisResult.meta_info?.domain || 'Не указано'}
                </span>
              </div>
            </div>

            {/* 2. Executive Summary */}
            <div className="bg-surface border border-white/5 rounded-2xl p-8">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-bold mb-4">
                📋 Executive Summary / Резюме проекта
              </h3>
              <div className="bg-white/5 border border-white/5 rounded-xl p-6 text-gray-300 leading-relaxed">
                {analysisResult.executive_summary}
              </div>
            </div>

            {/* 3. Tech Stack Card */}
            <div className="bg-surface border border-white/5 rounded-2xl p-8">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-bold mb-5">
                💻 Стек технологий проекта
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Detected */}
                <div className="p-5 bg-navy rounded-xl border border-white/5">
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3.5 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    Выявлено в документе:
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.tech_stack?.detected?.length > 0 ? (
                      analysisResult.tech_stack.detected.map(tech => (
                        <span key={tech} className="text-xs px-3 py-1.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-medium">
                          {tech}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-500 italic">Технологии не обнаружены</span>
                    )}
                  </div>
                </div>

                {/* Missing */}
                <div className="p-5 bg-navy rounded-xl border border-white/5">
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3.5 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-orange-400" />
                    Рекомендуется добавить (gap-анализ):
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.tech_stack?.missing?.length > 0 ? (
                      analysisResult.tech_stack.missing.map(tech => (
                        <span key={tech} className="text-xs px-3 py-1.5 rounded bg-orange-500/10 text-orange-300 border border-orange-500/20 font-medium">
                          {tech}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-500 italic">Нет рекомендаций</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* 4. Metrics List */}
            <div className="space-y-4">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-bold px-1">
                📊 Ключевые метрики аудита
              </h3>
              <div className="grid grid-cols-1 gap-4">
                {analysisResult.metrics?.map((metric) => {
                  const scoreColorClass = metric.type === 'risk' 
                    ? (metric.score > 60 ? 'text-red-400' : metric.score > 30 ? 'text-yellow-400' : 'text-emerald')
                    : (metric.score > 60 ? 'text-emerald' : metric.score > 30 ? 'text-yellow-400' : 'text-red-400');
                  
                  const levelBgClass = metric.level === 'Высокий' 
                    ? (metric.type === 'risk' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-emerald/10 text-emerald border-emerald/20')
                    : metric.level === 'Низкий'
                    ? (metric.type === 'risk' ? 'bg-emerald/10 text-emerald border-emerald/20' : 'bg-red-500/10 text-red-400 border-red-500/20')
                    : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';

                  return (
                    <div key={metric.type} className="bg-surface border border-white/5 rounded-2xl overflow-hidden hover:border-white/10 transition-colors">
                      {/* Metric Header */}
                      <div className="flex items-center justify-between p-6 border-b border-white/5 bg-white/[0.01]">
                        <div className="flex items-center gap-3">
                          <span className="font-semibold text-base text-white">{metric.label}</span>
                          <span className={`text-[11px] px-2.5 py-0.5 rounded border font-medium uppercase tracking-wide ${levelBgClass}`}>
                            {metric.level}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className={`text-xl font-bold ${scoreColorClass}`}>
                            {metric.score}%
                          </span>
                        </div>
                      </div>
                      {/* Metric Body */}
                      <div className="p-6 space-y-4 text-sm bg-navy/10">
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                            Обоснование
                          </h4>
                          <p className="text-gray-300 leading-relaxed">
                            {metric.reasoning}
                          </p>
                        </div>
                        {metric.recommendations && metric.recommendations.length > 0 && (
                          <div className="pt-4 border-t border-white/5">
                            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                              Рекомендации:
                            </h4>
                            <ul className="list-disc list-inside space-y-1.5 text-gray-300">
                              {metric.recommendations.map((rec, i) => (
                                <li key={i} className="leading-relaxed pl-1">
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 5. NER Highlighted Text */}
            <div className="bg-surface border border-white/5 rounded-2xl p-8">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-4">
                🏷️ Named Entity Recognition
              </h3>
              <div className="bg-navy rounded-xl p-6 border border-white/5 h-96 overflow-y-auto whitespace-pre-wrap">
                <NerHighlighter text={documentText} entities={entities} />
              </div>
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
