/**
 * Verify Google access token by calling userinfo endpoint
 * This is simpler for MVP - access tokens from Google Sign-In can be verified this way
 */
export async function verifyGoogleToken(req, res, next) {
  try {
    const authHeader = req.headers.authorization
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Missing or invalid authorization header' })
    }

    const accessToken = authHeader.split('Bearer ')[1]
    
    // Verify token by calling Google userinfo endpoint
    const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${accessToken}`
      }
    })

    if (!response.ok) {
      return res.status(401).json({ error: 'Invalid or expired token' })
    }

    const userInfo = await response.json()
    
    // Attach user info to request
    req.user = {
      email: userInfo.email,
      sub: userInfo.id,
      name: userInfo.name,
      picture: userInfo.picture
    }

    // Store the access token for Gmail API calls
    req.googleAccessToken = accessToken

    next()
  } catch (error) {
    console.error('Token verification error:', error)
    return res.status(401).json({ error: 'Invalid or expired token' })
  }
}

// Legacy alias for compatibility
export const auth = verifyGoogleToken
