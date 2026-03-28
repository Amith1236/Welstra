import { useState, useRef, useCallback } from "react";

const API_BASE = "http://localhost:8000";

const PIPELINE_STEPS = [
  { id: "job_extraction",      label: "Analysing resume",          desc: "Extracting your role & experience level" },
  { id: "candidate_discovery", label: "Searching jobs",            desc: "Finding matching roles on job boards" },
  { id: "candidate_triage",    label: "Filtering listings",        desc: "Removing outdated or unsuitable posts" },
  { id: "candidate_comparison",label: "Scoring matches",           desc: "Running heuristic comparison algorithm" },
  { id: "evidence",            label: "Gathering evidence",        desc: "Collecting supporting data per listing" },
  { id: "ranking",             label: "Ranking results",           desc: "Ordering top 10 matched positions" },
  { id: "summary",             label: "Generating summary",        desc: "Writing your personalised report" },
];

const TABS = ["Top Matches", "Interview Prep", "Company Intel", "AI Assistant"];

// ── Spinner ──────────────────────────────────────────────────────────────────
function Spinner({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="animate-spin">
      <circle cx="12" cy="12" r="10" stroke="#e5e7eb" strokeWidth="2.5" />
      <path d="M12 2a10 10 0 0 1 10 10" stroke="#111" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

// ── Upload Zone ───────────────────────────────────────────────────────────────
function UploadZone({ onFile }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") onFile(file);
  }, [onFile]);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
      className={`cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-200 flex flex-col items-center justify-center gap-4 py-16 px-8 select-none
        ${dragging ? "border-gray-400 bg-gray-50" : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/50"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
      />
      <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="#6b7280" strokeWidth="1.5" strokeLinejoin="round"/>
          <polyline points="14,2 14,8 20,8" stroke="#6b7280" strokeWidth="1.5" strokeLinejoin="round"/>
          <line x1="12" y1="18" x2="12" y2="12" stroke="#6b7280" strokeWidth="1.5" strokeLinecap="round"/>
          <polyline points="9,15 12,12 15,15" stroke="#6b7280" strokeWidth="1.5" strokeLinejoin="round"/>
        </svg>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-gray-800">Drop your resume here</p>
        <p className="text-xs text-gray-400 mt-1">PDF · up to 10 MB</p>
      </div>
    </div>
  );
}

// ── Pipeline Progress ─────────────────────────────────────────────────────────
function PipelineProgress({ currentStep, status }) {
  const currentIdx = PIPELINE_STEPS.findIndex(s => s.id === currentStep);

  return (
    <div className="space-y-1">
      {PIPELINE_STEPS.map((step, idx) => {
        const done    = idx < currentIdx || status === "completed";
        const active  = idx === currentIdx && status === "running";
        const pending = !done && !active;

        return (
          <div key={step.id} className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300
            ${active  ? "bg-gray-50 border border-gray-100" : ""}
            ${done    ? "opacity-60" : ""}
            ${pending ? "opacity-30" : ""}
          `}>
            {/* indicator */}
            <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
              {done && (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="8" fill="#111"/>
                  <polyline points="4.5,8 7,10.5 11.5,5.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
              {active  && <Spinner size={16} />}
              {pending && <div className="w-4 h-4 rounded-full border-2 border-gray-200" />}
            </div>
            {/* text */}
            <div className="min-w-0">
              <p className={`text-sm font-medium leading-none ${active ? "text-gray-900" : "text-gray-600"}`}>
                {step.label}
              </p>
              {active && (
                <p className="text-xs text-gray-400 mt-1">{step.desc}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Match Card ────────────────────────────────────────────────────────────────
function MatchCard({ result, onSelect }) {
  const score = Math.round((result.job_item?.match_score ?? 0) * 100);
  const flags = result.job_item?.red_flags ?? [];

  return (
    <div
      onClick={() => onSelect(result)}
      className="border border-gray-100 rounded-2xl p-5 hover:border-gray-300 hover:shadow-sm cursor-pointer transition-all duration-200 group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">{result.job_item?.job_name}</p>
          <p className="text-xs text-gray-500 mt-0.5">{result.job_item?.company}</p>
        </div>
        <div className="flex-shrink-0 text-right">
          <span className="text-lg font-semibold text-gray-900">{score}%</span>
          <p className="text-xs text-gray-400">match</p>
        </div>
      </div>

      {/* score bar */}
      <div className="mt-4 h-1 rounded-full bg-gray-100">
        <div
          className="h-1 rounded-full bg-gray-900 transition-all duration-700"
          style={{ width: `${score}%` }}
        />
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex flex-wrap gap-1">
          {flags.slice(0, 2).map(f => (
            <span key={f} className="text-xs px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-100">
              {f.replace(/_/g, " ")}
            </span>
          ))}
        </div>
        <span className="text-xs text-gray-400 group-hover:text-gray-600 transition-colors">
          {result.recommendation}
        </span>
      </div>
    </div>
  );
}

// ── Interview Prep Panel ──────────────────────────────────────────────────────
function InterviewPrep({ job }) {
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", content: `I'm your interview coach for the ${job?.job_name ?? "this"} role. Ask me anything — common questions, how to frame your experience, or what to research beforehand.` }
  ]);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: "user", content: chatInput };
    setMessages(prev => [...prev, userMsg]);
    setChatInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...messages, userMsg], job }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "Connection error — please check the backend is running." }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
              ${m.role === "user"
                ? "bg-gray-900 text-white rounded-br-sm"
                : "bg-gray-50 text-gray-800 border border-gray-100 rounded-bl-sm"}`}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-50 border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
              <Spinner size={14} />
            </div>
          </div>
        )}
      </div>
      <div className="flex gap-2 pt-4 border-t border-gray-100">
        <input
          value={chatInput}
          onChange={e => setChatInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Ask your interview coach..."
          className="flex-1 text-sm px-4 py-2.5 rounded-xl border border-gray-200 focus:outline-none focus:border-gray-400 bg-white placeholder:text-gray-400"
        />
        <button
          onClick={send}
          className="px-4 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}

// ── Company Intel Panel ───────────────────────────────────────────────────────
function CompanyIntel({ job }) {
  const intel = job?.supporting_data?.company_intel;
  const glassdoor = job?.supporting_data?.glassdoor_questions ?? [];

  if (!intel) return (
    <div className="text-center py-16 text-gray-400 text-sm">
      Company research will appear here once a role is selected.
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">About the company</h3>
        <p className="text-sm text-gray-700 leading-relaxed">{intel.description}</p>
      </div>

      {intel.highlights?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">Key highlights</h3>
          <div className="grid grid-cols-2 gap-3">
            {intel.highlights.map((h, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-500">{h.label}</p>
                <p className="text-sm font-medium text-gray-900 mt-0.5">{h.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {glassdoor.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">
            Interview questions from Glassdoor
          </h3>
          <div className="space-y-2">
            {glassdoor.map((q, i) => (
              <div key={i} className="flex gap-3 p-3 bg-gray-50 rounded-xl">
                <span className="text-xs text-gray-400 font-mono mt-0.5">{String(i + 1).padStart(2, "0")}</span>
                <p className="text-sm text-gray-700">{q}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {job?.link_to_job && (
        <a
          href={String(job.link_to_job)}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors"
        >
          Apply for this role
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M7 17L17 7M17 7H7M17 7v10" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </a>
      )}
    </div>
  );
}

// ── AI Assistant (Telegram / Updates) ────────────────────────────────────────
function AiAssistant() {
  const [chatId, setChatId] = useState("");
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);

  const subscribe = async () => {
    if (!chatId.trim()) return;
    setLoading(true);
    try {
      await fetch(`${API_BASE}/telegram/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId }),
      });
      setSubscribed(true);
    } catch {
      setSubscribed(true); // optimistic in demo
    }
    setLoading(false);
  };

  return (
    <div className="space-y-8">
      {/* Telegram */}
      <div className="border border-gray-100 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-sky-50 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M21.73 4.55L3.16 11.73c-1.2.47-1.19 1.14-.22 1.44l4.67 1.46 1.81 5.55c.23.65.12.91.79.91.51 0 .74-.24 1.03-.52l2.47-2.41 5.14 3.79c.95.52 1.63.25 1.87-.88l3.4-16.02c.35-1.4-.53-2.03-1.42-1.5z" stroke="#0ea5e9" strokeWidth="1.5" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">Telegram job alerts</p>
            <p className="text-xs text-gray-400">Get notified when new matching roles appear</p>
          </div>
        </div>
        {subscribed ? (
          <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 rounded-xl px-4 py-3">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="8" fill="#16a34a"/>
              <polyline points="4.5,8 7,10.5 11.5,5.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Subscribed — we'll message you about new roles
          </div>
        ) : (
          <div className="flex gap-2">
            <input
              value={chatId}
              onChange={e => setChatId(e.target.value)}
              placeholder="Your Telegram chat ID"
              className="flex-1 text-sm px-3 py-2.5 rounded-xl border border-gray-200 focus:outline-none focus:border-gray-400 bg-white placeholder:text-gray-400"
            />
            <button
              onClick={subscribe}
              disabled={loading}
              className="px-4 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
            >
              {loading ? <Spinner size={14} /> : "Subscribe"}
            </button>
          </div>
        )}
      </div>

      {/* Social media helper */}
      <div className="border border-gray-100 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <rect x="2" y="2" width="20" height="20" rx="5" stroke="#7c3aed" strokeWidth="1.5"/>
              <circle cx="12" cy="12" r="4" stroke="#7c3aed" strokeWidth="1.5"/>
              <circle cx="17.5" cy="6.5" r="1" fill="#7c3aed"/>
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">Social media content helper</p>
            <p className="text-xs text-gray-400">Generate LinkedIn posts, portfolio captions, and more</p>
          </div>
        </div>
        <div className="space-y-2">
          {[
            "Write a LinkedIn post announcing my job search",
            "Create a portfolio caption for my recent project",
            "Draft a cold outreach message to a hiring manager",
          ].map((prompt) => (
            <button
              key={prompt}
              className="w-full text-left text-sm text-gray-600 px-4 py-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [phase, setPhase]             = useState("idle");      // idle | uploading | running | done | error
  const [file, setFile]               = useState(null);
  const [investigationId, setId]      = useState(null);
  const [pipelineStatus, setPipeline] = useState({ status: "pending", current_agent: null });
  const [results, setResults]         = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [activeTab, setActiveTab]     = useState("Top Matches");
  const pollRef                       = useRef(null);

  const handleFile = async (f) => {
    setFile(f);
    setPhase("uploading");

    const form = new FormData();
    form.append("file", f);

    try {
      const uploadRes = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
      const { file_id } = await uploadRes.json();

      const startRes = await fetch(`${API_BASE}/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_file_id: file_id }),
      });
      const { investigation_id } = await startRes.json();
      setId(investigation_id);
      setPhase("running");
      startPolling(investigation_id);
    } catch {
      setPhase("error");
    }
  };

  const startPolling = (id) => {
    pollRef.current = setInterval(async () => {
      try {
        const res  = await fetch(`${API_BASE}/investigation/${id}`);
        const data = await res.json();
        setPipeline({ status: data.status, current_agent: data.current_agent });

        if (data.status === "completed") {
          clearInterval(pollRef.current);
          setResults(data);
          if (data.top_matches?.length) setSelectedJob(data.top_matches[0].job_item);
          setPhase("done");
        }
        if (data.status === "failed") {
          clearInterval(pollRef.current);
          setPhase("error");
        }
      } catch {
        /* keep polling */
      }
    }, 2000);
  };

  const reset = () => {
    clearInterval(pollRef.current);
    setPhase("idle");
    setFile(null);
    setId(null);
    setResults(null);
    setSelectedJob(null);
    setPipeline({ status: "pending", current_agent: null });
    setActiveTab("Top Matches");
  };

  // ── IDLE ──────────────────────────────────────────────────────────────────
  if (phase === "idle") {
    return (
      <div className="min-h-screen bg-white flex flex-col">
        {/* Nav */}
        <nav className="border-b border-gray-100 px-6 h-14 flex items-center justify-between">
          <span className="text-sm font-semibold tracking-tight text-gray-900">Welstra</span>
          <span className="text-xs text-gray-400">AI job search</span>
        </nav>

        {/* Hero */}
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="w-full max-w-md">
            <div className="mb-10 text-center">
              <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">
                Find your next role
              </h1>
              <p className="mt-3 text-sm text-gray-500 leading-relaxed">
                Upload your resume and our pipeline will match you to real job listings, research companies, and prep you for interviews.
              </p>
            </div>
            <UploadZone onFile={handleFile} />

            {/* Feature pills */}
            <div className="mt-8 flex flex-wrap justify-center gap-2">
              {["Job matching", "Company research", "Interview prep", "Telegram alerts"].map(f => (
                <span key={f} className="text-xs px-3 py-1.5 rounded-full bg-gray-50 text-gray-500 border border-gray-100">
                  {f}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── UPLOADING / RUNNING ───────────────────────────────────────────────────
  if (phase === "uploading" || phase === "running") {
    return (
      <div className="min-h-screen bg-white flex flex-col">
        <nav className="border-b border-gray-100 px-6 h-14 flex items-center justify-between">
          <span className="text-sm font-semibold tracking-tight text-gray-900">Welstra</span>
          <button onClick={reset} className="text-xs text-gray-400 hover:text-gray-600 transition-colors">Cancel</button>
        </nav>

        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="w-full max-w-sm">
            {/* file chip */}
            <div className="flex items-center gap-3 mb-8 p-3 rounded-xl bg-gray-50 border border-gray-100">
              <div className="w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center flex-shrink-0">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="#6b7280" strokeWidth="1.5" strokeLinejoin="round"/>
                  <polyline points="14,2 14,8 20,8" stroke="#6b7280" strokeWidth="1.5"/>
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-gray-800 truncate">{file?.name}</p>
                <p className="text-xs text-gray-400">{((file?.size ?? 0) / 1024).toFixed(1)} KB</p>
              </div>
            </div>

            <PipelineProgress
              currentStep={pipelineStatus.current_agent}
              status={pipelineStatus.status}
            />

            <p className="text-xs text-gray-400 text-center mt-6">
              This usually takes 30–90 seconds
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── ERROR ─────────────────────────────────────────────────────────────────
  if (phase === "error") {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4">
        <p className="text-sm text-red-600">Something went wrong. Please try again.</p>
        <button onClick={reset} className="text-sm text-gray-600 underline">Start over</button>
      </div>
    );
  }

  // ── DONE ──────────────────────────────────────────────────────────────────
  const matches = results?.top_matches ?? [];

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Nav */}
      <nav className="border-b border-gray-100 px-6 h-14 flex items-center justify-between sticky top-0 bg-white z-10">
        <span className="text-sm font-semibold tracking-tight text-gray-900">Welstra</span>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-400 hidden sm:block">{file?.name}</span>
          <button
            onClick={reset}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:border-gray-300 transition-colors"
          >
            New search
          </button>
        </div>
      </nav>

      {/* Summary bar */}
      <div className="border-b border-gray-100 px-6 py-4 bg-gray-50/60">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center gap-6">
          <div>
            <p className="text-xs text-gray-400">Identified role</p>
            <p className="text-sm font-semibold text-gray-900 mt-0.5">
              {results?.suitable_jobs?.[0]?.job_title ?? "—"}
              <span className="ml-2 text-xs font-normal text-gray-400 capitalize">
                {results?.suitable_jobs?.[0]?.job_level}
              </span>
            </p>
          </div>
          <div className="h-8 w-px bg-gray-200 hidden sm:block" />
          <div>
            <p className="text-xs text-gray-400">Matches found</p>
            <p className="text-sm font-semibold text-gray-900 mt-0.5">{matches.length}</p>
          </div>
          {results?.summary && (
            <>
              <div className="h-8 w-px bg-gray-200 hidden md:block" />
              <p className="text-xs text-gray-600 leading-relaxed max-w-md hidden md:block">
                {results.summary}
              </p>
            </>
          )}
        </div>
      </div>

      {/* Main layout */}
      <div className="flex-1 max-w-6xl mx-auto w-full flex flex-col lg:flex-row gap-0">

        {/* Left — job list (only visible on Top Matches tab on mobile) */}
        <aside className="w-full lg:w-80 xl:w-96 border-r border-gray-100 overflow-y-auto lg:max-h-[calc(100vh-8.5rem)]">
          <div className="p-4 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 px-1 mb-3">
              Top {matches.length} matches
            </p>
            {matches.map((r) => (
              <div
                key={r.rank}
                onClick={() => { setSelectedJob(r.job_item); setActiveTab("Interview Prep"); }}
              >
                <MatchCard result={r} onSelect={() => {}} />
              </div>
            ))}
          </div>
        </aside>

        {/* Right — detail panel */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="border-b border-gray-100 px-6 flex gap-1 sticky top-14 bg-white z-10">
            {TABS.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap
                  ${activeTab === tab
                    ? "border-gray-900 text-gray-900"
                    : "border-transparent text-gray-400 hover:text-gray-600"}`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-6">

            {activeTab === "Top Matches" && (
              <div className="max-w-2xl space-y-4">
                <div className="bg-gray-50 rounded-2xl p-5 border border-gray-100">
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {results?.summary ?? "Your top matches are shown on the left. Click any role to view the full breakdown, company research, and interview prep."}
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {matches.slice(0, 4).map(r => (
                    <MatchCard key={r.rank} result={r} onSelect={(r) => { setSelectedJob(r.job_item); setActiveTab("Interview Prep"); }} />
                  ))}
                </div>
              </div>
            )}

            {activeTab === "Interview Prep" && (
              <div className="max-w-2xl h-full flex flex-col" style={{ minHeight: "60vh" }}>
                {selectedJob ? (
                  <>
                    <div className="mb-5 pb-5 border-b border-gray-100">
                      <p className="text-xs text-gray-400 mb-1">Prepping for</p>
                      <p className="text-base font-semibold text-gray-900">{selectedJob.job_name}</p>
                      <p className="text-sm text-gray-500">{selectedJob.company}</p>
                    </div>
                    <div className="flex-1" style={{ minHeight: "400px" }}>
                      <InterviewPrep job={selectedJob} />
                    </div>
                  </>
                ) : (
                  <div className="text-center py-16 text-sm text-gray-400">
                    Select a role from the left to start interview prep
                  </div>
                )}
              </div>
            )}

            {activeTab === "Company Intel" && (
              <div className="max-w-2xl">
                {selectedJob ? (
                  <>
                    <div className="mb-5 pb-5 border-b border-gray-100">
                      <p className="text-xs text-gray-400 mb-1">Researching</p>
                      <p className="text-base font-semibold text-gray-900">{selectedJob.company}</p>
                      <p className="text-sm text-gray-500">{selectedJob.job_name}</p>
                    </div>
                    <CompanyIntel job={selectedJob} />
                  </>
                ) : (
                  <div className="text-center py-16 text-sm text-gray-400">
                    Select a role from the left to view company intelligence
                  </div>
                )}
              </div>
            )}

            {activeTab === "AI Assistant" && (
              <div className="max-w-xl">
                <AiAssistant />
              </div>
            )}

          </div>
        </main>
      </div>
    </div>
  );
}