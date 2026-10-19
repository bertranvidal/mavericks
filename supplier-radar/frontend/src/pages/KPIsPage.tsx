import { useEffect } from 'react'
import { Bell, AlertTriangle, Building2, Globe, Star } from 'lucide-react'
import { AlertsByPriorityChart, SuppliersByCountryChart, TopSuppliersChart } from '../components/Charts'
import { useApp } from '../context'

export default function KPIsPage() {
  const { kpis, alerts, suppliers, loadData } = useApp()

  useEffect(() => { loadData() }, [loadData])

  const bigCard = (title: string, value: string | number, sub: string, icon: React.ReactNode, accent: string) => (
    <div
      className="card p-7 flex flex-col gap-4 transition-transform duration-200 hover:-translate-y-1"
    >
      <div
        className="w-14 h-14 rounded-2xl flex items-center justify-center"
        style={{ background: `${accent}22`, border: `1px solid ${accent}44` }}
      >
        {icon}
      </div>
      <div>
        <p className="text-5xl font-black" style={{ color: accent }}>{value}</p>
        <p className="text-base font-semibold mt-2" style={{ color: '#ccc' }}>{title}</p>
        <p className="text-sm mt-1" style={{ color: '#666' }}>{sub}</p>
      </div>
    </div>
  )

  return (
    <div>
      <div
        className="px-8 py-6 sticky top-0 z-30"
        style={{ background: 'linear-gradient(90deg, #460073 0%, #7B2FBE 50%, #A100FF 100%)', borderBottom: '1px solid rgba(161,0,255,0.4)' }}
      >
        <h1 className="text-2xl font-bold text-white">Key Performance Indicators</h1>
        <p className="text-sm mt-0.5" style={{ color: 'rgba(255,255,255,0.7)' }}>Live risk metrics for Helixa Pharmaceuticals supply chain</p>
      </div>

      <div className="p-8">
        <div className="grid grid-cols-3 gap-5 mb-8">
          {bigCard('Total Alerts Detected', kpis?.total_alerts ?? '—', 'All news events affecting supply chain', <Bell size={26} style={{ color: '#A100FF' }} />, '#A100FF')}
          {bigCard('Critical Alerts', kpis?.critical_alerts ?? '—', 'Require immediate action', <AlertTriangle size={26} style={{ color: '#ff4d4d' }} />, '#ff4d4d')}
          {bigCard('Suppliers at Risk', kpis?.suppliers_at_risk ?? '—', 'Affected by current news events', <Building2 size={26} style={{ color: '#ff8800' }} />, '#ff8800')}
        </div>

        <div className="grid grid-cols-2 gap-5 mb-8">
          {bigCard('Countries Affected', kpis?.countries_affected ?? '—', 'Geographic exposure', <Globe size={26} style={{ color: '#7B2FBE' }} />, '#7B2FBE')}
          <div className="card p-7 flex flex-col gap-4 transition-transform duration-200 hover:-translate-y-1">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(255,77,77,0.15)', border: '1px solid rgba(255,77,77,0.3)' }}>
              <Star size={26} style={{ color: '#ff4d4d' }} />
            </div>
            <div>
              <p className="text-5xl font-black" style={{ color: '#ff4d4d' }}>{kpis?.most_exposed_supplier?.alert_count ?? '—'}</p>
              <p className="text-base font-semibold mt-2" style={{ color: '#ccc' }}>Most Exposed Supplier</p>
              <p className="text-sm mt-1" style={{ color: '#bbb' }}>{kpis?.most_exposed_supplier?.name ?? '—'}</p>
              <p className="text-xs mt-0.5" style={{ color: '#666' }}>{kpis?.most_exposed_supplier?.country ?? ''}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <AlertsByPriorityChart alerts={alerts} />
          <SuppliersByCountryChart alerts={alerts} suppliers={suppliers} />
          <TopSuppliersChart alerts={alerts} suppliers={suppliers} />
        </div>
      </div>
    </div>
  )
}
