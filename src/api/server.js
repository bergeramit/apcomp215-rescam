import express from 'express'
import cors from 'cors'
import bodyParser from 'body-parser'
import dotenv from 'dotenv'
import { verifyGoogleToken } from './middleware/auth.js'
const auth = verifyGoogleToken
import { setupGmailWatch, stopGmailWatch } from './routes/gmail.js'
import { getEmails, streamEmails } from './routes/emails.js'
import { handlePubSubWebhook } from './routes/pubsub.js'

// Remove unused import
// import { handleGoogleCallback, getGoogleAuthUrl } from './routes/auth.js'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 5050

app.use(cors())
app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }))

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' })
})

// Pub/Sub webhook (no auth - validates signature instead)
app.post('/api/pubsub/webhook', handlePubSubWebhook)

// Protected routes
app.post('/api/gmail/watch', auth, setupGmailWatch)
app.post('/api/gmail/stop', auth, stopGmailWatch)
app.get('/api/emails', auth, getEmails)
app.get('/api/emails/stream', streamEmails)

app.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`)
})

