import { Activity, CheckCircle, Clock } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function WorkflowStatus() {
  const [status, setStatus] = useState({ active_agents: 0, completed_tasks: 0, queue: [] })

  useEffect(() => {
    const poll = () =>
      fetch('/api/workflow/status')
        .then(r => r.json())
        .then(setStatus)
        .catch(() => {})
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="glass rounded-xl p-4 flex gap-6">
      <div className="flex items-center gap-2">
        <Activity size={16} className="text-green-400 animate-pulse" />
        <span className="text-sm text-slate-400">Active:</span>
        <span className="text-sm font-bold text-green-400">{status.active_agents}</span>
      </div>
      <div className="flex items-center gap-2">
        <CheckCircle size={16} className="text-blue-400" />
        <span className="text-sm text-slate-400">Done:</span>
        <span className="text-sm font-bold text-blue-400">{status.completed_tasks}</span>
      </div>
      <div className="flex items-center gap-2">
        <Clock size={16} className="text-yellow-400" />
        <span className="text-sm text-slate-400">Queue:</span>
        <span className="text-sm font-bold text-yellow-400">{status.queue.length}</span>
      </div>
    </div>
  )
}
