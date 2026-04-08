/**
 * Client for family-kitchen-recipes receipt-parsing API.
 *
 * Credentials and base URL are injected at Docker build time via VITE_ env vars:
 *   VITE_KITCHEN_API_URL          – e.g. https://recipes.example.com/api
 *   VITE_KITCHEN_SERVICE_USER     – service account username
 *   VITE_KITCHEN_SERVICE_PASSWORD – service account password
 *
 * The token is fetched fresh for each sendReceiptToKitchen() call so there is no
 * stale-token issue (kitchen tokens last 7 days, but a simple fresh fetch is cleaner).
 */

const KITCHEN_API_URL = import.meta.env.VITE_KITCHEN_API_URL || ''
const KITCHEN_USER = import.meta.env.VITE_KITCHEN_SERVICE_USER || ''
const KITCHEN_PASSWORD = import.meta.env.VITE_KITCHEN_SERVICE_PASSWORD || ''

export const isKitchenConfigured = () =>
  Boolean(KITCHEN_API_URL && KITCHEN_USER && KITCHEN_PASSWORD)

async function getKitchenToken() {
  const res = await fetch(`${KITCHEN_API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: KITCHEN_USER, password: KITCHEN_PASSWORD }),
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`Kitchen auth failed (${res.status}): ${body}`)
  }
  const data = await res.json()
  return data.access_token
}

/**
 * Fetch an attachment by its public URL and send it to the kitchen receipt API.
 * Returns the parsed ReceiptProcessResult from the kitchen API.
 */
export async function sendReceiptToKitchen(publicUrl) {
  if (!isKitchenConfigured()) {
    throw new Error('Kitchen API is not configured (missing VITE_KITCHEN_* env vars).')
  }

  // 1. Authenticate
  const token = await getKitchenToken()

  // 2. Fetch the image from budget-site (same origin)
  const imgRes = await fetch(publicUrl)
  if (!imgRes.ok) throw new Error(`Could not fetch attachment (${imgRes.status})`)
  const blob = await imgRes.blob()

  // 3. Determine filename from URL
  const filename = publicUrl.split('/').pop() || 'receipt.jpg'

  // 4. Send to kitchen
  const form = new FormData()
  form.append('image', blob, filename)

  const receiptRes = await fetch(`${KITCHEN_API_URL}/warehouse/receipt`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  if (!receiptRes.ok) {
    const body = await receiptRes.text()
    throw new Error(`Kitchen receipt API failed (${receiptRes.status}): ${body}`)
  }
  return receiptRes.json()
}

