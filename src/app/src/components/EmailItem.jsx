function EmailItem({ email }) {
  const getClassificationColor = (classification) => {
    if (!classification) return '#6c757d'
    const result = classification.result?.toLowerCase()
    if (result === 'benign') return '#28a745'
    if (result === 'spam') return '#ffc107'
    if (result === 'scam') return '#dc3545'
    if (result === 'suspicious') return '#fd7e14'
    return '#6c757d'
  }

  const getClassificationLabel = (classification) => {
    if (!classification) return 'Pending'
    return classification.result || 'Unknown'
  }

  return (
    <div style={{
      border: '1px solid #ddd',
      borderRadius: '4px',
      padding: '15px',
      backgroundColor: '#f9f9f9'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div>
          <strong>{email.subject || 'No Subject'}</strong>
          <div style={{ color: '#666', fontSize: '14px', marginTop: '4px' }}>
            From: {email.sender || 'Unknown'}
          </div>
        </div>
        <div style={{
          padding: '6px 12px',
          borderRadius: '4px',
          backgroundColor: getClassificationColor(email.classification),
          color: 'white',
          fontSize: '12px',
          fontWeight: 'bold'
        }}>
          {getClassificationLabel(email.classification)}
        </div>
      </div>
      {email.snippet && (
        <div style={{ color: '#666', fontSize: '14px', marginBottom: '10px' }}>
          {email.snippet}
        </div>
      )}
      {email.classification && (
        <div style={{ fontSize: '12px', color: '#666' }}>
          <div>Confidence: {(email.classification.confidence * 100).toFixed(1)}%</div>
          {email.classification.primary_reason && (
            <div style={{ marginTop: '4px' }}>Reason: {email.classification.primary_reason}</div>
          )}
        </div>
      )}
      <div style={{ fontSize: '12px', color: '#999', marginTop: '8px' }}>
        Received: {new Date(email.receivedAt).toLocaleString()}
      </div>
    </div>
  )
}

export default EmailItem
