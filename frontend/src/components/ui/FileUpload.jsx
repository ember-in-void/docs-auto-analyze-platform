// ==========================================
// FileUpload — Drag-and-drop file upload zone
// States: idle → dragging → uploading → complete
// ==========================================
import { useState, useRef } from 'react'

export default function FileUpload({ onUpload, accept = '.pdf,.docx,.txt' }) {
  const [state, setState] = useState('idle') // idle | dragging | uploading | complete
  const [file, setFile]   = useState(null)
  const inputRef = useRef(null)

  // --- Drag handlers ---
  function handleDragOver(e) {
    e.preventDefault()
    setState('dragging')
  }

  function handleDragLeave() {
    setState('idle')
  }

  function handleDrop(e) {
    e.preventDefault()
    const dropped = e.dataTransfer.files[0]
    if (dropped) processFile(dropped)
  }

  function handleSelect(e) {
    const selected = e.target.files[0]
    if (selected) processFile(selected)
  }

  async function processFile(f) {
    setFile(f)
    setState('uploading')
    try {
      if (onUpload) await onUpload(f)
      setState('complete')
    } catch {
      setState('idle')
    }
  }

  // --- Visual states ---
  const stateStyles = {
    idle:      'border-white/10 hover:border-electric/30',
    dragging:  'border-electric bg-electric/5 scale-[1.02]',
    uploading: 'border-amber-400/30 bg-amber-400/5',
    complete:  'border-emerald/30 bg-emerald/5',
  }

  const stateIcons = {
    idle:      '📄',
    dragging:  '⬇️',
    uploading: '⏳',
    complete:  '✅',
  }

  const stateLabels = {
    idle:      'Drag & drop a file here, or click to browse',
    dragging:  'Drop your file here...',
    uploading: `Uploading ${file?.name}...`,
    complete:  `${file?.name} uploaded successfully!`,
  }

  return (
    <div
      className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-500 ${stateStyles[state]}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => state !== 'uploading' && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleSelect}
        className="hidden"
      />

      <div className="text-4xl mb-4">{stateIcons[state]}</div>
      <p className="text-sm text-gray-400 mb-2">{stateLabels[state]}</p>
      <p className="text-xs text-gray-600">Supported: PDF, DOCX, TXT (max 10MB)</p>

      {/* Upload progress bar (mock) */}
      {state === 'uploading' && (
        <div className="mt-6 h-1 bg-white/5 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-electric to-emerald rounded-full animate-pulse" style={{ width: '70%' }} />
        </div>
      )}

      {state === 'complete' && (
        <button
          onClick={(e) => { e.stopPropagation(); setFile(null); setState('idle') }}
          className="mt-4 text-xs text-electric hover:underline"
        >
          Upload another file
        </button>
      )}
    </div>
  )
}
