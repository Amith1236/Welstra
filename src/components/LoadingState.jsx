const steps = [
  { label: 'Parsing your resume...', delay: 0 },
  { label: 'Researching company background...', delay: 3 },
  { label: 'Scraping job requirements...', delay: 6 },
  { label: 'Finding Glassdoor interview questions...', delay: 10 },
  { label: 'Tailoring tips to your profile...', delay: 14 },
]

import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'

export default function LoadingState() {
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    const timers = steps.map((step, i) =>
      setTimeout(() => setActiveStep(i), step.delay * 1000)
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="card flex flex-col items-center justify-center py-16 text-center">
      <div className="relative mb-8">
        <div className="w-14 h-14 rounded-2xl bg-gray-900 flex items-center justify-center">
          <Loader2 className="w-7 h-7 text-white animate-spin" />
        </div>
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">
        {steps[activeStep]?.label}
      </h3>
      <p className="text-sm text-gray-400">This usually takes 15–30 seconds</p>
      <div className="flex gap-1.5 mt-8">
        {steps.map((_, i) => (
          <div
            key={i}
            className={`h-1 rounded-full transition-all duration-500 ${
              i <= activeStep ? 'bg-gray-900 w-6' : 'bg-gray-200 w-3'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
