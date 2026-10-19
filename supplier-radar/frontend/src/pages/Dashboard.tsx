import { useEffect } from 'react'
import { Bell, AlertTriangle, Building2, Globe, Star } from 'lucide-react'
import KPICard from '../components/KPICard'
import { AlertsByPriorityChart, SuppliersByCountryChart, TopSuppliersChart } from '../components/Charts'
import { useApp } from '../context'

export default function Dashboard() {
  const { kpis, alerts, suppliers, loadData, loading } = useApp()

  useEffect(() => {
    loadData()
  }, [loadData])

  return (
    <div>
      {/* Header */}
      <div
        className="px-8 py-6 sticky top-0 z-30"
        style={{
          background: 'linear-gradient(90deg, #460073 0%, #7B2FBE 50%, #A100FF 100%)',
          borderBottom: '1px solid rgba(161,0,255,0.4)',
        }}
      >
        <h1 className="text-2xl font-bold tracking-tight text-white">Supplier Risk Radar</h1>
        <p className="text-sm mt-0.5" style={{ color: 'rgba(255,255,255,0.7)' }}>
          AI-powered news monitoring for Helixa Pharmaceuticals
        </p>
      </div>

      <div className="p-8">
        {loading && (
          <div className="text-center py-12" style={{ color: '#666' }}>
            <div className="inline-block w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mb-3" />
            <p>Loading data...</p>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4 mb-8">
          <KPICard
            title="Total Alerts"
            value={kpis?.total_alerts ?? '—'}
            icon={Bell}
            accent="#A100FF"
          />
          <KPICard
            title="Critical Alerts"
            value={kpis?.critical_alerts ?? '—'}
            icon={AlertTriangle}
            accent="#ff4d4d"
          />
          <KPICard
            title="Suppliers at Risk"
            value={kpis?.suppliers_at_risk ?? '—'}
            icon={Building2}
            accent="#ff8800"
          />
          <KPICard
            title="Countries Affected"
            value={kpis?.countries_affected ?? '—'}
            icon={Globe}
            accent="#7B2FBE"
          />
          {/* Most Exposed Supplier special card */}
          <div className="card p-5 transition-transform duration-200 hover:-translate-y-0.5">
            <div className="flex items-start justify-between mb-3">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{ background: 'rgba(255,77,77,0.15)', border: '1px solid rgba(255,77,77,0.3)' }}
              >
                <Star size={20} style={{ color: '#ff4d4d' }} />
              </div>
            </div>
            <p className="text-2xl font-bold truncate" style={{ color: '#ff4d4d' }}>
              {kpis?.most_exposed_supplier?.alert_count ?? '—'}
            </p>
            <p className="text-sm font-medium mt-1 truncate" style={{ color: '#ccc' }}>
              {kpis?.most_exposed_supplier?.name ?? 'Most Exposed'}
            </p>
            <p className="text-xs mt-0.5 truncate" style={{ color: '#666' }}>
              {kpis?.most_exposed_supplier?.country ?? ''}
            </p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-3 gap-4">
          <AlertsByPriorityChart alerts={alerts} />
          <SuppliersByCountryChart alerts={alerts} suppliers={suppliers} />
          <TopSuppliersChart alerts={alerts} suppliers={suppliers} />
        </div>
      </div>
    </div>
  )
}
