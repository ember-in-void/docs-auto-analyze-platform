// ==========================================
// ScoreGauge — SVG arc gauge for 0.0–1.0 scores
// ==========================================

const GAUGE_COLORS = {
  profitability: { low: '#ef4444', mid: '#f59e0b', high: '#22c55e' },
  risk:          { low: '#22c55e', mid: '#f59e0b', high: '#ef4444' },
  relevance:     { low: '#6366f1', mid: '#6366f1', high: '#6366f1' },
}

function getColor(type, value) {
  const palette = GAUGE_COLORS[type] ?? GAUGE_COLORS.relevance
  if (type === 'risk') {
    if (value < 0.35) return palette.low
    if (value < 0.65) return palette.mid
    return palette.high
  }
  if (value < 0.4) return palette.low
  if (value < 0.7) return palette.mid
  return palette.high
}

export default function ScoreGauge({ value = 0, label, type = 'relevance' }) {
  // SVG arc parameters
  const R    = 42
  const CX   = 56
  const CY   = 56
  const FULL = 2 * Math.PI * R
  const ARC  = FULL * 0.7          // 252° arc
  const OFFSET = FULL * 0.15       // start at ~-126° (top-left)
  const filled = ARC * Math.min(Math.max(value, 0), 1)
  const color  = getColor(type, value)
  const pct    = Math.round(value * 100)

  return (
    <div className="score-gauge-wrap">
      <svg width="112" height="80" viewBox="0 0 112 80" style={{ overflow: 'visible' }}>
        {/* Track */}
        <circle
          cx={CX} cy={CY} r={R}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="7"
          strokeDasharray={`${ARC} ${FULL - ARC}`}
          strokeDashoffset={OFFSET}
          strokeLinecap="round"
          transform={`rotate(-234 ${CX} ${CY})`}
        />
        {/* Fill */}
        <circle
          cx={CX} cy={CY} r={R}
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeDasharray={`${filled} ${FULL - filled}`}
          strokeDashoffset={OFFSET}
          strokeLinecap="round"
          transform={`rotate(-234 ${CX} ${CY})`}
          style={{ transition: 'stroke-dasharray 0.6s ease', filter: `drop-shadow(0 0 6px ${color}80)` }}
        />
        {/* Centre value */}
        <text
          x={CX} y={CY + 5}
          textAnchor="middle"
          fontSize="16"
          fontWeight="700"
          fontFamily="Inter, sans-serif"
          fill="var(--text-primary)"
        >
          {pct}%
        </text>
      </svg>
      <span className="score-gauge-label">{label}</span>
    </div>
  )
}
