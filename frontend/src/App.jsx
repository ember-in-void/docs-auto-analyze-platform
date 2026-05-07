// ==========================================
// App — Root component with routing
// ==========================================
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/layout/Navbar'
import ProtectedRoute from './components/auth/ProtectedRoute'

// --- Pages ---
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/DashboardPage'
import WorkspacePage from './pages/WorkspacePage'
import ArchitecturePage from './pages/ArchitecturePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

// --- Layout wrapper: hides Navbar on auth pages ---
function AppLayout() {
  const location = useLocation()
  const isAuthPage = ['/login', '/register'].includes(location.pathname)

  return (
    <>
      {!isAuthPage && <Navbar />}
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/architecture" element={<ArchitecturePage />} />

        {/* Protected routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />
        <Route path="/workspace" element={
          <ProtectedRoute><WorkspacePage /></ProtectedRoute>
        } />
        <Route path="/projects/:id" element={
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />

        {/* 404 */}
        <Route path="*" element={
          <div className="min-h-screen flex flex-col items-center justify-center">
            <div className="text-6xl font-bold text-gradient mb-4">404</div>
            <p className="text-gray-500">Page not found</p>
          </div>
        } />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </AuthProvider>
  )
}
