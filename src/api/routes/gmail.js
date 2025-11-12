import { setupGmailWatch as setupWatch, stopGmailWatch as stopWatch } from '../services/gmailService.js'
import { storeToken, storeLastHistoryId } from '../services/tokenStore.js'

export async function setupGmailWatch(req, res) {
  try {
    const userEmail = req.user?.email
    if (!userEmail) {
      return res.status(401).json({ error: 'User email not found' })
    }

    // Use the Google access token from the request
    const accessToken = req.googleAccessToken
    if (!accessToken) {
      return res.status(401).json({ error: 'Access token not found' })
    }

    // Store token for webhook processing
    await storeToken(userEmail, { access_token: accessToken })
    console.log(`[DEBUG] Stored access token for ${userEmail}`)

    const result = await setupWatch(userEmail, accessToken)
    
    // Store the initial historyId as the baseline for future queries
    await storeLastHistoryId(userEmail, result.historyId)
    console.log(`[DEBUG] Stored initial historyId ${result.historyId} for ${userEmail}`)
    
    res.json({ 
      success: true, 
      historyId: result.historyId,
      expiration: result.expiration
    })
  } catch (error) {
    console.error('Error setting up Gmail watch:', error)
    res.status(500).json({ error: error.message })
  }
}

export async function stopGmailWatch(req, res) {
  try {
    const userEmail = req.user?.email
    if (!userEmail) {
      return res.status(401).json({ error: 'User email not found' })
    }

    const accessToken = req.googleAccessToken
    await stopWatch(userEmail, accessToken)
    res.json({ success: true })
  } catch (error) {
    console.error('Error stopping Gmail watch:', error)
    res.status(500).json({ error: error.message })
  }
}

