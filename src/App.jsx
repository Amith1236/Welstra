import { useState } from 'react'
import Header from './components/Header'
import InputForm from './components/InputForm'
import ResultPanel from './components/ResultPanel'
import LoadingState from './components/LoadingState'
import { analyzeJob } from './api/client'

// ── Mock data for UI dev (remove when backend is ready) ───────────────────
const MOCK_RESULT = {
  job_title: 'Software Engineer (Backend)',
  company: 'Stripe',
  company_overview: {
    summary: 'Stripe is a financial infrastructure platform for businesses. Millions of companies — from the world\'s largest enterprises to the most ambitious startups — use Stripe to accept payments, grow their revenue, and accelerate new business opportunities.',
    highlights: [
      { label: 'Founded', value: '2010' },
      { label: 'Employees', value: '~8,000' },
      { label: 'Valuation', value: '$65B (2023)' },
      { label: 'HQ', value: 'San Francisco, CA' },
    ],
  },
  department_info: 'The Infrastructure team at Stripe builds the backbone of the payments platform — high-throughput, low-latency systems that process millions of API calls per second. The team is deeply technical and values ownership and autonomy.',
  role_breakdown: {
    responsibilities: [
      'Design and build scalable, high-availability backend systems in Ruby and Go',
      'Own services end-to-end from design through production monitoring',
      'Collaborate closely with product and infrastructure teams',
      'Participate in on-call rotations and drive incident response',
    ],
  },
  requirements: [
    'Strong fundamentals in distributed systems and databases',
    'Experience with API design and microservices architecture',
    'Comfort with ambiguity and driving projects independently',
    '2+ years of backend engineering experience (internships count)',
  ],
  interview_questions: [
    { question: 'Design a rate-limiting system for a public API.', source: 'Glassdoor, 2024' },
    { question: 'How would you ensure exactly-once payment processing?', source: 'Glassdoor, 2024' },
    { question: 'Walk me through a system you built and what you\'d do differently.', source: 'Glassdoor, 2023' },
    { question: 'How do you handle database migrations in a live system with no downtime?', source: 'Interview report' },
  ],
  resume_tips: {
    strengths: [
      'Your IoT + ESP32 experience shows systems-level thinking — highlight this',
      'DripSeek\'s AWS Bedrock usage aligns well with Stripe\'s cloud-native stack',
      'Research background (UROP) shows intellectual depth Stripe values',
    ],
    gaps: [
      'No explicit distributed systems experience — mention any concurrent programming',
      'Limited exposure to financial/payments domain — study up on idempotency',
    ],
    action_items: [
      'Add a line about scale in DripSeek — how many users, how many API calls/sec?',
      'Reorder resume to lead with backend projects over hardware',
      'Prepare a 5-min system design answer for rate limiting',
    ],
  },
  application_link: 'https://stripe.com/jobs',
  glassdoor_link: 'https://glassdoor.com/Interview/Stripe-Software-Engineer-Interview-Questions',
  already_subscribed_telegram: false,
}

export default function App() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [useMock, setUseMock] = useState(false) // toggle for dev

  const handleSubmit = async (formData) => {
    setLoading(true)
    setError(null)
    setResult(null)

    // Dev mode: use mock data
    if (useMock) {
      setTimeout(() => {
        setResult(MOCK_RESULT)
        setLoading(false)
      }, 3000)
      return
    }

    try {
      const data = await analyzeJob(formData)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-5xl mx-auto px-6 py-12">

        {/* Hero */}
        {!result && !loading && (
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 bg-gray-100 text-gray-600 text-xs font-medium px-3 py-1.5 rounded-full mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Powered by Tinyfish + OpenAI
            </div>
            <h1 className="text-4xl font-bold text-gray-900 tracking-tight mb-3">
              Land the job. Walk in prepared.
            </h1>
            <p className="text-gray-500 text-lg max-w-xl mx-auto">
              Upload your resume, tell us the role — and we'll research the company,
              find real interview questions, and tailor prep tips to your profile.
            </p>
          </div>
        )}

        {/* Dev toggle */}
        <div className="flex justify-end mb-4">
          <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={useMock}
              onChange={e => setUseMock(e.target.checked)}
              className="rounded"
            />
            Use mock data (dev mode)
          </label>
        </div>

        <div className={`grid gap-8 ${result ? 'grid-cols-1 lg:grid-cols-[380px_1fr]' : 'max-w-xl mx-auto'}`}>

          {/* Input column */}
          <div className="space-y-4">
            <div className="card">
              {result && (
                <div className="flex items-center justify-between mb-5">
                  <h3 className="font-semibold text-sm text-gray-700">Analyze Another Role</h3>
                  <button onClick={handleReset} className="text-xs text-gray-400 hover:text-gray-600">
                    Clear results
                  </button>
                </div>
              )}
              <InputForm onSubmit={handleSubmit} loading={loading} />
            </div>
          </div>

          {/* Result column */}
          <div>
            {loading && <LoadingState />}
            {error && (
              <div className="card border-red-100 bg-red-50">
                <p className="text-sm text-red-700 font-medium">Error</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            )}
            {result && <ResultPanel result={result} />}
          </div>

        </div>
      </main>
    </div>
  )
}
