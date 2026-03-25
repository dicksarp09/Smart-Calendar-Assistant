import React, { useEffect, useState, useCallback } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import TimeGridCalendar from './components/TimeGridCalendar'
import ChatPanel from './components/ChatPanel'
import EventModal from './components/EventModal'
import useCalendarStore from './store/useCalendarStore'

const App = () => {
  const { 
    isAuthenticated, 
    isLoading: authLoading,
    loginWithRedirect, 
    logout,
    getAccessTokenSilently,
    user
  } = useAuth0()
  
  const [isInitialized, setIsInitialized] = useState(false)
  const [isChatOpen, setIsChatOpen] = useState(false)

  // Development mode - auto-login with mock token
  const isDevMode = import.meta.env.VITE_ENVIRONMENT === 'development'
  
  // In dev mode, check for mock token instead of Auth0
  const [devAuthenticated, setDevAuthenticated] = useState(false)
  
  // Check for existing token on mount
  useEffect(() => {
    if (isDevMode) {
      const token = localStorage.getItem('auth_token')
      if (token) {
        setDevAuthenticated(true)
      }
    }
  }, [isDevMode])
  
  // Override isAuthenticated for dev mode
  const effectiveIsAuthenticated = isDevMode ? devAuthenticated : isAuthenticated

  // Get token and store in localStorage for API calls
  useEffect(() => {
    if (effectiveIsAuthenticated && !isDevMode) {
      // Only get real Auth0 token in production mode
      const setupAuth = async () => {
        try {
          const token = await getAccessTokenSilently()
          localStorage.setItem('auth_token', token)
          localStorage.setItem('user', JSON.stringify(user))
          setIsInitialized(true)
        } catch (error) {
          console.error('Error getting access token:', error)
        }
      }
      setupAuth()
    } else if (effectiveIsAuthenticated && isDevMode) {
      // In dev mode, just ensure user is set
      setIsInitialized(true)
    }
  }, [effectiveIsAuthenticated, isDevMode, getAccessTokenSilently, user])

  const handleLogin = () => {
    if (isDevMode) {
      // Generate a valid mock JWT-like token for development
      const mockPayload = {
        sub: 'dev|user123',
        email: 'dev@example.com',
        name: 'Dev User',
        iss: 'https://dev-s62m25igz6sdix66.eu.auth0.com/',
        aud: 'https://calendar-agent-api',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour
      }
      const mockToken = btoa(JSON.stringify(mockPayload))
      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('user', JSON.stringify({ name: 'Dev User', email: 'dev@example.com' }))
      setDevAuthenticated(true)
    } else {
      loginWithRedirect()
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    if (isDevMode) {
      setDevAuthenticated(false)
    } else {
      logout({ logoutParams: { returnTo: window.location.origin } })
    }
  }

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e) => {
    // Ignore if typing in input/textarea
    if (e.target.matches('input, textarea')) return
    
    // Cmd/Ctrl + K: Focus chat
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      setIsChatOpen(true)
    }
    
    // Cmd/Ctrl + N: New event
    if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
      e.preventDefault()
      useCalendarStore.getState().openModal('create')
    }
    
    // Escape: Close chat on mobile
    if (e.key === 'Escape') {
      setIsChatOpen(false)
    }
  }, [])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="loading">
        <p>Loading...</p>
      </div>
    )
  }

  // Login screen
  if (!effectiveIsAuthenticated) {
    return (
      <div className="app-container">
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          textAlign: 'center',
          padding: '2rem'
        }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            color: '#4f46e5',
            marginBottom: '1rem'
          }}>
            Calendar Intelligence
          </h1>
          <p style={{
            fontSize: '1.125rem',
            color: '#6b7280',
            marginBottom: '2rem',
            maxWidth: '500px'
          }}>
            Your AI-powered calendar assistant. Manage your schedule with natural language and let AI help you stay organized.
          </p>
          <button 
            onClick={handleLogin}
            className="login-button"
            style={{
              padding: '0.75rem 2rem',
              fontSize: '1rem'
            }}
          >
            {isDevMode ? 'Dev Login' : 'Log In with Auth0'}
          </button>
        </div>
      </div>
    )
  }

  // Get user display name
  const getUserDisplay = () => {
    if (isDevMode) {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        const userData = JSON.parse(storedUser)
        return userData.name || userData.email || 'Dev User'
      }
      return 'Dev User'
    }
    return user?.name || user?.email
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1 className="header-title">Calendar Intelligence</h1>
        <div className="header-actions">
          <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            {getUserDisplay()}
          </span>
          <button 
            onClick={handleLogout}
            className="login-button"
            style={{
              backgroundColor: '#ef4444'
            }}
          >
            Log Out
          </button>
        </div>
      </header>

      <main className="main-content">
        <div className="calendar-container">
          <TimeGridCalendar />
        </div>
        <ChatPanel isOpen={isChatOpen} onToggle={() => setIsChatOpen(!isChatOpen)} />
      </main>

      <EventModal />
    </div>
  )
}

export default App
