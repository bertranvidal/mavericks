import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { AlertResult, Supplier } from '../api'

function parseIds(s: string | undefined): string[] {
  if (!s) return []
  return s.split(';').map(x => x.trim()).filter(Boolean)
}

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: '#ff4d4d',
  HIGH: '#ff8800',
  MEDIUM: '#ffcc00',
  LOW: '#00d4aa',
}

const CHART_BG = { background: 'linear-gradient(145deg, #1a1a2e, #16213e)', border: '1px solid rgba(123,47,190,0.3)', borderRadius: 12 }

function TooltipStyle({ active, payload, label }: { active?: boolean; payload?: { value: number; fill: string }[]; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#1a1a2e', border: '1px solid rgba(123,47,190,0.4)', borderRadius: 8, padding: '8px 12px' }}>
      <p style={{ color: '#bbb', fontSize: 12, marginBottom: 4 }}>{label}</p>
      <p style={{ color: payload[0].fill, fontSize: 14, fontWeight: 600 }}>{payload[0].value}</p>
    </div>
  )
}

export function AlertsByPriorityChart({ alerts }: { alerts: AlertResult[] }) {
  const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
  alerts.forEach(a => {
    const p = a.Priority?.toUpperCase()
    if (p && counts[p] !== undefined) counts[p]++
  })
  const data = Object.entries(counts).map(([name, value]) => ({ name, value }))

  return (
    <div className="p-5" style={CHART_BG}>
      <p className="text-sm font-semibold mb-4" style={{ color: '#ccc' }}>Alerts by Priority</p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 20, top: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
          <XAxis type="number" tick={{ fill: '#666', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="name" tick={{ fill: '#999', fontSize: 12 }} axisLine={false} tickLine={false} width={70} />
          <Tooltip content={<TooltipStyle />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map(entry => (
              <Cell key={entry.name} fill={PRIORITY_COLORS[entry.name] ?? '#888'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function SuppliersByCountryChart({ alerts, suppliers }: { alerts: AlertResult[]; suppliers: Supplier[] }) {
  const atRiskIds = new Set(alerts.flatMap(a => parseIds(a.Affected_Supplier_IDs)))
  const countryCount: Record<string, number> = {}
  suppliers
    .filter(s => atRiskIds.has(s.Supplier_ID) || atRiskIds.has(s.Supplier_Name))
    .forEach(s => {
      countryCount[s.Country] = (countryCount[s.Country] ?? 0) + 1
    })
  const data = Object.entries(countryCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({ name, value }))

  return (
    <div className="p-5" style={CHART_BG}>
      <p className="text-sm font-semibold mb-4" style={{ color: '#ccc' }}>Suppliers at Risk by Country</p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ left: 0, right: 20, top: 0, bottom: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis dataKey="name" tick={{ fill: '#999', fontSize: 11 }} axisLine={false} tickLine={false} angle={-35} textAnchor="end" />
          <YAxis tick={{ fill: '#666', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<TooltipStyle />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="value" fill="#7B2FBE" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => <Cell key={i} fill={i === 0 ? '#A100FF' : '#7B2FBE'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function TopSuppliersChart({ alerts, suppliers }: { alerts: AlertResult[]; suppliers: Supplier[] }) {
  const alertCount: Record<string, number> = {}
  alerts.forEach(a => {
    (parseIds(a.Affected_Supplier_IDs)).forEach(sid => {
      alertCount[sid] = (alertCount[sid] ?? 0) + 1
    })
  })
  const data = Object.entries(alertCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([id, value]) => {
      const s = suppliers.find(s => s.Supplier_ID === id || s.Supplier_Name === id)
      return { name: s?.Supplier_Name ?? id, value }
    })

  return (
    <div className="p-5" style={CHART_BG}>
      <p className="text-sm font-semibold mb-4" style={{ color: '#ccc' }}>Top 5 Most Exposed Suppliers</p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ left: 0, right: 20, top: 0, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis dataKey="name" tick={{ fill: '#999', fontSize: 10 }} axisLine={false} tickLine={false} angle={-35} textAnchor="end" />
          <YAxis tick={{ fill: '#666', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<TooltipStyle />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => <Cell key={i} fill={i === 0 ? '#ff4d4d' : i === 1 ? '#ff8800' : '#7B2FBE'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
