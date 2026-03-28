export default function Header() {
  return (
    <header className="border-b border-gray-100 bg-white sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gray-900 flex items-center justify-center">
            <span className="text-white text-xs font-bold">W</span>
          </div>
          <span className="font-semibold text-sm tracking-tight">Welstra</span>
        </div>
        <span className="text-xs text-gray-400">AI Interview Planner</span>
      </div>
    </header>
  )
}
