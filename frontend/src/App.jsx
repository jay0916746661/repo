import { useState } from 'react'
import { Bot, MessageSquare, Workflow } from 'lucide-react'
import ChatInterface from './components/ChatInterface'
import AgentPanel from './components/AgentPanel'
import WorkflowStatus from './components/WorkflowStatus'
import ModelSelector from './components/ModelSelector'

const TABS = [
  { id: 'chat', label: '💬 AI 對話', icon: MessageSquare },
  { id: 'agents', label: '🤖 Agent 工具', icon: Bot },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [model, setModel] = useState('llama3')

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
            <Workflow size={20} />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-none">AI Workflow Dashboard</h1>
            <p className="text-xs text-slate-500 mt-0.5">Powered by Ollama · Local LLM</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <WorkflowStatus />
          <ModelSelector value={model} onChange={setModel} />
        </div>
      </header>

      <div className="border-b border-slate-800 px-6 flex gap-1 pt-2">
        {TABS.map(({ id, label }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === id
                ? 'bg-slate-800 text-white border-t border-x border-slate-700'
                : 'text-slate-500 hover:text-slate-300'
            }`}>{label}</button>
        ))}
      </div>

      <main className="flex-1 overflow-hidden p-6">
        <div className="h-full max-w-5xl mx-auto glass rounded-2xl overflow-hidden">
          {activeTab === 'chat' && <ChatInterface model={model} />}
          {activeTab === 'agents' && (
            <div className="p-6 h-full overflow-y-auto scrollbar-hide">
              <AgentPanel model={model} />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
