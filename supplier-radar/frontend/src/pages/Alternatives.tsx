import { useEffect, useState } from 'react'
import { ArrowRight, AlertCircle } from 'lucide-react'
import { fetchAlternatives } from '../api'
import type { Supplier, Alternative } from '../api'
import { useApp } from '../context'

function SupplierCard({ supplier, variant }: { supplier: Supplier; variant: 'risk' | 'safe' }) {
  const borderColor = variant === 'risk' ? 'rgba(255,77,77,0.5)' : 'rgba(0,212,170,0.5)'
  const accent = variant === 'risk' ? '#ff4d4d' : '#00d4aa'
  return (
    <div
      className="p-4 rounded-xl flex-1"
      style={{
        background: 'linear-gradient(145deg, #1a1a2e, #16213e)',
        border: `1px solid ${borderColor}`,
        boxShadow: `0 0 20px ${borderColor}22`,
      }}
    >
      <p className="text-xs font-semibold mb-1" style={{ color: accent }}>
        {variant === 'risk' ? 'AT RISK' : 'ALTERNATE'}
      </p>
      <p className="font-semibold" style={{ color: '#eee' }}>{supplier.Supplier_Name}</p>
      <p className="text-xs mt-0.5 mb-3" style={{ color: '#666' }}>{supplier.Country}, {supplier.City}</p>
      <div className="space-y-1.5 text-xs">
        <div className="flex justify-between">
          <span style={{ color: '#666' }}>Material</span>
          <span style={{ color: '#bbb' }} className="max-w-32 truncate text-right">{supplier.Material_Supplied}</span>
        </div>
        <div className="flex justify-between">
          <span style={{ color: '#666' }}>Quality Score</span>
          <span style={{ color: '#bbb' }}>{supplier.Quality_Score}</span>
        </div>
        <div className="flex justify-between">
          <span style={{ color: '#666' }}>Inventory</span>
          <span style={{ color: supplier.Inventory_Cover_Days < 30 ? '#ff8800' : '#bbb' }}>{supplier.Inventory_Cover_Days}d</span>
        </div>
      </div>
    </div>
  )
}

function AlternativeRow({ supplier }: { supplier: Supplier }) {
  const [alts, setAlts] = useState<Alternative[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchAlternatives(supplier.Supplier_ID)
      .then(setAlts)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [supplier.Supplier_ID])

  if (loading) return <div className="card p-5 mb-4 animate-pulse" style={{ height: 120 }} />

  const withDetails = alts.filter(a => a.alternate_supplier_id && a.alternate_supplier_details)
  if (!withDetails.length) return null

  return (
    <div className="card p-5 mb-4">
      <p className="text-xs font-semibold mb-3" style={{ color: '#888' }}>
        Materials: {alts.map(a => a.material).join(', ')}
      </p>
      <div className="flex items-center gap-4">
        <SupplierCard supplier={supplier} variant="risk" />
        <div className="shrink-0 flex flex-col items-center gap-1">
          <ArrowRight size={20} style={{ color: '#A100FF' }} />
        </div>
        <div className="flex-1 flex gap-3">
          {withDetails.slice(0, 2).map(alt => (
            <SupplierCard key={alt.alternate_supplier_id} supplier={alt.alternate_supplier_details as Supplier} variant="safe" />
          ))}
        </div>
      </div>
    </div>
  )
}

function parseIds(s: string | undefined): string[] {
  if (!s) return []
  return s.split(';').map(x => x.trim()).filter(Boolean)
}

export default function Alternatives() {
  const { suppliers, alerts, loadData, focusedSupplierId } = useApp()

  useEffect(() => { loadData() }, [loadData])

  const atRiskIds = new Set(alerts.flatMap(a => parseIds(a.Affected_Supplier_IDs)))
  const atRiskSuppliers = suppliers.filter(
    s => atRiskIds.has(s.Supplier_ID) && s.Approved_Alternate_ID
  )

  const focused = focusedSupplierId
    ? suppliers.filter(s => s.Supplier_ID === focusedSupplierId)
    : null

  const displaySuppliers = focused?.length ? focused : atRiskSuppliers

  return (
    <div>
      <div
        className="px-8 py-6 sticky top-0 z-30"
        style={{ background: 'linear-gradient(90deg, #460073 0%, #7B2FBE 50%, #A100FF 100%)', borderBottom: '1px solid rgba(161,0,255,0.4)' }}
      >
        <h1 className="text-2xl font-bold text-white">Alternatives</h1>
        <p className="text-sm mt-0.5" style={{ color: 'rgba(255,255,255,0.7)' }}>
          {displaySuppliers.length} at-risk supplier{displaySuppliers.length !== 1 ? 's' : ''} with approved alternates
          {focused?.length ? ' (filtered)' : ''}
        </p>
      </div>

      <div className="p-8">
        {displaySuppliers.length === 0 ? (
          <div className="text-center py-16" style={{ color: '#444' }}>
            <AlertCircle size={40} className="mx-auto mb-3 opacity-30" />
            <p>No at-risk suppliers with approved alternates found.</p>
            <p className="text-xs mt-1" style={{ color: '#333' }}>Run an analysis first to detect risks.</p>
          </div>
        ) : (
          displaySuppliers.map(s => <AlternativeRow key={s.Supplier_ID} supplier={s} />)
        )}
      </div>
    </div>
  )
}
