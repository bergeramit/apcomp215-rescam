import { google } from 'googleapis'

export async function getGmailClient(accessToken) {
  const oauth2Client = new google.auth.OAuth2()
  oauth2Client.setCredentials({ access_token: accessToken })
  return google.gmail({ version: 'v1', auth: oauth2Client })
}

export async function setupGmailWatch(userEmail, accessToken) {
  const gmail = await getGmailClient(accessToken)
  const topicName = `projects/${process.env.GCP_PROJECT_ID}/topics/${process.env.PUBSUB_TOPIC_NAME}`
  
  const response = await gmail.users.watch({
    userId: 'me',
    requestBody: {
      topicName: topicName,
      labelIds: ['INBOX']
    }
  })

  return {
    historyId: response.data.historyId,
    expiration: response.data.expiration
  }
}

export async function stopGmailWatch(userEmail, accessToken) {
  const gmail = await getGmailClient(accessToken)
  await gmail.users.stop({
    userId: 'me'
  })
}

export async function getMessage(gmailClient, messageId) {
  const response = await gmailClient.users.messages.get({
    userId: 'me',
    id: messageId,
    format: 'full'
  })
  return response.data
}

export async function getMessagesSinceHistoryId(gmailClient, historyId) {
    // Use the historyId directly - it's the last processed historyId (baseline)
    // startHistoryId is inclusive in Gmail API, so this will return changes at/after this historyId
    console.log(`[DEBUG] Querying from historyId: ${historyId}`)
    
    try {
      const response = await gmailClient.users.history.list({
        userId: 'me',
        startHistoryId: historyId,
        historyTypes: ['messageAdded'],
        maxResults: 100
      })
      
      console.log(`[DEBUG] History API response:`, JSON.stringify({
        historyId: response.data.historyId,
        historyLength: response.data.history?.length || 0,
        nextPageToken: response.data.nextPageToken || null
      }))
      
      const messageIds = []
      if (response.data.history) {
        console.log(`[DEBUG] Processing ${response.data.history.length} history records`)
        response.data.history.forEach((history, index) => {
          console.log(`[DEBUG] History record ${index}:`, {
            id: history.id,
            messagesAddedCount: history.messagesAdded?.length || 0,
            messagesDeletedCount: history.messagesDeleted?.length || 0
          })
          if (history.messagesAdded) {
            history.messagesAdded.forEach(msg => {
              console.log(`[DEBUG] Found message: ${msg.message.id}`)
              messageIds.push(msg.message.id)
            })
          }
        })
      } else {
        console.log(`[WARN] No history array in response`)
      }
      
      console.log(`[DEBUG] Total messageIds found: ${messageIds.length}`)
      return messageIds
    } catch (error) {
      console.error(`[ERROR] Gmail History API error:`, error.message)
      console.error(`[ERROR] Error details:`, error.response?.data || error)
      throw error
    }
  }

