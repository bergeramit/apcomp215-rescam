import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import EmailList from './EmailList'
import axios from 'axios'
import { getStoredToken, getStoredUser, signOut } from '../auth/googleAuth'

function Dashboard() {
  const navigate = useNavigate()
  const [user, setUser] = useState(getStoredUser())
  const [isWatching, setIsWatching] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!user) {
      navigate('/')
    }
  }, [user, navigate])

  const startWatching = async () => {
    try {
      setLoading(true)
      const token = getStoredToken()
      
      if (!token) {
        alert('Please sign in first')
        navigate('/')
        return
      }

      // Set up Gmail watch (the token already includes Gmail scope)
      await axios.post(
        '/api/gmail/watch',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setIsWatching(true)
      alert('Gmail monitoring started!')
    } catch (error) {
      console.error('Error starting watch:', error)
      alert('Error starting Gmail watch: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    signOut()
    setUser(null)
    navigate('/')
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div>
          <h1>Email Security Dashboard</h1>
          <p>Logged in as: {user?.email}</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          {!isWatching && (
            <button
              onClick={startWatching}
              disabled={loading}
              style={{
                padding: '10px 20px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Starting...' : 'Start Gmail Monitoring'}
            </button>
          )}
          <button
            onClick={handleLogout}
            style={{
              padding: '10px 20px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
      </div>
      <EmailList />
    </div>
  )
}

export default Dashboard

