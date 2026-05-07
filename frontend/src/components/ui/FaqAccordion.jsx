// ==========================================
// FaqAccordion — Expandable FAQ section
// ==========================================
import { useState } from 'react'

const FAQ_DATA = [
  {
    q: 'What types of documents does DocuAudit AI support?',
    a: 'We support PDF, DOCX, and TXT formats. Our NLP engine processes Technical Requirements, Architecture Documents, Business Plans, and project logs up to 10MB.',
  },
  {
    q: 'How accurate is the risk assessment?',
    a: 'Our NLP model (based on RuBERT for Russian-language docs) achieves 92%+ accuracy on sentiment-based risk classification. Results improve with more detailed documentation.',
  },
  {
    q: 'Can I integrate DocuAudit AI into existing workflows?',
    a: 'Yes. The platform exposes a REST API built in Go for high-throughput integration. You can programmatically upload documents and receive analysis results via JSON endpoints.',
  },
  {
    q: 'What is the system architecture?',
    a: 'DocuAudit AI uses a microservice architecture: React Frontend → Go Backend (REST API) → Python NLP Service (FastAPI + Transformers) → PostgreSQL. Everything runs in Docker containers.',
  },
  {
    q: 'Is my data secure?',
    a: 'All communication uses JWT authentication. Documents are processed in memory and never stored in raw form after analysis. The platform runs entirely in your own Docker environment.',
  },
]

export default function FaqAccordion() {
  const [openIndex, setOpenIndex] = useState(null)

  return (
    <div className="space-y-3">
      {FAQ_DATA.map((item, i) => (
        <div key={i} className="border border-white/5 rounded-xl overflow-hidden">
          <button
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
            className="w-full flex items-center justify-between px-6 py-5 text-left hover:bg-white/[0.02] transition-colors"
          >
            <span className="text-sm font-medium text-gray-200">{item.q}</span>
            <span
              className={`text-gray-500 transition-transform duration-300 ${openIndex === i ? 'rotate-45' : ''}`}
            >
              +
            </span>
          </button>
          <div
            className="overflow-hidden transition-all duration-500"
            style={{ maxHeight: openIndex === i ? '200px' : '0px' }}
          >
            <p className="px-6 pb-5 text-sm text-gray-400 leading-relaxed">
              {item.a}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
