import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900">
      <div className="flex flex-col items-center justify-center min-h-screen px-4 text-center">
        <div className="mb-8">
          <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
            <span className="text-4xl">🏥</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">CareFlow AI</h1>
          <p className="text-xl text-primary-100 max-w-lg">
            AI-Powered Hospital Management Platform
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 mt-8">
          <Link
            to="/user/login"
            className="px-8 py-4 bg-white text-primary-700 font-semibold rounded-xl hover:bg-primary-50 transition-colors shadow-lg"
          >
            Patient Portal
          </Link>
          <Link
            to="/admin/login"
            className="px-8 py-4 bg-primary-800 text-white font-semibold rounded-xl hover:bg-primary-900 transition-colors border border-primary-600 shadow-lg"
          >
            Admin Portal
          </Link>
        </div>
      </div>
    </div>
  )
}
