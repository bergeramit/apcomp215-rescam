import { useState, useEffect, useRef } from 'react'

function Inbox({ userEmail }) {
  const [emails, setEmails] = useState([])
  const [connected, setConnected] = useState(false)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    if (!userEmail) return

    // Create SSE connection
    const eventSource = new EventSource(`/api/emails/stream?user=${encodeURIComponent(userEmail)}`)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      console.log('SSE connection opened')
      setConnected(true)
    }

    // Listen for messages (SSE default event)
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'connected') {
          console.log('SSE connected event received')
          setConnected(true)
        } else if (data.type === 'new_email' && data.email) {
          const email = data.email
          // Add new email to the beginning of the list (newest first)
          setEmails(prevEmails => {
            // Check if email already exists to avoid duplicates
            if (prevEmails.some(e => e.id === email.id)) {
              return prevEmails
            }
            return [email, ...prevEmails]
          })
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      const state = eventSource.readyState
      if (state === EventSource.CONNECTING) {
        setConnected(false)
      } else if (state === EventSource.CLOSED) {
        setConnected(false)
      }
    }

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [userEmail])

  const truncateBody = (body, maxLength = 200) => {
    if (!body) return ''
    if (body.length <= maxLength) return body
    return body.substring(0, maxLength) + '...'
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  return (
    <div style={{
      marginTop: '20px',
      padding: '16px',
      border: '1px solid #ddd',
      borderRadius: '8px',
      backgroundColor: '#f9f9f9',
      maxHeight: '500px',
      overflowY: 'auto'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px'
      }}>
        <h3 style={{ margin: 0, fontSize: '18px' }}>Real-time Inbox</h3>
        <span style={{
          fontSize: '12px',
          color: connected ? '#28a745' : '#dc3545',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: connected ? '#28a745' : '#dc3545',
            display: 'inline-block'
          }}></span>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      
      {emails.length === 0 ? (
        <p style={{ color: '#666', fontSize: '14px', margin: 0 }}>
          No new emails yet. Waiting for incoming emails...
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {emails.map((email) => (
            <div
              key={email.id}
              style={{
                padding: '12px',
                backgroundColor: 'white',
                border: '1px solid #e0e0e0',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'start',
                marginBottom: '8px'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontWeight: 'bold',
                    color: '#333',
                    marginBottom: '4px'
                  }}>
                    {email.sender || 'Unknown Sender'}
                  </div>
                  <div style={{
                    color: '#555',
                    marginBottom: '4px',
                    fontWeight: '500'
                  }}>
                    {email.subject || 'No Subject'}
                  </div>
                </div>
                {email.timestamp && (
                  <div style={{
                    fontSize: '11px',
                    color: '#999',
                    whiteSpace: 'nowrap',
                    marginLeft: '12px'
                  }}>
                    {formatDate(email.timestamp)}
                  </div>
                )}
              </div>
              {email.body && (
                <div style={{
                  color: '#666',
                  fontSize: '13px',
                  lineHeight: '1.4',
                  marginTop: '8px',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {truncateBody(email.body)}
                </div>
              )}
              {email.snippet && !email.body && (
                <div style={{
                  color: '#666',
                  fontSize: '13px',
                  lineHeight: '1.4',
                  marginTop: '8px',
                  fontStyle: 'italic'
                }}>
                  {email.snippet}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Inbox

