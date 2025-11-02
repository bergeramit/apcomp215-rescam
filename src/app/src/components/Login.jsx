import { useEffect, useState } from 'react'
import { signInWithGoogle, initGoogleSignIn, storeAuthData, getStoredUser } from '../auth/googleAuth'
import { useNavigate } from 'react-router-dom'

function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    // Check if already logged in
    const user = getStoredUser()
    if (user) {
      navigate('/')
      return
    }

    // Initialize Google Sign-In
    initGoogleSignIn((accessToken, tokenResponse) => {
      // This callback will be used when user signs in
    })
  }, [navigate])

  const handleSignIn = async () => {
    try {
      setLoading(true)
      console.log('Starting Google sign-in...')
      const { accessToken, user } = await signInWithGoogle()
      console.log('Sign-in successful, storing auth data...', { email: user?.email })
      storeAuthData(accessToken, user)
      console.log('Auth data stored, navigating to dashboard...')
      // Small delay to ensure storage event is processed
      setTimeout(() => {
        navigate('/', { replace: true })
      }, 100)
    } catch (error) {
      console.error('Sign in error:', error)
      alert('Error signing in: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh',
      flexDirection: 'column',
      gap: '20px'
    }}>
      <h1>Rescam - Email Security</h1>
      <button 
        onClick={handleSignIn}
        disabled={loading}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          backgroundColor: '#4285f4',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
      >
        <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
          <g fill="none" fillRule="evenodd">
            <path d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
            <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/>
            <path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957C.348 6.173 0 7.55 0 9s.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
            <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
          </g>
        </svg>
        {loading ? 'Signing in...' : 'Sign in with Google'}
      </button>
    </div>
  )
}

export default Login
