// ==========================================
// WorkspacePage — Document upload & NER analysis
// ==========================================
import { useState } from 'react'
import FileUpload from '../components/ui/FileUpload'
import NerHighlighter from '../components/ui/NerHighlighter'
import GaugeChart from '../components/ui/GaugeChart'

// --- Mock NER results (shown after "upload") ---
const MOCK_TEXT = `Проект "CRM Migration" предполагает миграцию legacy-системы на платформу Salesforce с бюджетом 2.5 млн рублей. Дедлайн — 15 марта 2026. Исполнитель: ООО "ТехноСофт". Стек: React, Golang, PostgreSQL, Docker, Kubernetes.`

const MOCK_ENTITIES = [
  { text: 'Salesforce',    type: 'Technology',   start: 72, end: 82 },
  { text: '2.5 млн рублей', type: 'Budget',      start: 95, end: 111 },
  { text: '15 марта 2026',  type: 'Deadline',    start: 124, end: 138 },
  { text: 'ООО "ТехноСофт"', type: 'Organization', start: 155, end: 171 },
  { text: 'React',          type: 'Technology',   start: 179, end: 184 },
  { text: 'Golang',         type: 'Technology',   start: 186, end: 192 },
  { text: 'PostgreSQL',     type: 'Technology',   start: 194, end: 204 },
  { text: 'Docker',         type: 'Technology',   start: 206, end: 212 },
  { text: 'Kubernetes',     type: 'Technology',   start: 214, end: 224 },
]

const MOCK_SUMMARY = 'The CRM Migration project involves transitioning a legacy system to Salesforce. Key risk factors include tight deadline constraints and significant budget allocation. Technology stack is modern and well-suited for enterprise deployment.'

export default function WorkspacePage() {
  const [uploaded, setUploaded] = useState(false)

  async function handleUpload(file) {
    // Simulate upload delay
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setUploaded(true)
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-5xl mx-auto">
        {/* --- Header --- */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight">Document Analysis Workspace</h1>
          <p className="text-gray-400 mt-2">Upload IT documentation for automated NLP analysis and risk assessment.</p>
        </div>

        {/* --- Upload Zone --- */}
        <div className="mb-12">
          <FileUpload onUpload={handleUpload} />
        </div>

        {/* --- Results Panel (shown after upload) --- */}
        {uploaded && (
          <div className="space-y-8 animate-fade-in">
            {/* Score gauges */}
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-surface border border-white/5 rounded-2xl p-6 flex flex-col items-center">
                <GaugeChart value={72} label="Risk Level" color="#FF3366" />
              </div>
              <div className="bg-surface border border-white/5 rounded-2xl p-6 flex flex-col items-center">
                <GaugeChart value={85} label="Profitability" color="#00FF66" />
              </div>
              <div className="bg-surface border border-white/5 rounded-2xl p-6 flex flex-col items-center">
                <GaugeChart value={91} label="Relevance" color="#00F0FF" />
              </div>
            </div>

            {/* Summary */}
            <div className="bg-surface border border-white/5 rounded-2xl p-8">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-4">
                📋 Document Summary
              </h3>
              <p className="text-gray-300 leading-relaxed">{MOCK_SUMMARY}</p>
            </div>

            {/* NER Highlighted Text */}
            <div className="bg-surface border border-white/5 rounded-2xl p-8">
              <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-4">
                🏷️ Named Entity Recognition
              </h3>
              <div className="bg-navy rounded-xl p-6 border border-white/5">
                <NerHighlighter text={MOCK_TEXT} entities={MOCK_ENTITIES} />
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
