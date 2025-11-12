/**
 * Google Sign-In helper using Google Identity Services OAuth 2.0 Token Client
 * This gives us access tokens directly for Gmail API
 */
let tokenClient = null

export function initGoogleSignIn() {
  return new Promise((resolve, reject) => {
    // Load Google Identity Services script
    if (!window.google) {
      const script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.defer = true
      script.onload = () => {
        setupGoogleSignIn().then(resolve).catch(reject)
      }
      script.onerror = () => reject(new Error('Failed to load Google Sign-In script'))
      document.head.appendChild(script)
    } else {
      setupGoogleSignIn().then(resolve).catch(reject)
    }
  })
}

function setupGoogleSignIn() {
  return new Promise((resolve, reject) => {
    const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

    if (!GOOGLE_CLIENT_ID) {
      reject(new Error('VITE_GOOGLE_CLIENT_ID is not set'))
      return
    }

    tokenClient = window.google.accounts.oauth2.initTokenClient({
      client_id: GOOGLE_CLIENT_ID,
      scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email',
      callback: (response) => {
        if (response.error) {
          reject(new Error(response.error))
          return
        }
        resolve(response.access_token)
      },
    })
    resolve()
  })
}

export function signInWithGoogle() {
  return new Promise(async (resolve, reject) => {
    try {
      // Initialize if not already done
      if (!tokenClient) {
        await initGoogleSignIn()
      }

      if (!tokenClient) {
        reject(new Error('Google Sign-In not initialized'))
        return
      }

      // Create a promise that will be resolved by the callback
      let callbackResolve, callbackReject
      const tokenPromise = new Promise((resolve, reject) => {
        callbackResolve = resolve
        callbackReject = reject
      })

      // Override the callback temporarily
      const originalCallback = tokenClient.callback
      tokenClient.callback = (response) => {
        // Restore original callback
        tokenClient.callback = originalCallback
        
        if (response.error) {
          callbackReject(new Error(response.error))
          return
        }
        callbackResolve(response)
      }

      // Request access token
      tokenClient.requestAccessToken({ prompt: 'consent' })
      
      // Wait for callback
      const tokenResponse = await tokenPromise
      const accessToken = tokenResponse.access_token
      
      // Get user info
      const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      })
      
      if (!userInfoResponse.ok) {
        throw new Error('Failed to get user info')
      }
      
      const userInfo = await userInfoResponse.json()
      
      resolve({
        accessToken,
        user: userInfo,
        tokenResponse: tokenResponse
      })
    } catch (error) {
      reject(error)
    }
  })
}

export function signOut() {
  if (window.google && window.google.accounts) {
    window.google.accounts.oauth2.revoke(window.localStorage.getItem('google_access_token'), () => {
      console.log('Signed out')
    })
  }
  window.localStorage.removeItem('google_access_token')
  window.localStorage.removeItem('google_user')
}

export function getStoredToken() {
  return window.localStorage.getItem('google_access_token')
}

export function getStoredUser() {
  const userStr = window.localStorage.getItem('google_user')
  return userStr ? JSON.parse(userStr) : null
}

export function storeAuthData(accessToken, user) {
  window.localStorage.setItem('google_access_token', accessToken)
  window.localStorage.setItem('google_user', JSON.stringify(user))
  // Dispatch custom event for same-tab storage change detection
  window.dispatchEvent(new Event('auth-storage-change'))
}

