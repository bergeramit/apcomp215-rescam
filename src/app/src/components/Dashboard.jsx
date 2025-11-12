import { useState } from 'react'
import { getStoredUser, signOut, getStoredToken } from '../auth/googleAuth'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import Inbox from './Inbox'

function Dashboard() {
  const user = getStoredUser()
  const navigate = useNavigate()
  const [isWatching, setIsWatching] = useState(false)
  const [loading, setLoading] = useState(false)

  const startWatching = async () => {
    try {
      setLoading(true)
      const token = getStoredToken()
      
      if (!token) {
        alert('Please sign in first')
        navigate('/')
        return
      }

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

  const handleSignOut = () => {
    signOut()
    navigate('/')
  }

  if (!user) {
    return <div>Not authenticated</div>
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
          <h1 style={{ margin: 0, marginBottom: '8px' }}>Rescam - Email Security</h1>
          <p style={{ margin: 0, color: '#666' }}>
            Logged in as: <strong>{user.email}</strong>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          {!isWatching && (
            <button
              onClick={startWatching}
              disabled={loading}
              style={{
                padding: '8px 16px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '14px'
              }}
            >
              {loading ? 'Starting...' : 'Start Gmail Monitoring'}
            </button>
          )}
          <button
            onClick={handleSignOut}
            style={{
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Sign Out
          </button>
        </div>
      </div>

      <Inbox userEmail={user.email} />
    </div>
  )
}

export default Dashboard
