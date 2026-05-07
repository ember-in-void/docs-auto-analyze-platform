// ==========================================
// LandingPage — Hero, Features, Stats, FAQ
// ==========================================
import { Link } from 'react-router-dom'
import FaqAccordion from '../components/ui/FaqAccordion'
import Footer from '../components/layout/Footer'

// --- Features data ---
const FEATURES = [
  {
    icon: '📊',
    title: 'Document Summarization',
    desc: 'Automatically extract key points from Technical Requirements, Architecture Documents, and Project Proposals.',
  },
  {
    icon: '⚡',
    title: 'Risk Analysis',
    desc: 'NLP-powered sentiment analysis identifies potential project risks from unstructured documentation.',
  },
  {
    icon: '🏷️',
    title: 'NER Extraction',
    desc: 'Named Entity Recognition highlights Technologies, Budgets, Deadlines, and Organizations in your docs.',
  },
]

// --- Stats data ---
const STATS = [
  { value: '99.2%', label: 'Accuracy Score' },
  { value: '4,200+', label: 'Documents Analyzed' },
  { value: '12ms', label: 'Avg Latency' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* ========== HERO ========== */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Animated grid background */}
        <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-40" />

        {/* Gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-electric/5 rounded-full blur-[120px] animate-float" />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-emerald/5 rounded-full blur-[100px] animate-float animation-delay-200" />

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-24">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-electric/20 bg-electric/5 text-electric text-xs font-semibold uppercase tracking-wider mb-8 animate-fade-in">
            <span className="w-1.5 h-1.5 rounded-full bg-electric animate-pulse" />
            NLP-Powered Analysis Engine
          </div>

          {/* Headline */}
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6 animate-fade-in">
            Stop manual audits.
            <br />
            <span className="text-gradient">Let NLP evaluate</span>
            <br />
            your IT docs.
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 animate-fade-in animation-delay-200">
            DocuAudit AI connects your documentation, automates risk profiling,
            and surfaces profitability insights before you know to ask.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in animation-delay-400">
            <Link
              to="/dashboard"
              className="px-8 py-3.5 rounded-xl bg-electric text-navy-dark font-bold text-sm uppercase tracking-wider hover:shadow-[0_0_30px_rgba(0,240,255,0.3)] transition-all duration-500"
            >
              Start Free Trial
            </Link>
            <Link
              to="/architecture"
              className="px-8 py-3.5 rounded-xl border border-white/10 text-gray-300 font-semibold text-sm uppercase tracking-wider hover:bg-white/5 transition-colors"
            >
              See How It Works
            </Link>
          </div>

          {/* Stats bar */}
          <div className="mt-20 grid grid-cols-3 gap-8 max-w-lg mx-auto border-t border-white/5 pt-10 animate-fade-in animation-delay-600">
            {STATS.map(({ value, label }) => (
              <div key={label} className="text-center">
                <div className="text-2xl md:text-3xl font-light tracking-tight text-white">{value}</div>
                <div className="text-[10px] uppercase tracking-[0.15em] text-gray-500 mt-1">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== FEATURES ========== */}
      <section className="py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              Enterprise-grade <span className="text-gradient">document intelligence</span>
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Three core capabilities that transform how you evaluate IT projects.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES.map(({ icon, title, desc }, i) => (
              <div
                key={i}
                className="group p-8 rounded-2xl border border-white/5 bg-surface hover:border-electric/20 hover:bg-surface-hover transition-all duration-500"
              >
                <div className="text-4xl mb-5">{icon}</div>
                <h3 className="text-lg font-semibold mb-3 group-hover:text-electric transition-colors">{title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== FAQ ========== */}
      <section className="py-32 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold tracking-tight mb-12 text-center">
            Frequently Asked Questions
          </h2>
          <FaqAccordion />
        </div>
      </section>

      <Footer />
    </div>
  )
}
