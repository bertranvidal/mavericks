import { useEffect, useState } from 'react'
import { Search, Filter, Bell } from 'lucide-react'
import AlertCard from '../components/AlertCard'
import { useApp } from '../context'

const PRIORITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export default function Alerts() {
  const { alerts, loadData } = useApp()
  const [search, setSearch] = useState('')
  const [selectedPriorities, setSelectedPriorities] = useState<string[]>([])

  useEffect(() => {
    loadData()
  }, [loadData])

  const togglePriority = (p: string) => {
    setSelectedPriorities(prev =>
      prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]
    )
  }

  const filtered = alerts.filter(a => {
    const matchPriority = selectedPriorities.length === 0 || selectedPriorities.includes(a.Priority?.toUpperCase())
    const matchSearch = !search ||
      a.Headline?.toLowerCase().includes(search.toLowerCase()) ||
      a.Event_Type?.toLowerCase().includes(search.toLowerCase()) ||
      a.Reasoning?.toLowerCase().includes(search.toLowerCase())
    return matchPriority && matchSearch
  })

  const PRIORITY_COLORS: Record<string, string> = {
    CRITICAL: '#ff4d4d', HIGH: '#ff8800', MEDIUM: '#ffcc00', LOW: '#00d4aa',
  }

  return (
    <div>
      <div
        className="px-8 py-6 sticky top-0 z-30"
        style={{ background: 'linear-gradient(90deg, #460073 0%, #7B2FBE 50%, #A100FF 100%)', borderBottom: '1px solid rgba(161,0,255,0.4)' }}
      >
        <h1 className="text-2xl font-bold text-white">Alerts</h1>
        <p className="text-sm mt-0.5" style={{ color: 'rgba(255,255,255,0.7)' }}>
          {filtered.length} alert{filtered.length !== 1 ? 's' : ''} matching filters
        </p>
      </div>

      <div className="p-8">
        {/* Filter bar */}
        <div className="card p-4 mb-6 flex flex-wrap items-center gap-4">
          <div className="relative flex-1 min-w-52">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#666' }} />
            <input
              type="text"
              placeholder="Search alerts..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm rounded-lg outline-none"
              style={{ background: 'rgba(255,255,255,0.05)', color: '#eee', border: '1px solid rgba(123,47,190,0.3)' }}
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={14} style={{ color: '#666' }} />
            <span className="text-xs" style={{ color: '#666' }}>Priority:</span>
            {PRIORITIES.map(p => (
              <button
                key={p}
                onClick={() => togglePriority(p)}
                className="text-xs px-2.5 py-1 rounded-full font-semibold transition-all duration-150"
                style={{
                  color: PRIORITY_COLORS[p],
                  background: selectedPriorities.includes(p) ? `${PRIORITY_COLORS[p]}30` : 'rgba(255,255,255,0.05)',
                  border: `1px solid ${selectedPriorities.includes(p) ? PRIORITY_COLORS[p] + '88' : 'rgba(255,255,255,0.1)'}`,
                }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Alert list */}
        {filtered.length === 0 ? (
          <div className="text-center py-16" style={{ color: '#444' }}>
            <Bell size={40} className="mx-auto mb-3 opacity-30" />
            <p>No alerts found.</p>
          </div>
        ) : (
          filtered.map((alert, i) => <AlertCard key={alert.News_ID ?? i} alert={alert} />)
        )}
      </div>
    </div>
  )
}
