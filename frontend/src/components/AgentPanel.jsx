import { useState } from 'react'
import { Mail, Search, Loader2, Copy, Check } from 'lucide-react'

function SalesAgentForm({ model }) {
  const [form, setForm] = useState({ company: '', contact: '', product: '樂器/音響設備', language: '繁體中文' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const run = async () => {
    setLoading(true); setResult(null)
    try {
      const resp = await fetch('/api/agent/sales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, model })
      })
      const data = await resp.json()
      setResult(data.data)
    } catch (e) {
      setResult({ body: '❌ 錯誤：' + e.message })
    }
    setLoading(false)
  }

  const copyAll = () => {
    if (!result) return
    navigator.clipboard.writeText(`主旨：${result.subject}\n\n${result.body}\n\n${result.cta}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {[
          { key: 'company', label: '目標公司', placeholder: '例：小叮噹樂器行' },
          { key: 'contact', label: '聯絡人', placeholder: '例：王經理' },
          { key: 'product', label: '產品/服務', placeholder: '例：Gibson 吉他代理' },
          { key: 'language', label: '語言', placeholder: '繁體中文 / English' }
        ].map(({ key, label, placeholder }) => (
          <div key={key}>
            <label className="block text-xs text-slate-400 mb-1">{label}</label>
            <input
              value={form[key]}
              onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
              placeholder={placeholder}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
            />
          </div>
        ))}
      </div>
      <button
        onClick={run}
        disabled={loading || !form.company}
        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:opacity-90 disabled:opacity-40 rounded-lg py-2.5 text-sm font-medium transition-opacity flex items-center justify-center gap-2"
      >
        {loading ? <><Loader2 size={16} className="animate-spin" /> 生成中...</> : <><Mail size={16} /> 生成開發信</>}
      </button>
      {result && (
        <div className="glass rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-purple-400 font-medium">✉️ 生成結果</span>
            <button onClick={copyAll} className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors">
              {copied ? <><Check size={12} /> 已複製</> : <><Copy size={12} /> 複製全文</>}
            </button>
          </div>
          {result.subject && <div><span className="text-xs text-slate-500">主旨：</span><p className="text-sm font-medium text-yellow-300">{result.subject}</p></div>}
          {result.body && <div><span className="text-xs text-slate-500">內文：</span><p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">{result.body}</p></div>}
          {result.cta && <div><span className="text-xs text-slate-500">CTA：</span><p className="text-sm text-green-300">{result.cta}</p></div>}
        </div>
      )}
    </div>
  )
}

function ResearchAgentForm({ model }) {
  const [form, setForm] = useState({ topic: '', depth: '中等' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const run = async () => {
    setLoading(true); setResult(null)
    try {
      const resp = await fetch('/api/agent/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, model })
      })
      const data = await resp.json()
      setResult(data.data)
    } catch (e) {
      setResult('❌ 錯誤：' + e.message)
    }
    setLoading(false)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs text-slate-400 mb-1">研究主題</label>
        <input
          value={form.topic}
          onChange={e => setForm(p => ({ ...p, topic: e.target.value }))}
          placeholder="例：台灣樂器市場 2026 趨勢"
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
        />
      </div>
      <div>
        <label className="block text-xs text-slate-400 mb-1">分析深度</label>
        <select
          value={form.depth}
          onChange={e => setForm(p => ({ ...p, depth: e.target.value }))}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
        >
          <option>簡略</option><option>中等</option><option>深入</option>
        </select>
      </div>
      <button
        onClick={run}
        disabled={loading || !form.topic}
        className="w-full bg-gradient-to-r from-green-600 to-teal-600 hover:opacity-90 disabled:opacity-40 rounded-lg py-2.5 text-sm font-medium transition-opacity flex items-center justify-center gap-2"
      >
        {loading ? <><Loader2 size={16} className="animate-spin" /> 分析中...</> : <><Search size={16} /> 執行市場研究</>}
      </button>
      {result && (
        <div className="glass rounded-xl p-4">
          <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">{result}</p>
        </div>
      )}
    </div>
  )
}

export default function AgentPanel({ model }) {
  const [activeAgent, setActiveAgent] = useState('sales')
  return (
    <div className="h-full flex flex-col">
      <div className="flex gap-2 mb-4">
        {[{ id: 'sales', label: '✉️ 銷售開發信' }, { id: 'research', label: '🔍 市場研究' }].map(({ id, label }) => (
          <button key={id} onClick={() => setActiveAgent(id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeAgent === id ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}>{label}</button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {activeAgent === 'sales' && <SalesAgentForm model={model} />}
        {activeAgent === 'research' && <ResearchAgentForm model={model} />}
      </div>
    </div>
  )
}
