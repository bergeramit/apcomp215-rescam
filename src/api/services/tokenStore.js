// Simple in-memory token store (replace with database in production)
const tokenStore = new Map()

export async function storeToken(userEmail, tokens) {
  const existing = tokenStore.get(userEmail) || {}
  tokenStore.set(userEmail, { ...existing, ...tokens })
}

export async function getStoredToken(userEmail) {
  return tokenStore.get(userEmail)
}

// Store the last processed historyId (baseline for querying)
export async function storeLastHistoryId(userEmail, historyId) {
  const existing = tokenStore.get(userEmail) || {}
  existing.lastHistoryId = historyId
  tokenStore.set(userEmail, existing)
  console.log(`[DEBUG] Stored lastHistoryId ${historyId} for ${userEmail}`)
}

// Get the last processed historyId
export async function getLastHistoryId(userEmail) {
  const data = tokenStore.get(userEmail)
  return data?.lastHistoryId || null
}

