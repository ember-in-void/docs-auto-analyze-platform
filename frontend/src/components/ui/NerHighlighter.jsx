// ==========================================
// NerHighlighter — Named Entity Recognition display
// Highlights entities in text with colored tags
// ==========================================

/**
 * Entity type → color mapping
 * WHY: Different entity types need distinct visual treatment
 * so the user can quickly identify categories at a glance.
 */
const ENTITY_COLORS = {
  Technology:   { bg: 'bg-electric/15', text: 'text-electric',  border: 'border-electric/30' },
  Budget:       { bg: 'bg-emerald/15',  text: 'text-emerald',   border: 'border-emerald/30' },
  Deadline:     { bg: 'bg-crimson/15',  text: 'text-crimson',   border: 'border-crimson/30' },
  Organization: { bg: 'bg-purple-400/15', text: 'text-purple-400', border: 'border-purple-400/30' },
  Person:       { bg: 'bg-amber-400/15',  text: 'text-amber-400',  border: 'border-amber-400/30' },
}

/**
 * NerHighlighter renders text with inline entity tags.
 * @param {Array} entities - [{ text: "React", type: "Technology", start: 0, end: 5 }]
 * @param {string} text - original text to display
 */
export default function NerHighlighter({ text = '', entities = [] }) {
  if (!text) return null

  // --- Sort entities by position to avoid overlap ---
  const sorted = [...entities].sort((a, b) => a.start - b.start)

  const parts = []
  let cursor = 0

  sorted.forEach((entity, i) => {
    // Plain text before entity
    if (entity.start > cursor) {
      parts.push(
        <span key={`t-${i}`} className="text-gray-300">
          {text.slice(cursor, entity.start)}
        </span>
      )
    }

    // Entity tag
    const colors = ENTITY_COLORS[entity.type] || ENTITY_COLORS.Technology
    const safeText = entity.text.toLowerCase().replace(/[^a-zа-я0-9]/g, '-')
    parts.push(
      <span
        key={`e-${i}`}
        id={`entity-${safeText}`}
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-sm font-medium border ${colors.bg} ${colors.text} ${colors.border} transition-all duration-300`}
        title={entity.type}
      >
        {entity.text}
        <span className="text-[10px] opacity-60 uppercase">{entity.type}</span>
      </span>
    )

    cursor = entity.end
  })

  // Remaining text
  if (cursor < text.length) {
    parts.push(
      <span key="tail" className="text-gray-300">
        {text.slice(cursor)}
      </span>
    )
  }

  return <div className="leading-relaxed">{parts}</div>
}
