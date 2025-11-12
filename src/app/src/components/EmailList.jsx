import { useState } from 'react'
import axios from 'axios'
import EmailItem from './EmailItem'
import { getStoredToken, getStoredUser } from '../auth/googleAuth'

function EmailList() {
  const [emails, setEmails] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasFetched, setHasFetched] = useState(false)
  const user = getStoredUser()

  const fetchEmails = async () => {
    try {
      setLoading(true)
      const token = getStoredToken()
      if (!token) {
        console.error('No token available')
        return
      }

      const response = await axios.get('/api/emails', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setEmails(response.data.emails || [])
      setHasFetched(true)
    } catch (error) {
      console.error('Error fetching emails:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h2>Email Classifications</h2>
        <button
          onClick={fetchEmails}
          disabled={loading}
          style={{
            padding: '8px 16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          {loading ? 'Loading...' : 'Refresh Emails'}
        </button>
      </div>
      {loading && !hasFetched ? (
        <div style={{ padding: '20px' }}>Loading emails...</div>
      ) : emails.length === 0 ? (
        <p>No emails classified yet. {hasFetched ? 'Click "Refresh Emails" to load them.' : 'Click "Refresh Emails" to fetch your email classifications.'}</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {emails.map((email) => (
            <EmailItem key={email.id} email={email} />
          ))}
        </div>
      )}
    </div>
  )
}

export default EmailList

