import { useState, useRef } from 'react'
import { Upload, X, FileText, Loader2 } from 'lucide-react'

export default function InputForm({ onSubmit, loading }) {
  const [jobTitle, setJobTitle] = useState('')
  const [company, setCompany] = useState('')
  const [telegramHandle, setTelegramHandle] = useState('')
  const [resume, setResume] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef()

  const handleFile = (file) => {
    if (!file) return
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    if (!allowed.includes(file.type) && !file.name.endsWith('.pdf') && !file.name.endsWith('.docx')) {
      alert('Please upload a PDF or DOCX file.')
      return
    }
    setResume(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!jobTitle || !company || !resume) return
    const fd = new FormData()
    fd.append('resume', resume)
    fd.append('job_title', jobTitle)
    fd.append('company', company)
    if (telegramHandle) fd.append('telegram_handle', telegramHandle.replace('@', ''))
    onSubmit(fd)
  }

  const canSubmit = jobTitle.trim() && company.trim() && resume && !loading

  return (
    <form onSubmit={handleSubmit} className="space-y-5">

      {/* Resume Upload */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Resume</label>
        {resume ? (
          <div className="flex items-center gap-3 border border-gray-200 rounded-lg px-4 py-3 bg-gray-50">
            <FileText className="w-4 h-4 text-gray-500 shrink-0" />
            <span className="text-sm text-gray-700 truncate flex-1">{resume.name}</span>
            <button type="button" onClick={() => setResume(null)} className="text-gray-400 hover:text-gray-600">
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => fileRef.current.click()}
            className={`border-2 border-dashed rounded-xl px-6 py-10 text-center cursor-pointer transition
              ${dragOver ? 'border-gray-900 bg-gray-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}
          >
            <Upload className="w-6 h-6 mx-auto mb-2 text-gray-400" />
            <p className="text-sm font-medium text-gray-700">Drop your resume here</p>
            <p className="text-xs text-gray-400 mt-1">PDF or DOCX</p>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => handleFile(e.target.files[0])}
            />
          </div>
        )}
      </div>

      {/* Job Title + Company */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Job Title</label>
          <input
            className="input-field"
            placeholder="e.g. Software Engineer"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Company</label>
          <input
            className="input-field"
            placeholder="e.g. Google"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            required
          />
        </div>
      </div>

      {/* Telegram Handle */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Telegram Handle <span className="text-gray-400 font-normal">(optional — get job updates)</span>
        </label>
        <input
          className="input-field"
          placeholder="@yourusername"
          value={telegramHandle}
          onChange={(e) => setTelegramHandle(e.target.value)}
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!canSubmit}
        className="btn-primary w-full flex items-center justify-center gap-2 py-3"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Researching role...
          </>
        ) : (
          'Analyze & Prepare'
        )}
      </button>
    </form>
  )
}
