import { ExternalLink, Building2, Briefcase, MessageSquare, Lightbulb, Send, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { subscribeTelegram } from '../api/client'

function Section({ icon: Icon, title, color = 'gray', children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen)
  const colors = {
    gray:   'bg-gray-50 border-gray-200 text-gray-700',
    blue:   'bg-blue-50 border-blue-100 text-blue-700',
    green:  'bg-green-50 border-green-100 text-green-700',
    purple: 'bg-purple-50 border-purple-100 text-purple-700',
    amber:  'bg-amber-50 border-amber-100 text-amber-700',
  }
  return (
    <div className="card">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between gap-3 mb-0"
      >
        <div className="flex items-center gap-2.5">
          <span className={`p-1.5 rounded-lg border ${colors[color]}`}>
            <Icon className="w-4 h-4" />
          </span>
          <span className="font-semibold text-sm">{title}</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>
      {open && <div className="mt-4">{children}</div>}
    </div>
  )
}

function BulletList({ items }) {
  if (!items?.length) return <p className="text-sm text-gray-400">No data available.</p>
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2.5 text-sm text-gray-700">
          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-gray-400 shrink-0" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}

function TelegramSubscribe({ result }) {
  const [handle, setHandle] = useState('')
  const [status, setStatus] = useState(null) // null | 'loading' | 'done' | 'error'

  const handleSubscribe = async () => {
    if (!handle) return
    setStatus('loading')
    try {
      await subscribeTelegram({
        telegram_handle: handle.replace('@', ''),
        job_title: result.job_title,
        company: result.company,
      })
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'done') {
    return (
      <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-100 rounded-lg px-4 py-3">
        <Send className="w-4 h-4" />
        Subscribed! Our bot will message you with updates.
      </div>
    )
  }

  return (
    <div className="flex gap-2">
      <input
        className="input-field flex-1"
        placeholder="@yourusername"
        value={handle}
        onChange={e => setHandle(e.target.value)}
        disabled={status === 'loading'}
      />
      <button
        onClick={handleSubscribe}
        disabled={!handle || status === 'loading'}
        className="btn-primary flex items-center gap-1.5 whitespace-nowrap"
      >
        <Send className="w-3.5 h-3.5" />
        {status === 'loading' ? 'Subscribing...' : 'Get Updates'}
      </button>
      {status === 'error' && <p className="text-xs text-red-500 mt-1">Failed — try again.</p>}
    </div>
  )
}

export default function ResultPanel({ result }) {
  if (!result) return null

  const {
    job_title,
    company,
    company_overview,
    department_info,
    role_breakdown,
    requirements,
    interview_questions,
    resume_tips,
    application_link,
    glassdoor_link,
    already_subscribed_telegram,
  } = result

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{job_title}</h2>
          <p className="text-sm text-gray-500 mt-0.5">{company}</p>
        </div>
        <div className="flex gap-2 shrink-0">
          {application_link && (
            <a href={application_link} target="_blank" rel="noopener noreferrer" className="btn-primary flex items-center gap-1.5">
              Apply Now <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
          {glassdoor_link && (
            <a href={glassdoor_link} target="_blank" rel="noopener noreferrer" className="btn-secondary flex items-center gap-1.5">
              Glassdoor <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* Company Overview */}
      <Section icon={Building2} title="Company Overview" color="blue">
        {company_overview?.summary && (
          <p className="text-sm text-gray-700 leading-relaxed mb-4">{company_overview.summary}</p>
        )}
        {company_overview?.highlights?.length > 0 && (
          <div className="grid grid-cols-2 gap-2">
            {company_overview.highlights.map((h, i) => (
              <div key={i} className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
                <p className="text-xs font-medium text-blue-800">{h.label}</p>
                <p className="text-sm text-blue-700 mt-0.5">{h.value}</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Department Info */}
      {department_info && (
        <Section icon={Briefcase} title="Department & Team" color="purple">
          <p className="text-sm text-gray-700 leading-relaxed">{department_info}</p>
        </Section>
      )}

      {/* Role Breakdown */}
      <Section icon={Briefcase} title="Role Breakdown" color="gray">
        {role_breakdown?.responsibilities?.length > 0 && (
          <>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Responsibilities</p>
            <BulletList items={role_breakdown.responsibilities} />
          </>
        )}
        {requirements?.length > 0 && (
          <>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-4 mb-2">Requirements</p>
            <BulletList items={requirements} />
          </>
        )}
      </Section>

      {/* Interview Questions */}
      <Section icon={MessageSquare} title="Likely Interview Questions" color="amber">
        {interview_questions?.length > 0 ? (
          <div className="space-y-2">
            {interview_questions.map((q, i) => (
              <div key={i} className="bg-amber-50 border border-amber-100 rounded-lg px-4 py-3">
                <p className="text-sm text-amber-900 font-medium">{q.question}</p>
                {q.source && (
                  <p className="text-xs text-amber-600 mt-1">Source: {q.source}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No interview questions found.</p>
        )}
      </Section>

      {/* Resume Tips */}
      <Section icon={Lightbulb} title="Tips Based on Your Resume" color="green">
        {resume_tips?.strengths?.length > 0 && (
          <>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Your Strengths for This Role</p>
            <BulletList items={resume_tips.strengths} />
          </>
        )}
        {resume_tips?.gaps?.length > 0 && (
          <>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-4 mb-2">Areas to Highlight / Address</p>
            <BulletList items={resume_tips.gaps} />
          </>
        )}
        {resume_tips?.action_items?.length > 0 && (
          <>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-4 mb-2">Action Items</p>
            <BulletList items={resume_tips.action_items} />
          </>
        )}
      </Section>

      {/* Telegram Subscribe */}
      {!already_subscribed_telegram && (
        <Section icon={Send} title="Get Job Update Alerts" color="blue" defaultOpen={false}>
          <p className="text-sm text-gray-600 mb-3">
            Our Telegram bot will notify you of new openings and application deadlines for this role.
          </p>
          <TelegramSubscribe result={result} />
        </Section>
      )}

    </div>
  )
}
