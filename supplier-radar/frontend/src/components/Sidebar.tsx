import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Bell, Building2, GitCompare, BarChart3, Play, Download, Loader2 } from 'lucide-react'
import { useApp } from '../context'
import { exportExcel } from '../api'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/suppliers', label: 'Suppliers', icon: Building2 },
  { to: '/alternatives', label: 'Alternatives', icon: GitCompare },
  { to: '/kpis', label: 'KPIs', icon: BarChart3 },
]

export default function Sidebar() {
  const { source, setSource, mode, setMode, analyse, analyzing } = useApp()

  return (
    <aside
      className="fixed left-0 top-0 h-full w-64 flex flex-col z-40"
      style={{
        background: 'linear-gradient(180deg, #12122a 0%, #0f0f23 100%)',
        borderRight: '1px solid rgba(123,47,190,0.3)',
      }}
    >
      {/* Logo */}
      <div className="p-5 border-b" style={{ borderColor: 'rgba(123,47,190,0.3)' }}>
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #7B2FBE, #A100FF)' }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold" style={{ color: '#A100FF' }}>SUPPLIER RADAR</p>
            <p className="text-xs" style={{ color: '#666' }}>Helixa Pharma</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <p className="px-5 mb-2 text-xs font-semibold uppercase tracking-widest" style={{ color: '#555' }}>Navigation</p>
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-3 mx-2 rounded-lg mb-1 text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'text-white'
                  : 'hover:text-white'
              }`
            }
            style={({ isActive }) =>
              isActive
                ? { background: 'linear-gradient(90deg, rgba(123,47,190,0.4), rgba(161,0,255,0.2))', color: '#fff', borderLeft: '3px solid #A100FF' }
                : { color: '#888' }
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Analysis Controls */}
      <div className="p-4 border-t" style={{ borderColor: 'rgba(123,47,190,0.3)' }}>
        <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: '#555' }}>Analysis</p>

        <div className="mb-3">
          <label className="block text-xs mb-1" style={{ color: '#888' }}>Source</label>
          <select
            value={source}
            onChange={e => setSource(e.target.value)}
            className="w-full text-sm px-3 py-2 rounded-lg outline-none"
            style={{ background: '#1a1a2e', color: '#eee', border: '1px solid rgba(123,47,190,0.4)' }}
          >
            <option value="live">Live</option>
            <option value="test">Test</option>
            <option value="validation">Validation</option>
          </select>
        </div>

        <div className="mb-4">
          <label className="block text-xs mb-1" style={{ color: '#888' }}>Engine</label>
          <select
            value={mode}
            onChange={e => setMode(e.target.value)}
            className="w-full text-sm px-3 py-2 rounded-lg outline-none"
            style={{ background: '#1a1a2e', color: '#eee', border: '1px solid rgba(123,47,190,0.4)' }}
          >
            <option value="rules">Rules</option>
            <option value="models">Models</option>
          </select>
        </div>

        <button
          onClick={analyse}
          disabled={analyzing}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 mb-2"
          style={{
            background: analyzing ? 'rgba(123,47,190,0.3)' : 'linear-gradient(135deg, #7B2FBE, #A100FF)',
            color: '#fff',
            cursor: analyzing ? 'not-allowed' : 'pointer',
          }}
        >
          {analyzing ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
          {analyzing ? 'Analysing...' : 'Analyse'}
        </button>

        <button
          onClick={exportExcel}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all duration-200"
          style={{ background: 'rgba(0,212,170,0.1)', color: '#00d4aa', border: '1px solid rgba(0,212,170,0.3)' }}
        >
          <Download size={14} />
          Export Excel
        </button>
      </div>
    </aside>
  )
}
