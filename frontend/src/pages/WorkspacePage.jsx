// ==========================================
// WorkspacePage — Document upload & NER analysis
// ==========================================
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import FileUpload from '../components/ui/FileUpload'
import NerHighlighter from '../components/ui/NerHighlighter'
import client from '../api/client'


export default function WorkspacePage() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [uploaded, setUploaded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // State for real NLP results
  const [documentText, setDocumentText] = useState('')
  const [entities, setEntities] = useState([])
  const [analysisResult, setAnalysisResult] = useState(null)
  const [activeTab, setActiveTab] = useState('audit')

  useEffect(() => {
    if (!projectId) return

    // Store the last visited project ID in localStorage
    localStorage.setItem('lastProjectId', projectId)

    async function loadData() {
      setLoading(true)
      setError('')
      try {
        // 1. Fetch project details
        let projData
        try {
          projData = await client.get(`/projects/${projectId}`)
          setProject(projData)
        } catch (err) {
          console.error('Project not found or access denied:', err)
          localStorage.removeItem('lastProjectId')
          navigate('/dashboard', { replace: true })
          return
        }

        // 2. Fetch documents and predictions
        const [docs, preds] = await Promise.all([
          client.get(`/projects/${projectId}/documents`),
          client.get(`/projects/${projectId}/predictions`)
        ])

        if (docs && docs.length > 0 && preds && preds.length > 0) {
          const latestDoc = docs[0]
          const latestPred = preds[0]

          setDocumentText(latestDoc.content || '')
          setAnalysisResult(latestPred)

          let parsedEntities = []
          if (typeof latestPred.entities === 'string') {
            try {
              parsedEntities = JSON.parse(latestPred.entities)
            } catch (e) {
              console.error('Failed to parse entities JSON string:', e)
            }
          } else if (Array.isArray(latestPred.entities)) {
            parsedEntities = latestPred.entities
          }
          setEntities(parsedEntities)
          setUploaded(true)
        } else {
          // Reset states if no document/prediction exists yet
          setDocumentText('')
          setAnalysisResult(null)
          setEntities([])
          setUploaded(false)
        }
      } catch (err) {
        console.error('Error loading workspace data:', err)
        setError(err.message || 'Ошибка загрузки данных проекта.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [projectId, navigate])

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
          <h1 className="text-3xl font-bold tracking-tight">
            Workspace: {project ? project.name : 'Document Analysis'}
          </h1>
          <p className="text-gray-400 mt-2">
            {project?.description || 'Upload IT documentation for automated NLP analysis and risk assessment.'}
          </p>
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
            {/* Tab switch navigation */}
            <div className="flex border-b border-white/10 mb-6 gap-6">
              <button
                onClick={() => setActiveTab('audit')}
                className={`pb-4 px-2 text-sm font-semibold tracking-wide border-b-2 transition-all duration-300 flex items-center gap-2 ${
                  activeTab === 'audit'
                    ? 'border-electric text-electric font-bold'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                📋 Общий аудит проекта
              </button>
              <button
                onClick={() => setActiveTab('gap')}
                className={`pb-4 px-2 text-sm font-semibold tracking-wide border-b-2 transition-all duration-300 flex items-center gap-2 ${
                  activeTab === 'gap'
                    ? 'border-electric text-electric font-bold'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                🔍 Gap-анализ ТЗ
              </button>
            </div>

            {/* TAB CONTENT: General Audit */}
            {activeTab === 'audit' && (
              <div className="space-y-8">
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

            {/* TAB CONTENT: Gap Analysis */}
            {activeTab === 'gap' && (
              <div className="space-y-8 animate-fade-in">
                {/* 1. Completeness Score */}
                {(() => {
                  const completeness = analysisResult.gap_analysis?.completeness_score ?? 0;
                  const scoreColor = completeness > 75 
                    ? 'text-emerald' 
                    : completeness > 45 
                    ? 'text-yellow-400' 
                    : 'text-red-400';
                  
                  const scoreBarBg = completeness > 75 
                    ? 'bg-emerald' 
                    : completeness > 45 
                    ? 'bg-yellow-400' 
                    : 'bg-red-400';

                  return (
                    <div className="bg-surface border border-white/5 rounded-2xl p-8 flex flex-col md:flex-row items-center justify-between gap-6">
                      <div className="flex-1 text-left">
                        <h3 className="text-sm uppercase tracking-wider text-gray-500 font-bold mb-2">
                          📊 Полнота документации ТЗ (Completeness Score)
                        </h3>
                        <p className="text-gray-400 text-xs leading-relaxed max-w-xl">
                          Показатель полноты отражает степень соответствия документа целям аудита. 
                          Веса разделов: Суть проекта и цели — 20%, Стек технологий — 20%, 
                          Ключевые риски — 30%, Экономический потенциал — 30%.
                        </p>
                      </div>
                      <div className="flex flex-col items-center justify-center shrink-0">
                        <div className="flex items-baseline gap-1">
                          <span className={`text-4xl font-extrabold tracking-tight ${scoreColor}`}>
                            {completeness}
                          </span>
                          <span className="text-gray-500 text-sm font-semibold">%</span>
                        </div>
                        <div className="w-48 bg-white/10 h-2 rounded-full mt-3 overflow-hidden">
                          <div className={`h-full ${scoreBarBg} transition-all duration-1000`} style={{ width: `${completeness}%` }} />
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* 2. Project Metadata Extraction */}
                <div className="bg-surface border border-white/5 rounded-2xl p-8">
                  <h3 className="text-sm uppercase tracking-wider text-gray-500 font-bold mb-5">
                    📌 Извлеченные метаданные
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { 
                        label: 'Название проекта', 
                        value: analysisResult.gap_analysis?.metadata?.project_name, 
                        bg: 'bg-white/[0.02] border-white/5',
                        textClr: 'text-white'
                      },
                      { 
                        label: 'Дата документа', 
                        value: analysisResult.gap_analysis?.metadata?.document_date, 
                        bg: 'bg-blue-500/5 border-blue-500/10',
                        textClr: 'text-blue-300'
                      },
                      { 
                        label: 'Срок (дедлайн)', 
                        value: analysisResult.gap_analysis?.metadata?.deadline, 
                        bg: 'bg-purple-500/5 border-purple-500/10',
                        textClr: 'text-purple-300'
                      },
                      { 
                        label: 'Бюджет', 
                        value: analysisResult.gap_analysis?.metadata?.budget, 
                        bg: 'bg-emerald/5 border-emerald/10',
                        textClr: 'text-emerald'
                      }
                    ].map((item, idx) => (
                      <div key={idx} className={`p-4 border rounded-xl ${item.bg}`}>
                        <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider block mb-1">
                          {item.label}
                        </span>
                        <span className={`text-xs font-semibold ${item.textClr} block truncate`}>
                          {item.value || 'Не указано'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Helper function to get badge */}
                {(() => {
                  const getStatusBadge = (status) => {
                    switch (status) {
                      case 'present':
                        return (
                          <span className="text-[9px] px-2 py-0.5 rounded border bg-emerald/10 text-emerald border-emerald/20 font-bold uppercase tracking-wide">
                            Заполнено
                          </span>
                        );
                      case 'partial':
                        return (
                          <span className="text-[9px] px-2 py-0.5 rounded border bg-yellow-500/10 text-yellow-400 border-yellow-500/20 font-bold uppercase tracking-wide">
                            Частично
                          </span>
                        );
                      case 'missing':
                        return (
                          <span className="text-[9px] px-2 py-0.5 rounded border bg-red-500/10 text-red-400 border-red-500/20 font-bold uppercase tracking-wide">
                            Отсутствует
                          </span>
                        );
                      default:
                        return null;
                    }
                  };

                  const gapData = analysisResult.gap_analysis;

                  return (
                    <div className="space-y-6">
                      <h3 className="text-sm uppercase tracking-wider text-gray-500 font-bold px-1">
                        📋 Сопоставление с эталонной структурой ТЗ
                      </h3>
                      
                      <div className="grid grid-cols-1 gap-6">
                        {/* Section 1: Purpose */}
                        <div className="bg-surface border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-colors">
                          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                            <span className="font-semibold text-sm text-white">1. Суть проекта и цели</span>
                            {getStatusBadge(gapData?.sections?.purpose?.status)}
                          </div>
                          <div className="space-y-3 text-xs">
                            {gapData?.sections?.purpose?.extracted_text && (
                              <div>
                                <h5 className="font-medium text-gray-500 mb-1">Извлеченный фрагмент:</h5>
                                <p className="text-gray-300 bg-white/5 p-3 rounded-lg leading-relaxed italic">
                                  "{gapData.sections.purpose.extracted_text}"
                                </p>
                              </div>
                            )}
                            {gapData?.sections?.purpose?.gaps?.length > 0 && (
                              <div>
                                <h5 className="font-medium text-red-400/80 mb-1">Выявленные пробелы (Gaps):</h5>
                                <ul className="list-disc list-inside space-y-1 text-red-300/90 pl-1">
                                  {gapData.sections.purpose.gaps.map((g, i) => (
                                    <li key={i}>{g}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Section 2: Tech Stack */}
                        <div className="bg-surface border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-colors">
                          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                            <span className="font-semibold text-sm text-white">2. Технологический стек</span>
                            {getStatusBadge(gapData?.sections?.tech_stack?.status)}
                          </div>
                          <div className="space-y-4 text-xs">
                            <div>
                              <h5 className="font-medium text-gray-500 mb-2">Извлеченные технологии:</h5>
                              <div className="flex flex-wrap gap-2">
                                {gapData?.sections?.tech_stack?.extracted_technologies?.length > 0 ? (
                                  gapData.sections.tech_stack.extracted_technologies.map(tech => (
                                    <span key={tech} className="px-2.5 py-1 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-medium text-[11px]">
                                      {tech}
                                    </span>
                                  ))
                                ) : (
                                  <span className="text-gray-500 italic text-[11px]">Технологии в тексте не идентифицированы</span>
                                )}
                              </div>
                            </div>
                            {gapData?.sections?.tech_stack?.architecture_description && (
                              <div>
                                <h5 className="font-medium text-gray-500 mb-1">Описание архитектуры:</h5>
                                <p className="text-gray-300 bg-white/5 p-3 rounded-lg leading-relaxed">
                                  {gapData.sections.tech_stack.architecture_description}
                                </p>
                              </div>
                            )}
                            {gapData?.sections?.tech_stack?.gaps?.length > 0 && (
                              <div>
                                <h5 className="font-medium text-red-400/80 mb-1">Выявленные пробелы (Gaps):</h5>
                                <ul className="list-disc list-inside space-y-1 text-red-300/90 pl-1">
                                  {gapData.sections.tech_stack.gaps.map((g, i) => (
                                    <li key={i}>{g}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Section 3: Risks */}
                        <div className="bg-surface border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-colors">
                          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                            <span className="font-semibold text-sm text-white">3. Ключевые риски и безопасность</span>
                            {getStatusBadge(gapData?.sections?.risks?.status)}
                          </div>
                          <div className="space-y-3 text-xs">
                            {gapData?.sections?.risks?.extracted_risks?.length > 0 && (
                              <div>
                                <h5 className="font-medium text-gray-500 mb-2">Извлеченные риски:</h5>
                                <div className="space-y-2">
                                  {gapData.sections.risks.extracted_risks.map((risk, i) => (
                                    <div key={i} className="p-3 bg-white/5 rounded-lg border border-white/5 text-left">
                                      <div className="flex items-center justify-between mb-1.5">
                                        <span className="font-bold text-[10px] text-gray-400 uppercase tracking-wide">
                                          Риск {i + 1}
                                        </span>
                                        {risk.category && (
                                          <span className="text-[9px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                            {risk.category}
                                          </span>
                                        )}
                                      </div>
                                      <p className="text-gray-300 italic">"{risk.text}"</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {gapData?.sections?.risks?.gaps?.length > 0 && (
                              <div>
                                <h5 className="font-medium text-red-400/80 mb-1">Выявленные пробелы (Gaps):</h5>
                                <ul className="list-disc list-inside space-y-1 text-red-300/90 pl-1">
                                  {gapData.sections.risks.gaps.map((g, i) => (
                                    <li key={i}>{g}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Section 4: Economics */}
                        <div className="bg-surface border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-colors">
                          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                            <span className="font-semibold text-sm text-white">4. Экономический потенциал</span>
                            {getStatusBadge(gapData?.sections?.economics?.status)}
                          </div>
                          <div className="space-y-3 text-xs">
                            {gapData?.sections?.economics?.extracted_metrics?.length > 0 && (
                              <div>
                                <h5 className="font-medium text-gray-500 mb-2">Экономические маркеры и показатели:</h5>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                                  {gapData.sections.economics.extracted_metrics.map((metric, i) => (
                                    <div key={i} className="flex justify-between p-2.5 bg-white/5 rounded-lg border border-white/5">
                                      <span className="text-gray-400">{metric.metric}:</span>
                                      <span className="font-semibold text-white">{metric.value}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {gapData?.sections?.economics?.gaps?.length > 0 && (
                              <div>
                                <h5 className="font-medium text-red-400/80 mb-1">Выявленные пробелы (Gaps):</h5>
                                <ul className="list-disc list-inside space-y-1 text-red-300/90 pl-1">
                                  {gapData.sections.economics.gaps.map((g, i) => (
                                    <li key={i}>{g}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>

                      </div>
                    </div>
                  );
                })()}

                {/* 3. Clarifying Questions */}
                {analysisResult.gap_analysis?.clarifying_questions?.length > 0 && (
                  <div className="bg-gradient-to-br from-electric/10 to-emerald/5 border border-electric/20 rounded-2xl p-8 relative overflow-hidden animate-slide-up text-left">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-electric/10 rounded-full blur-3xl -z-10" />
                    <h3 className="text-sm font-bold text-electric uppercase tracking-wider mb-4 flex items-center gap-2">
                      💡 Уточняющие вопросы к заказчику (Рекомендации)
                    </h3>
                    <p className="text-xs text-gray-400 mb-5 leading-relaxed">
                      Чтобы закрыть критические пробелы в разделах "Риски" и "Экономика" (влияющих на инвестиционную привлекательность проекта), 
                      задайте заказчику следующие вопросы:
                    </p>
                    <div className="space-y-3">
                      {analysisResult.gap_analysis.clarifying_questions.map((q, idx) => (
                        <div key={idx} className="flex gap-4 p-4 rounded-xl bg-navy/60 border border-white/5 hover:border-white/10 transition-colors">
                          <span className="font-bold text-electric text-sm shrink-0">Q{idx + 1}</span>
                          <p className="text-xs text-gray-200 font-medium leading-relaxed">
                            {q}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            )}

          </div>
        )}
      </div>
    </div>
  )
}
