import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min — tinyfish research can be slow
})

// ── POST /api/analyze
// body: FormData { resume: File, job_title: string, company: string, telegram_handle?: string }
// returns: AnalysisResult
export async function analyzeJob(formData) {
  const res = await api.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

// ── POST /api/subscribe-telegram
// body: { telegram_handle: string, job_title: string, company: string }
export async function subscribeTelegram(payload) {
  const res = await api.post('/subscribe-telegram', payload)
  return res.data
}

// ── GET /api/health
export async function healthCheck() {
  const res = await api.get('/health')
  return res.data
}
