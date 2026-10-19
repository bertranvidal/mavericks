import { useState } from 'react'
import { ChevronDown, ChevronUp, ArrowRight } from 'lucide-react'
import type { AlertResult } from '../api'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context'

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: '#ff4d4d',
  HIGH: '#ff8800',
  MEDIUM: '#ffcc00',
  LOW: '#00d4aa',
}

interface Props {
  alert: AlertResult
}

export default function AlertCard({ alert }: Props) {
  const [expanded, setExpanded] = useState(false)
  const navigate = useNavigate()
  const { setFocusedSupplierId } = useApp()
  const color = PRIORITY_COLORS[alert.Priority?.toUpperCase()] ?? '#888'

  const handleViewAlternatives = (supplierId: string) => {
    setFocusedSupplierId(supplierId)
    navigate('/alternatives')
  }

  return (
    <div
      className="card mb-3 overflow-hidden transition-all duration-200"
      style={{ borderLeft: `4px solid ${color}` }}
    >
      <div
        className="flex items-center justify-between p-4 cursor-pointer"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0"
            style={{ background: `${color}22`, color, border: `1px solid ${color}44` }}
          >
            {alert.Priority}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate" style={{ color: '#eee' }}>{alert.Headline}</p>
            <p className="text-xs mt-0.5" style={{ color: '#777' }}>
              {alert.News_ID} &bull; {alert.Event_Type}
            </p>
          </div>
        </div>
        <div className="flex-shrink-0 ml-3" style={{ color: '#666' }}>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t" style={{ borderColor: 'rgba(123,47,190,0.2)' }}>
          <p className="text-sm mt-3 mb-3 leading-relaxed" style={{ color: '#bbb' }}>{alert.Summary}</p>

          <div className="grid grid-cols-2 gap-3 mb-3 text-xs">
            <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p style={{ color: '#666' }}>Risk Flag</p>
              <p style={{ color: alert.Risk_Flag === 'YES' ? '#ff4d4d' : '#00d4aa' }}>{alert.Risk_Flag}</p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p style={{ color: '#666' }}>Urgent</p>
              <p style={{ color: alert.Urgency_Flag === 'YES' ? '#ff8800' : '#00d4aa' }}>{alert.Urgency_Flag}</p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p style={{ color: '#666' }}>Spend at Risk</p>
              <p style={{ color: '#eee' }}>€{(alert.Spend_At_Risk_EUR ?? 0).toLocaleString()}</p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p style={{ color: '#666' }}>Inventory Cover</p>
              <p style={{ color: '#eee' }}>{alert.Inventory_Cover_Days} days</p>
            </div>
          </div>

          {alert.Affected_Suppliers?.length > 0 && (
            <div className="mb-3">
              <p className="text-xs mb-2" style={{ color: '#666' }}>Affected Suppliers</p>
              <div className="flex flex-wrap gap-2">
                {alert.Affected_Suppliers.map(s => (
                  <span
                    key={s}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{ background: 'rgba(161,0,255,0.15)', color: '#c084fc', border: '1px solid rgba(161,0,255,0.3)' }}
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {alert.Recommended_Action && (
            <div className="mb-3 p-3 rounded-lg text-xs" style={{ background: 'rgba(123,47,190,0.1)', border: '1px solid rgba(123,47,190,0.2)' }}>
              <p className="font-semibold mb-1" style={{ color: '#A100FF' }}>Recommended Action</p>
              <p style={{ color: '#ccc' }}>{alert.Recommended_Action}</p>
            </div>
          )}

          {alert.Affected_Suppliers?.length > 0 && (
            <button
              onClick={() => handleViewAlternatives(alert.Affected_Suppliers[0])}
              className="flex items-center gap-1.5 text-xs font-semibold py-1.5 px-3 rounded-lg transition-colors duration-200"
              style={{ background: 'rgba(0,212,170,0.1)', color: '#00d4aa', border: '1px solid rgba(0,212,170,0.3)' }}
            >
              View Alternatives <ArrowRight size={12} />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
