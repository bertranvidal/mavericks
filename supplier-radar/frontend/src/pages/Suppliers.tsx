import { useEffect, useState } from 'react'
import { Building2, X } from 'lucide-react'
import type { Supplier } from '../api'
import { useApp } from '../context'

export default function Suppliers() {
  const { suppliers, alerts, loadData } = useApp()
  const [selected, setSelected] = useState<Supplier | null>(null)

  useEffect(() => { loadData() }, [loadData])

  const atRiskIds = new Set(alerts.flatMap(a => a.Affected_Suppliers ?? []))
  const isAtRisk = (s: Supplier) => atRiskIds.has(s.Supplier_ID) || atRiskIds.has(s.Supplier_Name)

  const fmt = (n: number) => n != null ? `€${n.toLocaleString()}` : '—'

  return (
    <div>
      <div
        className="px-8 py-6 sticky top-0 z-30"
        style={{ background: 'linear-gradient(90deg, #460073 0%, #7B2FBE 50%, #A100FF 100%)', borderBottom: '1px solid rgba(161,0,255,0.4)' }}
      >
        <h1 className="text-2xl font-bold text-white">Suppliers</h1>
        <p className="text-sm mt-0.5" style={{ color: 'rgba(255,255,255,0.7)' }}>{suppliers.length} suppliers in database</p>
      </div>

      <div className="p-8">
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(123,47,190,0.3)', background: 'rgba(123,47,190,0.1)' }}>
                {['ID', 'Name', 'Country', 'City', 'Material', 'Annual Spend', 'Single Source', 'Criticality', 'Inv. Days', 'Status'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide" style={{ color: '#888' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {suppliers.map(s => {
                const risk = isAtRisk(s)
                return (
                  <tr
                    key={s.Supplier_ID}
                    onClick={() => setSelected(s)}
                    className="cursor-pointer transition-colors duration-150"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(123,47,190,0.08)')}
                    onMouseLeave={e => (e.currentTarget.style.background = '')}
                  >
                    <td className="px-4 py-3" style={{ color: '#888' }}>{s.Supplier_ID}</td>
                    <td className="px-4 py-3 font-medium" style={{ color: '#eee' }}>{s.Supplier_Name}</td>
                    <td className="px-4 py-3" style={{ color: '#bbb' }}>{s.Country}</td>
                    <td className="px-4 py-3" style={{ color: '#888' }}>{s.City}</td>
                    <td className="px-4 py-3 max-w-32 truncate" style={{ color: '#bbb' }}>{s.Material_Supplied}</td>
                    <td className="px-4 py-3" style={{ color: '#bbb' }}>{fmt(s.Annual_Spend_EUR)}</td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs px-2 py-0.5 rounded-full"
                        style={s.Single_Source === 'Yes' ? { color: '#ff4d4d', background: 'rgba(255,77,77,0.1)', border: '1px solid rgba(255,77,77,0.3)' } : { color: '#00d4aa', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.3)' }}
                      >
                        {s.Single_Source}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs px-2 py-0.5 rounded-full"
                        style={s.Criticality === 'Critical' ? { color: '#ff4d4d', background: 'rgba(255,77,77,0.1)' } : s.Criticality === 'High' ? { color: '#ff8800', background: 'rgba(255,136,0,0.1)' } : { color: '#888', background: 'rgba(255,255,255,0.05)' }}
                      >
                        {s.Criticality}
                      </span>
                    </td>
                    <td className="px-4 py-3" style={{ color: s.Inventory_Cover_Days < 30 ? '#ff8800' : '#bbb' }}>{s.Inventory_Cover_Days}</td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs px-2 py-0.5 rounded-full font-semibold"
                        style={risk ? { color: '#ff4d4d', background: 'rgba(255,77,77,0.15)', border: '1px solid rgba(255,77,77,0.4)' } : { color: '#00d4aa', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.3)' }}
                      >
                        {risk ? 'AT RISK' : 'OK'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail drawer */}
      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-end"
          style={{ background: 'rgba(0,0,0,0.6)' }}
          onClick={() => setSelected(null)}
        >
          <div
            className="w-96 h-full overflow-y-auto p-6"
            style={{ background: '#12122a', borderLeft: '1px solid rgba(123,47,190,0.4)' }}
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(123,47,190,0.2)' }}>
                  <Building2 size={18} style={{ color: '#A100FF' }} />
                </div>
                <div>
                  <p className="font-semibold" style={{ color: '#eee' }}>{selected.Supplier_Name}</p>
                  <p className="text-xs" style={{ color: '#666' }}>{selected.Supplier_ID}</p>
                </div>
              </div>
              <button onClick={() => setSelected(null)} style={{ color: '#666' }}>
                <X size={18} />
              </button>
            </div>

            {[
              ['Category', selected.Category],
              ['Material', selected.Material_Supplied],
              ['Country', selected.Country],
              ['City', selected.City],
              ['Annual Spend', fmt(selected.Annual_Spend_EUR)],
              ['Single Source', selected.Single_Source],
              ['Approved Alternate', selected.Approved_Alternate_ID ?? 'None'],
              ['Inventory Cover', `${selected.Inventory_Cover_Days} days`],
              ['Criticality', selected.Criticality],
              ['Quality Score', selected.Quality_Score],
            ].map(([label, value]) => (
              <div key={label as string} className="flex justify-between py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                <span className="text-xs" style={{ color: '#666' }}>{label}</span>
                <span className="text-sm font-medium" style={{ color: '#ccc' }}>{value ?? '—'}</span>
              </div>
            ))}

            <div className="mt-4 p-3 rounded-lg" style={{ background: isAtRisk(selected) ? 'rgba(255,77,77,0.1)' : 'rgba(0,212,170,0.1)', border: `1px solid ${isAtRisk(selected) ? 'rgba(255,77,77,0.3)' : 'rgba(0,212,170,0.3)'}` }}>
              <p className="text-sm font-semibold" style={{ color: isAtRisk(selected) ? '#ff4d4d' : '#00d4aa' }}>
                {isAtRisk(selected) ? 'AT RISK — active alerts detected' : 'No active alerts'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
