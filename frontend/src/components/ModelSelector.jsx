import { useEffect, useState } from 'react'
import { Cpu } from 'lucide-react'

export default function ModelSelector({ value, onChange }) {
  const [models, setModels] = useState(['llama3', 'mistral', 'gemma'])

  useEffect(() => {
    fetch('/api/models')
      .then(r => r.json())
      .then(d => { if (d.models?.length) setModels(d.models) })
      .catch(() => {})
  }, [])

  return (
    <div className="flex items-center gap-2">
      <Cpu size={14} className="text-purple-400" />
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-purple-500"
      >
        {models.map(m => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>
    </div>
  )
}
