// ==========================================
// GaugeChart — SVG speedometer / gauge
// Props: value (0-100), label, color
// ==========================================

/**
 * GaugeChart renders a semi-circular SVG gauge.
 * WHY: Provides an intuitive visual representation of risk/profitability
 * scores without heavy charting libraries.
 */
export default function GaugeChart({ value = 0, label = '', color = '#00F0FF', size = 120 }) {
  // --- SVG arc math ---
  const radius = 40
  const circumference = Math.PI * radius // semi-circle
  const progress = (Math.min(Math.max(value, 0), 100) / 100) * circumference
  const center = size / 2

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size / 2 + 16} viewBox={`0 0 ${size} ${size / 2 + 16}`}>
        {/* Background arc */}
        <path
          d={`M ${center - radius} ${center} A ${radius} ${radius} 0 0 1 ${center + radius} ${center}`}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d={`M ${center - radius} ${center} A ${radius} ${radius} 0 0 1 ${center + radius} ${center}`}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          style={{ transition: 'stroke-dashoffset 1s ease-out', filter: `drop-shadow(0 0 6px ${color}40)` }}
        />
        {/* Value text */}
        <text x={center} y={center - 8} textAnchor="middle" className="fill-white text-2xl font-bold" style={{ fontSize: '22px' }}>
          {Math.round(value)}%
        </text>
      </svg>
      {label && (
        <span className="text-[11px] uppercase tracking-widest text-gray-500 font-medium">
          {label}
        </span>
      )}
    </div>
  )
}
