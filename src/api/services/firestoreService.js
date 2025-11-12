import { Firestore, FieldValue } from '@google-cloud/firestore'

// Initialize Firestore with the specific database ID
const firestore = new Firestore({
  projectId: process.env.GCP_PROJECT_ID,
  databaseId: 'user-emails'
})

const COLLECTION_NAME = 'user-emails-incoming'

/**
 * Store a raw email in Firestore
 * @param {string} userEmail - The user's email address (user-id)
 * @param {Object} rawEmail - The raw Gmail message object
 * @param {string} messageId - The Gmail message ID
 * @returns {Promise<void>}
 */
export async function storeEmailInFirestore(userEmail, rawEmail, messageId) {
  try {
    console.log(`[DEBUG] Storing email ${messageId} in Firestore for user ${userEmail}`)
    
    // Create document with user-id and raw email
    const docRef = firestore.collection(COLLECTION_NAME).doc(messageId)
    
    await docRef.set({
      'user-id': userEmail,
      'raw-email': rawEmail,
      'stored-at': FieldValue.serverTimestamp(),
      'message-id': messageId
    })
    
    console.log(`[SUCCESS] Email ${messageId} stored in Firestore successfully`)
  } catch (error) {
    console.error(`[ERROR] Failed to store email ${messageId} in Firestore:`, error.message)
    console.error(`[ERROR] Stack trace:`, error.stack)
    // Don't throw - we don't want to break the email processing flow if Firestore fails
  }
}

