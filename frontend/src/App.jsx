// ==========================================
// App — Root router and layout shell
// ==========================================
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/"                  element={<ProjectsPage />} />
            <Route path="/projects/:id"      element={<ProjectDetailPage />} />
            <Route path="*"                  element={
              <div className="page" style={{ paddingTop: 80, textAlign: 'center' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>404</div>
                <p style={{ color: 'var(--text-muted)' }}>Страница не найдена</p>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
