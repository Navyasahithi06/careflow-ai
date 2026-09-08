interface StatsCardProps {
  title: string
  value: string | number
  icon: string
  color?: string
}

export default function StatsCard({ title, value, icon, color = 'bg-primary-50 text-primary-600' }: StatsCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}
