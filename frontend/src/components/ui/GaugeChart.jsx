// ==========================================
// GaugeChart — SVG speedometer / gauge via Recharts
// Props: value (0-100), label, color
// ==========================================
import { PieChart, Pie, Cell } from 'recharts'

export default function GaugeChart({ value = 0, label = '', color = '#00F0FF', size = 160 }) {
  const safeValue = Math.min(Math.max(value, 0), 100)
  
  // Data for the PieChart: 
  // - First slice is the "filled" part (progress)
  // - Second slice is the "empty" part
  const data = [
    { name: 'progress', value: safeValue },
    { name: 'remainder', value: 100 - safeValue },
  ]

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size / 2 }}>
        <PieChart width={size} height={size}>
          <Pie
            data={data}
            cx={size / 2}
            cy={size / 2}
            startAngle={180}
            endAngle={0}
            innerRadius={size / 2 - 15}
            outerRadius={size / 2 - 5}
            paddingAngle={0}
            dataKey="value"
            stroke="none"
          >
            {/* The filled progress part */}
            <Cell fill={color} style={{ filter: `drop-shadow(0 0 6px ${color}40)` }} />
            {/* The empty background part */}
            <Cell fill="rgba(255,255,255,0.06)" />
          </Pie>
        </PieChart>
        
        {/* Value text placed exactly at the bottom-center of the half-pie */}
        <div 
          className="absolute bottom-0 left-0 right-0 text-center flex flex-col items-center justify-end"
          style={{ height: '100%' }}
        >
          <span className="text-2xl font-bold fill-white" style={{ marginBottom: '-4px' }}>
            {Math.round(safeValue)}%
          </span>
        </div>
      </div>
      
      {label && (
        <span className="text-[11px] uppercase tracking-widest text-gray-500 font-medium mt-3">
          {label}
        </span>
      )}
    </div>
  )
}
