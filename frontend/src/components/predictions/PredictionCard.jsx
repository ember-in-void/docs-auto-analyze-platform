// ==========================================
// PredictionCard — Full analysis result card
// ==========================================
import ScoreGauge from './ScoreGauge'

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function PredictionCard({ prediction }) {
  const { profitability_score, risk_score, relevance_score, summary, keywords, model_version, generated_at } = prediction

  return (
    <div className="prediction-card">
      {/* Header */}
      <div className="prediction-header">
        <div className="prediction-header-left">
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            Результаты NLP-анализа
          </span>
          <span className="prediction-model-badge">{model_version}</span>
        </div>
        <span className="prediction-date">🕐 {formatDate(generated_at)}</span>
      </div>

      {/* Score Gauges */}
      <div className="prediction-scores">
        <div className="prediction-score-cell">
          <ScoreGauge
            value={profitability_score}
            label="Рентабельность"
            type="profitability"
          />
        </div>
        <div className="prediction-score-cell">
          <ScoreGauge
            value={risk_score}
            label="Уровень риска"
            type="risk"
          />
        </div>
        <div className="prediction-score-cell">
          <ScoreGauge
            value={relevance_score}
            label="Актуальность"
            type="relevance"
          />
        </div>
      </div>

      {/* Body */}
      <div className="prediction-body">
        <p className="prediction-summary">{summary}</p>

        {keywords?.length > 0 && (
          <>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
              Ключевые термины
            </div>
            <div className="prediction-keywords">
              {keywords.map((kw) => (
                <span key={kw} className="prediction-keyword">{kw}</span>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
