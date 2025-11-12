import { exec } from 'child_process'
import { promisify } from 'util'
import { saveEmailClassification, getEmailClassificationsPath } from './gcsService.js'

const execAsync = promisify(exec)

/**
 * For MVP: Call model_rag.py via subprocess
 * In production, this should be an HTTP API call or Cloud Function
 */
export async function classifyEmail(emailContent, userEmail, messageId) {
  try {
    // Save email temporarily to GCS for model to read
    const { Storage } = await import('@google-cloud/storage')
    const storage = new Storage()
    const bucket = storage.bucket(process.env.GCS_BUCKET_NAME || 'rescam-dataset-bucket')
    const tempFileName = `temp-emails/${userEmail}/${messageId}.txt`
    const blob = bucket.file(tempFileName)
    await blob.save(emailContent, { contentType: 'text/plain' })

    // Call model_rag.py (assumes model container is accessible or runs locally)
    // For MVP, we'll need to mount the models directory or use HTTP API
    const command = [
      'python3',
      '/app/models/model_rag.py',
      '--project_id', process.env.GCP_PROJECT_ID || '1097076476714',
      '--location', 'us-east1',
      '--index_endpoint_id', '3044332193032699904',
      '--deployed_index_id', 'phishing_emails_deployed_1760372787396',
      '--gcs_bucket_name', process.env.GCS_BUCKET_NAME || 'rescam-dataset-bucket',
      '--gcs_file_name', tempFileName
    ].join(' ')

    const { stdout, stderr } = await execAsync(command, {
      cwd: '/app',
      env: {
        ...process.env,
        GOOGLE_APPLICATION_CREDENTIALS: process.env.GOOGLE_APPLICATION_CREDENTIALS
      }
    })

    // Parse classification result
    let classification
    try {
      // Extract JSON from output
      const jsonMatch = stdout.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        classification = JSON.parse(jsonMatch[0])
      } else {
        throw new Error('No JSON found in output')
      }
    } catch (e) {
      // Fallback
      classification = {
        classification: 'unknown',
        confidence: 0.5,
        primary_reason: stdout.substring(0, 200)
      }
    }

    // Clean up temp file
    await blob.delete()

    return classification
  } catch (error) {
    console.error('Error classifying email:', error)
    // For MVP: Return basic classification if model fails
    // In production, this should fail or retry
    return {
      classification: 'pending',
      confidence: 0.0,
      primary_reason: 'Classification pending - model unavailable',
      indicators: [],
      recommended_action: 'allow'
    }
  }
}

