// ==========================================
// ArchitecturePage — System architecture for thesis
// Visual layout of the microservice stack
// ==========================================

// --- Architecture layers ---
const LAYERS = [
  {
    icon: '🖥️',
    name: 'React Frontend',
    tech: 'Vite + Tailwind CSS',
    desc: 'SPA with responsive UI, interactive charts, and real-time document analysis interface.',
    color: 'border-electric/30 bg-electric/5',
    textColor: 'text-electric',
  },
  {
    icon: '🔗',
    name: 'REST API',
    tech: 'HTTP/JSON',
    desc: 'RESTful communication layer between frontend and backend with JWT authentication.',
    color: 'border-white/10 bg-white/5',
    textColor: 'text-gray-300',
  },
  {
    icon: '⚡',
    name: 'Go Backend',
    tech: 'Golang + Chi Router',
    desc: 'High-performance API server handling auth, CRUD, and orchestration of NLP analysis requests.',
    color: 'border-cyan-400/30 bg-cyan-400/5',
    textColor: 'text-cyan-400',
  },
  {
    icon: '📡',
    name: 'HTTP Client',
    tech: 'Internal HTTP',
    desc: 'Service-to-service communication for NLP analysis requests between Go backend and Python service.',
    color: 'border-white/10 bg-white/5',
    textColor: 'text-gray-300',
  },
  {
    icon: '🧠',
    name: 'Python NLP Service',
    tech: 'FastAPI + Transformers',
    desc: 'RuBERT-based sentiment analysis, Named Entity Recognition, and document summarization engine.',
    color: 'border-emerald/30 bg-emerald/5',
    textColor: 'text-emerald',
  },
  {
    icon: '🗄️',
    name: 'PostgreSQL',
    tech: 'v16 + pgx Driver',
    desc: 'Relational database storing projects, documents, analysis results, and user accounts.',
    color: 'border-blue-400/30 bg-blue-400/5',
    textColor: 'text-blue-400',
  },
]

// --- Tech stack cards ---
const TECH_STACK = [
  { name: 'React 18',       category: 'Frontend',   desc: 'Component-based UI library with hooks and context API' },
  { name: 'Tailwind CSS',   category: 'Styling',     desc: 'Utility-first CSS framework for rapid UI development' },
  { name: 'Go 1.25',        category: 'Backend',     desc: 'High-performance compiled language for the API server' },
  { name: 'Chi Router',     category: 'Routing',     desc: 'Lightweight HTTP router with middleware support' },
  { name: 'FastAPI',        category: 'ML Service',  desc: 'Modern Python web framework for the NLP microservice' },
  { name: 'Transformers',   category: 'NLP',         desc: 'Hugging Face library for RuBERT model inference' },
  { name: 'PostgreSQL 16',  category: 'Database',    desc: 'Enterprise-grade relational database with UUID support' },
  { name: 'Docker Compose', category: 'DevOps',      desc: 'Container orchestration for all microservices' },
]

export default function ArchitecturePage() {
  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-5xl mx-auto">
        {/* --- Header --- */}
        <div className="text-center mb-16">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            System <span className="text-gradient">Architecture</span>
          </h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            A microservice-based platform connecting React, Golang, Python NLP, and PostgreSQL — 
            all containerized with Docker Compose.
          </p>
        </div>

        {/* --- Architecture Flow --- */}
        <div className="relative mb-24">
          {/* Vertical connector line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-electric/30 via-emerald/20 to-blue-400/20 -translate-x-1/2" />

          <div className="space-y-4">
            {LAYERS.map((layer, i) => (
              <div key={i} className="relative flex items-center justify-center animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
                {/* Node dot */}
                <div className="absolute left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-surface border-2 border-white/20 z-10" />

                {/* Card */}
                <div className={`w-full max-w-md mx-auto border rounded-xl p-5 ${layer.color} ${i % 2 === 0 ? 'mr-auto md:mr-[52%]' : 'ml-auto md:ml-[52%]'}`}>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl">{layer.icon}</span>
                    <div>
                      <h3 className={`font-semibold text-sm ${layer.textColor}`}>{layer.name}</h3>
                      <span className="text-[11px] text-gray-500">{layer.tech}</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{layer.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Docker wrapper label */}
          <div className="mt-8 text-center">
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-surface text-xs text-gray-400 font-medium">
              🐳 All services wrapped in Docker Compose
            </span>
          </div>
        </div>

        {/* --- Tech Stack Grid --- */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold tracking-tight mb-8 text-center">Technology Stack</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {TECH_STACK.map((tech, i) => (
              <div key={i} className="p-5 rounded-xl border border-white/5 bg-surface hover:border-electric/20 transition-all duration-500 group">
                <span className="text-[10px] uppercase tracking-wider text-gray-600 font-medium">{tech.category}</span>
                <h4 className="text-sm font-semibold mt-1 group-hover:text-electric transition-colors">{tech.name}</h4>
                <p className="text-xs text-gray-500 mt-2 leading-relaxed">{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
