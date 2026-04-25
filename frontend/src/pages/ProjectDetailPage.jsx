// ==========================================
// ProjectDetailPage — Project detail with tabs
// ==========================================
import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import TopBar from '../components/layout/TopBar'
import DocumentCard from '../components/documents/DocumentCard'
import DocumentForm from '../components/documents/DocumentForm'
import PredictionCard from '../components/predictions/PredictionCard'
import Modal from '../components/ui/Modal'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import { StatusBadge } from '../components/ui/Badge'
import { useDocuments } from '../hooks/useDocuments'
import { usePredictions } from '../hooks/usePredictions'
import { getProjectById } from '../api/projects'
import { useEffect } from 'react'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit', month: 'long', year: 'numeric',
  })
}

export default function ProjectDetailPage() {
  const { id }                          = useParams()
  const [project, setProject]           = useState(null)
  const [projectLoading, setProjectLoading] = useState(true)
  const [activeTab, setActiveTab]       = useState('documents')
  const [showDocModal, setShowDocModal] = useState(false)
  const [saving, setSaving]             = useState(false)
  const [docError, setDocError]         = useState(null)

  const { documents, loading: docsLoading, create: createDoc, remove: removeDoc } = useDocuments(id)
  const { predictions, loading: predsLoading, generating, generate } = usePredictions(id)

  // --- Load project ---
  useEffect(() => {
    getProjectById(id)
      .then(setProject)
      .finally(() => setProjectLoading(false))
  }, [id])

  // --- Handlers ---
  async function handleCreateDoc(formData) {
    setSaving(true)
    setDocError(null)
    try {
      await createDoc(formData)
      setShowDocModal(false)
    } catch (err) {
      setDocError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleGenerate() {
    try {
      await generate()
      setActiveTab('predictions')
    } catch {
      // error is stored in hook
    }
  }

  if (projectLoading) return (
    <>
      <TopBar title="Загрузка..." breadcrumb="Проект" />
      <div className="page"><Spinner /></div>
    </>
  )

  if (!project) return (
    <>
      <TopBar title="Проект не найден" breadcrumb="Проекты" />
      <div className="page">
        <EmptyState icon="🔍" title="Проект не найден" description="Возможно, он был удалён." />
      </div>
    </>
  )

  return (
    <>
      <TopBar
        title={project.name}
        breadcrumb={`Проекты / ${project.name}`}
        actions={
          <button
            className="btn btn-primary"
            id="btn-generate-prediction"
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? '⚙ Анализ...' : '⚡ Запустить анализ'}
          </button>
        }
      />

      <div className="page">
        {/* Back */}
        <Link to="/" className="back-link">← Все проекты</Link>

        {/* Project Header */}
        <div className="project-detail-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 className="project-detail-title">{project.name}</h1>
            <StatusBadge status={project.status} />
          </div>
          <div className="project-detail-meta">
            <span className="project-detail-date">Создан: {formatDate(project.created_at)}</span>
            <span className="project-detail-date">·</span>
            <span className="project-detail-date">{documents.length} документ(ов)</span>
            <span className="project-detail-date">·</span>
            <span className="project-detail-date">{predictions.length} анализ(ов)</span>
          </div>
          {project.description && (
            <p className="project-detail-desc">{project.description}</p>
          )}
        </div>

        <div className="divider" />

        {/* Tabs */}
        <div className="tabs">
          <button
            id="tab-documents"
            className={`tab${activeTab === 'documents' ? ' active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            📄 Документы
            <span className="tab-count">{documents.length}</span>
          </button>
          <button
            id="tab-predictions"
            className={`tab${activeTab === 'predictions' ? ' active' : ''}`}
            onClick={() => setActiveTab('predictions')}
          >
            🧠 Прогнозы
            <span className="tab-count">{predictions.length}</span>
          </button>
        </div>

        {/* ========== Documents Tab ========== */}
        {activeTab === 'documents' && (
          <>
            <div className="generate-section">
              <p className="generate-hint">
                Добавьте технические задания, архитектурные документы и логи
                — они будут использоваться NLP-модулем для анализа.
              </p>
              <button
                className="btn btn-secondary"
                id="btn-add-document"
                onClick={() => setShowDocModal(true)}
              >
                + Добавить документ
              </button>
            </div>

            {docsLoading && <Spinner />}

            {!docsLoading && documents.length === 0 && (
              <EmptyState
                icon="📄"
                title="Документы не добавлены"
                description="Загрузите ТЗ, архитектурные решения или логи для анализа."
                action={
                  <button className="btn btn-primary" onClick={() => setShowDocModal(true)}>
                    + Добавить документ
                  </button>
                }
              />
            )}

            {!docsLoading && documents.length > 0 && (
              <div className="grid" style={{ gridTemplateColumns: '1fr' }}>
                {documents.map((d) => (
                  <DocumentCard key={d.id} doc={d} onDelete={removeDoc} />
                ))}
              </div>
            )}
          </>
        )}

        {/* ========== Predictions Tab ========== */}
        {activeTab === 'predictions' && (
          <>
            <div className="generate-section">
              <p className="generate-hint">
                Нажмите «Запустить анализ» — система обработает документы
                и вычислит оценки рентабельности, рисков и актуальности.
              </p>
              <button
                className="btn btn-primary"
                id="btn-generate-prediction-tab"
                onClick={handleGenerate}
                disabled={generating || documents.length === 0}
                title={documents.length === 0 ? 'Сначала добавьте документы' : ''}
              >
                {generating ? '⚙ Выполняется анализ...' : '⚡ Запустить анализ'}
              </button>
            </div>

            {predsLoading && <Spinner />}

            {!predsLoading && predictions.length === 0 && (
              <EmptyState
                icon="🧠"
                title="Анализ ещё не запускался"
                description="Запустите NLP-анализ, чтобы получить оценки проекта."
              />
            )}

            {!predsLoading && predictions.length > 0 && (
              <div className="grid" style={{ gridTemplateColumns: '1fr', gap: 16 }}>
                {predictions.map((p) => (
                  <PredictionCard key={p.id} prediction={p} />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Add Document Modal */}
      {showDocModal && (
        <Modal
          title="Добавить документ"
          onClose={() => { setShowDocModal(false); setDocError(null) }}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowDocModal(false)}>Отмена</button>
              <button
                className="btn btn-primary"
                form="document-form"
                type="submit"
                disabled={saving}
              >
                {saving ? 'Сохранение...' : 'Добавить'}
              </button>
            </>
          }
        >
          <DocumentForm onSubmit={handleCreateDoc} loading={saving} />
          {docError && (
            <div style={{ color: 'var(--danger)', fontSize: 12, marginTop: 8 }}>⚠ {docError}</div>
          )}
        </Modal>
      )}
    </>
  )
}
