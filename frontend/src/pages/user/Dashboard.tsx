import StatsCard from '../../components/StatsCard'

export default function UserDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Patient Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of your health management</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Upcoming Appointments" value="—" icon="📅" color="bg-blue-50 text-blue-600" />
        <StatsCard title="Active Tokens" value="—" icon="🎫" color="bg-green-50 text-green-600" />
        <StatsCard title="Total Payments" value="—" icon="💳" color="bg-purple-50 text-purple-600" />
        <StatsCard title="Consultations" value="—" icon="💬" color="bg-orange-50 text-orange-600" />
      </div>
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <p className="text-gray-500 text-center py-8">
          Dashboard data will appear here once appointments and consultations are implemented.
        </p>
      </div>
    </div>
  )
}
