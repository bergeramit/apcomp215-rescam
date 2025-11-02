import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import { getStoredUser } from './auth/googleAuth'

function AppContent() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const location = useLocation()

  const checkAuth = () => {
    const user = getStoredUser()
    setIsAuthenticated(!!user)
    setLoading(false)
  }

  useEffect(() => {
    checkAuth()
  }, [])

  // Re-check auth when route changes (in case user just signed in)
  useEffect(() => {
    checkAuth()
  }, [location])

  // Listen for storage changes (when auth data is stored)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'google_user' || e.key === 'google_access_token') {
        checkAuth()
      }
    }
    window.addEventListener('storage', handleStorageChange)
    // Also listen for same-tab storage changes via custom event
    window.addEventListener('auth-storage-change', checkAuth)
    
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('auth-storage-change', checkAuth)
    }
  }, [])

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading...</div>
  }

  return (
    <Routes>
      <Route path="/" element={isAuthenticated ? <Dashboard /> : <Login />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
