import type { LucideIcon } from 'lucide-react'

interface Props {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  accent?: string
  large?: boolean
}

export default function KPICard({ title, value, subtitle, icon: Icon, accent = '#A100FF', large }: Props) {
  return (
    <div
      className={`card p-${large ? '6' : '5'} flex flex-col gap-3 transition-transform duration-200 hover:-translate-y-0.5`}
      style={{ minWidth: 0 }}
    >
      <div className="flex items-start justify-between">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: `${accent}22`, border: `1px solid ${accent}44` }}
        >
          <Icon size={20} style={{ color: accent }} />
        </div>
        <div
          className="text-xs px-2 py-0.5 rounded-full font-medium"
          style={{ background: `${accent}22`, color: accent }}
        >
          LIVE
        </div>
      </div>
      <div>
        <p className={`font-bold ${large ? 'text-4xl' : 'text-3xl'}`} style={{ color: accent }}>
          {value}
        </p>
        <p className="text-sm font-medium mt-1" style={{ color: '#ccc' }}>{title}</p>
        {subtitle && <p className="text-xs mt-0.5" style={{ color: '#666' }}>{subtitle}</p>}
      </div>
    </div>
  )
}
