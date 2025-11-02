import { PubSub } from '@google-cloud/pubsub'
import { notifyEmailUpdate } from './emails.js'
import { getGmailClient, getMessagesSinceHistoryId, getMessage } from '../services/gmailService.js'
import { classifyEmail } from '../services/modelService.js'
import { saveEmailClassification } from '../services/gcsService.js'
import { getStoredToken, getLastHistoryId, storeLastHistoryId } from '../services/tokenStore.js'

const pubsub = new PubSub({
  projectId: process.env.GCP_PROJECT_ID
})

export async function handlePubSubWebhook(req, res) {
  try {
    // Pub/Sub push delivery sends messages in a specific format
    const message = req.body.message
    
    if (!message || !message.data) {
      return res.status(400).json({ error: 'Invalid message format' })
    }

    // Decode base64 message data
    const messageData = JSON.parse(
      Buffer.from(message.data, 'base64').toString('utf-8')
    )

    const userEmail = messageData.emailAddress
    const historyId = messageData.historyId

    console.log(`[DEBUG] Pub/Sub webhook received for ${userEmail}, historyId: ${historyId}`)

    // Acknowledge receipt immediately
    res.status(200).send()

    // Get stored access token
    const tokenData = await getStoredToken(userEmail)
    const accessToken = tokenData?.access_token || null
    
    if (!accessToken) {
      console.error(`[ERROR] No access token available for user: ${userEmail}`)
      console.error(`[ERROR] Message data keys:`, Object.keys(messageData))
      return
    }

    console.log(`[DEBUG] Access token found, processing notification for ${userEmail}`)

    // Process in background
    processGmailNotification(userEmail, historyId, accessToken).catch(err => {
      console.error(`[ERROR] Background processing error for ${userEmail}:`, err)
      console.error(`[ERROR] Stack trace:`, err.stack)
    })

  } catch (error) {
    console.error('Error handling Pub/Sub webhook:', error)
    res.status(500).send()
  }
}

async function processGmailNotification(userEmail, notificationHistoryId, accessToken) {
  try {
    console.log(`[DEBUG] ========== Processing Gmail Notification ==========`)
    console.log(`[DEBUG] User: ${userEmail}`)
    console.log(`[DEBUG] Notification historyId: ${notificationHistoryId}`)
    
    const gmail = await getGmailClient(accessToken)
    console.log(`[DEBUG] Gmail client created`)
    
    // Get the stored last processed historyId (baseline from watch setup)
    let lastProcessedHistoryId = await getLastHistoryId(userEmail)
    
    if (!lastProcessedHistoryId) {
      console.log(`[WARN] No stored historyId for ${userEmail}`)
      console.log(`[WARN] This should only happen if watch was set up before this code was deployed`)
      console.log(`[WARN] Please re-setup Gmail monitoring to store the initial historyId`)
      // Fallback: use notificationHistoryId directly (might miss some messages, but better than erroring)
      lastProcessedHistoryId = notificationHistoryId
    } else {
      console.log(`[DEBUG] Using stored lastProcessedHistoryId: ${lastProcessedHistoryId}`)
    }
    
    // Query from the stored historyId, not the notification historyId
    // This ensures we get all messages since the last processed point
    console.log(`[DEBUG] Querying from stored historyId: ${lastProcessedHistoryId}`)
    const messageIds = await getMessagesSinceHistoryId(gmail, lastProcessedHistoryId)
    console.log(`[DEBUG] Found ${messageIds.length} new message(s)`)
    
    if (messageIds.length === 0) {
      console.log(`[WARN] No new messages found for ${userEmail}`)
      console.log(`[DEBUG] Notification historyId: ${notificationHistoryId}, Last processed: ${lastProcessedHistoryId}`)
      // Still update the historyId even if no messages found (notification was sent for a reason)
      await storeLastHistoryId(userEmail, notificationHistoryId)
      return
    }

    console.log(`[INFO] Processing ${messageIds.length} message(s) for ${userEmail}`)

    // Process each message
    for (const messageId of messageIds) {
      try {
        console.log(`[ERROR] Processing message ${messageId}`)
        
        // Fetch full message
        const message = await getMessage(gmail, messageId)
        console.log(`[ERROR] Message ${messageId} fetched successfully`)
        
        // Parse email content
        const emailContent = parseGmailMessage(message)
        const metadata = extractGmailMetadata(message)
        console.log(`[ERROR] Email parsed - Subject: ${metadata.subject}, From: ${metadata.sender}`)
        
        // Classify email
        console.log(`[ERROR] Starting classification for message ${messageId}`)
        const classification = await classifyEmail(emailContent, userEmail, messageId)
        console.log(`[ERROR] Classification complete:`, JSON.stringify(classification))
        
        // Save to GCS
        const emailData = {
          id: messageId,
          threadId: message.threadId || '',
          receivedAt: new Date(parseInt(message.internalDate)).toISOString(),
          sender: metadata.sender,
          subject: metadata.subject,
          snippet: message.snippet || '',
          body: emailContent,
          classification: classification,
          processedAt: new Date().toISOString()
        }
        
        console.log(`[ERROR] Saving email classification to GCS`)
        await saveEmailClassification(userEmail, emailData)
        console.log(`[ERROR] Email saved to GCS successfully`)
        
        // Notify frontend via SSE
        notifyEmailUpdate(userEmail, emailData, 'new_email')
        
        console.log(`[SUCCESS] Processed email ${messageId} for ${userEmail}`)
      } catch (error) {
        console.error(`[ERROR] Error processing message ${messageId}:`, error.message)
        console.error(`[ERROR] Stack trace:`, error.stack)
      }
    }
    
    // Update the stored historyId to the notification historyId after successful processing
    // This ensures the next query starts from the correct point
    await storeLastHistoryId(userEmail, notificationHistoryId)
    console.log(`[DEBUG] Updated lastHistoryId to ${notificationHistoryId} for ${userEmail}`)
    
  } catch (error) {
    console.error(`[ERROR] Error processing Gmail notification for ${userEmail}:`, error.message)
    console.error(`[ERROR] Stack trace:`, error.stack)
  }
}

function parseGmailMessage(message) {
  const payload = message.payload || {}
  const headers = payload.headers || []
  
  const subject = headers.find(h => h.name === 'Subject')?.value || 'No Subject'
  const sender = headers.find(h => h.name === 'From')?.value || 'Unknown'
  const date = headers.find(h => h.name === 'Date')?.value || ''
  
  let body = ''
  if (payload.parts) {
    for (const part of payload.parts) {
      if (part.mimeType === 'text/plain' && part.body?.data) {
        body = Buffer.from(part.body.data, 'base64').toString('utf-8')
        break
      }
    }
  } else if (payload.body?.data) {
    body = Buffer.from(payload.body.data, 'base64').toString('utf-8')
  }
  
  return `From: ${sender}\nSubject: ${subject}\nDate: ${date}\n\n${body}`
}

function extractGmailMetadata(message) {
  const headers = message.payload?.headers || []
  return {
    sender: headers.find(h => h.name === 'From')?.value || 'Unknown',
    subject: headers.find(h => h.name === 'Subject')?.value || 'No Subject',
    date: headers.find(h => h.name === 'Date')?.value || ''
  }
}

