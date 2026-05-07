// ==========================================
// Footer — Minimal DocuAudit AI footer
// ==========================================

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-navy-dark">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-electric to-emerald" />
            <span className="text-sm font-semibold tracking-tight text-gray-300">
              DocuAudit AI
            </span>
          </div>
          <p className="text-xs text-gray-500">
            © 2026 DocuAudit AI — Automated Risk & Profitability Assessment
          </p>
          <div className="flex gap-6 text-xs text-gray-500">
            <span>Diploma Project</span>
            <span>NLP Platform</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
